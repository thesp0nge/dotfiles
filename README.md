# My dotfiles collection

## Tmux
Tmux has a very simple configuration based on TPM as a plugin manager and catppucin mocha as theme. <C-a> is the leader key

## NeoVim

## zsh

## getmail
Make sure password is in your keyring

## systemd

Enable the services
```
systemctl --user enable get_mail.service
systemctl --user enable timer.service
```

Start them
```
systemctl --user start get_mail
systemctl --user start timer
```
