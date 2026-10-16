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
| Evolutions | Conditional evolutions whose conditions depend only on the Pokémon (gender, friendship, a known move or move type, a held item, not another region) or on the time of day (set with `SetTimeOfDay`): built to meet them, then run | 94 run, 0 problems | NATIVE |
| Evolutions | **Every** conditional evolution Averon can meet (`test/averon_evolution_conditions.c`): conditions set up (personality, nature, weather, overworld steps, party species/type, trade partner, bag items, evolution trackers, crits, current damage, Attack vs Defense, contest stats, time), run in its own mode (level, item, trade, spin, script trigger, battle end), and required to produce **exactly** its own form, so an earlier edge cannot shadow it. Includes all 63 Alcremie spin forms | 182 run, 0 failed, 0 shadowed | NATIVE |
| Evolutions | Not run: region- and upstream-map-gated edges (listed below) and Shedinja's split from Nincada | 27 | — |
| Breeding | Every breedable species (1,145) hatches, through the real `GetEggSpecies`, from an enabled, non-battle-only species that is the bottom of its own family (`test/averon_breeding.c`) | 0 problems | NATIVE |
| Breeding | Offspring species, regional forms, Shellos form, egg moves, natures | Upstream `test/daycare.c` | NATIVE (existing) |
| Trade evolutions | Solo alternatives | Codex audit `audit-averon-solo-evolutions.py`; Linking Cord test | SOURCE / NATIVE (existing) |
| Forms | Every allowed form change targets an enabled species. Faint and end-of-battle changes without a target revert to the saved form, by design | 2,481 changes, 0 problems | NATIVE |
| Forms | Form tables and form-change tables are consistent | Upstream `test/species.c` | NATIVE (existing) |
| Forms disabled in release | Every reference to Primal Groudon/Kyogre and Ultra Necrozma is guarded | 0 unguarded | SOURCE |
| Mega Evolution | Every held-stone Mega uses an item with `HOLD_EFFECT_MEGA_STONE` and targets an enabled species | 209 Megas, 0 problems | NATIVE |
| Battle-only forms | Every form reached in battle (Mega, weather, HP thresholds, Battle Bond, switch-in, begin-battle and the excluded gimmicks) has the end-of-battle revert that `TryRevertPartyMonFormChange` applies, so it cannot stay in the party or as the follower | 298 changes, 0 problems | NATIVE |
| Mega Evolution after battle | A Mega Evolved Venusaur is plain Venusaur in the party after a won battle and keeps its stone | Real battle | NATIVE |
| Mega restrictions (`test/battle/averon_mega.c`) | A Mega Stone for another species does nothing; after one Pokémon Mega Evolves its partner cannot; a Mega stays Mega through switching out and back; Rayquaza Mega Evolves through Dragon Ascent without a stone and not without it | 4 tests | NATIVE |
| Mega Ring (SOURCE, **owner decision**) | `CanMegaEvolve` (`src/battle_util.c`) requires `ITEM_MEGA_RING` in the Bag in the real game (the check is skipped under `TESTING`). Averon must give the player a Mega Ring somewhere, or no Mega Evolution is possible. The same-turn block on a second Mega is enforced by the battle menu (GUI) | — | SOURCE |
| Mega Evolution, other endings (`test/battle/averon_mega_endings.c`) | Back to base form, with its stone, after the player Teleports away, a wild Whirlwind, fainting before a win, and a loss; no second Mega after the first Mega Pokémon faints | 5 tests | NATIVE |
| Held items after battle (`test/battle/averon_held_items.c`) | `B_RESTORE_HELD_BATTLE_ITEMS` Gen 9 (upstream: "TODO: use in tests"). Non-Berry items lost to a trainer come back (Knock Off, Thief, Focus Sash, Air Balloon); an eaten Berry stays eaten; Trick reverts. **Defect found and fixed** (`9d91390a`, `TryRestoreHeldItems`): a player Pokémon that started empty-handed kept an item stolen from a trainer (on a win or a loss), and an item Bestowed to a partner existed twice. Now returned to the teammate or dropped if a trainer started with it; items from wild Pokémon (Magician) are kept. Fix disabled: 3 tests fail | 7 tests | NATIVE |
| Mega Evolution in battle | Works; Primal Reversion, Z-Move, Dynamax, Tera and Ultra Burst are blocked | `averon_battle_rules.c` | NATIVE (existing) |
| Learnsets | Level-up, teachable and egg moves are real moves, never Z-Moves or Max Moves; levels are at most 100 and in order | 78,179 entries, 0 problems | NATIVE |
| Physical/special split | Dark physical, Ghost special | `averon_battle_rules.c` | NATIVE (existing) |
| Battle mechanics | Upstream suite | 5,932 total; 327 expected failures, each classified (`averon-native-test-baseline.txt`) | NATIVE |
| Followers | Every enabled species, male and female, resolves to graphics with images, animations, OAM and a 16/32/64 px size | 3,142 lookups, 0 problems | NATIVE |
| Followers | Species without their own sprite use the substitute placeholder (`OW_SUBSTITUTE_PLACEHOLDER`) | **174 of 3,142 lookups** | NATIVE |
| Followers | Normal and shiny overworld palettes exist in pairs (male and female) | 0 problems | NATIVE |
| Followers | Every species ID fits the 12 species bits of a follower graphics ID | `NUM_SPECIES` ≤ 4096 | NATIVE |
| Follower lifecycle (`test/averon_followers.c`) | The real `UpdateFollowingPokemon` on existing maps: the first party Pokémon that is not fainted or an egg follows; reordering and fainting change it; empty or all-fainted party and `FLAG_TEMP_HIDE_FOLLOWER` remove it; a follower larger than 32×32 walks outdoors but is removed indoors (upstream rule), a small one stays; respawned with the right species after each warp; shiny and female variants carried; after a flash save and load the saved lead follows; hidden while surfing or underwater | 8 tests | NATIVE |
| Followers rendered on a map | Movement, animation, palettes on screen, Surf/door transitions, Fly | Not run | GUI needed |
| EXP | Held-item Gen 5 EXP Share, caps, large rewards | `averon_exp.c`, `averon_candy.c` | NATIVE (existing) |
| Level 100 | Every growth rate: EXP rises at each level and fits the 21-bit box field; a level-100 Pokémon given more EXP stays at 100 | 6 growth rates, 0 problems | NATIVE |
| Gen 5 held EXP Share (`test/battle/averon_exp_share.c`, caps lifted) | Lead alone gets all, the bench nothing; one holder: lead and holder half each; two holders share their half; a participating holder gets both halves (not party-wide); switched-in Pokémon share; a participant that fainted gets nothing; a trainer's Pokémon gives the same EXP as a wild one (no 1.5x); Gen 5 level scaling (lower level gains more); a holder at level 100 or above the cap gains nothing; both Pokémon in a double battle share. Mutation (`B_SPLIT_EXP` Gen 6+) fails 3 of the 7 | 7 tests | NATIVE |
| EXP on capture | `B_EXP_CATCH` is `GEN_LATEST`: the party gains EXP for a capture, which is a Gen 6+ behavior, not Gen 5. Upstream test passes. **Owner decision** whether to keep it | — | SOURCE |
| Level 100 under Averon's caps | With every cap flag set (eight badges, assault, Champion) the cap is `MAX_LEVEL`, and a level-99 Pokémon gains EXP in a real battle. Without Champion the last cap still blocks it. A level-100 Pokémon gains none. Mutation (final cap 76) fails | 3 cases | NATIVE |
| Pokédex | Every enabled species has a national dex number from 1 to `NATIONAL_DEX_COUNT`, which the seen/caught flag arrays hold | 0 problems | NATIVE |
| Pokédex | Setting every seen and caught flag changes no other SaveBlock1 byte, counts the full dex, and survives a real flash save and load | Pass | NATIVE |
| Box storage | Species, item, ball, EXP and move fields fit their bit widths | Upstream `sBoxPokemonConstantsFit` (build fails otherwise) | BUILD (existing) |
| Box storage and saves | Every enabled species and form (1,571) is stored in the PC boxes with a held item, a move, a level and a personality, written to flash, cleared and read back: checksum valid, every field equal | 4 saves, 0 problems | NATIVE |

