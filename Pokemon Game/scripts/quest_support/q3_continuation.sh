# Claude QUEST-support continuation, appended after the Q3 block of Playtest's
# unchanged "Launch actual graphical mGBA" step (see compose_q3_run.py).
# It runs in the same shell, so it reuses that step's emulator, read-only
# debugger FIFO, window id and capture/press helpers. Ordinary input only.
# Requires Q3X (observer path). Never uploads or edits a ROM or save.
echo "QA_Q3_INTERACTION_STATUS=$qa_q3_outcome"
q3x_rc=99
if [ "$qa_q3_outcome" = "REAL_ELIO_BATTLE_EXIT_SCOPED" ]; then
  set +e
  python3 -u "$Q3X" --controller-dir "Pokemon Game/scripts/qa" --fifo "$qa_fifo" \
    --outdir "$RUNNER_TEMP/averon-playtest" --window "$win" \
    > "$RUNNER_TEMP/averon-playtest/q3x.log" 2>&1
  q3x_rc=$?
  set -e
  cat "$RUNNER_TEMP/averon-playtest/q3x.log"
fi
echo "Q3X_RC=$q3x_rc"

# Close the emulator so mGBA writes its flash file, then decode the saved slot.
flash="Pokemon Game/engine/pokeemerald.sav"
kill "$emu_pid"; wait "$emu_pid" 2>/dev/null || true
kill "$qa_pid" 2>/dev/null || true; wait "$qa_pid" 2>/dev/null || true
if ! test -s "$flash"; then
  echo "Q3X_FLASH_MISSING: no flash file after shutdown; no Continue evidence"
  exit 0
fi
echo "Q3X_FLASH $(stat -c '%s' "$flash") bytes sha256=$(sha256sum "$flash" | cut -c1-64)"
python3 - "$flash" <<'PY' || true
import json, sys
sys.path.insert(0, "Pokemon Game/scripts/qa")
import quest_state_controller as qc
s = qc.decode_flash_q2(open(sys.argv[1], "rb").read())
print("Q3X_SAVED_SLOT", json.dumps({k: s[k] for k in ("slot", "saveCounter", "mapGroup", "mapNum", "x", "y", "warpId")}))
PY

# Fresh emulator process from the same flash, no debugger: title -> Continue.
sleep 2
mgba -2 "Pokemon Game/engine/pokeemerald.gba" > "$RUNNER_TEMP/averon-playtest/mgba-relaunch.log" 2>&1 &
emu_pid=$!
win=""
for i in $(seq 1 40); do
  win=$(xdotool search --onlyvisible --name "mGBA" 2>/dev/null | head -n1 || true)
  test -n "$win" && break
  sleep 0.5
done
if test -z "$win"; then
  echo "Q3X_RELAUNCH_BLOCKED: no mGBA window"
  exit 0
fi
sleep 9; capture "q3x-relaunch-boot"
press Return; sleep 4; capture "q3x-relaunch-title"
press x; sleep 3; capture "q3x-relaunch-main-menu"
press x; sleep 7; capture "q3x-relaunch-continued-1"
sleep 3; capture "q3x-relaunch-continued-2"
kill "$emu_pid" 2>/dev/null || true
# No debugger in this process: compare the Continue frame with the last
# pre-save clinic field frame. A score, not a verdict; Playtest judges.
python3 - "$RUNNER_TEMP/averon-playtest/q3-play-x-after-party.png" \
  "$RUNNER_TEMP/averon-playtest/q3x-relaunch-continued-2.png" <<'PY' || true
import os, subprocess, sys
before, after = sys.argv[1:]
if not (os.path.exists(before) and os.path.exists(after)):
    sys.exit(print("Q3X_CONTINUE_MATCH unavailable: missing pre-save or Continue frame"))
a, b = (subprocess.check_output(["convert", p, "-depth", "8", "RGB:-"]) for p in (before, after))
if len(a) != len(b):
    sys.exit(print("Q3X_CONTINUE_MATCH unavailable: frame sizes differ"))
same = sum(a[i:i+3] == b[i:i+3] for i in range(0, len(a), 3)) / (len(a) // 3)
diff = sum(abs(x - y) for x, y in zip(a, b)) / len(a)
print(f"Q3X_CONTINUE_MATCH same_pixels={same:.3f} mean_abs_diff={diff:.2f}"
      " (pre-save q3-play-x-after-party vs q3x-relaunch-continued-2)")
PY
echo "Q3X_DONE"
