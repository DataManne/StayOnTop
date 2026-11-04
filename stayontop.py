#!/usr/bin/env python3
"""StayOnTop: remembers per-app workspace, 'on all workspaces' and 'always on top'
(X11 / Cinnamon on Linux Mint) and re-applies them when the window reappears.
Requires: wmctrl, x11-utils (xprop).
"""
import json, os, subprocess, time

STATE = os.path.expanduser("~/.config/stayontop/state.json")


def run(*c):
    return subprocess.run(c, capture_output=True, text=True).stdout


def windows():
    out = {}
    for line in run("wmctrl", "-lx").splitlines():
        p = line.split(None, 4)
        if len(p) < 4:
            continue
        wid, desk, cls = p[0], int(p[1]), p[3]
        st = run("xprop", "-id", wid, "_NET_WM_STATE", "_NET_WM_WINDOW_TYPE")
        if "_TYPE_NORMAL" not in st and "_TYPE_DIALOG" not in st:
            continue
        out[wid] = (cls, {"sticky": desk == -1 or "_STICKY" in st,
                          "above": "_STATE_ABOVE" in st,
                          "desktop": None if desk == -1 else desk})
    return out


def apply(wid, w):
    if w.get("desktop") is not None:
        run("wmctrl", "-i", "-r", wid, "-t", str(w["desktop"]))
    for k in ("sticky", "above"):
        run("wmctrl", "-i", "-r", wid, "-b", ("add," if w[k] else "remove,") + k)


def load():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def main():
    saved, known = load(), {}
    while True:
        try:
            cur = windows()
        except Exception:
            time.sleep(1)
            continue
        for wid, (cls, st) in cur.items():
            if wid not in known:
                w = saved.get(cls)
                if w and w != st:
                    apply(wid, w)
                    st = dict(w)
                known[wid] = st
            elif known[wid] != st:
                known[wid] = st
                saved[cls] = st
                os.makedirs(os.path.dirname(STATE), exist_ok=True)
                with open(STATE, "w") as f:
                    json.dump(saved, f, indent=2)
        for wid in set(known) - set(cur):
            del known[wid]
        time.sleep(1)


if __name__ == "__main__":
    main()
