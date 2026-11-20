#!/usr/bin/env python3
"""Migrate the current user's configuration with a reversible backup."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
import colorscheme as cs
from render import dump_toml

SOURCE=Path(__file__).resolve().parent

def read(path):
    return path.read_text() if path.exists() else ""

def block(text,body):
    begin="# BEGIN seasonal-colorscheme"
    end="# END seasonal-colorscheme"
    if begin in text or end in text:
        raise ValueError("An existing seasonal-colorscheme hook needs review.")
    return text.rstrip()+"\n\n"+begin+"\n"+body.rstrip()+"\n"+end+"\n"

def logical_lines(text):
    pending=""
    for line in text.splitlines(keepends=True):
        pending+=line
        if line.rstrip().endswith("\\"):
            continue
        yield pending
        pending=""
    if pending:
        raise ValueError("Unterminated tmux continuation")

def preflight():
    if os.geteuid()==0:
        raise ValueError("Run without sudo.")
    if os.environ.get("ZDOTDIR",str(cs.HOME))!=str(cs.HOME):
        raise ValueError("Custom ZDOTDIR requires manual migration.")
    if Path(os.environ.get("XDG_CONFIG_HOME",cs.CONFIG)).expanduser()!=cs.CONFIG:
        raise ValueError("Custom XDG_CONFIG_HOME requires manual migration.")
    configured=os.environ.get("STARSHIP_CONFIG")
    if configured and Path(configured).expanduser()!=cs.CONFIG/"starship.toml":
        raise ValueError("Custom STARSHIP_CONFIG requires manual migration.")
    if cs.ROOT.exists() or cs.ROOT.is_symlink():
        raise ValueError(str(cs.ROOT)+" already exists; inspect before installing again.")
    for relative in cs.managed_paths():
        p=cs.HOME/relative
        if p.is_dir() and relative!=".config/colorscheme":
            raise ValueError("Expected a file, found directory: "+str(p))
    a=tomllib.loads(read(cs.CONFIG/"alacritty/alacritty.toml"))
    s=tomllib.loads(read(cs.CONFIG/"starship.toml"))
    a.pop("colors",None)
    general=a.setdefault("general",{})
    imports=general.setdefault("import",[])
    legacy=a.pop("import",[])
    if not isinstance(imports,list) or not isinstance(legacy,list):
        raise ValueError("Unexpected Alacritty import syntax")
    general["import"]=list(dict.fromkeys(legacy+imports+
        [str(cs.ROOT/"current/alacritty.toml")]))
    a_text=dump_toml(a)
    tomllib.loads(a_text)
    old_palette=s.get("palette")
    if old_palette and old_palette in s.get("palettes",{}):
        s["palettes"].pop(old_palette)
    s["palette"]="seasonal"
    s_text=dump_toml(s)
    tomllib.loads(s_text)
    tmux=cs.HOME/".tmux.conf"
    if not tmux.exists() and (cs.CONFIG/"tmux/tmux.conf").exists():
        tmux=cs.CONFIG/"tmux/tmux.conf"
    kept,theme=[],[]
    for line in logical_lines(read(tmux)):
        (theme if re.search(r"#[0-9a-fA-F]{6}",line) else kept).append(line)
    tmux_text=block("".join(kept),
        'source-file "$HOME/.config/colorscheme/current/tmux.conf"')
    zsh_text=block(read(cs.HOME/".zshrc"),
        'source "$HOME/.config/colorscheme/hooks/zsh.zsh"')
    ranger_text=block(read(cs.CONFIG/"ranger/rc.conf"),"set colorscheme seasonal")
    return a_text,s_text,tmux,tmux_text,"".join(theme),zsh_text,ranger_text

def backup():
    directory=cs.STATE/"backups"/dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    directory.mkdir(parents=True,mode=0o700)
    manifest={}
    for relative in cs.managed_paths():
        src=cs.HOME/relative
        exists=src.exists() or src.is_symlink()
        manifest[relative]=exists
        if exists:
            dest=directory/relative
            dest.parent.mkdir(parents=True,exist_ok=True)
            if src.is_symlink():
                dest.symlink_to(os.readlink(src))
            elif src.is_dir():
                shutil.copytree(src,dest,symlinks=True)
            else:
                shutil.copy2(src,dest)
    cs.atomic(directory/"manifest.json",json.dumps(manifest,indent=2))
    settings=[]
    if shutil.which("gsettings"):
        prefixes=[["gsettings"]]
        for base in (cs.HOME/".local/share/gnome-shell/extensions",
                     Path("/usr/share/gnome-shell/extensions")):
            schema=base/"user-accent-colors@fabito02/schemas"
            if (schema/"gschemas.compiled").exists():
                prefixes.append(["gsettings","--schemadir",str(schema)])
                break
        pairs=[(prefixes[0],"org.gnome.desktop.interface","color-scheme"),
               (prefixes[0],"org.gnome.desktop.interface","accent-color")]
        if len(prefixes)>1:
            pairs += [(prefixes[1],"org.gnome.shell.extensions.chromaleon",key)
                      for key in ("gnome-colors","accent-color","custom-color")]
        for prefix,schema,key in pairs:
            r=cs.run(prefix+["get",schema,key])
            if r:
                settings.append((prefix,[schema,key,r.stdout.strip()]))
    cs.atomic(directory/"gnome-settings.json",json.dumps(settings))
    return directory

def install(no_systemd=False):
    a,s,tmux,t,template,z,r=preflight()
    cs.STATE.mkdir(parents=True,exist_ok=True)
    directory=backup()
    print("Backup: "+str(directory),flush=True)
    print("Recovery: python3 "+str(SOURCE/"colorscheme.py")+" restore "+str(directory),flush=True)
    cs.ROOT.mkdir(mode=0o700)
    (cs.ROOT/"bin").mkdir()
    for name in ("colorscheme.py","render.py"):
        shutil.copy2(SOURCE/name,cs.ROOT/"bin"/name)
    shutil.copy2(SOURCE/"palettes.json",cs.ROOT/"palettes.json")
    shutil.copytree(SOURCE/"hooks",cs.ROOT/"hooks")
    cs.atomic(cs.ROOT/"tmux-template.conf",template)
    cs.regenerate()
    cs.atomic(cs.CONFIG/"starship/base.toml",s)
    cs.atomic(cs.CONFIG/"alacritty/alacritty.toml",a)
    cs.atomic(tmux,t)
    cs.atomic(cs.HOME/".zshrc",z)
    cs.atomic(cs.CONFIG/"ranger/rc.conf",r)
    ranger_dir=cs.CONFIG/"ranger/colorschemes"
    ranger_dir.mkdir(parents=True,exist_ok=True)
    init=ranger_dir/"__init__.py"
    if not init.exists():
        cs.atomic(init,"")
    link=ranger_dir/"seasonal.py"
    if link.exists() or link.is_symlink():
        link.unlink()
    cs.atomic(link, 'from pathlib import Path\n_theme = Path.home() / ".config/colorscheme/current/ranger.py"\nexec(compile(_theme.read_text(), str(_theme), "exec"))\n')
    cs.atomic(cs.CONFIG/"nvim/plugin/seasonal-theme.lua",
              (SOURCE/"hooks/nvim.lua").read_text())
    launcher='#!/bin/sh\nexec /usr/bin/python3 "$HOME/.config/colorscheme/bin/colorscheme.py" "$@"\n'
    cs.atomic(cs.HOME/".local/bin/colorscheme",launcher,0o700)
    for unit in (SOURCE/"units").glob("*"):
        cs.atomic(cs.CONFIG/"systemd/user"/unit.name,unit.read_text())
    cs.atomic(cs.STATE/"mode.json",json.dumps({"mode":"auto"})+"\n")
    cs.apply()
    if not no_systemd:
        for args in [
            ["systemctl","--user","daemon-reload"],
            ["systemctl","--user","enable","--now","colorscheme.timer",
             "colorscheme-login.service"]]:
            subprocess.run(args,check=True)
    print("Installed. Run: exec zsh")
    print("Reopen Neovim and Ranger once to load their hooks.")
    print("Rollback: ~/.local/bin/colorscheme restore "+str(directory))
    return directory

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--no-systemd",action="store_true",
                        help="Install without activating user units")
    args=parser.parse_args()
    try:
        install(args.no_systemd)
    except Exception as error:
        print("Installation failed: "+str(error),file=sys.stderr)
        print("If a backup path was printed, use restore as documented.",file=sys.stderr)
        sys.exit(1)
