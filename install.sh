#!/bin/sh
# Install or update StayOnTop. Safe to re-run.
# Autostart pulls the latest code from git at every login, so manual updates are optional.
set -e
REPO=https://github.com/DataManne/StayOnTop
DIR="$HOME/.local/share/stayontop"

command -v wmctrl >/dev/null && command -v xprop >/dev/null || sudo apt install -y wmctrl x11-utils

if [ -d "$DIR/.git" ]; then
    git -C "$DIR" pull -q --ff-only
else
    git clone -q "$REPO" "$DIR"
fi

mkdir -p "$HOME/.local/bin" "$HOME/.config/autostart"
ln -sf "$DIR/stayontop.py" "$HOME/.local/bin/stayontop"
cat > "$HOME/.config/autostart/stayontop.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=StayOnTop
Exec=sh -c 'git -C "$DIR" pull -q --ff-only; exec python3 "$DIR/stayontop.py"'
EOF

# restart the daemon (not the --list viewer)
pkill -f "stayontop.py$" 2>/dev/null || true
nohup python3 "$DIR/stayontop.py" >/dev/null 2>&1 &
echo "StayOnTop installed/updated. Live view: stayontop --list"
