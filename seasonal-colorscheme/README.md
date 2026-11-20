# Seasonal colorscheme manager

Palette stagionali per Alacritty, tmux, Starship, Zsh/fzf/dircolors, Neovim, Ranger e accento GNOME. Le preferenze dei programmi restano nelle rispettive configurazioni; i colori attivi passano da ~/.config/colorscheme/current.

## Stato della consegna

Implementazione in bozza. L'ambiente di esecuzione dell'assistente era indisponibile: i test inclusi non sono stati eseguiti e non è stata effettuata una prova reale su GNOME/systemd. Eseguire i controlli sotto prima della migrazione. Non eseguire i vecchi apply-theme.sh sopra questa installazione, perché sovrascrivono configurazioni complete e rimuoverebbero gli hook.

## Installazione sul laptop esistente

Richiede Python >=3.11 e i programmi già configurati. Non installa pacchetti, plugin o font, non modifica PAM e non cambia il prefisso tmux.

Dalla directory seasonal-colorscheme:

    python3 -m unittest discover -s tests -v
    python3 -m py_compile colorscheme.py install.py render.py
    zsh -n hooks/zsh.zsh
    systemd-analyze --user verify units/*.service units/*.timer
    systemd-analyze calendar '*-03,06,09,12-01 00:00:00'
    bash install.sh

Il controllo systemd può segnalare che ~/.local/bin/colorscheme non esiste prima dell'installazione: ripeterlo sulle unità installate dopo la migrazione.

Avviare l'installer come utente della sessione GNOME, senza sudo. Al termine:

    exec zsh
    ~/.local/bin/colorscheme status
    systemctl --user list-timers colorscheme.timer

Chiudere e riaprire Neovim e Ranger una volta, per caricare gli hook. Controllare che ~/.local/bin sia in PATH; i servizi usano comunque il percorso assoluto.

## Date e selezione

- Winter: dal 1 dicembre a fine febbraio.
- Spring: dal 1 marzo al 31 maggio.
- Summer: dal 1 giugno al 31 agosto.
- Autumn: dal 1 settembre al 30 novembre.

Il timer usa la mezzanotte nel fuso orario configurato sul laptop. Persistent=true recupera i cambi mancati. colorscheme-login.service verifica la data anche a ogni avvio della sessione grafica. Non serve abilitare il lingering: il tema serve quando la sessione è attiva.

    colorscheme winter
    colorscheme spring
    colorscheme summer
    colorscheme autumn
    colorscheme auto
    colorscheme status

Una scelta manuale resta attiva anche dopo logout, reboot e cambio di stagione. auto cancella l'override e applica subito la stagione della data corrente. Lo stesso è disponibile attraverso systemd:

    systemctl --user start colorscheme@winter.service
    systemctl --user start colorscheme@auto.service
    systemctl --user start colorscheme.service

Le unità sono oneshot senza RemainAfterExit: ogni start ripete l'operazione.

## Dove sono i file

~/.config/colorscheme contiene autumn, winter, spring e summer. Ogni directory contiene palette.json, alacritty.toml, tmux.conf, starship.toml, dircolors, zsh.zsh, nvim.lua e ranger.py. current è un collegamento alla stagione attiva.

~/.config/colorscheme/palettes.json è la sorgente completa delle quattro palette. Dopo averlo modificato:

    colorscheme regenerate

Questo rigenera i file delle quattro stagioni e riapplica la selezione corrente. I file generati possono essere personalizzati direttamente se non si intende usare regenerate.

~/.config/starship/base.toml contiene le preferenze del prompt; ~/.config/starship.toml viene generato dal gestore perché Starship non supporta gli import. Modificare il file base per personalizzare il prompt.

Lo stato auto/manuale e i backup sono in ~/.local/state/colorscheme, o nel percorso XDG_STATE_HOME configurato.

## Migrazione e limiti

- Alacritty: conserva le opzioni TOML e gli import, rimuove colors dal file principale e aggiunge l'import della palette. La serializzazione conserva i valori, ma non i commenti; il backup conserva l'originale.
- tmux: sposta le righe logiche contenenti colori esadecimali in un template dedicato, preservando i formati di status e il prefisso attuale. I colori noti delle vecchie palette vengono rimappati; i colori personalizzati sconosciuti restano invariati. Il gestore ricarica solo il frammento colori nelle sessioni vive.
- Starship: conserva il prompt e usa una palette semantica seasonal; personalizzazioni con RGB letterali nei campi style restano letterali.
- Zsh: conserva la configurazione e aggiunge un hook. I colori vengono aggiornati al prompt successivo, senza sostituire la shell o interrompere i programmi. Eventuali assegnazioni di colori legacy già presenti restano nel file, ma il nuovo hook applica i valori stagionali dopo di esse.
- Neovim: aggiunge un plugin di caricamento dopo la configurazione attuale; i file di colori precedenti non vengono cancellati. Le sessioni avviate dopo l'installazione registrano un socket privato e ricevono l'aggiornamento del tema. I gruppi comuni, Tree-sitter, diagnostica, Telescope, Oil, cmp e lualine sono coordinati; plugin con propri colori RGB possono richiedere adattamenti.
- Ranger: mantiene rc.conf, associazioni e plugin; il piccolo loader legge il tema corrente senza affidarsi alla cache bytecode del collegamento. Chiudere e riaprire Ranger dopo un cambio. Colori approssimati a xterm-256.
- GNOME: imposta preferenza scura e accento nativo. Se trova lo schema ChromaLeon, imposta l'accento RGB esatto. Non installa estensioni. Errori gsettings sono riportati e non impediscono l'applicazione agli altri tool.
- Questo è un gestore per percorsi standard ~/.config e ~/.zshrc. Percorsi XDG_CONFIG_HOME, ZDOTDIR o STARSHIP_CONFIG personalizzati vengono rifiutati prima della migrazione.
- I precedenti colori possono rimanere in asset non più attivi o in opzioni personalizzate. La migrazione privilegia la conservazione della configurazione rispetto alla rimozione indiscriminata di file.
- Un'installazione già presente non viene sovrascritta: per reinstallare, ripristinare prima il backup.

## Backup e ripristino

L'installer stampa subito il percorso del backup privato, prima di modificare i file. Sono conservati contenuti, symlink e assenza originale dei file gestiti.

    colorscheme restore ~/.local/state/colorscheme/backups/PERCORSO-STAMPATO

Il ripristino disabilita il timer e il servizio di login, ripristina i file e le impostazioni GNOME salvate e conserva la configurazione sostituita in before-restore. Lo stato runtime degli editor e dei terminali già aperti non viene ripristinato: riaprirli o ricaricarli.

Se l'installazione si interrompe prima che il launcher sia stato creato, dal checkout usare:

    python3 colorscheme.py restore /percorso/del/backup

## Verifica dell'implementazione

I test coprono tutte le date di confine, febbraio bisestile, persistenza dell'override manuale, roundtrip TOML, generazione palette, migrazione in una home isolata, conservazione di prefisso tmux e preferenze e ripristino dei file. Non sono stati eseguiti dall'assistente per indisponibilità dell'ambiente.

Fonti: systemd.timer(5), systemd.time(7), Alacritty configuration reference, Starship configuration reference e documentazione dei colorscheme di Ranger.
