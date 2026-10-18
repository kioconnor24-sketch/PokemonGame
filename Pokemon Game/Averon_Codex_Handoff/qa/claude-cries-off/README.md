# Cries-OFF graphical QA and RELEASE clinic crash: Claude takeover of PR #117 (2026-10-17)

This is supporting emulator evidence collected by Claude. It is not human listening, not a Delta (iOS) test, and not an independent review. It contains no ROMs, ELFs, saves or raw audio; `audio.raw` and `audio.wav` stay local.

## Builds (this host, from PR #117 source)

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
1. The game's own `SaveSuccessCallback` is observed, and no error callback is observed.
2. The save leaves a complete flash slot (14 ids, checksums valid, one counter) that is newer than the slot before it. Sector sizes come from a `sizeof` probe: SB2/SB1/PC = 3884/15568/34144 B.
3. A later `--expect-saved` fresh-process CONTINUE restores the map, position, party, flags, money and Bag pockets.

13 host tests cover corrupt, mixed, missing, duplicate and truncated slots, error dialogs, and lost state. The wrapper refuses to run with uncommitted engine, driver or wrapper changes.

## Runs (cries-OFF unless noted)

| Run | Result | Notes |
| --- | --- | --- |
| run01-newgame | **PASS** | Real input: naming → harbor → parcel → Piplup → SAVE. Success dialog seen; slot valid at counter 1. |
| run02a | observer bug (kept) | CONTINUE matched, but my checker compared a JSON list with a tuple. Fixed, with a test. |
| run02b | stopped (kept) | CONTINUE PASS; follower script PASS; Pokédex entry opened. The wrapper overshot to the SIZE page. Fixed. |
| run02-continue | **PARTIAL → CRASH** | CONTINUE == saved state **PASS**. Talking to the follower (`playfirstmoncry`) **PASS**: emote shown, control returned. Pokédex list, entry, CRY page and 3 replays, then close **PASS**. Walk to Alderfield **PASS** (no wild battle happened on the way). **Clinic heal: game crashed.** |
| run03-heal-repro-off | **CRASH reproduced** | Same save, straight to the clinic heal. |
| run04-heal-repro-on | **CRASH reproduced on cries-ON RELEASE** | So it is **not caused by the cries change**. |
| run05-normal-battles | **PASS** (normal `make CRIES=off`, ROM `473030df…`, source `19d8fe6c`) | All with real input, starting from the run02 save:<br>• Capture: Sentret caught, party of 2.<br>• 8 wild battles.<br>• Trainer battle: Sam on Orchard Lane, 2 Pokémon, won; Piplup learned Water Gun.<br>• 5 Alderfield clinic heals, no crash.<br>• SAVE: `SaveReturnSuccessCallback`; flash slot counter 2 is valid and newer than 1.<br>• Audio: 910 of 914 one-second windows audible, so music and SFX play with cries off. This is a level meter, not human listening. |

Not yet tested on the OFF build:
- fresh-process CONTINUE of run05's save (run06);
- faint/whiteout and evolution;
- clinic heal and SAVE→CONTINUE on the **RELEASE** OFF build: blocked on the crash fix below;
- Mega Evolution: no Averon content can reach it, so only the native tests cover it;
- the `playmoncry` script command: no Averon map uses it, so only the native tests cover it.

Human listening and Delta remain **UNTESTED**.

## DEFECT (root cause found, fix in a separate PR): RELEASE build crashes at the Alderfield clinic heal

**Root cause.** This is a baseline `main` defect. It reproduces on unchanged `main` RELEASE `c918e880…` and has nothing to do with cries. The full trace evidence is in [`debug/clinic-crash-root-cause/`](debug/clinic-crash-root-cause/README.md).
1. After the heal, the shared nurse script calls `BufferUnionRoomPlayerName`.
2. Averon clinics never run `InitUnionRoom`, so `sUnionRoomPlayerName` is still zero-filled. Zero is not EOS.
3. `StringCopy` into `gStringVar1` therefore runs to the next `0xFF`. On RELEASE/LTO that is about 35 KB later, so the copy zeroes every `gHeap` block header.
4. The next text-printer `Alloc` returns `0x10`.
5. `RunTextPrinters` then calls a BIOS open-bus value.

**Fix:** branch `claude/clinic-union-room-overflow` makes the buffer `EOS` from boot and adds the native test `test/averon_clinic_union_room.c`.

The investigation notes below are kept as they were written before the cause was known.

**Symptom:** mGBA 0.10.5 logs `GBA Memory: Jumped to invalid address: E55EC002` (or `E3A02004`) and then `The game crashed!`.

**Reproduction:** with Piplup as the only party member and the follower out, talk to the Alderfield clinic nurse and answer YES. The game has crashed in 6 out of 6 attempts on the RELEASE ROMs, both ON and OFF, and also on unchanged `main` RELEASE. Normal builds have healed at this clinic many times during M1 QA without a crash.

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
1. Run the same heal on a plain `main` RELEASE ROM to confirm main has it. The ROM was built locally (`/root/claude-dev/wt-mainrel`) but not yet run.
2. Single-step from `ScrCmd_waitmessage` to the bad jump to find the faulting instruction.
3. Check whether it also happens without the follower, and with a normal (non-RELEASE) build that has LTO enabled.
4. Fix it with a focused regression test.

Until then, the RELEASE build is not acceptable as the playable profile, whether cries are ON or OFF.

## Tooling issue found

When mGBA dies, the driver's `emu.Gdb._packet` spins forever (`recv` returns `b""` on EOF), so a crashed run hangs instead of failing. This is in Claude's driver (`scripts/claude_play/emu.py`).

It is fixed separately in PR #122, together with a regression test. A Claude read-only reviewer pass found no blocking issues, but that pass is not independent review. The PR needs the owner to review and merge it, because auto mode blocks Claude from merging its own PRs. This PR does not change `emu.py`.
