# StayOnTop

Daemon for Linux Mint (Cinnamon, X11) that remembers each app's workspace, "visible on all workspaces" and "always on top" across app and OS restarts.

## Install / update

    curl -fsSL https://raw.githubusercontent.com/DataManne/StayOnTop/main/install.sh | sh

Re-run the same command to update. Autostart also runs `git pull` at each login, so updates arrive automatically.
After install, use `stayontop --list` for the live view.

## How it works

Polls every second, keyed by `WM_CLASS`. When you change a window's state it is saved to `~/.config/stayontop/state.json`, and re-applied when that app's window next appears. Apps with several windows share one state. Untested.

## Live view

    python3 ~/.local/bin/stayontop.py --list

Refreshes every second: window ID, workspace (ALL = every workspace), on-top, whether a state is saved, slot, title.
Each window gets its own slot (`class#1`, `class#2`, ...), assigned in order of appearance.
