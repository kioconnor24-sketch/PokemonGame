# W15 Solaceon Ruins depths: checkpoint

OFF-ENGINE staging, stacked on W8 (`claude/lost-tower-w8`, `5823b4d3`). New construction in Averon's General + Cave banks only.

## Maps (7)

**Ruin chambers SolaceonRuins_A/B/C.** W8's three chambers, re-staged on their own derived layouts. Each is a copy of its stock Desert Ruins / Island Cave / Ancient Tomb blockdata with **one** changed cell: a Granite Cave down-ladder at (8,5) in the inner room. The stock Hoenn layouts are untouched. W8's three warps are kept verbatim; warp 3 is the new ladder.

**New floors:**

| Map | Size | Ladders |
| --- | --- | --- |
| SolaceonRuins_B1F (hub) | 44×30 | 3 up (A, B, C), 2 down (West, East) |
| SolaceonRuins_B2F_West | 30×22 | up, down |
| SolaceonRuins_B2F_East | 30×22 | up, down |
| SolaceonRuins_B3F_Sanctum | 36×24 | two up-ladders, closing the loop |

The new floors use W1's cave kit, Granite Cave ladders and the ruin chambers' own pillar (725, always on open floor as in the source).

## Graph

`A/B/C → B1F → (B2F_West | B2F_East) → B3F_Sanctum`

- Every warp is a ladder pair with a reciprocal index.
- All three Route 209 chambers join one network.
- The sanctum is reached two ways.

## Tests run

- `test_sinnoh_solaceon_depths.py` 6/6 (with W8's `test_sinnoh_lost_tower.py` 6/6). The tests cover:
  - a reproducible build;
  - one changed cell per chamber;
  - W8's warps preserved;
  - reciprocal ladders, plus a one-way negative;
  - every ladder reachable on its floor, with the floor closed;
  - network connectivity and the loop.
- Static map_qa (#252 at `64d0e222`) on the hearthome-solaceon scene + W8 + W15: Route 209 and all 7 maps, **0 findings**.
- No ROM, mGBA or Save/Continue claim for W15 yet. That belongs to the connected-batch integration gate.

## Not included

There are no objects, Unown, braille, encounters, items or story. Sections are MAPSEC_PENDING_OWNER, and new layout and map IDs are needed at integration (owner-gated).
