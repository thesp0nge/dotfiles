"""Theme-only renderers; no third-party Python dependencies."""
import json
from pathlib import Path

def nearest(value):
    rgb = bytes.fromhex(value.removeprefix("#"))
    levels = (0,95,135,175,215,255)
    colors = {16+36*r+6*g+b:(rv,gv,bv)
              for r,rv in enumerate(levels) for g,gv in enumerate(levels)
              for b,bv in enumerate(levels)}
    colors.update({232+i:(8+10*i,)*3 for i in range(24)})
    return min(colors,key=lambda n:sum((a-b)**2 for a,b in zip(rgb,colors[n])))

def toml_value(value):
    if isinstance(value,str):
        return json.dumps(value,ensure_ascii=False)
    if isinstance(value,bool):
        return str(value).lower()
    if isinstance(value,(int,float)):
        return repr(value)
    if isinstance(value,list):
        return "["+", ".join(toml_value(v) for v in value)+"]"
    if isinstance(value,dict):
        return "{ "+", ".join(json.dumps(k)+" = "+toml_value(v)
                             for k,v in value.items())+" }"
    raise ValueError("Unsupported TOML value: "+repr(value))

def dump_toml(data):
    lines=[]
    def table(obj,path):
        scalars={k:v for k,v in obj.items() if not isinstance(v,dict)}
        if path:
            lines.append("["+".".join(json.dumps(k) for k in path)+"]")
        for key,value in scalars.items():
            lines.append(json.dumps(key)+" = "+toml_value(value))
        if scalars or path:
            lines.append("")
        for key,value in obj.items():
            if isinstance(value,dict):
                table(value,path+[key])
    table(data,[])
    return "\n".join(lines)+"\n"

