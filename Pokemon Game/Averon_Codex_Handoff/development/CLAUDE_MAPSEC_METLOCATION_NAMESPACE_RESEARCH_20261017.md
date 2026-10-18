# Map-section / met-location namespace for full Averon + Sinnoh: research

**Claude, 2026-10-17. Status: RESEARCH.** No production section IDs, names, maps or save-format changes are made or proposed for merge here. Owner decisions are listed in §5.

**Source:** `main` at `ab6d1695`. Facts come from `scripts/audit-averon-mapsec-namespace.py`, which is added in the same PR as this document, and from direct source reads.

## 1. Facts

| Item | Value / location |
| --- | --- |
| Sections | **215** (values 0–214, in `src/data/region_map/region_map_sections.json` order) |
| `MAPSEC_NONE` | **215**, which equals the count; it is used as a table sentinel and in "met somewhere" comparisons |
| Reserved met codes | `0xFD` egg, `0xFE` in-game trade, `0xFF` fateful encounter |
| Spare values before the reserved codes | **37** (216–252) |
| Saved width: Pokémon | `PokemonSubstruct3.metLocation` is `u8`. It is encrypted inside every party and PC Pokémon |
| Saved width: TV | `global.tv.h` records store `mapsec_u8_t` (6 fields) |
| ROM-only widths | `MapHeader.regionMapSectionId` is `mapsec_u8_t`; `RegionMap.mapSecId` is already `mapsec_u16_t` |
| Region from section | `GetRegionForSectionId()` (`include/regions.h`) is a range check: the Kanto range, otherwise Hoenn |
| Averon content | the 16 maps in `gMapGroup_AveronOpening` use **6** sections: Saltmere 209, Coastal Meadow 210, Windrow 211, Orchard Lane 212, Alderfield 213, Coastal Bluffs 214 |
| Other sections | 198 are used only by upstream maps; 11 by no map; 84 are named by behavioural code; **125** are named only in lookup tables (names, region-map layout, popups, previews, landmarks, match call) |
| Spare Pokémon bits | `PokemonSubstruct0.unused_04:3`, `PokemonSubstruct1.unused_04:5` and `unused_06:3`. **No code in `src` references them**, so every existing Pokémon has them at zero. `dynamaxLevel:4` is *not* spare: 33 code sites read it |
| Summary screen | `metLocation < MAPSEC_NONE` prints the name; `>= MAPSEC_NONE` prints "somewhere"; the specials are compared exactly |

**What natural saves can hold.** In normal play, existing saves can only hold met values 209–214 and `0xFD`–`0xFF`:
- every Averon map has one of the six sections;
- eggs, gifts and catches take the current map's section;
- upstream maps are reachable only through the debug menu.

DEV-fixture saves made on upstream maps can hold other values, including 215.

**The real limit.** The constraint is the 8-bit *saved* met location and the position of `MAPSEC_NONE`. It is not the number of maps: map IDs are a separate namespace (951 registered).

## 1b. What else a section number reaches

`audit-averon-mapsec-namespace.py` measures all of this, with fixture tests for each parser.

| Surface | Today, for Averon's 6 sections | What a new Averon or Sinnoh section needs |
| --- | --- | --- |
| **Fly**: `sMapHealLocations[mapsec][3]` in `src/region_map.c` (protected file) | The table has 154 designated rows and ends before value 192 (`MAPSEC_EMBER_SPA` + 1). Averon's sections have **no row**. `FilterFlyDestination` and `SetFlyDestination` bounds-check against `ARRAY_COUNT`, so Fly to them does nothing. The native test `Averon Fly bounds rejects invalid sections…` asserts this for Saltmere and Alderfield | A row for every section that can be flown to. **Hazard:** adding one row past 214 makes C zero-fill every gap row (`{0, 0, HEAL_LOCATION_NONE = 0}`). `SetFlyDestination` would then warp those sections to map group 0 / num 0, which is **PetalburgCity**. The existing bounds test fails in that case, so keep it. Fill or guard the gap rows in the same change |
| **Town Map**: `region_map_layout*.h` grids (`mapsec_u8_t`) for Hoenn, Kanto and Sevii | **None** of the six sections appears on any grid. The Town Map and the Fly cursor can't select them | A new layout grid and graphics, plus a `GetRegionMapType` case. The grid's cells are `mapsec_u8_t`, so a 16-bit runtime namespace (option B or C) also has to widen the grid type or give Averon/Sinnoh their own grid |
| **Engine region**: `GetRegionForSectionId` (`include/regions.h`) | A range check: `[MAPSEC_PALLET_TOWN, MAPSEC_SPECIAL_AREA)` is Kanto, everything else is Hoenn. Averon's sections report **`REGION_HOENN`** | The region feeds 7 call sites: region-conditioned evolution (`IF_REGION` / `IF_NOT_REGION`), egg regional forms in `daycare.c`, Kanto vs Hoenn battle music, and the Town Map type. Species data has 25 such evolution conditions: Alola 6, Galar 4, Hisui 15, **Sinnoh 0**. Reporting Sinnoh sections as `REGION_SINNOH` changes no evolution today. Reporting them as `REGION_HISUI` would enable 8 Hisuian evolutions and block 7. That is a story decision. Either way it needs a per-section region table instead of the range |
| **Map-name popup**: `sMapSectionToThemeId[MAPSEC_COUNT - KANTO_MAPSEC_COUNT - 1]` | Sized from `MAPSEC_COUNT`, so it grows automatically. Averon's sections get the default theme (index 0) | Nothing is required. Set a theme only if one is wanted |
| **Map registration**: `data/maps/map_groups.json` plus each `map.json` `region_map_section` | 16 maps in `gMapGroup_AveronOpening` | The audit fails on any map that names an unknown section. Map IDs are independent of section values |
| **Averon's own region record**: `averon_region_save.h` | Region codes `NONE`, `AVERON`, `SINNOH`, stored in SaveBlock3, format 1 | Independent of section values. It is not derived from `GetCurrentRegion()` |

