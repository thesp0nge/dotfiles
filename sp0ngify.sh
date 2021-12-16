#!/bin/bash

WGET=`which wget`
CONF_DST=$HOME"/.config"
if [ ! -x $WGET ]; then
    echo "[!] missing wget. I don't know how to download files"
    exit 1
fi

echo "[+] Installing TMUX in .config/tmux"
TMUX_DATA="https://github.com/thesp0nge/dotfiles/raw/master/data/tmux.tar.gz"
TMUX_DST=$CONF_DST"/tmux"
TMUX_LN=$HOME"/.tmux.conf"

if [ -d $TMUX_DST ]; then
    echo "[!] $TMUX_DST exists. Giving up"
    exit 1
fi

if [ -x  $TMUX_LN ]; then
    echo "[!] $TMUX_LN exists. Giving up"
    exit 1
fi

mkdir -pv $TMUX_DST
$WGET $TMUX_DATA
tar xfv tmux.tar.gz -C $CONF_DST

if [ -f $TMUX_DST"/tmux.conf" ]; then
    echo "[+] Ok"
else
    echo "[!] Failed."
    exit 1
fi

ln -s $TMUX_DST"/tmux.conf" $TMUX_LN

echo $TMUX_DST
