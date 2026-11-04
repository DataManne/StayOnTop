#!/usr/bin/env python3
"""Daemon that remembers and restores window workspace, 'visible on all
workspaces' (sticky) and 'keep on top' (above) state per application.

Requires an X11 session (e.g. Linux Mint Cinnamon) with wmctrl and xprop.
State is stored in ~/.config/stayontop/state.json, so it survives both
application restarts and OS restarts.

Usage: stayontop.py [--interval SECONDS] [--state FILE]
"""
import argparse
import json
import os
import subprocess
import time

DEFAULT_STATE = os.path.expanduser("~/.config/stayontop/state.json")
ALL_DESKTOPS = 0xFFFFFFFF


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout


def list_windows():
    """Yield (window_id, desktop, wm_class, title) for normal windows."""
    for line in run("wmctrl", "-lx").splitlines():
        parts = line.split(None, 4)
        if len(parts) < 4:
            continue
        wid, desktop, wm_class = parts[0], int(parts[1]), parts[2]
        if desktop == -1 and "desktop" in wm_class.lower():
            continue
        yield wid, desktop, wm_class, parts[4] if len(parts) > 4 else ""


def window_state(wid):
    out = run("xprop", "-id", wid, "_NET_WM_STATE", "_NET_WM_WINDOW_TYPE")
    if "_NET_WM_WINDOW_TYPE_NORMAL" not in out and "_NET_WM_WINDOW_TYPE_DIALOG" not in out:
        return None
    return {"sticky": "_NET_WM_STATE_STICKY" in out,
            "above": "_NET_WM_STATE_ABOVE" in out}


def apply_state(wid, saved):
    if saved["sticky"] or saved["above"]:
        flags = [f for f, on in (("sticky", saved["sticky"]), ("above", saved["above"])) if on]
        run("wmctrl", "-i", "-r", wid, "-b", "add," + ",".join(flags))
    if not saved["sticky"]:
        run("wmctrl", "-i", "-r", wid, "-t", str(saved["desktop"]))


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def poll(state, seen):
    """One pass. Restores state for new windows, records changes otherwise.
    Returns True if state changed."""
    changed = False
    current = set()
    for wid, desktop, wm_class, _title in list_windows():
        current.add(wid)
        info = window_state(wid)
        if info is None:
            continue
        saved = state.get(wm_class)
        if wid not in seen:
            seen.add(wid)
            if saved:
                apply_state(wid, saved)
                continue
        now = {"desktop": ALL_DESKTOPS if info["sticky"] else desktop,
               "sticky": info["sticky"], "above": info["above"]}
        if info["sticky"] and saved:
            now["desktop"] = saved["desktop"]
        if saved != now:
            if not info["sticky"] or not saved:
                now["desktop"] = desktop
            state[wm_class] = now
            changed = True
    seen.intersection_update(current)
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--state", default=DEFAULT_STATE)
    args = ap.parse_args()
    state = load(args.state)
    seen = set()
    while True:
        if poll(state, seen):
            save(args.state, state)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
