import weechat
import subprocess

weechat.register(
    "libera_password",
    "Paolo Perego",
    "1.0",
    "GPL3",
    "Get Libera password from Gnome keyring and connect to Libera",
    "",
    "",
)


def connect_libera_with_password(data, signal, signal_data):
    # Questo verrà eseguito quando i plugin sono caricati (inclusi gli script)
    # o quando si riceve il segnale specificato
    try:
        # Esegui secret-tool per recuperare la password.
        # Assicurati che gli attributi 'service' e 'account' corrispondano a quelli
        # che hai usato per salvare la password nel keyring.
        password = (
            subprocess.check_output(
                ["secret-tool", "lookup", "service", "weechat", "account", "thesp0nge"]
            )
            .decode("utf-8")
            .strip()
        )

        if password:
            weechat.command("", f"/set irc.server.libera.password {password}")
            weechat.prnt("", "DEBUG: Password for Libera set from Gnome keyring.")
            weechat.command("", "/connect libera")  # QUESTA RIGA È FONDAMENTALE
            weechat.prnt("", "DEBUG: Connect command issued.")
        else:
            weechat.prnt(
                "",
                "No password found in keyring for Libera with service=weechat, account=thesp0nge.",
            )

    except subprocess.CalledProcessError as e:
        weechat.prnt("", "Error getting password from Gnome keyring: %s" % e)
    except Exception as e:
        weechat.prnt("", "An unexpected error occurred: %s" % e)
    return weechat.WEECHAT_RC_OK


# Aggancia la funzione a un segnale che si attiva all'avvio di WeeChat
# 'weechat_plugins_loaded' è un buon segnale per questo scopo.
weechat.hook_signal("weechat_plugins_loaded", "connect_libera_with_password", "")

# Se preferisci un comando manuale oltre all'autostart, puoi aggiungere anche questo:
weechat.hook_command(
    "libera_connect",
    "Connect to Libera using password from keyring",
    "",
    "",
    "",
    "connect_libera_with_password",
    "",
)