def render(p):
    out={}
    ansi=dict(black=p["panel"],red=p["red"],green=p["green"],
              yellow=p["secondary"],blue=p["blue"],magenta=p["warm"],
              cyan=p["cyan"],white=p["white"])
    bright={k:p.get("bright_"+("warm" if k=="magenta" else k),v)
            for k,v in ansi.items()}
    bright.update(black=p["dim"],white=p["bright_white"])
    out["alacritty.toml"]=dump_toml({"colors":{
        "primary":{"background":p["background"],"foreground":p["foreground"]},
        "cursor":{"text":p["background"],"cursor":p["accent"]},
        "selection":{"text":p["foreground"],"background":p["selection"]},
        "normal":ansi,"bright":bright}})
    options={
        "status-style":f'fg={p["foreground"]},bg={p["panel"]}',
        "message-style":f'fg={p["background"]},bg={p["accent"]}',
        "message-command-style":f'fg={p["foreground"]},bg={p["panel"]}',
        "mode-style":f'fg={p["foreground"]},bg={p["selection"]}',
        "pane-border-style":f'fg={p["dim"]}',
        "pane-active-border-style":f'fg={p["accent"]}',
        "status-left-style":f'fg={p["accent"]},bg={p["panel"]},bold',
        "status-right-style":f'fg={p["muted"]},bg={p["panel"]}',
        "window-status-style":f'fg={p["muted"]},bg={p["panel"]}',
        "window-status-current-style":f'fg={p["accent"]},bg={p["selection"]},bold',
        "window-status-activity-style":f'fg={p["secondary"]},bg={p["panel"]}',
        "display-panes-active-colour":p["accent"],
        "display-panes-colour":p["dim"]}
    out["tmux.conf"]="".join(f'set -g {k} "{v}"\n' for k,v in options.items())
    out["starship.toml"]=dump_toml({"palettes":{"seasonal":{
        k:v for k,v in p.items() if k!="gnome_native"}}})
    dc={"DIR":"accent","LINK":"blue","ORPHAN":"red","MISSING":"red",
        "EXEC":"green","FIFO":"secondary","SOCK":"warm","BLK":"secondary",
        "CHR":"secondary","SETUID":"red","SETGID":"red",
        "*.zip":"secondary","*.gz":"secondary","*.tar":"secondary",
        "*.xz":"secondary","*.7z":"secondary","*.rpm":"secondary",
        "*.png":"warm","*.jpg":"warm","*.mp4":"warm","*.mp3":"warm",
        "*.pdf":"blue","*.md":"blue","*.bak":"dim","*~":"dim"}
    out["dircolors"]="TERM *\n"+"\n".join(
        kind+" 38;2;"+";".join(str(v) for v in bytes.fromhex(p[key][1:]))
        for kind,key in dc.items())+"\n"
    fzf=",".join(f"{name}:{p[key]}" for name,key in [
        ("fg","foreground"),("bg","background"),("hl","accent"),
        ("fg+","foreground"),("bg+","selection"),("hl+","accent"),
        ("info","secondary"),("prompt","accent"),("pointer","accent"),
        ("marker","green"),("spinner","accent"),("header","muted")])
    out["zsh.zsh"]=f'''# Load after plugins.
export FZF_DEFAULT_OPTS="$FZF_DEFAULT_OPTS --color={fzf}"
if command -v dircolors >/dev/null; then
    eval "$(dircolors -b "$HOME/.config/colorscheme/current/dircolors")"
fi
typeset -gA ZSH_HIGHLIGHT_STYLES
ZSH_HIGHLIGHT_STYLES[command]='fg={p["green"]}'
ZSH_HIGHLIGHT_STYLES[builtin]='fg={p["accent"]}'
ZSH_HIGHLIGHT_STYLES[alias]='fg={p["green"]}'
ZSH_HIGHLIGHT_STYLES[path]='fg={p["blue"]}'
ZSH_HIGHLIGHT_STYLES[unknown-token]='fg={p["red"]}'
'''
    groups={
        "Normal":("foreground","background"),"NormalFloat":("foreground","panel"),
        "FloatBorder":("accent","panel"),"Comment":("dim",None),
        "String":("green",None),"Character":("green",None),
        "Number":("secondary",None),"Boolean":("secondary",None),
        "Constant":("secondary",None),"Function":("accent",None),
        "Identifier":("foreground",None),"Statement":("accent",None),
        "Keyword":("accent",None),"Type":("blue",None),"PreProc":("cyan",None),
        "Special":("warm",None),"Delimiter":("muted",None),
        "Visual":(None,"selection"),"Search":("background","secondary"),
        "IncSearch":("background","accent"),"CursorLine":(None,"panel"),
        "LineNr":("dim",None),"CursorLineNr":("accent",None),
        "StatusLine":("foreground","panel"),"StatusLineNC":("dim","panel"),
        "Pmenu":("foreground","panel"),"PmenuSel":("foreground","selection"),
        "DiagnosticError":("red",None),"DiagnosticWarn":("secondary",None),
        "DiagnosticInfo":("blue",None),"DiagnosticHint":("green",None),
        "GitSignsAdd":("green",None),"GitSignsChange":("secondary",None),
        "GitSignsDelete":("red",None),"WinSeparator":("dim",None),
        "DiffAdd":(None,"diff_add"),"DiffChange":(None,"diff_change"),
        "DiffDelete":("red","diff_delete"),"DiffText":(None,"selection")}
    lua=['vim.opt.termguicolors = true','vim.g.colors_name = "seasonal"']
    for group,(fg,bg) in groups.items():
        props={k:p[v] for k,v in (("fg",fg),("bg",bg)) if v}
        body=", ".join(k+" = "+json.dumps(v) for k,v in props.items())
        lua.append(f'vim.api.nvim_set_hl(0, "{group}", {{{body}}})')
    for group,target in {
        "@comment":"Comment","@string":"String","@number":"Number",
        "@boolean":"Boolean","@function":"Function","@keyword":"Keyword",
        "@type":"Type","@variable":"Identifier","@constant":"Constant",
        "TelescopeNormal":"NormalFloat","TelescopeBorder":"FloatBorder",
        "TelescopeSelection":"PmenuSel","WhichKey":"Function",
        "WhichKeyNormal":"NormalFloat","OilDir":"Function",
        "CmpItemAbbr":"Normal","CmpItemAbbrMatch":"Function"}.items():
        lua.append(f'vim.api.nvim_set_hl(0, "{group}", {{ link = "{target}" }})')
    lua += ['local ok, lualine = pcall(require, "lualine")',
            'if ok and type(lualine.get_config) == "function" then',
            '  local config = lualine.get_config()',
            '  if config.options then','    config.options.theme = {']
    for mode,color in [("normal","accent"),("insert","green"),
                       ("visual","secondary"),("replace","red"),
                       ("command","blue"),("inactive","dim")]:
        lua.append('      '+mode+' = { a = {fg="'+p["background"]+'",bg="'+p[color]+
                   '"}, b = {fg="'+p["foreground"]+'",bg="'+p["panel"]+
                   '"}, c = {fg="'+p["muted"]+'",bg="'+p["background"]+'"} },')
    lua += ['    }','    lualine.setup(config)','  end','end',""]
    out["nvim.lua"]="\n".join(lua)
    ints={k:nearest(v) for k,v in p.items() if k!="gnome_native"}
    out["ranger.py"]='''from ranger.colorschemes.default import Default
from ranger.gui.color import bold, reverse, BRIGHT
C = '''+repr(ints)+'''
class Scheme(Default):
    progress_bar_color = C["accent"]
    def use(self, context):
        fg, bg, attr = super().use(context)
        keys = ["panel","red","green","secondary","blue","warm","cyan","foreground"]
        mapping = {i:C[key] for i,key in enumerate(keys)}
        if BRIGHT:
            mapping.update({i+BRIGHT:C[key] for i,key in enumerate(keys)})
        fg, bg = mapping.get(fg,fg), mapping.get(bg,bg)
        if context.reset:
            return -1,-1,0
        if context.in_browser:
            if context.directory:
                fg, attr = C["accent"], attr|bold
            elif context.executable:
                fg = C["green"]
            if context.container:
                fg = C["secondary"]
            if context.link:
                fg = C["blue"] if context.good else C["red"]
            if context.marked:
                fg, attr = C["secondary"], attr|bold
            if context.selected:
                bg, attr = C["selection"], (attr & ~reverse)|bold
                if not context.marked:
                    fg = C["foreground"]
            if context.error or context.badinfo:
                fg = C["red"]
        return fg,bg,attr
'''
    out["palette.json"]=json.dumps(p,indent=2)+"\n"
    return out

def write_profiles(root,palettes):
    for season,palette in palettes.items():
        target=Path(root)/season
        target.mkdir(parents=True,exist_ok=True)
        for name,content in render(palette).items():
            (target/name).write_text(content)
