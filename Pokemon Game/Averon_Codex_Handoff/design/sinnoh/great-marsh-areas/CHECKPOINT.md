# W18 Great Marsh areas: checkpoint

OFF-ENGINE staging, stacked on W10 (`claude/great-marsh-w10`, `614036f7`). New construction with W10's attested composition: General + Dewford, Lake Verity grass, tall grass, 2×2 trees and ponds (strict 8-neighbour patterns), and Dewford sand.

## Maps (4)

**GreatMarsh (W10, re-staged)**
- Exactly two 4-cell gaps are cut in its tree ring, by removing whole trees: north (x 22–25) and west (rows 18–21).
- The header is unchanged apart from the connections. The gate house and the Pastoria link are as in W10.

**New 48×40 areas: GreatMarsh_North, GreatMarsh_NorthWest and GreatMarsh_West.** Each has five or six ponds, tall-grass patches (art only) and sand walkways inside a closed tree ring.

## Graph

`NorthWest — North | West — GreatMarsh`, with vertical links North–GreatMarsh and NorthWest–West.

- There are four reciprocal connection pairs, all at offset 0, so every area is reached two ways.
- Both sides of every seam are open on the same cells.

## Tests run

- `test_sinnoh_great_marsh_areas.py` 6/6 (with W10's 4/4). The tests cover:
  - a reproducible build;
  - W10's marsh changes only at the two gaps;
  - every word is attested in Lake Verity or Dewford;
  - reciprocal seams, with closed-gap and wrong-offset negatives;
  - one walkable world from the gate doorstep through all seams, and the rings are closed elsewhere.
- Static map_qa (#252 `64d0e222`) on eastern-loop + W10 + W18: Pastoria, the gate and all four areas, **0 findings** (8 seam tiles per area, no pockets).
- No ROM, mGBA or Save claim yet. The seams get their live check at the connected-batch integration gate.

## Not included

No Safari mechanic, encounters, objects, story or sections (MAPSEC_PENDING_OWNER). The new layout and map IDs are owner-gated.
