#!/usr/bin/env python3
"""Seasonal palette manager. Python >=3.11, standard library only."""
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

from render import dump_toml, write_profiles

SEASONS=("winter","spring","summer","autumn")
HOME=Path.home()
CONFIG=HOME/".config"
ROOT=CONFIG/"colorscheme"
STATE=Path(os.environ.get("XDG_STATE_HOME",HOME/".local/state"))/"colorscheme"

def season_for_date(date):
    return SEASONS[(date.month % 12)//3]

def selected_season(mode,date):
    if mode.get("mode")=="manual":
        season=mode.get("season")
        if season not in SEASONS:
            raise ValueError("Invalid manual season in mode.json")
        return season
    return season_for_date(date)

def atomic(path,text,mode=0o600):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,"w") as stream:
            stream.write(text)
        os.chmod(tmp,mode)
        os.replace(tmp,path)
    finally:
        if os.path.lexists(tmp):
            os.unlink(tmp)

def switch_link(root,season):
    if season not in SEASONS or not (root/season).is_dir():
        raise ValueError("Missing/invalid season: "+season)
    current=root/"current"
    if current.exists() and not current.is_symlink():
        raise ValueError("current exists and is not a symlink")
    tmp=root/(".current-"+str(os.getpid()))
    try:
        tmp.symlink_to(season)
        os.replace(tmp,current)
    finally:
        if tmp.is_symlink():
            tmp.unlink()

def run(args):
    try:
        return subprocess.run(args,check=True,capture_output=True,text=True,
                              timeout=10)
    except (OSError,subprocess.SubprocessError) as error:
        print("Warning: "+str(error),file=sys.stderr)
        return None

def gnome(palette):
    if not shutil.which("gsettings"):
        return
    run(["gsettings","set","org.gnome.desktop.interface","color-scheme","prefer-dark"])
    run(["gsettings","set","org.gnome.desktop.interface","accent-color",
         palette["gnome_native"]])
    uuid="user-accent-colors@fabito02"
    for base in (HOME/".local/share/gnome-shell/extensions",
                 Path("/usr/share/gnome-shell/extensions")):
        schemas=base/uuid/"schemas"
        if not (schemas/"gschemas.compiled").exists():
            continue
        prefix=["gsettings","--schemadir",str(schemas),"set",
                "org.gnome.shell.extensions.chromaleon"]
        for key,value in (("gnome-colors","false"),("accent-color",palette["accent"]),
                          ("custom-color","true")):
            run(prefix+[key,value])
        break

def regenerate():
    palettes=json.loads((ROOT/"palettes.json").read_text())
    staging=Path(tempfile.mkdtemp(prefix=".render-",dir=ROOT))
    try:
        write_profiles(staging,palettes)
        # Check TOML and Python themes before replacing installed files.
        for season in SEASONS:
            for name in ("alacritty.toml","starship.toml"):
                tomllib.loads((staging/season/name).read_text())
            compile((staging/season/"ranger.py").read_text(),"ranger.py","exec")
        template=ROOT/"tmux-template.conf"
        if template.exists():
            import re
            old={}
            for p in palettes.values():
                old.update({v.lower():k for k,v in p.items() if v.startswith("#")})
            for season in SEASONS:
                p=palettes[season]
                content=re.sub(r"#[0-9a-fA-F]{6}",
                    lambda m:p.get(old.get(m[0].lower(),""),m[0]),
                    template.read_text())
                with (staging/season/"tmux.conf").open("a") as stream:
                    stream.write("\n# Migrated status formats and color options\n"+content)
        for season in SEASONS:
            target=ROOT/season
            target.mkdir(exist_ok=True)
            for path in (staging/season).iterdir():
                atomic(target/path.name,path.read_text())
    finally:
        shutil.rmtree(staging)

def apply(mode=None):
    mode=mode if mode is not None else json.loads((STATE/"mode.json").read_text())
    season=selected_season(mode,dt.date.today())
    target=ROOT/season
    base=tomllib.loads((CONFIG/"starship/base.toml").read_text())
    fragment=tomllib.loads((target/"starship.toml").read_text())
    base.setdefault("palettes",{}).update(fragment["palettes"])
    base["palette"]="seasonal"
    rendered=dump_toml(base)
    tomllib.loads(rendered)
    switch_link(ROOT,season)
    atomic(CONFIG/"starship.toml",rendered)
    alacritty=CONFIG/"alacritty/alacritty.toml"
    if alacritty.exists():
        alacritty.touch()
    palette=json.loads((target/"palette.json").read_text())
    gnome(palette)
    if shutil.which("tmux"):
        sessions=subprocess.run(["tmux","list-sessions"],capture_output=True)
        if sessions.returncode==0:
            run(["tmux","source-file",str(target/"tmux.conf")])
    runtime=os.environ.get("XDG_RUNTIME_DIR")
    if runtime and shutil.which("nvim"):
        for socket in (Path(runtime)/"colorscheme").glob("nvim-*.sock"):
            if socket.is_socket():
                run(["nvim","--server",str(socket),"--remote-expr",
                     'execute("doautocmd <nomodeline> User SeasonalColorscheme")'])
    atomic(STATE/"applied.json",json.dumps({
        "season":season,"mode":mode.get("mode","auto"),
        "applied_at":dt.datetime.now().astimezone().isoformat()},indent=2)+"\n")
    print("Colorscheme: "+season+" ("+mode.get("mode","auto")+")")

