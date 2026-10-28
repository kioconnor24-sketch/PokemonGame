# Packet E plan: Route 208 → Hearthome → Route 209 → Solaceon (C48 step 3–5)

Written 2026-10-28 against main `f9d646c8`. Packet C (#337, head `0cdccf0d`) and packet D (#347, head `759dcf4a`) are still open.

This is a design document only. It installs nothing, allocates no section, slot or ID, and edits no Codex file. Every fact below was read from the staged sources on main; the commands are at the end.

## Dependencies

- **Packet C** must be on main. It provides production Oreburgh City and section 227.
- **Packet D** must be on main as a production installer, not only the DEV preparer in #347. Mt. Coronet 1F South is the only physical way into Route 208.
- **Section values:**
  - The owner's decision request for 228+ is #15 6444910204, item 2.
  - The owner answered "full permission" in a Claude session on 2026-10-28. The relayed #15 comment is pending; posting it was blocked by the permission system.
  - Packet E may not use a value until that record exists on #15.

## The 26 maps, in proposed slot order

P is the first slot after packet D's last production slot.

| Slot | Map | Source (latest re-stage; same choice as the C46 live gate) | Warps kept in packet E |
| --- | --- | --- | --- |
| P+0 | Route208 | Codex `hearthome-solaceon` + Claude `city-shells` Route208 overlay | 0 Access, 1 House1, **2 Coronet South (new, see below)** |
| P+1 | Route208_Access | `hearthome-solaceon` (neutral gate art) | 0 Route208, 1 Hearthome |
| P+2 | HearthomeCity | `hearthome-solaceon` | 0 Route208_Access, 1 Route209_Access |
| P+3 | Route209_Access | `hearthome-solaceon` | 0 Hearthome, 1 Route209 |
| P+4 | Route209 | `hearthome-solaceon` + Claude `lost-tower` Route209 overlay | 0 Access, 1 Lost Tower, 2 Ruins A, 3 Ruins B, 4 Ruins C |
| P+5 | SolaceonTown | `hearthome-solaceon` + Claude `solaceon-ruins-entrance` overlay | 0 Center, 1 Mart, 2 House1, 3–4 Ruins Entrance |
| P+6 | Route210_South | `hearthome-solaceon` + Claude `city-shells` overlay | 0 House1 |
| P+7 | Route208_House1 | `city-shells` | both → Route208 1 |
| P+8 | SolaceonTown_PokemonCenter_1F | `city-shells` | → Solaceon 0 |
| P+9 | SolaceonTown_Mart | `city-shells` | → Solaceon 1 |
| P+10 | SolaceonTown_House1 | `city-shells` | → Solaceon 2 |
| P+11 | Route210_South_House1 | `city-shells` | → Route210_South 0 |
| P+12…17 | LostTower_1F…6F | `lost-tower` (stock Mt. Pyre stair graph, renamed) | 1F: four doors → Route209 1; full stair graph |
| P+18 | SolaceonRuins_Entrance | `solaceon-ruins-entrance` | → Solaceon 3/4, → B1F 5 |
| P+19 | SolaceonRuins_B1F | `solaceon-ruins-entrance` (the variant with the Entrance warp) | A, B, C, B2F W, B2F E, Entrance |
| P+20…22 | SolaceonRuins_A, _B, _C | `solaceon-depths` | Route209 doors + B1F |
| P+23 | SolaceonRuins_B2F_West | `solaceon-depths` | B1F, Sanctum |
| P+24 | SolaceonRuins_B2F_East | **`solaceon-depths`** (2 warps, no Maniac Tunnel warp) | B1F, Sanctum |
| P+25 | SolaceonRuins_B3F_Sanctum | `solaceon-depths` | B2F W/E |

Use `solaceon-depths`' B2F_East, not `maniac-ruins-link`'s. The latter carries a third warp at (24,16) to `MANIAC_TUNNEL_B1F`, which belongs to packet G. With the depths variant, nothing has to be closed by hand.

## The one new join: Route 208 ↔ Mt. Coronet 1F South

Both sides already exist; each was closed on purpose because the other side wasn't built.

| Side | Cell | Now (closed) | Restore to | Evidence |
| --- | --- | --- | --- | --- |
| Route208 | (8,19) | `0x04A7` | `0x00A7`, donor collision 0 | `hearthome-solaceon/source-receipt.json` `closure_changes`: before 167, after 1191, "unbuilt source destination" |
| Coronet South | (36,20), index 876 | `0x3604` (packet D cave wall) | `0x321A` | #347 `prepare_runtime.py`: donor `0x3607`, converted `0x361A`; same arrow metatile as the west port |

**Behavior check:** `0xA7` in `hearthome-solaceon/outdoor-family/primary-attributes.bin` is attribute `0x60`, `MB_NON_ANIMATED_DOOR`. That's the same native door behavior packet D restores on Route 207. On Coronet South, `0x21A` is `MB_SOUTH_ARROW_WARP` (reviewed on #347).

**Warp indices:** the donor pair is Route208 warp 0 ↔ South warp 1. Packet E appends rather than reorders, so existing returns keep their indices:
- Route208 gets warp **2** at (8,19) → `MAP_MT_CORONET_1F_SOUTH` dest **1**. Index 1 is already House1 in the `city-shells` overlay.
- South gets warp **1** at (36,20) → `MAP_ROUTE208` dest **2**.

**Upper floor:** packet D's 2F ladder wall (29,2) stays closed in packet E.

## Exits that stay closed in packet E

| Map | Exit | Opens in |
| --- | --- | --- |
| HearthomeCity | Route 212 Access door (8–9,46), `central-joins` overlay | F |
| HearthomeCity | every building door: no Hearthome interiors are staged anywhere on main | gap: needs a new interiors batch |
| HearthomeCity | the clipped south gateway (already drawn as rail by Codex) | — |
| Route210_South | north connection to Route210_North (−57) and east to Route215 (+26), `central-joins` | later |
| SolaceonRuins_B2F_East | Maniac Tunnel | G (by choosing the `solaceon-depths` variant) |
| Route208 | the 9 other `closure_changes` cells (top and bottom edges, east seam endpoint) | unchanged |

Hearthome without interiors is the one honest gap. The doors stay closed, as Oreburgh's mine stayed closed in packet C. A Hearthome interiors batch (Center, Mart, houses, Contest Hall, Gym shells) could be staged under the same `city-shells` rules before or after packet E.

## Traversal facts to re-check in the packet E gate

- **Route 209 mud:** 4 `MB_MUDDY_SLOPE` cells. C46 walked them with `mud_qa`, down seams last.
- **Route 208 bridge:** 58 elevation-15 cells, unchanged. Codex walked the upper bridge 87/87 on #227.
- **Surf and bike:** packet E needs neither. The way in is on foot: Route 207 (upper) → Coronet South → Route 208. The Oreburgh → Route 207 uphill mud stays bike-only, as recorded in C48.
- **C46 evidence on the same sources:** Solaceon network 183/183 + 3/3 NORMAL/RELEASE. It must be re-run on the production install, not reused.

## Proposed section order

Packet D goes first: Route 206 = 228, Route 207 = 229, Mt. Coronet = 230. Packet E then gets:

| Value | Section | Maps |
| --- | --- | --- |
| 231 | ROUTE 208 | Route208, Route208_Access, Route208_House1 |
| 232 | HEARTHOME CITY | HearthomeCity |
| 233 | ROUTE 209 | Route209, Route209_Access |
| 234 | SOLACEON TOWN | SolaceonTown and its 3 interiors |
| 235 | SOLACEON RUINS | Entrance, B1F, A–C, B2F W/E, B3F |
| 236 | LOST TOWER | LostTower_1F…6F |
| 237 | ROUTE 210 | Route210_South, Route210_South_House1 |

Access gates take their route's section. Oreburgh Gate has its own (223) only because Oreburgh Gate is a named place. The values follow the C48 order and are append-only. They are a proposal until the owner record is on #15. 237 is beyond the originally proposed 228–236.

## Installer checklist (same as packet C)

1. One combined installer at `west-packet-e/install_packet_e.py`:
   - It reads the sources above read-only and appends 26 slots, 26 layouts and the registry entries.
   - It adds sections 231–237 to `region_map_sections.json` and `scripts/averon-mapsec-pins.json` together.
   - It replaces each header's `MAPSEC_PENDING_OWNER` with the section above.
   - It applies the two-cell Coronet join, and changes nothing else.
   - It refuses to run twice, and `--check` reports any tampered file.
2. Make the packet A–D tests tolerate appended packets, as packet C did: slice the prefix and don't assert a total.
3. Add the new section terms to the Sinnoh lists in `engine/test/averon_location_compatibility.c`. This is test-only and must leave both ROMs byte-identical. Packet C needed the same change for 227.
4. Re-pin the Codex DEV families to the new prefix. `hearthome-solaceon`'s own DEV assembler appends these same seven maps, so after packet E it needs a production profile like W25's `rebase_on_production_city`, or retirement. That is Codex's file: claim it on #15 and coordinate.
5. Gate on the exact head:
   - NORMAL/RELEASE builds and native suite equal to the baseline;
   - full traversal of all 26 maps plus the Route 207 / Coronet South entry, both mud directions and the bridge;
   - Save → fresh Continue 3/3 in both profiles.
6. Owner exact-path handoff on #15 for the engine paths and the two identity files, then merge with `--match-head-commit`.

## Reproduce the facts in this plan

- **Warps and connections:** `git show origin/main:"Pokemon Game/Averon_Codex_Handoff/design/sinnoh/<family>/staged/<Map>/map.json"` for each source above.
- **Route 208 closure:** `hearthome-solaceon/source-receipt.json` → `closure_changes.Route208` and `source_geometry_headers.Route208.warp_events[0]` (`(8,19)` → `MAP_MT_CORONET_1F_SOUTH` 1).
- **Door behavior:** word `0xA7` of `hearthome-solaceon/outdoor-family/primary-attributes.bin` is `0x60`; `include/constants/metatile_behaviors.h` index `0x60` is `MB_NON_ANIMATED_DOOR`.
