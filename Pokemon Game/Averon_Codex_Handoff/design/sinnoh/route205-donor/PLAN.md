> **2026-10-21 verified status:** Both205 halves are now preserved and connected-scratch-tested: paired67/67, fresh Continue3/3 and supplementary bridge/walkway69/69 each. [Exact-source checkpoint](CHECKPOINT.md). Production saved-location identities remain owner-pending. The earlier conversion plan below is historical context.

# Route 205 South: conversion (done) and plan record

## Status (2026-10-20): converted and tested in a throwaway build

`build_route205.py` converts all 40 donor Mauville IDs to Averon tiles of the same movement behavior. Changed
cells: 166, every one listed and asserted. The table below is the plan this followed.

**Five-map corridor throwaway**, installed with stand-in sections and never committed; ROM `9e08dbc9…`, 0 warnings.
The corridor is Route 204 → Ravaged Path → Route 204 north → Floaroma Town (+ Meadow) → Route 205 South.

| Check | Result |
| --- | --- |
| Static | **0 findings** |
| NORMAL mGBA | **56/56**, including the Floaroma ↔ Route 205 seam both ways with the follower |
| Save → fresh Continue | **3/3** |
| `negative-route205-wrong-offset` | **FAIL as required**: static `seam-mismatch`, and both seam crossings fail |

Fixed while building:
- Route 205's west mountain floor at (0, 16/17/21) faced nothing across the seam. It is solid rock now.

Documented departures:
- **Sideways stair:** the donor's 3-cell sideways stair (MB_SIDEWAYS_STAIRS_RIGHT_SIDE) is plain walkable ground.
  Averon's General has no such metatile.
- **South plank bridge:** drawn with Averon's log bridge (MB_BRIDGE_OVER_OCEAN). The kept elevation-3 bits govern
  crossing.

Not run: RELEASE, which belongs to the production PR. Section IDs: see `SECTION_RECOMMENDATION.md`.

---


**Source:** LiderMorti00 rev `38228bb5`, `data/layouts/Route205_South/map.bin` (git blob `569eaa93…`).
32×96 cells, `gTileset_General` + `gTileset_Mauville`, the same banks as Floaroma.

**Donor connections:**
- `left` Floaroma Town, offset +64: the bottom path, rows ≈ 86–88, heading west into Floaroma's east edge;
- `up` Route 205 North, +20;
- `right` Valley Windworks, 0.

The donor's warps go to Eterna Forest (14, 12)/(15, 12) and a house (21, 22). Only the Floaroma connection is in scope;
the others stay closed until their maps exist.

## What already works in Averon's art

Rendering in Averon's own banks (`route205-south-averon-banks-unconverted.png`) shows the primary geometry intact:
mountains, cliffs, the river, the long log bridge, paths, tall grass and the house roof.

**Secondary IDs:** 40 IDs across **167 cells (≈5%)**. None is record- and attribute-identical to Averon's Mauville
bank.
- **Floaroma end (rows 64–95):** 12 IDs, ≈40 cells.
- **North:** 28 IDs.

The contact sheet `secondary-ids-averon-same-id.png` shows Averon's art at these IDs, in ID order (a donor-art sheet is kept private: its redistribution is not documented)
(Averon's art at the same IDs).

## Role families and the planned Averon equivalent

| IDs | Donor role | Plan |
| --- | --- | --- |
| 539–543, 547–550, 557, 565 | Forest tunnel (the same set as the Floaroma/Meadow tunnels) | Tree halves and grass, as in `floaroma-donor/build_floaroma.py`. The Eterna Forest entrance stays **sealed** until Eterna Forest exists. |
| 706–708, 714–716 | Log bridge | Averon's Mauville draws log-bridge art at these IDs: verify attributes, then keep or remap. |
| 566, 567, 944–950 | White fences (river garden, south) | Averon General fence family (313/320/322/329), by orientation. |
| 924–927, 932–935, 940–942 | Cliff and rock trims, a plant | Averon General rock and mountain edges by role, checked against the neighboring primary cells. |
| 956–958 | Plank bridge (south-east, over the river) | Averon bridge tiles (Mauville/General). Must keep the bridge's walkability and elevation bits. |

## Order of work

1. **Floaroma end first** (rows 64–95, 12 IDs) plus the Floaroma ↔ Route 205 seam. That gives a connected
   **Route 204 → Floaroma → Route 205 South (south part)** corridor. The north end stays closed at a visibly blocked
   boundary until the north half is converted.
2. **North half** (28 IDs), with the Eterna Forest entrance sealed.
3. Same tooling and gates as the Floaroma corridor:
   - asserted remap tables, collision/elevation preserved;
   - zero `map_qa` static findings for the batch;
   - a throwaway mGBA run before any production PR.

No section IDs are assigned; that is an owner decision covering the whole corridor.

## Next batch assessment: Valley Windworks (Route 205 South's east edge)

Donor `ValleyWindworks`: 32×99 cells, General + Mauville. It uses **55 secondary IDs over 170 cells** of 3,168.
Connections: left Route 205 South (0), up Route 205 North (−9). It has 1 interior warp, 4 objects and 2 triggers,
none of which are imported.

| Area | In Averon's banks | Needs |
| --- | --- | --- |
| Top two-thirds | Solid mountain filler | Nothing |
| Facility building | Draws acceptably as an Averon-style building | Closed shell |
| Riverbank and grass | Fine | Nothing |
| **Wind turbines** (the row of structures at the bottom, plus pieces on the right) | **No Averon equivalent**; they draw as teal stripes | New compatible art, or a deliberate neutral substitute (e.g. solid rock or posts). This is a visual design decision, not a behavior-preserving remap. |

The site is a story location in the original games, so it would stay neutral: no Galactic content.

**Recommended order:** convert the non-turbine area with the same behavior-matched method. Ask the owner whether the
turbines may be replaced by neutral solid scenery until compatible art exists. Then connect it to Route 205 South's
east edge.
