# Cries-OFF graphical QA and RELEASE clinic crash: Claude takeover of PR #117 (2026-10-17)

This is supporting emulator evidence collected by Claude. It is not human listening, not a Delta (iOS) test, and not an independent review. It contains no ROMs, ELFs, saves or raw audio; `audio.raw` and `audio.wav` stay local.

## Builds (this host, from PR #117 source)

**Current head:** `c77fbd69`, which is #117 merged with main `43a95f85`. It includes the clinic-heal fix #124 (`3f754bec`) and the GDB fail-fast driver fix #122. Both profiles build with exit 0. The only warnings are the 4 newlib stub notes plus 1 assembler warning (`.rodata.compound_string… size is not a multiple of its entry size`). The assembler warning is pre-existing: main's RELEASE build has it too:

| ROM | ROM sha256 | ELF sha256 |
| --- | --- | --- |
| `make RELEASE=1 CRIES=off` | `06e3e40a9a7f…` | `32531a987b8d…` |
| `make RELEASE=1 CRIES=on` | `4dbf3be40291…` | `016a8dad1118…` |

The OFF ROM is byte-identical to the one built from the earlier test merge `claude/test-merge-117-124`, so the build is reproducible.

Native `Averon cry safety` on `c77fbd69`: **9/9 PASS** on each profile, both headless (`make CRIES=… check`) and non-headless (hydra on the unpatched test ELF). After the review fixes it is **10/10** on each profile, both headless and non-headless. The new test reads BGM volume straight after `PlayCry_Normal`/`ByMode`/`Script`, and is RED if the OFF gating is removed. See `builds-c77fbd69/README.md`.

The earlier builds, from before the merge:

| ROM | ROM sha256 | ELF sha256 |
| --- | --- | --- |
| `make RELEASE=1 CRIES=off` | `7692bb76de28…` | `2c23b1021d47…` |
| `make RELEASE=1 CRIES=on` | `b937b91ad540…` | `2e4de9c9f93d…` |

Hashes differ from Codex's because the build environment differs. `codex_cry_profiles.py` on this host reports:
- ON uses 26,855,196 B and OFF uses 17,438,636 B, a saving of **9,416,560 B**. Codex measured 9,416,568 B.
- **530** song objects and **156** non-cry samples are byte-identical between the two profiles.

The native `Averon cry safety` tests were rebuilt without the headless patch (`headless=0`) and run through `mgba-rom-test-hydra`:
- **ON 9/9 PASS**
- **OFF 9/9 PASS**

This reproduces Codex's result.

## RELEASE save check (`scripts/coordination/codex_cry_gameplay.py`)

`gSaveAttemptStatus` cannot be trusted in RELEASE: LTO removes the stores to it. A save now has to pass three checks:
1. The game's own success callback is observed (`SaveSuccessCallback` or `SaveReturnSuccessCallback`; runs 05 and 07 saw the latter), and no error callback is observed.
2. The save leaves a complete flash slot (14 ids, checksums valid, one counter) that is newer than the slot before it. Sector sizes come from a `sizeof` probe: SB2/SB1/PC = 3884/15568/34144 B.
3. A later `--expect-saved` fresh-process CONTINUE restores the map, position, party, money, **14 named story flags** (`game.py`) and the **Poké Ball and Berry pockets** (`RESTORED_KEYS`). Other flags and pockets are not compared.

18 host tests in `test_codex_cry_gameplay.py` cover corrupt, mixed, missing, duplicate and truncated slots, error dialogs and lost state. `test_codex_cry_profiles.py` adds 5 more. No CI workflow runs either module yet. The wrapper refuses to run with uncommitted engine, driver or wrapper changes.

## Runs (cries-OFF unless noted)

