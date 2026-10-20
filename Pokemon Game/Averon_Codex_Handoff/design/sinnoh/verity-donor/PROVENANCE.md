# Verity Lakefront and Lake Verity: donor geometry import

**Credit:** Verity Lakefront and Lake Verity layouts by LiderMorti00
([Sinnoh-pokeemerald-expansion](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion)), used with the
owner-reported permission in [Issue #15 comment 6274520543](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6274520543).

**Section:** 220 `MAPSEC_LAKE_VERITY`, shared by both maps under
[owner decision 6272466493](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6272466493).

## Source

Donor revision: `38228bb574a3557345852b758d5f1a65eb01bb22`. Both blobs are checked by `build_verity.py`, which reads the
donor through `scripts/sinnoh-donor-map-pilot.py` `read_donor_map` (#176).

| Donor layout | Size | Git blob | Source SHA-256 |
| --- | --- | --- | --- |
| `VerityLakefront/map.bin` | 20×20 | `916c66be28572f75c70af7a0ff25bcec17a78c05` | `e97bc235…` |
| `LakeVerity/map.bin` | 48×46 | `1fba9218763961d1e2298f404d2bed0ed6a13c41` | `29a1730c…` |

Output hashes and changed-cell counts are in `verity-convert-receipt.json`. Renders: `lakefront_built.png`,
`lake_built.png`.

## Graphics: Averon's own banks, no donor art

Both maps use `gTileset_General` + `gTileset_Dewford`, the same banks as Route 201, Sandgem and Twinleaf.
The shared General bank is not modified.

| Item | Treatment |
| --- | --- |
| **Primary IDs** (22 Lakefront, 41 Lake) | Kept. `metatile_attributes` words match Averon's General, except ID 3 (sign: layer type only) and ID 510. Averon defines 510 as pond water under a tree canopy, which is surfable; the donor marks it normal. Averon's behavior is kept. |
| **Secondary IDs** (12 Lakefront, 11 Lake: donor Petalburg) | Replaced with Averon General equivalents (`SECONDARY` in the builder): tree quarters → Averon tree halves in their neighbors' phase; tunnel floors → grass; the two canopy-over-shore corners → the vertical shore tile above them. |

Why not reuse the donor's Petalburg as an isolated secondary? Its entrance metatiles draw mostly from donor *primary*
tiles (475–477, 0–59, palette 2), which differ from Averon's General, so pairing it with Averon's General would draw
the wrong art.

The seam never shows a secondary tile on either side (Route 201 x 0–9 and Lakefront x 10–19 are primary-only), so the
choice of secondary bank cannot break the seam.

## Navigation

| Item | Detail |
| --- | --- |
| **Route 201 west ↔ Lakefront east** | Lakefront `right` **−1** ↔ Route 201 `left` **+1**. The donor's ledge (Lakefront row 11) meets Route 201's (row 12). |
| **Seam cell edits** (7) | Make walkability exactly reciprocal (zero `map_qa` static findings): remove the edge tree at x 18–19, rows 7–9; a bush at (19, 6) and (19, 14); collision on the canopy at (19, 15). |
| **Access edits** (2) | Open the top of the donor's L-shaped ledge, (6, 6) → grass, with the cap moved to (6, 7). Every Lakefront exit is then reachable on foot from the lake entrance, and both ledges remain one-way shortcuts. |
| **Lakefront ↔ Lake** | The donor's two reciprocal pairs: Lakefront (2, 4)/(3, 4) ↔ Lake (38, 43)/(39, 43), warp IDs 0/1. Averon's General and Dewford have **no north arrow warp**, so each tunnel floor is a step-on warp: a coord trigger (`VAR_TEMP_1` = 0) runs exactly `warp <map>, <id>` then `end`. `DoWarp` locks field controls itself, so there is no `waitstate`, and a broken trigger cannot freeze the player. `map_qa` enters these from the approach tile and expects arrival on the warp tile. |
| **Island cave mouth** (23, 19) | Non-animated door with no warp: story-reserved. Collision set; art kept. |
| **Other edges** | All closed. The lake has no edge connection. |

## Not imported

All donor objects (story characters and an item ball), the 34 coord/story triggers, both hidden items and their reused
flags, donor scripts and text, music, encounters and donor map/section IDs. Added only: one neutral `LAKE VERITY` sign
on the donor's sign cell (1, 6), and the four one-line warp triggers. Music is `MUS_ROUTE101`, as on Route 201. No
encounter table, so tall grass has no wild battles.
