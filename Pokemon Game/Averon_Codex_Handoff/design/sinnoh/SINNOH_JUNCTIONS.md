# Sinnoh next-area junctions (C4 interface specification)

**Status: SPECIFICATION ONLY.** This page adds no map, map/section ID, connection, encounter or story content. It records how the areas next to Sandgem must meet, so each one can be built and tested in isolation once the owner approves it. Rows refer to [`SINNOH_AREA_REGISTER.csv`](../../development/SINNOH_AREA_REGISTER.csv).

## Engine rules every junction follows

- **Connection offset.**
  - The connected map is drawn at `offset` along the shared edge, in the current map's coordinates (`fieldmap.c` `Fill*Connection`).
  - Crossing the edge moves the player by `pos -= offset`. Reciprocal entries are therefore exact negatives: for A → B = `k`, B → A = `-k`.
  - For `up`/`down` connections the offset is along x; for `left`/`right` it is along y.
- **Seam rule.**
  - Every walkable tile on A's edge must face a walkable tile on B's edge, and vice versa. Otherwise a player can stand on an edge tile that leads nowhere, or see a road end in a wall.
  - Unapproved neighbours stay closed: trees on the edge, or a map `border` of trees, which is what the camera shows past an unconnected edge.
- **Camera margin (directional).** The map buffer extends `MAP_OFFSET` = 7 tiles past the north, south and west edges and 8 past the east edge (`MAP_OFFSET_W` = 15 = 7 + 8). Each `Fill*Connection` copies the neighbour's strip **adjacent to the seam**, and that strip must look coherent (no stray buildings or cut-off roofs):

  | Neighbour lies to the… | Function | Neighbour strip copied |
  | --- | --- | --- |
  | north | `FillNorthConnection` | its **last (southern) 7 rows**, `y2 = cHeight − 7` |
  | south | `FillSouthConnection` | its **first (northern) 7 rows** |
  | west | `FillWestConnection` | its **last (eastern) 7 columns**, `x2 = cWidth − 7` |
  | east | `FillEastConnection` | its **first (western) 8 columns** (`MAP_OFFSET + 1`) |