| Run | Result | Notes |
| --- | --- | --- |
| run01-newgame | **PASS** | Real input: naming → harbor → parcel → Piplup → SAVE. Success dialog seen; slot valid at counter 1. |
| run02a | observer bug (kept; written as `run02-continue` and renamed afterwards, so its `mgba.log` names that folder) | CONTINUE matched, but my checker compared a JSON list with a tuple. Fixed, with a test. |
| run02b | stopped (kept; same renaming as run02a) | CONTINUE PASS; follower script PASS; Pokédex entry opened. The wrapper overshot to the SIZE page. Fixed. |
| run02-continue | **PARTIAL → CRASH** | CONTINUE == saved state **PASS**. Talking to the follower (`playfirstmoncry`) **PASS**: emote shown, control returned. Pokédex list, entry, CRY page and 3 replays, then close **PASS**. Walk to Alderfield **PASS** (no wild battle happened on the way). **Clinic heal: game crashed.** |
| run03-heal-repro-off | **CRASH reproduced** | Same save, straight to the clinic heal. |
| run04-heal-repro-on | **CRASH reproduced on cries-ON RELEASE** | ON and OFF both contain this PR's `sound.c` change, so this run alone does not clear the PR. The proof that the crash is not caused by cries is the later repro on **unchanged main** RELEASE, plus the root cause below. |
| run05-normal-battles | **PASS** (normal `make CRIES=off`, ROM `473030df…`, source `19d8fe6c`) | All with real input, starting from the run02 save. **12 battles** (`events.jsonl`: 12 `battle-start`):<br>• Capture: Sentret caught, party of 2.<br>• 10 other wild battles. Piplup learned Water Gun at L8 in `wild006`, before the trainer.<br>• Trainer battle: Sam on Orchard Lane, 2 Pokémon, won.<br>• **9** Alderfield clinic heals (`healed` events), no crash.<br>• SAVE: `SaveReturnSuccessCallback`; flash slot counter 2 is valid and newer than 1.<br>• Audio: 910 of 914 one-second windows non-silent with cries off. A level meter can't tell music from SFX, and this is not human listening. |
| run06-normal-continue | **PASS** (same ROM; source `90863ffd`, evidence-only change) | • Fresh-process CONTINUE matches run05's saved state: map, position, party, money, 14 named flags, and the Poké Ball and Berry pockets.<br>• Talking to the follower (`playfirstmoncry` path): control returned.<br>• Pokédex list, entry, CRY page and 3 replays, then close.<br>• First clinic heal after power-on: no crash. This build still has the unbounded Union Room copy (no fix); it just doesn't crash here.<br>• Audio: 52 of 62 windows audible. |
| run07-normal-evolve-whiteout | **PASS** (normal `make CRIES=off`, from the natural M1 save `4ca9b7f4…`) | • `evolve_lead`: after 22 wild battles Piplup reached L16 and evolved into Prinplup through the real evolution scene; 6 scene frames kept.<br>• `q3_whiteout`: the whole party fainted, then respawned at the Alderfield clinic. Clinic check passed: healed, follower present, same members, money lost.<br>• SAVE: success callback; both flash slots valid.<br>See `run07-…/RESULT.md`. |
| run08-release-heal-battles | **STOPPED, partial** (RELEASE OFF `06e3e40a…`, head `c77fbd69`) | • **First clinic heal after power-on: no crash**, plus 2 more heals on the fixed RELEASE build.<br>• It then exposed a **QA driver defect**: under LTO the battle controller is `HandleInputChooseAction.lto_priv.N`, so the driver's exact-name **action-menu** logic (throw a ball, run) never ran and the catch phase looped. The move menu (`HandleInputChooseMove` keeps its plain name) still worked: 46 `turn` events.<br>• Fixed in the wrapper (`use_source_function_names`, with a test) and rerun as run09. See `run08-…/STOPPED.md`. |
| run09-release-battles | **PASS** (RELEASE OFF `06e3e40a…`, wrapper with source function names, `source_unchanged: true`) | From run02's save `73c3b87d`, with real input. **8 battles** (`events.jsonl`):<br>• First clinic heal after power-on, then **6 heals in total**, no crash.<br>• **Capture:** one Poké Ball throw caught a Fletchling, party of 2.<br>• Wild battles trained Piplup to L8; it learned Water Gun.<br>• **Trainer battle:** Sam beaten, no whiteout.<br>• **SAVE:** `SaveSuccessCallback` and `SaveReturnSuccessCallback`; flash slots valid, counter 2 newer than 1.<br>• Audio: 815 of 819 windows non-silent. |
| run10-release-continue | **PASS** (same ROM) | • **Fresh-process CONTINUE** of run09's save matched the saved state (`continue-check.json`, no problems).<br>• A clinic heal after the reload: no crash. |
| run11-release-on-check | **PASS** (**cries-ON** RELEASE `4dbf3be4…`) | Checks that the reversible ON profile still runs on the merged head, from save `73c3b87d`:<br>• First clinic heal after power-on: no crash.<br>• **Capture** after 2 ball throws, party of 2.<br>• Pokédex list, entry, **CRY page** and 3 replays (`PlayCry_NormalNoDucking` with cries enabled), then close.<br>This is runtime evidence only. Whether the cries are audible was not judged by a human. |
| run12-release-evolve-whiteout | **PASS** (RELEASE OFF `06e3e40a…`, natural M1 save `4ca9b7f4…`, `source_unchanged: true`) | **29 battles** (`events.jsonl`):<br>• `evolve_lead`: after 19 wild battles Piplup reached L16 and **evolved into Prinplup** through the real evolution scene; 6 scene frames kept.<br>• `q3_whiteout`: a genuine loss over 10 battles, then respawn at the Alderfield clinic. Clinic check passed: healed, follower present, same members, money lost.<br>• **SAVE:** `SaveSuccessCallback` and `SaveReturnSuccessCallback`; both flash slots valid, newest counter 15 versus 14.<br>• Audio: 1383 of 1398 windows non-silent. |

**Provenance note.** `provenance-*.json` records the checked-out commit, not the ROM's build input. Runs 06 and 07 have `source_unchanged: false` because evidence-only commits landed during the run: 90863ffd..a1acf662 and 3ca8cbc0..a276745e. Neither range touches the engine, driver or wrapper (`git diff --stat` on those paths is empty). run08 also has `source_unchanged: false`: the Makefile and `test/averon_cry_safety.c` were edited during the run, after its ROM had been copied. Because it was stopped with SIGINT, its `provenance-end.json` has no `completed` key. The ROM sha256 in each provenance file identifies what actually ran.

