# LEGEND results — 2026-10-16

Scope: branch `claude/legend-encounter-state` (Epic #42 Phase C, claim in
#15 comment 6207075486). A generic, fail-closed outcome contract for any
one-of-a-kind static encounter. **No encounter uses it**: there is no species
choice, placement, map, scene or flag allocation, and the macros are not
registered in `event_scripts.s`. Nothing here is EMULATOR-TESTED.

Labels: **NATIVE** means executed in the native test ROM; **SOURCE** means a
script reads the code; **GUI** means a rendered emulator run (none yet).

## The defect this replaces

The only existing static-legendary template, the upstream Hoenn scripts
(`NavelRock_Top`, `TerraCave_End`, `MarineCave_End`, `SkyPillar_Top`,
`DesertRuins` and others), branches on `B_OUTCOME_WON`, `B_OUTCOME_RAN` and
`B_OUTCOME_PLAYER_TELEPORTED` and treats every other outcome as caught. When
the wild Pokémon itself ends the battle with Roar, Whirlwind, Teleport or
Emergency Exit, the outcome is `B_OUTCOME_MON_TELEPORTED`, so that template
marks the legendary caught and removes it although it is not in the party.
It is then lost for good, which breaks roadmap B3.4.

## How to rerun

From `Pokemon Game/engine`:

```bash
make -j20 -O check TESTS="Averon legend"
```

```bash
python3 ../scripts/test-averon-legend.py
```

## Evidence

| Case | Evidence | Label |
| --- | --- | --- |
| A wild level-70 Ho-Oh's Whirlwind ends the battle as `B_OUTCOME_MON_TELEPORTED`; the contract records nothing and the encounter stays available | Real wild battle | NATIVE |
| The upstream script pattern, run with that outcome, sets the caught flag | Script engine | NATIVE |
| Emergency Exit escape: available, nothing recorded | Real wild battle | NATIVE |
| Knockout: defeated, not caught | Real wild battle | NATIVE |
| Master Ball capture: caught, defeated cleared | Real wild battle, one-member party | NATIVE |
| Capture with a full party | The Gen 7+ swap-into-party menu (`B_CATCH_SWAP_INTO_PARTY`, compile-time) cannot be answered by the headless runner; the outcome is still `CAUGHT` | GUI case, not run |
| Every value 0–0x1FF: only `CAUGHT` is caught, only `WON` is defeated | Classifier | NATIVE |
| Every engine outcome other than those two records nothing | All 12 `B_OUTCOME_*` values | NATIVE |
| A capture is final: a later knockout, teleport or retry cannot undo it | Contract | NATIVE |
| A defeat is retryable only by the caller's policy or an explicit retry | Contract | NATIVE |
| A stale `CAUGHT` from an earlier battle is never recorded (`Begin` clears the outcome) | Script engine | NATIVE |
| Macro expansion: `Begin`, `setwildbattle` (species, level), `dowildbattle`, then `Record` | Compiled bytes | NATIVE |
| Check and retry macros | Script engine | NATIVE |
| Caught and defeated states survive a real flash save and load | Upstream Ho-Oh flags as stand-ins | NATIVE |
| A player loss ends the script in a whiteout before anything is recorded | `CB2_EndScriptedWildBattle` | SOURCE |
| Every `B_OUTCOME_*` in `constants/battle.h` is in the native outcome table; the classifier has exactly two non-default cases; no game script uses the macros | `test-averon-legend.py` | SOURCE |

## Still needs

1. Owner decisions per encounter: species, location, whether a defeat may be
   retried and when, and the two saved flags it uses.
2. A handoff to register `data/scripts/averon_legend.inc` in `event_scripts.s`.
3. ChatGPT QA emulator cases once an approved encounter exists: catch,
   knockout, run, the wild Pokémon's Whirlwind or Roar, a full-party catch, and
   save before and after.
