# Route 205 South: measured conversion plan (Phase C)

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

Side-by-side sheets, in ID order: `secondary-ids-donor-art.png` (donor art) and `secondary-ids-averon-same-id.png`
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
