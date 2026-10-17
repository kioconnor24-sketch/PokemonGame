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
| Nurse heal dialogue | Run 1: **NOT OBSERVED** (observer defects 1–2, below). Run 2: **OBSERVED**, see below |
| Q3 Save + Continue at clinic | Local runs 1–2: **NOT DONE**. **CI run 38996685926: save written at (75,11) x7 y4 and Continue restored the clinic field**; see CI runs below |

In short, the run shows a genuine Elio defeat followed by a whiteout respawn at
the clinic's source-defined respawn tile. It does **not** show nurse healing
or Save/Continue at the clinic.

**Run 2 (2026-10-17, same ROM `ea245cde…`, same #71 head, observer `7770455e`):**
the workflow step was unchanged, followed by the observer with defects 1–2
fixed. Ordinary input only; read-only GDB.

- `q3-play-x-002` and `-003` show the whiteout text, white on black at 0.965
  and 0.922 black. A advanced it, and the position read (75,11) x7 y4.
- `q3-play-x-004` to `-013` show the source after-whiteout nurse script
  (`EventScript_AfterWhiteOutHeal`) in the lit clinic, with the player in
  front of the nurse. The text, advanced only with A, read:
  "First, you should restore your POKéMON to full health." →
  "Your POKéMON have been healed to perfect health." →
  "If your POKéMON's energy, HP, is down, please come see us." →
  "If you're planning to go far in the field, you should buy some POTIONS
  at the POKéMON MART." → "We hope you excel!" Badge01 stayed false and the
  party count stayed 1.
- `q3-play-x-014` is the idle clinic field. The lit floor reads 0.33 on the
  shared panel crop (defect 3), so the observer pressed A, re-talked to the
  nurse and repeated ordinary heal conversations until its 90-frame limit.
  Its Start press then landed in an open text box (`save-q3x-save-open.png`
  shows a text box and no Start menu). The stale menu globals passed the
  menu check, and the step stopped with `SAVE confirm callback never
  observed`. Nothing was saved; flash sha256 `2dfa3d1c…` still decodes to
  the Q2 slot.
- Not measured: party HP. The read-only probe has no HP field, so "healed"
  rests on the game's own message above. HP also returns through the
  whiteout itself (`HealPlayerParty` in `overworld.c`).

**Observer defects (`q3_post_battle_observer.py` as run):**
1. Its text detector only looks for the white dialogue box. The whiteout
   message is white text on black, so the observer treated it as idle
   instead of pressing A. Fix: also press A while the frame is mostly black
   with text (or until the field is visible via `assert-ui --kind field`).
2. The Start menu offered actions `[2,4,5,6,7]`, with no POKéMON (1), so the
   party-screen step raised. The Q4 developer gift gives a Pokémon without
   the normal "has Pokémon" unlock. That is a fixture property, not a claimed
   game defect. Skip the party screen when action 1 is absent.
3. (Run 2) The clinic floor reads 0.33 on the panel crop, above the generic
   0.30 field threshold, while clinic text boxes read 0.85–1.00. The
   observer now treats only > 0.60 as text and stops if the clinic never
   goes idle. Before trusting the menu globals it requires a visible Start
   window (0.90 bright when open, ≤ 0.23 in every other calibration frame).

Defects 1–2 were fixed in `7770455e`, defect 3 in `a6c32659`.

**CI runs** (`.github/workflows/averon-quest-support-q3.yml`, pinned #71 `f34eab21`):

| Run | Observer | Result |
|---|---|---|
| [38993271535](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38993271535) | `a6c32659` | The manager opened the frames: the whiteout text (`q3-play-x-002`), the nurse's after-whiteout heal (`-006` to `-012`) and a clinic Start → SAVE were real. Both "continued" frames still showed the CONTINUE / NEW GAME menu, so Continue was **not** shown (defect 5) |
| [38994567345](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38994567345) | `a6c32659` | Annotations: whiteout text `x-001`/`-002`, nurse `x-003` to `-012`. **Flash after shutdown: slot 0, save counter 2, map (75,11) x7 y4**, a new save at the clinic nurse tile. Observer rc 1, "Save message never closed" (defect 4) |
| [38996685926](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38996685926) | `96f49e7c` | **Full path, observer rc 0.** Whiteout text `x-001`/`-002`; nurse `x-003` to `-012`; `Q3X_SAVE_SUCCESS` (game callback, back in `CB2_Overworld`); flash slot 0, counter 2, (75,11) x7 y4. Then a no-debugger relaunch: after 3 A presses (title → menu → CONTINUE), `Q3X_CONTINUE_RESULT CLINIC_FIELD`, with 0.999 identical pixels against the pre-save clinic frame (mean difference 0.05). Artifact 12087349379. For Playtest's verdict |

4. The post-save check used the generic 0.30 field threshold, which the lit
   clinic floor (0.33) exceeds. Fixed in `20f7a8ea`: the 0.60 clinic
   calibration, and the success callback printed when it occurs.
5. The relaunch's fixed key sequence stopped at the CONTINUE menu. Fixed in
   `96f49e7c`: after the title, press A at most four times. After each press,
   `frame_match.py` compares the frame with the last pre-save clinic field
   frame, and the presses stop as soon as it matches (so A is never pressed
   beside the nurse). The job fails unless both the observer and this check
   pass.

**Reproduce:** push to this PR (the workflow runs on changes to itself or to
`scripts/quest_support/**`), or locally: build the ROM at the #71 head, then
run `compose_q3_run.py --workflow <#71>/.github/workflows/averon-rendered-playtest.yml
--out run.sh` and `Q3X=<observer path> bash run.sh` from the #71 checkout.

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

## 3. #14 → #25 integration (status 2026-10-17)

Steps 1–2 of the earlier plan are done; the rest waits on Playtest:

- **Core:** the scripted-battle core merged as core-only #81 (`6d5c0967`).
  #25 returned `config/battle.h` to its base (`ba24e52d`) so #81 had no
  protected overlap.
- **#25 now:** after `090ecbdb` (main merged) and the owner-directed
  `bfffafac` (include held back), #25 is a draft whose only remaining
  change is its evidence document. #14's `exclusive-files` is green.
- **Next, after Playtest's GATE A on #23:**
  1. Merge #14 normally.
  2. Merge main into #25 and restore the scripted-battle include, plus the
     LEGEND include from `claude/legend-registration` (`901a3533`). Both go
     above the QUEST include, under #25's existing `event_scripts.s` handoff.
  3. Verify and merge.
- **Proof:** the end state (main + #48 + #14 + #25 + LEGEND) already passes
  the integration contract, normal and release builds, and the full
  unfiltered native suite (6,093 tests, strict baseline OK):
  [#15 6228649047](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6228649047).
- **Not linked yet:** with no scene caller, LEGEND and SCRIPTED natives are
  dead-stripped from the ROM. This is recorded as POST-CONTENT in
  `BACKEND_TO_SINNOH_EXECUTION.md` (#85).
