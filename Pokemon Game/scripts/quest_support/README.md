# QUEST support (Claude): Q3 clinic evidence and #14 → #25 integration plan

Diagnostic support only. **Playtest alone decides Q1–Q5 PASS/PARTIAL/FAIL**
([#23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23)); Codex
alone integrates. Nothing here approves #14 or #25.

## 1. Q3 clinic run (2026-10-17)

**Source:** PR #71 head `f34eab2184c40a7f6ab1bd74274c3058c7c0fdc9`
(Manager's clinic-expectation fix, based on QA #20 `e46beacf` → QUEST #14).

**Where it ran**
- Locally in a Claude cloud container: Xvfb + openbox + Debian `mgba-sdl`
  0.10.2 + xdotool + ImageMagick, i.e. the same packages the workflow
  installs. ROM built locally with arm-none-eabi-gcc 14.2.1:
  `pokeemerald.gba` SHA-256
  `ea245cdee799e3a51e129cb67b796fee00318cbec0f3363c6f3dfc03458ec6b0`. CI uses the
  Ubuntu toolchain, so its hash differs.
- The workflow's own "Launch actual graphical mGBA" step ran unchanged up to
  the end of its Q3 block. After that, `q3_post_battle_observer.py` ran in the
  same emulator process, followed by a no-debugger relaunch from the real flash
  file.
- **CI on the same head:** [run 38987375760](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38987375760)
  (workflow_dispatch) concluded success on every step; its screenshots and logs
  are artifact 12084371086. Claude's cloud proxy cannot download Actions
  logs/artifacts, so that run's case lines are for Playtest to read.

**Observed locally (screenshots and read-only GDB JSON)**

| Stage | Result |
|---|---|
| Q1 researcher offer, decline/accept | `QA_Q1_OFFER_PARTIAL_OBSERVED` (as before) |
| Q1 no-badge gate | `QA_Q1_BADGE_GATE_NEGATIVE_PASS` (as before) |
| Q2 artist, tree, real SAVE | `QA_SAVE_REAL_SUCCESS` (callback seen, 3 Oran) |
| Q4 Script4 gift | `QA_Q4_GIFT_POSITIVE_FLAG_PARTY_PASS` |
| Q3 clinic entry (#71 expectation) | `QA_Q3_SOURCE_HEAL_WARP_PRESENT`: inside clinic (75,11); saved heal = (75,9) x17 y13 warp -1 = `HEAL_LOCATION_ALDERFIELD` |
| Q3 Elio battle | real battle, 80 ordinary A presses; `QA_Q3_ORIGINAL_BATTLE_EXIT_NO_BADGE` |
| **Q3 whiteout destination** | **NEW:** frame `q3-play-x-002` reads "…scurried to a POKéMON CENTER, protecting the exhausted and fainted POKéMON…"; read-only position right after = map **(75,11) x7 y4**, the `respawn_map`/`respawn_x`/`respawn_y` of `HEAL_LOCATION_ALDERFIELD` in `src/data/heal_locations.json`. Badge01 stays false, party count 1. |
| Nurse heal dialogue | **NOT OBSERVED** (observer defect, below) |
| Q3 Save + Continue at clinic | **NOT DONE**: the flash still holds the Q2 slot (counter 1, map 75/6 x19 y14) |

In short, the run shows a genuine Elio defeat followed by a whiteout respawn at
the clinic's source-defined respawn tile. It does **not** show nurse healing
or Save/Continue at the clinic.

**Observer defects (`q3_post_battle_observer.py` as run):**
1. Its text detector only looks for the white dialogue box. The whiteout
   message is white text on black, so the observer treated it as idle
   instead of pressing A. Fix: also press A while the frame is mostly black
   with text (or until the field is visible via `assert-ui --kind field`).
2. The Start menu offered actions `[2,4,5,6,7]`, with no POKéMON (1), so the
   party-screen step raised. The Q4 developer gift gives a Pokémon without
   the normal "has Pokémon" unlock. That is a fixture property, not a claimed
   game defect. Skip the party screen when action 1 is absent.

**Reproduce:** build the ROM at the #71 head, then run the workflow step with
`RUNNER_TEMP` set. After the Q3 block, call:

```
python3 -u "Pokemon Game/scripts/quest_support/q3_post_battle_observer.py" \
  --controller-dir "Pokemon Game/scripts/qa" --fifo "$qa_fifo" \
  --outdir "$RUNNER_TEMP/averon-playtest" --window "$win"
```

## 2. Remaining Q1–Q5 cases: exact obstacle

- **Badge01 → Hiker (Q1 positive):** Elio (`TRAINER_AVERON_ELIO`) fields
  Bunnelby 12, Lechonk 13 and Lillipup 15. The only fixture party is the
  Q4 gift (one Lv 5 Wobbuffet, in this run). A legitimate win needs ordinary
  training of a real party: hours of play. The no-write rule forbids setting
  badges, levels or party. **Blocked for automation**; needs a human
  playthrough or an owner-approved save fixture.
- **Full-Bag / full-party refusal (Q1, Q2, Q4):** these need a full Balls or
  Berries pocket and six party Pokémon reached by ordinary play. Same
  obstacle; no existing fixture provides them.
- **Q5 audio/input:** CI and this container use `SDL_AUDIODRIVER=dummy`, so
  there is no audio evidence. This needs a human or Delta run.

## 3. #14 → #25 integration plan (read-only rehearsal)

**Heads checked:** main `59a23eeb`, #14 `db6baaea` (118 behind main), #25
`f324e485` (96 behind).

1. **Overlap:** the only shared file is `engine/data/event_scripts.s`. #14
   appends `AveronFieldLab_Gift::`/`AveronFieldLab_TryGift::` stubs near
   line 1785; #25 adds `.include "data/scripts/averon_scripted_battle.inc"`
   near line 78. `git merge` of main ← #14 ← #25 is **conflict-free**
   (local rehearsal 54945294; CI below).
2. **IDs:** #14 takes saved flag `0x37` (`FLAG_AVERON_DEV_GIFT_RECEIVED`,
   previously `FLAG_UNUSED_0x037`). #25 binds `B_FLAG_NO_WHITEOUT` to
   RAM-only `FLAG_SPECIAL_FLAG_UNUSED_0x4003`. No collision; main has not
   changed `flags.h` since #14's base. `audit-averon-event-ids.py`: 0
   blockers.
3. **Rehearsal checks:**
   - `check_integration_contract.py` PASS, including the battle macro include
     (line 81) preceding the QUEST include (line 1770).
   - Source tests: 9/9 `test-averon-scripted-battle.py`,
     7/7 `test-averon-quest-flow.py`, 10/10 `test-averon-sidequests.py`.
   - CI [combined run 38987964339](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38987964339)
     (main + #14 + #25): compile, native/save tests and readiness report all
     success (artifact 12084190737).
4. **Gate blocker (real, not textual):** both PRs currently fail the required
   `exclusive-files` check, because `check_protected_files.py` fails any PR
   whose protected paths overlap another *open* PR. #14's grandfathering
   exempts it only from the approval and frozen-map checks, not from the
   overlap rule. #14 therefore cannot get a green required check while #25
   still touches `event_scripts.s`, even after Playtest acceptance.
5. **Suggested legitimate order (Codex decides):**
   1. On #25, a normal commit temporarily drops its one
      `event_scripts.s` line. #25 is still a draft; its remaining protected
      path, `config/battle.h`, is already approved by
      [6209610910](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6209610910).
      No PR is closed or hidden. (#25's source contract will then report the
      missing include. That is expected while #25 is a draft.)
   2. Re-run #14's `exclusive-files`; once Playtest accepts, merge #14
      normally. Main checks are non-strict, so #14 need not be rebased; the
      rehearsal shows the merge is clean.
   3. Merge main into #25 and restore the `.include` line, which must stay
      above the QUEST include.
   4. Re-run guard, contract, source and native checks, then merge #25. Its
      `event_scripts.s` approval is already recorded.
   5. Post-merge: run the full native suite and baseline check, the release
      build, and `report-averon-save-headroom.py`.
