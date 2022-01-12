#!/bin/bash

WGET=`which wget`
CONF_DST=$HOME"/.config"
if [ ! -x $WGET ]; then
    echo "[!] missing wget. I don't know how to download files"
    exit 1
fi

function install_tmux() {
    echo "[+] Installing TMUX in .config/tmux"
    TMUX_DATA="https://github.com/thesp0nge/dotfiles/raw/master/data/tmux.tar.gz"
    TMUX_DST=$CONF_DST"/tmux"
    TMUX_LN=$HOME"/.tmux.conf"

    if [ -d $TMUX_DST ]; then
        echo "[!] $TMUX_DST exists. Giving up"
        return 2
    fi

    if [ -x  $TMUX_LN ]; then
        echo "[!] $TMUX_LN exists. Giving up"
        return 2
    fi

    mkdir -pv $TMUX_DST
    $WGET $TMUX_DATA
    tar xf tmux.tar.gz -C $CONF_DST 2

    if [ -f $TMUX_DST"/tmux.conf" ]; then
        echo "[+] Ok"
    else
        echo "[!] Failed."
        return 3
    fi

    ln -s $TMUX_DST"/tmux.conf" $TMUX_LN
    ln -s $TMUX_DST $HOME"/.tmux"

    rm tmux.tar.gz
    echo "[*] tmux configuration installed. Please lunch tmux and press ^A+I to install plugins"

    return 0
}

function install_zsh {
    echo "[*] check if zsh is installed"
    grep zsh /etc/shells > /dev/null
    if [ $? -ne 0 ]; then
        echo "[!] zsh is not installed, please install it first."
        return 3
    fi

    echo "[*] check if oh-my-zsh is present"
    if [ -d $HOME".oh-my-zsh/" ]; then
        echo "[+] present. Skipping installation"
    else
        echo "[*] installing oh-my-zsh"
        sh -c "$(wget https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)"
    fi

    echo "[*] check if poweline theme is present"
    if [ -d $HOME/.oh-my-zsh/custom/themes/powerlevel10k ]; then
        echo "[+] present. Skipping installation"
    else
        echo "[*] installing poweline theme"
        git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
    fi

    $WGET https://raw.githubusercontent.com/thesp0nge/dotfiles/master/zsh/zshrc
    mv zshrc $HOME/.zshrc
    ZSH=`which zsh`
    CHSH=`which chsh`
    $CHSH -s $ZSH

    return 0
}

echo "[*] setting up environment for $LOGNAME"
install_tmux
if [ $? -eq 3 ]; then
    exit 1
fi
install_zsh
if [ $? -eq 3 ]; then
    exit 1
fi
