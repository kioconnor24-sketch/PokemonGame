# Pokémon mechanics and data readiness — 2026-10-16

Branch `claude/pokemon-readiness`. Runtime checks of the species, evolution,
form, learnset, follower, Pokédex and level-100 data the engine actually
compiles, plus a capacity report. No game data or engine source is changed.

Labels: **NATIVE** = executed in the native test ROM. **SOURCE** = a script or
reading of the code. **BUILD** = linker or ELF output. **GUI** = rendered
emulator run; there is none for this work.

## Read this first: what native tests can and cannot see

Native tests build with `include/config/test.h`, which turns every species and
form on. The release build differs only in two flags that `species_enabled.h`
turns off: `P_PRIMAL_REVERSIONS` and `P_ULTRA_BURST_FORMS`, which cover
Groudon-Primal, Kyogre-Primal and Ultra Necrozma. So:

- the NATIVE checks below cover a **superset** of the release species. Every
  property they check still holds for the release subset, except a reference
  *into* one of those three forms;
- that remaining case is covered by `scripts/test-averon-release-forms.py`
  (SOURCE): every table reference to them sits under the matching `#if`;
- **correction to #30:** because the release tables have no Primal form
  change, Primal Reversion could not happen in the release ROM even before
  #30. The reversion it fixed was visible only under the test configuration.
  The change remains harmless defense in depth, and it keeps the native tests
  matching the locked rule.

## How to rerun

From `Pokemon Game/engine`:

```bash
make -j20 -O check TESTS="Averon every"
```

```bash
python3 ../scripts/test-averon-release-forms.py
```

## Coverage

| Area | What is checked | Result | Label |
| --- | --- | --- | --- |
| Species data | Every enabled species: valid types, nonzero base stats, first ability set, all abilities in range | 0 problems | NATIVE |
| Evolutions | Every evolution target is an enabled species | 697 edges, 0 problems | NATIVE |
| Evolutions | Every unconditional level evolution (at its level) and item evolution (with its item) actually triggers through `GetEvolutionTargetSpecies` | 465 run, 0 problems | NATIVE |
| Evolutions | Evolutions with extra conditions (gender, time, friendship, held item, move, party, ...) | 209 **not run** | — |
| Trade evolutions | Solo alternatives | Codex audit `audit-averon-solo-evolutions.py`; Linking Cord test | SOURCE / NATIVE (existing) |
| Forms | Every allowed form change targets an enabled species. Faint and end-of-battle changes without a target revert to the saved form, by design | 2,481 changes, 0 problems | NATIVE |
| Forms | Form tables and form-change tables are consistent | Upstream `test/species.c` | NATIVE (existing) |
| Forms disabled in release | Every reference to Primal Groudon/Kyogre and Ultra Necrozma is guarded | 0 unguarded | SOURCE |
| Mega Evolution | Every held-stone Mega uses an item with `HOLD_EFFECT_MEGA_STONE` and targets an enabled species | 209 Megas, 0 problems | NATIVE |
| Mega Evolution in battle | Works; Primal Reversion, Z-Move, Dynamax, Tera and Ultra Burst are blocked | `averon_battle_rules.c` | NATIVE (existing) |
| Learnsets | Level-up, teachable and egg moves are real moves, never Z-Moves or Max Moves; levels are at most 100 and in order | 78,179 entries, 0 problems | NATIVE |
| Physical/special split | Dark physical, Ghost special | `averon_battle_rules.c` | NATIVE (existing) |
| Battle mechanics | Upstream suite | 5,932 total; 327 expected failures, each classified (`averon-native-test-baseline.txt`) | NATIVE |
| Followers | Every enabled species, male and female, resolves to graphics with images, animations, OAM and a 16/32/64 px size | 3,142 lookups, 0 problems | NATIVE |
| Followers | Species without their own sprite use the substitute placeholder (`OW_SUBSTITUTE_PLACEHOLDER`) | **174 of 3,142 lookups** | NATIVE |
| Followers | Normal and shiny overworld palettes exist in pairs (male and female) | 0 problems | NATIVE |
| Followers | Every species ID fits the 12 species bits of a follower graphics ID | `NUM_SPECIES` ≤ 4096 | NATIVE |
| Followers rendered on a map | Walking, surfing, shiny, transform | Not run | GUI needed |
| EXP | Held-item Gen 5 EXP Share, caps, large rewards | `averon_exp.c`, `averon_candy.c` | NATIVE (existing) |
| Level 100 | Every growth rate: EXP rises at each level and fits the 21-bit box field; a level-100 Pokémon given more EXP stays at 100 | 6 growth rates, 0 problems | NATIVE |
| Pokédex | Every enabled species has a national dex number from 1 to `NATIONAL_DEX_COUNT`, which the seen/caught flag arrays hold | 0 problems | NATIVE |
| Pokédex | Setting every seen and caught flag changes no other SaveBlock1 byte, counts the full dex, and survives a real flash save and load | Pass | NATIVE |
| Box storage | Species, item, ball, EXP and move fields fit their bit widths | Upstream `sBoxPokemonConstantsFit` (build fails otherwise) | BUILD (existing) |

## Two engine weak points (no current data triggers them)

1. `LoadDynamicFollowerPalette` (`src/event_object_movement.c`) uses the
   overworld palettes when the *other* palette of the pair exists, then loads
   the one it needs. A species with only one of the two would load a NULL
   palette (wrong colors, not a crash). The palette-pair test keeps the data
   safe.
2. `GetSetPokedexFlag` (`src/pokedex.c`) subtracts 1 from the dex number with
   no bounds check. Dex number 0 or above `NATIONAL_DEX_COUNT` would write
   outside the flag arrays. The dex-number test keeps the data safe.

Both are upstream code. A defensive fix would touch shared engine files, so it
is not made here; the tests guard the data instead.

## Capacity (BUILD, main `0dd026f6` + #25)

| Resource | Used | Size | Free |
| --- | --- | --- | --- |
| ROM | 26,729,652 B | 32 MiB | about 6.8 MB (20.3%) |
| EWRAM | 226,416 B | 256 KiB | 35,728 B (13.6%) |
| IWRAM | 28,392 B | 32 KiB | 4,376 B (13.4%) |
| SaveBlock1 (flags, vars, dex, bag) | 15,568 B | 15,872 B (4 sectors) | **304 B** |
| SaveBlock2 | 3,884 B | 3,968 B (1 sector) | **84 B** |
| SaveBlock3 | about 4 B | 1,624 B | 1,620 B |
| Pokémon storage | 34,144 B | 35,712 B | 1,568 B |

Save sizes are ELF symbol sizes (`arm-none-eabi-nm -S`) minus the 128-byte ASLR
pad, against `include/save.h`. Upstream `STATIC_ASSERT`s in `src/save.c` stop a
build that overflows.

For the second region: reusing existing flag and var IDs costs no save space,
but any new saved structure must go in SaveBlock3 or take space from elsewhere.
SaveBlock1 and SaveBlock2 are nearly full. Codex was told in #15.

## Still needs

1. GUI: followers on a real map (walking, surfing, shiny, gender forms, Mega
   reverting after battle), a full-party catch (the swap menu), Pokédex screens
   with all forms.
2. The 209 conditional evolutions: per-condition native cases (time of day,
   friendship, held item, gender, move, party member).
3. A decision on the 174 placeholder follower lookups: they need art, which is
   frozen.
