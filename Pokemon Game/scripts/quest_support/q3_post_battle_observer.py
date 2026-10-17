#!/usr/bin/env python3
"""Local-only Q3 post-battle observer (Claude support run, not a repo file).

Runs after the workflow's own q3-battle-play step inside the SAME emulator
process. Ordinary key input only; every state read goes through the existing
read-only GDB daemon of quest_state_controller.py. Nothing is written to game
memory, flags, party, items or saves except by the game's own Save UI.
"""
import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ap = argparse.ArgumentParser()
ap.add_argument("--controller-dir", required=True)
ap.add_argument("--fifo", required=True)
ap.add_argument("--outdir", required=True)
ap.add_argument("--window", required=True)
a = ap.parse_args()
sys.path.insert(0, a.controller_dir)
import quest_state_controller as qc  # noqa: E402

args = SimpleNamespace(fifo=a.fifo, outdir=a.outdir, window=a.window)
out = Path(a.outdir)


def observe(tag):
    frame = out / f"{tag}.png"
    qc.grab(a.window, frame)
    obj = qc.snapshot_detail(args, tag)
    pos = obj["position"]
    panel = qc.white_panel_ratio(frame)
    print("Q3X", tag, json.dumps(pos, sort_keys=True), f"panel={panel:.2f}", frame, flush=True)
    return pos, panel


# 1. Whiteout / respawn / nurse: advance only visible text with A.
idle_in_clinic = 0
last = None
for n in range(1, 61):
    pos, panel = observe(f"q3-play-x-{n:03d}")
    last = pos
    where = (pos["mapGroup"], pos["mapNum"])
    if pos.get("inBattle"):
        qc.qa_key(a.window, "x", wait=0.7)
        continue
    if where == (75, 11) and panel <= 0.30:
        idle_in_clinic += 1
        if idle_in_clinic >= 3:
            break
        time.sleep(1.0)
        continue
    idle_in_clinic = 0
    if panel > 0.30:
        qc.qa_key(a.window, "x", wait=1.0)
    else:
        time.sleep(1.0)
print("Q3X_RESPAWN_RESULT", json.dumps(last, sort_keys=True), flush=True)
if (last["mapGroup"], last["mapNum"]) != (75, 11):
    print("Q3X_NOT_IN_CLINIC: stop; do not claim clinic recovery", flush=True)
    sys.exit(3)


# 2. Ordinary Start menu: select an action by source enum id, verified by
# the read-only cursor after every key (same rule as q2_save).
def select_action(action, label):
    qc.qa_key(a.window, "Return", wait=1.5)
    state, _ = qc.save_probe(args, f"save-q3x-{label}-open")
    menu = state["menu"]
    if menu["actions"].count(action) != 1:
        raise qc.Blocked(f"Start action {action} not offered: {menu}")
    dest = menu["actions"].index(action)
    for attempt in range(9):
        if menu["selected"] == action:
            break
        direction = "Down" if menu["cursor"] < dest else "Up"
        old = menu["cursor"]
        qc.qa_key(a.window, direction, wait=0.65)
        state, _ = qc.save_probe(args, f"save-q3x-{label}-move-{attempt+1}")
        menu = state["menu"]
        if menu["cursor"] not in (old, old + (1 if direction == "Down" else -1)):
            raise qc.Blocked(f"Uncontrolled cursor: {menu}")
    if menu["selected"] != action:
        raise qc.Blocked(f"Could not select action {action}: {menu}")
    qc.qa_key(a.window, "x", wait=2.0)


# Party screen after the nurse (visible HP bars), then back to the field.
select_action(1, "party")  # MENU_ACTION_POKEMON
qc.grab(a.window, out / "q3x-party-after-clinic.png")
print("Q3X_PARTY_SCREEN", out / "q3x-party-after-clinic.png", flush=True)
qc.qa_key(a.window, "z", wait=2.0)
qc.qa_key(a.window, "z", wait=1.5)
pos, panel = observe("q3-play-x-after-party")

# 3. Ordinary SAVE -> YES, accepted only on the game's success callback.
select_action(5, "save")  # MENU_ACTION_SAVE
for attempt in range(20):
    state, frame = qc.save_probe(args, f"save-q3x-confirm-wait-{attempt+1}")
    if state["menu"]["savePhase"] == "SaveConfirmInputCallback":
        break
    time.sleep(0.35)
else:
    raise qc.Blocked("SAVE confirm callback never observed")
qc.qa_key(a.window, "x", wait=0.8)
ok = False
for attempt in range(50):
    state, frame = qc.save_probe(args, f"save-q3x-write-{attempt+1}")
    phase = state["menu"]["savePhase"]
    if phase == "SaveOverwriteInputCallback":
        if state["menu"]["differentSaveFile"] != 0:
            raise qc.Blocked("Different-save overwrite: not guessing")
        qc.qa_key(a.window, "x", wait=0.9)
    elif phase in ("SaveSuccessCallback", "SaveReturnSuccessCallback"):
        ok = True
        break
    elif phase == "SaveErrorCallback":
        raise qc.Blocked("In-game save error callback")
    time.sleep(0.3)
if not ok:
    raise qc.Blocked("No save success callback")
for i in range(30):
    state, frame = qc.save_probe(args, f"save-q3x-return-{i+1}")
    if qc.white_panel_ratio(frame) <= 0.30:
        print("Q3X_SAVE_SUCCESS", json.dumps(state, sort_keys=True), flush=True)
        break
    time.sleep(0.45)
else:
    raise qc.Blocked("Save message never closed")