- **Tree phase.** The placeholder round trees are 2 × 2 metatiles: top halves on even rows, left halves on even columns. Two rules keep them whole across a seam:
  - the connection **offset**, which runs along the seam, must be **even**;
  - the map on the west or north side needs an **even width or height**, so its edge column or row is a right or bottom half.

  Otherwise every tree facing the seam pairs mismatched halves. The Route 201 mGBA dry run (#135) found this at offset −5. −4 fixes it (Route 201 is 64 wide), and `verify_route201_plan.py` check 7 enforces it.
- **Map size.** `(width + 15) × (height + 14) ≤ MAX_MAP_DATA_SIZE` (10,240) for every map.
- **Ledges.** `PlayerJumpLedge` never checks the landing tile, so every ledge must land on walkable ground. The Route 201 proof checks this.

**Camera strips at each junction** (per the table above; sizes from the built Sandgem 28-row layout, the Route 201 64 × 22 candidate and the ~64 × 48 Jubilife reference):

| Junction | Standing in | Buffer holds |
| --- | --- | --- |
| A | Sandgem (Route 201 is west) | Route 201's eastern 7 columns, x 57–63 |
| A | Route 201 (Sandgem is east) | Sandgem's western 8 columns, x 0–7 |
| B | Route 201 (Twinleaf is south) | Twinleaf's northern 7 rows: unknown, reference unavailable |
| B | Twinleaf (Route 201 is north) | Route 201's southern 7 rows, y 15–21 |
| C | Route 201 (Lakefront is west) | Lakefront's eastern 7 columns: unknown |
| C | Lakefront (Route 201 is east) | Route 201's western 8 columns, x 0–7 |
| D | Sandgem (Route 202 is north) | Route 202's southern 7 rows: unknown |
| D | Route 202 (Sandgem is south) | Sandgem's northern 7 rows, y 0–6 |
| E | Route 202 (Jubilife is north) | Jubilife's southern 7 rows, about y 41–47 |
| E | Jubilife (Route 202 is south) | Route 202's northern 7 rows: unknown |

## Junction A: Route 201 ↔ Sandgem Town (east)

| | Route 201 (SN-R201, design #135) | Sandgem Town (SN-T02, #133) |
| --- | --- | --- |
| Edge | east, x 63 | west, x 0 |
| Open rows | 6–9 (road 7–8) | 10–13 (road 11–12), read from the built `map.bin` |
| Connection entry | `right` → Sandgem, offset **−4** | `left` → Route 201, offset **+4** |

- **Proof.** `verify_route201_plan.py` checks this seam against the built Sandgem layout, including tree phase. It passes, and an odd −5 offset is caught. A throwaway mGBA dry run crossed rows 6, 8 and 9 in both directions and landed exactly at Route (63, y) ↔ Sandgem (0, y + 4) ([#135 `dry-run/`](https://github.com/kioconnor24-sketch/PokemonGame/pull/135)).
- **Hazard.** Both entries are added together, only after Route 201 is approved. A one-sided entry would let the player walk out of one map and arrive at the wrong row, or be unable to return.

## Junction B: Route 201 ↔ Twinleaf Town (south)

| | Route 201 | Twinleaf Town (SN-T01) |
| --- | --- | --- |
| Edge | south, y 21 | north, y 0 |
| Open columns | 15–17, a **3-wide** sand path | **reference unavailable** |
| Connection entry | `down` → Twinleaf, offset `15 − t` | `up` → Route 201, offset `t − 15` |

Here `t` is the left column of Twinleaf's 3-wide north path.

- **Reference gap.** The only overhead found for this area, the "Route 201 / Twinleaf Town" image, shows Route 201 only. Twinleaf's footprint is not specified here and must not be guessed.
- **Requirement.** Twinleaf's north edge must be open on exactly 3 columns, ideally a 3-wide road.
- **Hazard.** Twinleaf is DPPt's player-home town. It is reserved for the owner's story decisions, so no houses or story buildings are reserved here.

## Junction C: Route 201 ↔ Lake Verity side (west)

| | Route 201 | Verity Lakefront (SN-L04) → Lake Verity (SN-L01) |
| --- | --- | --- |
| Edge | west, x 0 | east edge of Verity Lakefront |
| Open rows | **two openings**: 8–11 above the long ledge, 13–14 below it | Lakefront: **reference unavailable** |
| Connection entry | `left` → Lakefront, offset `8 − v` | `right` → Route 201, offset `v − 8` |

Here `v` is the Lakefront row that meets Route 201 row 8.

- **What the reference shows.** The Lake Verity overhead (864 × 648 px = 54 × 40.5 tiles) covers only the lake map. It is entered from a grass clearing at its south-east, around tiles 38–43 × 33–35, which in DPPt leads from Verity Lakefront. Lakefront itself has no reference.
- **Hazards.**
  - Route 201's long ledge reaches the west edge on row 12. The Lakefront side must continue that ledge, or close row 12 with a wall, so both openings stay separate and one-way behaviour stays consistent across the seam.
  - Lake Verity is a legendary-lake site. Its event content is reserved for owner approval, so only geometry belongs here.

## Junction D: Sandgem Town ↔ Route 202 (north)

| | Sandgem Town (#133, built) | Route 202 (SN-R202) |
| --- | --- | --- |
| Edge | north, y 0 | south edge |
| Open columns | road 21–22 inside the clearing 19–24, from the built layout | **reference unavailable**; see [`route202/ROUTE202_REFERENCE_STATUS.md`](route202/ROUTE202_REFERENCE_STATUS.md) |
| Connection entry | `up` → Route 202, offset `21 − s` | `down` → Sandgem, offset `s − 21` |

Here `s` is the column of Route 202's south road that meets Sandgem x 21.

- **Requirement.** Route 202's south edge must be open on columns that line up with Sandgem's 6 open columns, 19–24, with its road meeting 21–22. Any other open tile on that edge would face Sandgem's tree line.
- **Camera.** Seen from Sandgem, Route 202 is a north neighbour, so the buffer holds Route 202's **last (southern) 7 rows**; those rows must read as forest-framed path. From Route 202, Sandgem is a south neighbour, so the buffer holds Sandgem's **first (northern) 7 rows**, which already exist in the built layout.

## Junction E: Route 202 ↔ Jubilife City (north)

| | Route 202 | Jubilife City (SN-T03) |
| --- | --- | --- |
| Edge | north edge | south, bottom row |
| Open columns | **reference unavailable** | stairs on columns **44–46**, 3 wide, at the end of the 4-wide central avenue (columns 43–46) |
| Connection entry | `up` → Jubilife, offset `q − 44` | `down` → Route 202, offset `44 − q` |

Here `q` is the left column of Route 202's 3-wide north opening.

- **What the reference shows.** The Jubilife overhead is 1024 × 772 px, about 64 × 48 tiles. Size check: (64 + 15) × (48 + 14) = 4,898 ≤ 10,240.
- **Hazards.**
  - Route 202's north opening is **unobserved** (see the reference status). The requirement is that its north edge is open on exactly the 3 Jubilife stair columns. **If** a reference later shows a 2-wide road there, the third stair column still needs a walkable Route 202 tile; otherwise that stair tile is a walkable dead end facing trees. This is a proposed matching requirement, not evidence of the Route 202 endpoint.
  - Jubilife is a large city and is **not** proposed for building; this records only its south interface.

## Accessibility notes for whoever builds these

1. **Twinleaf → Sandgem crosses Route 201's big tall-grass patch.** In DPPt this is the only way through: the short ledge blocks the direct path. Once wild encounters are approved, that walk requires entering grass, so the player must already have a usable party. Today there is no encounter table, so there is no risk.
2. **One-way ledges must never create a pocket.** Every new map with ledges needs the same reachability proof as Route 201: every tile can return to an exit.
3. **Two openings on one edge (Route 201 west) need two separate seam checks.**
4. **Follower:** crossing a connection is a normal step, not a warp, so the follower walks across. Each built seam must still be walked in mGBA in both directions with the follower visible, just as the Sandgem door round trip was.

## What starts next

Building any of these needs explicit owner approval of that map and its section ID (217 and up, allocated by Codex). Route 201 (#135) is the only one with a full original reference and a construction-ready design.