def set_mode(command):
    mode={"mode":"auto"} if command=="auto" else {"mode":"manual","season":command}
    # Check required files before persisting a new selection.
    season=selected_season(mode,dt.date.today())
    if not (ROOT/season/"palette.json").is_file():
        raise ValueError("Install profiles first")
    apply(mode)
    atomic(STATE/"mode.json",json.dumps(mode)+"\n")

def restore(backup):
    backup=Path(backup).expanduser().resolve()
    allowed=(STATE/"backups").resolve()
    if backup.parent!=allowed:
        raise ValueError("Backup must be directly inside "+str(allowed))
    manifest=json.loads((backup/"manifest.json").read_text())
    # Only paths selected by our installer may be restored.
    for relative in manifest:
        if relative not in managed_paths():
            raise ValueError("Unexpected backup path: "+relative)
    if shutil.which("systemctl"):
        run(["systemctl","--user","disable","--now","colorscheme.timer",
             "colorscheme-login.service"])
    recovery=STATE/"before-restore"/dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    recovery.mkdir(parents=True)
    for relative,existed in manifest.items():
        dest=HOME/relative
        if dest.exists() or dest.is_symlink():
            save=recovery/relative
            save.parent.mkdir(parents=True,exist_ok=True)
            shutil.move(str(dest),save)
        if existed:
            dest.parent.mkdir(parents=True,exist_ok=True)
            src=backup/relative
            if src.is_dir() and not src.is_symlink():
                shutil.copytree(src,dest,symlinks=True)
            elif src.is_symlink():
                dest.symlink_to(os.readlink(src))
            else:
                shutil.copy2(src,dest)
    if shutil.which("systemctl"):
        run(["systemctl","--user","daemon-reload"])
    settings=backup/"gnome-settings.json"
    if settings.exists():
        for args,value in json.loads(settings.read_text()):
            run(args+["set",*value])
    print("Restored files. Restart Ranger, Neovim and Zsh; reload tmux if needed.")
    print("Replaced configuration preserved in "+str(recovery))

def managed_paths():
    return [
        ".config/colorscheme",".local/bin/colorscheme",
        ".config/alacritty/alacritty.toml",".config/starship.toml",
        ".config/starship/base.toml",".tmux.conf",".config/tmux/tmux.conf",
        ".zshrc",".config/ranger/rc.conf",
        ".config/ranger/colorschemes/seasonal.py",
        ".config/ranger/colorschemes/__init__.py",
        ".config/nvim/plugin/seasonal-theme.lua",
        ".config/systemd/user/colorscheme.service",
        ".config/systemd/user/colorscheme@.service",
        ".config/systemd/user/colorscheme-login.service",
        ".config/systemd/user/colorscheme.timer"]

def main():
    if os.geteuid()==0:
        raise SystemExit("Run as your desktop user, without sudo.")
    if Path(os.environ.get("XDG_CONFIG_HOME",CONFIG)).expanduser()!=CONFIG:
        raise SystemExit("This migration requires the standard ~/.config path.")
    STATE.mkdir(parents=True,exist_ok=True)
    with (STATE/"lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        args=sys.argv[1:]
        command=args[0] if args else "status"
        if command=="status":
            for name in ("mode.json","applied.json"):
                path=STATE/name
                print(name+": "+(path.read_text().strip() if path.exists() else "not installed"))
        elif command=="restore" and len(args)==2:
            restore(args[1])
        elif command=="apply" and len(args)==1:
            apply()
        elif command in ("auto",*SEASONS) and len(args)==1:
            set_mode(command)
        elif command=="regenerate" and len(args)==1:
            regenerate()
            apply()
        else:
            raise SystemExit("Usage: colorscheme [status|apply|auto|winter|spring|summer|autumn|regenerate|restore BACKUP]")

if __name__=="__main__":
    try:
        main()
    except (ValueError,OSError,KeyError,tomllib.TOMLDecodeError) as error:
        raise SystemExit(str(error))
