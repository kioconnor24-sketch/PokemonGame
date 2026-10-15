# SCRIPTED-BATTLE results — 2026-10-15

Scope: PR #25 (`claude/scripted-battle`). These are **script building blocks
and native tests only**. No scripted battle is registered in the game yet:
`event_scripts.s` does not include `averon_scripted_battle.inc`, and the
release `B_FLAG_NO_WHITEOUT` is still `0`, so in the ROM a loss still whites
out. Nothing here is EMULATOR-TESTED.

## How to rerun

From `Pokemon Game/engine` in a WSL checkout with the existing toolchain:

```bash
make -j20 -O check TESTS=Averon
```

```bash
python3 "../scripts/test-averon-scripted-battle.py"
```

Test builds map `B_FLAG_NO_WHITEOUT` to `TESTING_FLAG_UNUSED_3` in
`include/config/test.h`, so the real lost-battle path runs in native tests.
One test fails if that mapping is ever lost.

## QA_MATRIX rows and current evidence

| QA_MATRIX row | What is proven now | Status | Still needs |
| --- | --- | --- | --- |
| Renn's scripted loss always progresses; money protection | Real AI trainer loss with the flag: no whiteout text, money unchanged. Without it: whiteout text, money lost. Respawn heals the party, keeps money and targets the last heal location (clinic or home). Example script records progress before the battle and continues on a win too | NATIVE-TESTED (primitives) | Registered scene, Renn trainer, release flag; emulator run |
| Nuzlocke exception | Not applicable: Nuzlocke is paused (AGENTS.md) | NOT RUN | Owner decision to resume Nuzlocke |
| Nadia's follow-up starts without healing, recoverable after loss, leaves badge | `Finish` never heals; respawn after a loss keeps `FLAG_BADGE01_GET`; badge survives a real flash save/load | NATIVE-TESTED (primitives) | Registered Gym script and ambush trainer (two Pokémon per the design); emulator run |
| Ten single-Pokémon operative battles keep HP/status | A real won battle carries HP damage and poison back into the party; `Finish` leaves HP and burn untouched between battles | NATIVE-TESTED (primitives) | Operative trainers (one Pokémon each); registered chain; emulator run |
| Ally heal after the tenth opponent, once per phase | Example script heals only after the last win; the source check rejects a win falling into the loss path | SOURCE | Registered chain; emulator run |
| Checkpoint resilience for the chain | A loss mid-chain respawns safely. Whether beaten operatives stay beaten after a retry is not decided | BLOCKED | Owner/design decision; a saved progress var (Codex handoff) |
| No-whiteout state never leaks into ordinary battles | `Finish` clears the flag on a win or a loss; an ordinary loss after a scripted battle whites out and takes money; mutation (no clear in `Finish`) makes the leak test fail | NATIVE-TESTED | Release flag; emulator run |
| Save/reload mid-sequence | A RAM-only special flag is not restored from a real flash save, while the badge is. Scripted sequences run inside one locked script, so saving is not possible mid-sequence | NATIVE-TESTED (candidate flag) | Codex handoff to adopt the special flag in `config/battle.h` |

## Integration steps (after QUEST #14 merges and Codex hands off)

1. `include/config/battle.h`: `#define B_FLAG_NO_WHITEOUT FLAG_SPECIAL_FLAG_UNUSED_0x4003`.
   RAM-only, so no `flags.h` or SaveBlock change and no use of the tentative
   `0x38–0x3F` range.
2. `data/event_scripts.s`: include `data/scripts/averon_scripted_battle.inc`.
3. Trainers and scenes once the owner approves rosters and text.
4. Then: native tests that run the registered scenes, a real ROM build, and
   ChatGPT QA emulator cases for each row above.
