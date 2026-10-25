# W1: Route 218 → Canalave City → Iron Island (western lane)

Claims: #15 6391099398 (W1) and 6391598421 (W1b). Manager allocation: 6390351229 / 6391428534.

## What exists

Route218_East, Route218, Route218_West and CanalaveCity are already on main as source, art and DEV runtime (Codex #234/#236/#239). W1 reuses them **read-only** through `canalave-west/prepare_runtime.py`'s `assemble()`.

The pinned donor (`38228bb5`) has no Iron Island and no Canalave interiors. So everything below is **new construction in Averon's own stock banks**: no donor pixels, no new tileset, and no change to any shared bank.

| Map | Layout | How it is built |
| --- | --- | --- |
| IronIsland (40×32) | new, General + Dewford | **Rectangular shore:** every shore cell's 8-neighbour sand/water pattern occurs with the same metatile in Route 105/106/107 or Dewford. An unattested pattern refuses the build.<br>**Hills:** Lake Verity's islet hill, stretched along its uniform rows and columns.<br>**Pieces copied from stock maps:** Route 106's open cave mouth, and Dewford's house, pier and boulders.<br>**Also:** Verity trees and sand walkways. |
| IronIsland_1F / B1F / B2F | new, General + Cave | Rectangular chambers and rock blocks in Oreburgh Gate 1F's wall kit, with Granite Cave's exit mouth and ladders. |
| IronIsland_House, CanalaveCity_House1/2 | `LAYOUT_HOUSE1` | Shared layout, unchanged. Neutral shells: no NPCs or services. |
| CanalaveCity_Harbor | `LAYOUT_HARBOR` | Shared layout, unchanged. The gangway (8,10) is a step-on portal. |
| CanalaveCity_PokemonCenter_1F | `LAYOUT_POKEMON_CENTER_1F` | Shared layout, unchanged. No nurse and no heal location. |
| CanalaveCity (overlay) | canalave-west's map.bin | **One cell changes:** the closed pier house's door picture (29,13), 525 → 537. 537 is the same bank's real door, already used at (7,17); the cell keeps its collision and elevation.<br>**Warps:** four door warps are appended, at the Center (28,22), the pier house (29,13), and houses (7,17) and (9,31). |

**Neutral DEV portal:** the Harbor gangway (8,10) ↔ Iron Island's pier end (38,20). Each tile is both the arrival warp and the step-on trigger, as in Floaroma Meadow. There's no boat, ferry story, NPC, flag or unlock. Keeping the portal in production is an owner decision.

**Sections:** `MAPSEC_PENDING_OWNER` throughout. There are no objects, encounters, items or save changes.

## Reproduce

```bash
python3 build_iron_island.py --engine "<repo>/Pokemon Game/engine" --out <dir>
```

Run from repo root:

```bash
python3 -m unittest "Pokemon Game/scripts/tests/test_sinnoh_iron_island.py"
```

Use `prepare_runtime.py --repo <disposable checkout> --install` only on a marked `claude/iron-island-scratch-*` branch.

## Evidence (DEV only; temporary slots, stand-in section MAPSEC_ROUTE_201; not production acceptance)

| Check | Result |
| --- | --- |
| Source tests | 10/10 |
| Static `map_qa`, 13 maps | 0 findings |
| First 10-map NORMAL run (ROM `0174858f…`) | 52/54. Both failures were the original split portal: the trigger sat beside the arrival warp, so the return never fired. Fixed in `c02eb666`. |
| W1b 13-map NORMAL (ROM `7df42ba8…`) | 145/147, Save → fresh Continue 3/3. Both portals and every door pass. The two failures were the B1F and B2F **up-ladder** round trips: the tool stood on the ladder and pushed away. A ladder warps on step-on, so the tooling now approaches it from a neighbour (#252 `eca0a39e`). The geometry is unchanged. |
| W1b RELEASE | W1B_RELEASE |

**Build note:** `map_data_rules.mk:32` can run `mapjson groups` twice under `make -j` and empty `src/data/heal_locations.json`. Every build here restores the file first and requires it unchanged afterwards. The one failed RELEASE build was caught by this exit-code gate.
