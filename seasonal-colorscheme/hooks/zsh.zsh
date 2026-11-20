# Installed once at the end of .zshrc.
autoload -Uz add-zsh-hook
typeset -g _seasonal_last_path=''
typeset -g _seasonal_fzf_base="${FZF_DEFAULT_OPTS:-}"
_seasonal_refresh() {
    local palette_dir="$HOME/.config/colorscheme/current"
    local resolved="${palette_dir:A}"
    if [[ "$resolved" != "$_seasonal_last_path" && -r "$palette_dir/zsh.zsh" ]]; then
        export FZF_DEFAULT_OPTS="$_seasonal_fzf_base"
        source "$palette_dir/zsh.zsh"
        zstyle ':completion:*' list-colors "${(@s.:.)LS_COLORS}"
        _seasonal_last_path="$resolved"
    fi
}
add-zsh-hook -d precmd _seasonal_refresh 2>/dev/null
add-zsh-hook precmd _seasonal_refresh
_seasonal_refresh
