# Route 202: donor geometry import

**Imported:** one file's block geometry only. The 30×34 `map.bin` (2,040 bytes) of `Route202` from
[LiderMorti00/Sinnoh-pokeemerald-expansion](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion).

**Credit:** Route 202 map layout by LiderMorti00 (Sinnoh-pokeemerald-expansion), used with the owner-reported
permission recorded in [Issue #15 comment 6274520543](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6274520543).

| Item | Value |
| --- | --- |
| Donor revision | `38228bb574a3557345852b758d5f1a65eb01bb22` (checked against the local clone's `git rev-parse HEAD`) |
| Donor path | `data/layouts/Route202/map.bin` |
| Git blob | `25c724524810a7a188d30947cb885a4e5e44e8b9`, checked locally, matching PR #176 |
| SHA-256 | `9f58a62052998ed869259356c395302ef5bfa35624b612c0e68ae1922e00437b` (input = output) |
| Converter | `scripts/sinnoh-donor-map-pilot.py` from PR #176 at `54264fe4` |
| Manifest | `route202-remap.json` |
| Receipt | `route202-convert-receipt.json` |
| Builder | `build_route202.py` |

**Graphics: no donor art is used.** The donor draws this map with its own Sinnoh-style `gTileset_General`. Every one of
those files differs from Averon's: tiles, metatiles, attributes and all 16 palettes. The route is drawn with
**Averon's existing** `gTileset_General` + `gTileset_Dewford`, the same banks as Sandgem, Route 201 and Twinleaf. As a
result, the donor's pine trees and sign look like Averon's round trees and sign, in the same cells
(`route202-built.png`). Nothing in the shared General bank is changed.

**Per-ID verification (all 25 IDs the route uses are primary):**

| Check | Result |
| --- | --- |
| Behavior | `metatile_attributes.bin` matches word-for-word on 24 IDs. ID 3 (the sign) differs only in layer-type bits `0x1000`, which control drawing order; its behavior byte is `0x00` on both sides. |
| Collision and elevation | Stored in `map.bin`; byte-identical. |
| Role | Every ID keeps its role (grass, tall grass, path, ledge, tree, sign) when rendered in both banks. |

PR #176's ten "structurally unmatched" IDs (3, 454, 455, 462, 463, 470, 471, 478, 479, 487) are those art-only
differences: tree quarters and the sign.

**Not imported:** six object events (trainers and NPCs), ten coordinate events, the hidden item, donor scripts and
text, music, the donor connections (Sandgem −2, Jubilife −38) and the donor map and section IDs.

**Averon additions:**

| Addition | Detail |
| --- | --- |
| Signs | Three route signs on the donor's sign cells (14, 3), (11, 14) and (21, 25), with neutral text: `ROUTE 202`, and `SOUTH: SANDGEM TOWN` on the north sign |
| Music | `MUS_ROUTE101`, like Route 201 |
| Section | 219 `MAPSEC_ROUTE_202` |
| Sandgem junction | Route 202 `down` **+4** ↔ Sandgem `up` **−4**. The donor's south opening x 22–27 meets Sandgem's north opening x 19–24, giving a 5-wide walkable overlap (Sandgem x 19–23) that includes Sandgem's road. The offset is even, so tree columns stay aligned. |
| North edge | The opening (x 8–15) stays **closed** until Jubilife exists |
