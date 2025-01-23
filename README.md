# My dotfiles collection

My dotfiles collection to be installed with stow command line utility.

## Tmux

Tmux has a very simple configuration based on TPM as a plugin manager and
catppucin mocha as theme. <C-a> is the leader key

## NeoVim

## zsh

## getmail

Make sure password is in your keyring

## systemd

Ensure python keyring library is enabled.

First run: getmail --store-password-in-keyring enter the password and exit

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

## password

To store password in keyring use this: secret-tool store --label=msmtp host
imap.suse.de service smtp user pperego\@mail
