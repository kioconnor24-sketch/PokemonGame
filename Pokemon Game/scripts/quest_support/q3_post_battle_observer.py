#!/usr/bin/env python3
"""Q3 post-battle observer: whiteout text, clinic nurse, party, SAVE (Claude QUEST support).

Runs after the workflow's own q3-battle-play step inside the SAME emulator
process. Ordinary key input only; every state read goes through the existing
read-only GDB daemon of quest_state_controller.py. Nothing is written to game
memory, flags, party, items or saves except by the game's own Save UI.
"""
import argparse
import json
import subprocess
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


def black_ratio(path):
    """Share of near-black pixels in the whole 480x320 frame."""
    rgb = subprocess.check_output(["convert", str(path), "-depth", "8", "RGB:-"])
    if len(rgb) != 480 * 320 * 3:
        raise qc.Blocked("Unknown frame geometry for black ratio")
    return sum(max(rgb[i:i+3]) <= 40 for i in range(0, len(rgb), 3)) / (480 * 320)


def start_window_ratio(path):
    """Bright share inside the Start menu window (top right). Calibrated on
    the 2026-10-17 runs: an open Start menu is ~0.90; the clinic, a dialogue
    box or the overworld behind a closed menu are <= 0.23."""
    rgb = subprocess.check_output(["convert", str(path), "-crop", "110x150+355+30", "+repage",
                                   "-depth", "8", "RGB:-"])
    if len(rgb) != 110 * 150 * 3:
        raise qc.Blocked("Wrong Start window crop size")
    return sum(min(rgb[i:i+3]) >= 190 for i in range(0, len(rgb), 3)) / (110 * 150)


def observe(tag):
    frame = out / f"{tag}.png"
    qc.grab(a.window, frame)
    obj = qc.snapshot_detail(args, tag)
    pos = obj["position"]
    panel = qc.white_panel_ratio(frame)
    black = black_ratio(frame)
    print("Q3X", tag, json.dumps(pos, sort_keys=True), f"panel={panel:.2f}", f"black={black:.3f}",
          frame, flush=True)
    return pos, panel, black


# 1. Whiteout / respawn / nurse: advance only visible text with A.
# Calibrated on the 2026-10-17 runs: the whiteout message (white text on
# black) is 0.92-0.98 black and a full fade 1.00. In the clinic a dialogue
# box reads 0.85-1.00 on the shared panel crop, but the lit clinic floor
# alone reads 0.33, above the controller's generic 0.30 field threshold.
# A is pressed only on dialogue boxes and whiteout text, never on a bare
# fade or on the field, so the player never re-talks to the nurse.
WHITEOUT_TEXT = (0.85, 0.995)
DIALOGUE = 0.60
idle_in_clinic = 0
last = None
whiteout_frames, clinic_dialogue_frames = [], []
for n in range(1, 91):
    tag = f"q3-play-x-{n:03d}"
    pos, panel, black = observe(tag)
    last = pos
    where = (pos["mapGroup"], pos["mapNum"])
    if pos.get("inBattle"):
        qc.qa_key(a.window, "x", wait=0.7)
        continue
    whiteout_text = WHITEOUT_TEXT[0] < black < WHITEOUT_TEXT[1]
    if where == (75, 11) and panel <= DIALOGUE and black < WHITEOUT_TEXT[0]:
        idle_in_clinic += 1
        if idle_in_clinic >= 3:
            break
        time.sleep(1.0)
        continue
    idle_in_clinic = 0
    if panel > DIALOGUE:
        if where == (75, 11):
            clinic_dialogue_frames.append(tag)
        qc.qa_key(a.window, "x", wait=1.0)
    elif whiteout_text:
        whiteout_frames.append(tag)
        qc.qa_key(a.window, "x", wait=1.0)
    else:
        time.sleep(1.0)
print("Q3X_WHITEOUT_TEXT_FRAMES", json.dumps(whiteout_frames), flush=True)
print("Q3X_CLINIC_DIALOGUE_FRAMES", json.dumps(clinic_dialogue_frames), flush=True)
print("Q3X_RESPAWN_RESULT", json.dumps(last, sort_keys=True), flush=True)
if (last["mapGroup"], last["mapNum"]) != (75, 11):
    print("Q3X_NOT_IN_CLINIC: stop; do not claim clinic recovery", flush=True)
    sys.exit(3)
if idle_in_clinic < 3:
    print("Q3X_CLINIC_NOT_IDLE: dialogue still open after the frame limit; stop before the Start menu",
          flush=True)
    sys.exit(4)


# 2. Ordinary Start menu: select an action by source enum id, verified by
# the read-only cursor after every key (same rule as q2_save).
def select_action(action, label, optional=False):
    """Open Start and choose `action`. With optional, close Start and return
    False if the game does not offer it."""
    qc.qa_key(a.window, "Return", wait=1.5)
    state, frame = qc.save_probe(args, f"save-q3x-{label}-open")
    # The menu globals keep their last values after the menu closes, so a
    # Start press swallowed by an open text box would read as a stale menu.
    window = start_window_ratio(frame)
    print("Q3X_START_WINDOW", label, f"{window:.3f}", frame, flush=True)
    if window < 0.60:
        raise qc.Blocked(f"No visible Start menu window for {label} ({window:.3f}); not trusting menu globals")
    menu = state["menu"]
    if optional and action not in menu["actions"]:
        print("Q3X_ACTION_NOT_OFFERED", action, json.dumps(menu, sort_keys=True), flush=True)
        qc.qa_key(a.window, "z", wait=1.5)
        return False
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
    return True


# Party screen after the nurse (visible HP bars), then back to the field.
# The Q4 developer gift gives a Pokemon without the POKEMON Start entry, so
# the party screen is evidence only when the game itself offers it.
if select_action(1, "party", optional=True):  # MENU_ACTION_POKEMON
    qc.grab(a.window, out / "q3x-party-after-clinic.png")
    print("Q3X_PARTY_SCREEN", out / "q3x-party-after-clinic.png", flush=True)
    qc.qa_key(a.window, "z", wait=2.0)
    qc.qa_key(a.window, "z", wait=1.5)
pos, panel, black = observe("q3-play-x-after-party")

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
        print("Q3X_SAVE_SUCCESS_CALLBACK", phase, f"attempt={attempt+1}", flush=True)
        ok = True
        break
    elif phase == "SaveErrorCallback":
        raise qc.Blocked("In-game save error callback")
    time.sleep(0.3)
if not ok:
    raise qc.Blocked("No save success callback")
for i in range(30):
    state, frame = qc.save_probe(args, f"save-q3x-return-{i+1}")
    # Same clinic calibration as the whiteout loop: the lit floor reads 0.33.
    if qc.white_panel_ratio(frame) <= DIALOGUE:
        print("Q3X_SAVE_SUCCESS", json.dumps(state, sort_keys=True), flush=True)
        break
    time.sleep(0.45)
else:
    raise qc.Blocked("Save message never closed")