## Evolutions that cannot happen in Averon (NATIVE, pinned list)

Every Averon map reports `REGION_HOENN`, because `GetRegionForSectionId`
(`include/regions.h`) knows only Kanto and Hoenn. Averon's maps are also not
the upstream Hoenn maps. So an evolution gated on another region
(`IF_REGION`) or on an upstream map (`IF_IN_MAP`, `IF_IN_MAPSEC`) can never
happen. The test `Averon lists the evolution targets that only another region
or an upstream map can reach` computes every target with no other possible
evolution and fails if the list changes:

- **Ursaluna** (a National Dex species in its own right): its only evolution
  needs Hisui and a Peat Block;
- **Alolan** Raichu, Exeggutor and Marowak;
- **Galarian** Weezing and Mr. Mime;
- **Hisuian** Typhlosion, Samurott, Decidueye, Lilligant, Braviary, Sliggoo
  and Avalugg (and so Hisuian Goodra through Sliggoo).

These need another source (gift, wild, in-game trade) or a region rule, which
is an owner decision. The map-gated evolutions (Magnezone, Probopass and
Vikavolt at New Mauville; Leafeon at Petalburg Woods; Glaceon and Crabominable
at the Shoal Cave ice room) all have a stone alternative, and the stone
evolutions trigger natively, so none of those species is lost. For the second
region: a Sinnoh map would also report `REGION_HOENN` unless the region
mapping changes (Codex's TWO-REGION area).

## Obedience against Averon's level caps (SOURCE, for the owner and Codex)

`GetAttackerObedienceForAction` (`src/battle_util.c`) lets Pokémon obey up
to level 10 with no badges, then 20, 30, ... 80 per badge, and without limit
after badge 8. Under `B_OBEDIENCE_MECHANICS GEN_LATEST`, the player's own
Pokémon are judged by their **met** level and others by their current level.
Averon's caps are 15, 23 and 31 at zero, one and two badges, above the
obedience levels 10, 20 and 30. So at those stages a traded or gifted
Pokémon at the cap, or the player's own Pokémon caught above the obedience
level, can disobey. Pokémon the player raised from a low met level obey.
This is a design interplay in Codex's region-aware obedience area, not
changed here.

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

Where the ROM goes (BUILD, `arm-none-eabi-nm -S` on the same ELF; sized
symbols total 25.42 MiB):

| Category | ROM |
| --- | --- |
| Cries (1,158) | **8.98 MiB** |
| Battle front sprites | 1.51 MiB |
| Party icons | 1.38 MiB |
| Follower sprites (Pokémon) | 1.35 MiB |
| Battle back sprites | 0.85 MiB |
| Species info table | 0.40 MiB |
| Palettes (battle and overworld) | 0.17 MiB |
| Learnsets (level-up, teachable, egg) | 0.15 MiB |
| Trainers, moves, items tables | 0.23 MiB |

Cries take about a third of the used ROM, more than all Pokémon graphics
together. If maps and music for two regions run short of the 6.8 MB free,
cry compression or sample-rate settings are the largest single lever; that
needs review before any change.

For the second region: reusing existing flag and var IDs costs no save space,
but any new saved structure must go in SaveBlock3 or take space from elsewhere.
SaveBlock1 and SaveBlock2 are nearly full. Codex was told in #15.

## Still needs

1. GUI: followers on a real map (walking, surfing, shiny, gender forms, Mega
   reverting after battle), a full-party catch (the swap menu), Pokédex screens
   with all forms.
2. Shedinja: `CreateShedinja` (`src/evolution_scene.c`, static, runs only in
   the evolution scene) adds Shedinja when Nincada evolves into Ninjask with a
   free party slot and, under `P_SHEDINJA_BALL` Gen 4+, a Poké Ball in the bag,
   which it uses up (SOURCE). A native or GUI run needs the evolution scene.
   A rendered spin/step trigger in the overworld also needs GUI.
3. Owner decision on how the 13 region-only forms and Ursaluna are obtained.
4. A decision on the 174 placeholder follower lookups: they need art, which is
   frozen.