## 2. Safety net added now (no owner decision needed)

`averon-mapsec-pins.json` together with `audit-averon-mapsec-namespace.py --check-pins` pin the six shipped values (209–214). The check fails if either of these happens:
- any of the six moves, for example because an upstream merge inserts a section earlier in the JSON;
- `MAPSEC_NONE` would reach `0xFD`.

Without the pin check, either change would silently re-label the met location of every saved Pokémon. It has 9 tests, one of which runs against the real engine.

## 3. Options

| | Idea | Save impact | Capacity | Main costs and risks |
| --- | --- | --- | --- | --- |
| **A** | Keep 8 bits. **Append** after 214, then **reuse** values that no Averon map and no behavioural code uses | None for natural saves: pinned values never move. Appending shifts `MAPSEC_NONE`, which natural saves never store | 37 spare + up to 125 candidates ≈ **162** | Each reused value must stop being assigned by any upstream map still built. Its table rows must be rewritten. `GetRegionForSectionId` needs a per-section region table. Upstream merges will conflict in those tables. Tight for a full canonical Sinnoh, which has about 100+ met names, plus Averon |
| **B** | Widen runtime sections to u16, and store an 8-bit *met code* through an append-only, many-to-one table | None | Unlimited runtime sections; ≤ 253 met *names* | A permanent mapping that must never be reordered. Some met locations show at coarser granularity. TV records need mapping or dropping. Widening `MapHeader` affects the ROM only |
| **C** | **13-bit met location:** the low 8 bits stay in `metLocation`, and the high 5 bits go in `Substruct1.unused_04` | None. Old Pokémon have zero high bits, so their values are unchanged. No size change, no migration | 8,192 | A new `MON_DATA` accessor. Every consumer of `metLocation` must use the full value: summary, egg hatch, daycare, trade, battle-controller transfer buffers, scrcmd. `MapHeader` widens to u16. Risk that upstream later claims those bits. The only option that gives every location its own identity with no migration |
| **D** | Versioned migration that grows `BoxPokemon` | Every save migrates | Unlimited | **Not recommended.** Changing the struct size cascades into PC storage (only 1,568 B free), trades, the daycare and every saved Pokémon. Highest risk |
| **E** | A region namespace in `metGame` (4 bits) | None | 2 × 253 | **Not recommended.** `metGame` drives the origin text on the summary screen (`VERSION_*` ranges) and is copied through battle controllers. It overloads the field's meaning |

## 4. Suggested path

1. **Now:** keep the pin check, and wire it into CI when the workflow owners agree.
2. **First Sinnoh prototype:** append the few sections it needs after 214, using the 37 spare values. That's option A with no reuse, so pinned values and old saves are unaffected.
3. **Before the full Sinnoh atlas** needs more than about 160 named sections, choose between **C** (true 13-bit identity, no migration) and **B** (a mapping layer).
   - Prototype C behind tests first. Write a Pokémon with high bits set, then save, load, trade and hatch it, and check the summary text.
   - Add a regression test proving that existing 8-bit values still read back unchanged.

## 5. Owner decisions needed (none are taken here)

- **Option choice:** A only, A followed by C, or A followed by B.
- **Reuse of retired upstream values.** If allowed, which upstream areas are retired from the build?
- **Sinnoh met names:** canonical DPPt granularity, or grouped names.
- **Region of each section.** This replaces the Kanto/Hoenn range check.
- **Section IDs, names and region-map tiles** for any new Averon or Sinnoh area. These are owner-reserved.

## 6. Tests to require before any change

- **Pins:** the existing check.
- **Golden met-name round trip** for each pinned value:
  1. create the Pokémon;
  2. save;
  3. load;
  4. read the summary string;
  5. check that string is unchanged.
- **Old-save fixture:** a save from before the change loads unchanged, and every met name still renders.
- **For option C:**
  - high-bit values survive save/load, PC deposit and withdrawal, daycare and egg hatch, and the battle-controller copy;
  - the specials 0xFD–0xFF still compare correctly.
- **For any appended section:** confirm `MAPSEC_NONE` is never written to saved data from shipped maps. The inventory tool's "unknown section" check covers map assignment.
