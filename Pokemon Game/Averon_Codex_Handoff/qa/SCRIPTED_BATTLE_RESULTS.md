# SCRIPTED-BATTLE results — 2026-10-15

Scope: PR #25 (`claude/scripted-battle`). The building blocks are installed
in the ROM: `event_scripts.s` includes `averon_scripted_battle.inc`, and the
release `B_FLAG_NO_WHITEOUT` is the RAM-only `FLAG_SPECIAL_FLAG_UNUSED_0x4003`
(owner gate exception and Codex handoff, #15 comment 6205844637). **No scene
uses them yet**: Renn, the operatives and the ambush wait for approved
trainers and text, so no scripted battle can be played. Nothing here is
EMULATOR-TESTED.

## How to rerun

From `Pokemon Game/engine` in a WSL checkout with the existing toolchain:

```bash
make -j20 -O check TESTS=Averon
```

```bash
python3 "../scripts/test-averon-scripted-battle.py"
```

Native tests use the release flag. One test fails if `B_FLAG_NO_WHITEOUT`
is ever not `FLAG_SPECIAL_FLAG_UNUSED_0x4003`.

Labels: **NATIVE** means executed in the native test ROM. **SOURCE** means a
script reads the code; it checks the listed callers, but it is not a full
control-flow proof. **GUI** means a rendered emulator run by ChatGPT QA. No
GUI evidence exists yet.

## Flag lifecycle evidence

| Boundary | Evidence | Label |
| --- | --- | --- |
| Where the flag is stored | Its byte is in EWRAM and outside SaveBlock1, 2, 3 and Pokémon storage (all including their ASLR padding); setting it changes no saved byte. Mutation: moving the flag to saved flag `0x20` fails this and two other tests | NATIVE |
| Flash save and load | A set flag is not restored by a real `TrySavingData`/`LoadGameSave` round trip; a badge flag is | NATIVE |
| Scripted battle, win or loss | The macro's `Begin` and `Finish` natives, run by the script engine around a real AI battle: the flag survives the battle, then `Finish` reports the result in `VAR_RESULT` and clears it; a loss keeps the money. Mutations: `Finish` not clearing the flag fails 5 tests; `Finish` always reporting a win fails 3 | NATIVE |
| Low-level `LoadGameSave` alone | It copies flash into the save blocks and does **not** clear a set flag. Safety comes from the RAM reset on every real entry path (next three rows), not from the load itself | NATIVE |
| Boot | crt0 zeroes EWRAM before `intro.c` loads the save | SOURCE |
| Soft reset, then Continue | `DoSoftReset` ends in `SoftReset(RESET_ALL)`; main menu Continue is reached only from boot or that reset | SOURCE |
| In-process reload | `ReloadSave` calls `RegisterRamReset(RESET_EWRAM)` before `LoadGameSave(SAVE_NORMAL)`; these three files are the only normal-save loaders | SOURCE |
| Ordinary loss after a scripted win, or after a scripted loss and respawn | The next ordinary trainer loss whites out and takes money in both cases | NATIVE |
| Switching inside a chain battle | Damage and poison carry back for every Pokémon the player switched in | NATIVE |
| The macro's full expansion | `Begin`, one `trainerbattle` (always fight, continue script, single, not rematch) and `Finish`, in that order | NATIVE (bytes); the `trainerbattle` itself needs the overworld and is not run |

## QA_MATRIX rows and current evidence

| QA_MATRIX row | What is proven now | Status | Still needs |
| --- | --- | --- | --- |
| Renn's scripted loss always progresses; money protection | Real AI trainer loss with the flag: no whiteout text, money unchanged. Without it: whiteout text, money lost. Respawn heals the party, keeps money and targets the last heal location (clinic or home). Example script records progress before the battle and continues on a win too | NATIVE-TESTED (primitives) | Approved Renn trainer and scene; emulator run |
| Nuzlocke exception | Not applicable: Nuzlocke is paused (AGENTS.md) | NOT RUN | Owner decision to resume Nuzlocke |
| Nadia's follow-up starts without healing, recoverable after loss, leaves badge | `Finish` never heals; respawn after a loss keeps `FLAG_BADGE01_GET`; badge survives a real flash save/load | NATIVE-TESTED (primitives) | Registered Gym script and ambush trainer (two Pokémon per the design); emulator run |
| Ten single-Pokémon operative battles keep HP/status | A real won battle carries HP damage and poison back into the party; `Finish` leaves HP and burn untouched between battles | NATIVE-TESTED (primitives) | Operative trainers (one Pokémon each); registered chain; emulator run |
| Ally heal after the tenth opponent, once per phase | Example script heals only after the last win; the source check rejects a win falling into the loss path | SOURCE | Registered chain; emulator run |
| Checkpoint resilience for the chain | A loss mid-chain respawns safely. Whether beaten operatives stay beaten after a retry is not decided | BLOCKED | Owner/design decision; a saved progress var (Codex handoff) |
| No-whiteout state never leaks into ordinary battles | `Finish` clears the flag on a win or a loss; an ordinary loss after a scripted battle whites out and takes money; mutation (no clear in `Finish`) makes the leak test fail | NATIVE-TESTED (release flag) | Emulator run once a scene exists |
| Save/reload mid-sequence | A RAM-only special flag is not restored from a real flash save, while the badge is. Scripted sequences run inside one locked script, so saving is not possible mid-sequence | NATIVE-TESTED (release flag); every reset that precedes a save load wipes RAM (SOURCE check) | Emulator run once a scene exists |

## Integration status

1. Done: `include/config/battle.h` sets `B_FLAG_NO_WHITEOUT` to
   `FLAG_SPECIAL_FLAG_UNUSED_0x4003`. It is RAM-only, so there is no
   `flags.h` or SaveBlock change, and `0x38–0x3F` stays unallocated.
2. Done: `data/event_scripts.s` includes `data/scripts/averon_scripted_battle.inc`.
3. #25 merges only after QUEST #14. QUEST's own `event_scripts.s` lines are
   kept when #25 is rebased.
4. Waiting: trainers and scenes, once the owner approves rosters and text.
   Then native tests that run each registered scene, and ChatGPT QA
   emulator cases for each row above.

## Known gap: running from a scripted battle

`B_RUN_TRAINER_BATTLE` is `TRUE`, so the player can Run from a trainer battle,
which forfeits. `BattleScript_ForfeitBattleGaveMoney` (`battle_scripts_1.s`)
runs `getmoneyreward` without checking `B_FLAG_NO_WHITEOUT`, so a forfeit
takes whiteout money even in a scripted battle (SOURCE). The test runner has no
Run action, so this path cannot be executed natively.

Owner decision (2026-10-16): the player cannot run from a scripted battle;
ordinary trainer battles keep forfeiting. The fix is one line in
`CanPlayerForfeitNormalTrainerBattle()` (`src/battle_main.c`, shared). It is
claimed in #15 and waits for Codex's acknowledgement. Its native test already
fails before the fix and is held back until then.
