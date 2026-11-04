# StayOnTop

Daemon for Linux Mint (X11) that remembers each application's workspace,
"visible on all workspaces" and "keep on top" settings and restores them when
the app or the OS restarts.

## Install
    sudo apt install wmctrl x11-utils
    mkdir -p ~/.local/share/stayontop ~/.config/autostart
    cp stayontop.py ~/.local/share/stayontop/
    sed "s|/home/USER|$HOME|" autostart/stayontop.desktop > ~/.config/autostart/stayontop.desktop

State is saved in `~/.config/stayontop/state.json`, keyed by window class.
