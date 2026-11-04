#!/usr/bin/env python3
"""StayOnTop: remembers per-window workspace, 'on all workspaces' and 'always on top'
(X11 / Cinnamon on Linux Mint) and re-applies them when the window reappears.

  stayontop.py          run the daemon
  stayontop.py --list   live, auto-refreshing table of windows and their state

Windows of the same app get separate slots (class#1, class#2, ...), so one
window's settings no longer bleed into another. Slots are assigned in the order
windows appear. Requires: wmctrl, x11-utils (xprop).
"""
import json, os, subprocess, sys, time

STATE = os.path.expanduser("~/.config/stayontop/state.json")


def run(*c):
    return subprocess.run(c, capture_output=True, text=True).stdout


def windows():
    """{wid: {class, title, desktop, sticky, above}} for normal windows."""
    out = {}
    for line in run("wmctrl", "-lx").splitlines():
        p = line.split(None, 4)
        if len(p) < 4:
            continue
        wid, desk, cls = p[0], int(p[1]), p[2]
        title = p[4] if len(p) > 4 else ""
        st = run("xprop", "-id", wid, "_NET_WM_STATE", "_NET_WM_WINDOW_TYPE")
        if "_TYPE_NORMAL" not in st and "_TYPE_DIALOG" not in st:
            continue
        out[wid] = {"class": cls, "title": title,
                    "sticky": desk == -1 or "_STICKY" in st,
                    "above": "_STATE_ABOVE" in st,
                    "desktop": None if desk == -1 else desk}
    return out


def state_of(w):
    return {k: w[k] for k in ("sticky", "above", "desktop")}


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


def save(saved):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE + ".tmp", "w") as f:
        json.dump(saved, f, indent=2)
    os.replace(STATE + ".tmp", STATE)


def assign_key(cls, keys):
    used = {k for k in keys.values() if k.rsplit("#", 1)[0] == cls}
    n = 1
    while f"{cls}#{n}" in used:
        n += 1
    return f"{cls}#{n}"


def daemon():
    saved, known, keys = load(), {}, {}
    while True:
        try:
            cur = windows()
        except Exception:
            time.sleep(1)
            continue
        for wid in sorted(cur, key=lambda x: int(x, 16)):
            w = cur[wid]
            st = state_of(w)
            if wid not in known:
                keys[wid] = assign_key(w["class"], keys)
                want = saved.get(keys[wid])
                if want and want != st:
                    apply(wid, want)
                    st = dict(want)
                known[wid] = st
            elif known[wid] != st:
                known[wid] = st
                saved[keys[wid]] = st
                save(saved)
        for wid in set(known) - set(cur):
            del known[wid], keys[wid]
        time.sleep(1)


def listing():
    saved = load()
    keys = {}
    try:
        while True:
            cur = windows()
            saved = load()
            for wid in list(keys):
                if wid not in cur:
                    del keys[wid]
            rows = []
            for wid in sorted(cur, key=lambda x: int(x, 16)):
                w = cur[wid]
                keys.setdefault(wid, assign_key(w["class"], keys))
                ws = "ALL" if w["desktop"] is None else str(w["desktop"] + 1)
                rows.append((wid, ws, "yes" if w["above"] else "-",
                             "yes" if keys[wid] in saved else "-",
                             keys[wid], w["title"]))
            print("\033[2J\033[H", end="")
            print(f"{'ID':<11}{'WORKSPACE':<11}{'ON TOP':<8}{'SAVED':<7}{'SLOT':<28}TITLE")
            for r in rows:
                print(f"{r[0]:<11}{r[1]:<11}{r[2]:<8}{r[3]:<7}{r[4][:27]:<28}{r[5][:60]}")
            print("\nCtrl+C to quit")
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    listing() if "--list" in sys.argv else daemon()