Not yet tested on the OFF build:
- Mega Evolution: no Averon content can reach it, so only the native tests cover it;
- the `playmoncry` script command: no Averon map uses it, so only the native tests cover it.

Human listening and Delta remain **UNTESTED**.

## DEFECT (FIXED on main by #124 `3f754bec` and merged into this branch at `c77fbd69`): RELEASE build crashed at the Alderfield clinic heal

**Root cause.** This is a baseline `main` defect. It reproduces on unchanged `main` RELEASE `c918e880…` and has nothing to do with cries. The full trace evidence is in [`debug/clinic-crash-root-cause/`](debug/clinic-crash-root-cause/README.md).
1. After the heal, the shared nurse script calls `BufferUnionRoomPlayerName`.
2. Averon clinics never run `InitUnionRoom`, so `sUnionRoomPlayerName` is still zero-filled. Zero is not EOS.
3. `StringCopy` into `gStringVar1` therefore runs to the next `0xFF`. On RELEASE/LTO that is about 35 KB later, so the copy zeroes every `gHeap` block header.
4. The next text-printer `Alloc` returns `0x10`.
5. `RunTextPrinters` then calls a BIOS open-bus value.

**Fix:** PR #124, branch `claude/clinic-union-room-overflow`. It makes the buffer `EOS` from boot and adds the native test `test/averon_clinic_union_room.c`.
- The test **crashes without the fix** and **passes with it**.
- The fixed RELEASE ROM healed twice at the clinic on the save that always crashed, with the heap intact; see [`fix-verification/`](debug/clinic-crash-root-cause/fix-verification/README.md).

The investigation notes below are kept as they were written before the cause was known.

**Symptom:** mGBA 0.10.5 logs `GBA Memory: Jumped to invalid address: E55EC002` (or `E3A02004`) and then `The game crashed!`.

**Reproduction:** with Piplup as the only party member and the follower out, talk to the Alderfield clinic nurse and answer YES. It crashed on every unfixed RELEASE attempt: the 3 committed runs (02, 03 and 04, ON and OFF) plus the debug runs, including unchanged `main` RELEASE. Normal builds have healed at this clinic many times during M1 QA without a crash.

**Where it crashes** (`debug/crash_regs.py`, hardware breakpoints, key input only):
1. The nurse script runs normally through `FldEff_PokecenterHeal`, the ball animation, the MUS_HEAL fanfare, `HealPlayerParty` and `UpdateFollowingPokemon`.
2. It then runs the Pokérus, Trainer Hill and Union Room checks, `message gText_RestoredPkmnToFullHealth` and `waitmessage`.
3. The crash comes while "Thank you for waiting…" is printing.

**Ruled out:**
- *Entering the clinic.* Walking from the door to the counter with no debugger traffic did not crash.
- *Debugger traffic.* The crash also happens with key presses only.
- *The fanfare ending.* A breakpoint on `Task_Fanfare`'s BGM-resume path never fired before the crash.

**Clues:**
- The bad jump target is an ARM instruction word, and it differs between runs. `E3A02004` occurs in ROM inside `sio32intr_clock_master`, but read watchpoints on those words never fired. `E55EC002` does not occur in the ROM at all.
- RELEASE stack use is higher: 2,648–2,724 B of the 3,984 B region, compared with ≤2,376 B on normal builds. Write watchpoints on the last IWRAM variables (`gPostBattleMovementScript`, `gMenuCallback`) and on `gMPlayJumpTable` entries never fired, so a simple stack overflow into `.iwram.bss` looks **unlikely**. I have not confirmed that mGBA watchpoints catch every write.
- Script commands tagged `requests_effects=1` correctly run from ROM mirror 1 (`+ROM_SIZE`, `script.c`). That is upstream design, not the bug.

**Next steps:**
1. Run the same heal on a plain `main` RELEASE ROM to confirm main has it. The ROM was built locally (`/root/claude-dev/wt-mainrel`) but not yet run. *[Later: done. Main crashes too, and the cause is above.]*
2. Single-step from `ScrCmd_waitmessage` to the bad jump to find the faulting instruction.
3. Check whether it also happens without the follower, and with a normal (non-RELEASE) build that has LTO enabled.
4. Fix it with a focused regression test.

Until then, the RELEASE build is not acceptable as the playable profile, whether cries are ON or OFF.

## Tooling issue found

When mGBA dies, the driver's `emu.Gdb._packet` spins forever (`recv` returns `b""` on EOF), so a crashed run hangs instead of failing. This is in Claude's driver (`scripts/claude_play/emu.py`).

It is fixed separately in PR #122, together with a regression test. A Claude read-only reviewer pass found no blocking issues, but that pass is not independent review. The PR needs the owner to review and merge it, because auto mode blocks Claude from merging its own PRs. This PR does not change `emu.py`.
