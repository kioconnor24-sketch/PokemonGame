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
  exit 4
fi
echo "Q3X_FLASH $(stat -c '%s' "$flash") bytes sha256=$(sha256sum "$flash" | cut -c1-64)"
if python3 - "$flash" <<'PY'
import json, sys
sys.path.insert(0, "Pokemon Game/scripts/qa")
import quest_state_controller as qc
s = qc.decode_flash_q2(open(sys.argv[1], "rb").read())
print("Q3X_SAVED_SLOT", json.dumps({k: s[k] for k in ("slot", "saveCounter", "mapGroup", "mapNum", "x", "y", "warpId")}))
# Required evidence: the saved slot must be the Alderfield clinic (75,11).
if (s["mapGroup"], s["mapNum"]) != (75, 11):
    print("Q3X_SAVED_SLOT_NOT_CLINIC")
    sys.exit(1)
PY
then
  :
else
  echo "Q3X_SAVED_SLOT_INVALID: flash did not decode to the clinic slot"
  exit 6
fi

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
  exit 5
fi
sleep 9; capture "q3x-relaunch-boot"
press Return; sleep 4; capture "q3x-relaunch-title"
# Ordinary A presses: title -> main menu -> CONTINUE (the default entry).
# After each press compare the frame with the last pre-save clinic field
# frame, and stop as soon as it matches: A is never pressed once the
# overworld is back, where it would talk to the nurse. No debugger here, so
# the match score is the evidence; Playtest judges the frames.
frame_match="$(dirname "$Q3X")/frame_match.py"
before="$RUNNER_TEMP/averon-playtest/q3-play-x-after-party.png"
continue_result="NOT_SHOWN"
for attempt in 1 2 3 4; do
  press x; sleep 7; capture "q3x-relaunch-a-$attempt"
  set +e
  score=$(python3 "$frame_match" --min 0.70 "$before" "$RUNNER_TEMP/averon-playtest/q3x-relaunch-a-$attempt.png")
  match_rc=$?
  set -e
  echo "Q3X_RELAUNCH_A attempt=$attempt $score"
  if [ "$match_rc" -eq 0 ]; then continue_result="CLINIC_FIELD"; break; fi
  if [ "$match_rc" -eq 2 ]; then continue_result="UNAVAILABLE"; break; fi
done
sleep 3; capture "q3x-relaunch-continued"
kill "$emu_pid" 2>/dev/null || true
echo "Q3X_CONTINUE_RESULT $continue_result after $attempt A press(es); last: $score"
# Exit codes: 3 Continue not shown, 4 no flash, 5 no relaunch window,
# 6 saved slot missing or not the clinic; the observer's own code otherwise.
# Exit non-zero unless the observer and the Continue check both succeeded,
# so the job's status means something; the evidence uploads either way.
if [ "$q3x_rc" -ne 0 ]; then exit "$q3x_rc"; fi
[ "$continue_result" = "CLINIC_FIELD" ] || exit 3
echo "Q3X_DONE"
