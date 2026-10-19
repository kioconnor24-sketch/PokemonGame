# Route 202: reference status (C3). No candidate geometry yet

**Status: BLOCKED ON A TRUSTWORTHY REFERENCE.** I could not obtain a full original DPPt overhead of Route 202. Without one, drawing its path, ledges and grass would be invention, which the assignment rules out ("if unavailable say so, do not hallucinate"). So no Route 202 overhead or collision candidate is proposed yet. Its two ends are fixed by built or referenced neighbours and are specified in [`../SINNOH_JUNCTIONS.md`](../SINNOH_JUNCTIONS.md) (junctions D and E).

## What was searched (2026-10-18)

| Source | Result |
| --- | --- |
| Elite Fourum "Mapping out Gen 4 cards…" thread (the source of the Route 201, Sandgem, Lake Verity and Jubilife overheads) | Has sections for Route 201 / Twinleaf, Sandgem, Lake Verity, Jubilife and Route 203. **No Route 202 section.** |
| Serebii Pokéarth, DPPt page (`/pokearth/sinnoh/4th/route202.shtml`) | Only map image is `maps/sinnoh-pt/2.png`, **256 × 192 px: one DS screen (16 × 12 tiles)**, not the route |
| Serebii Pokéarth, BDSP page | `maps/sinnoh-bdsp/2.jpg`, a 640 × 360 3D screenshot, not an overhead |
| The Spriters Resource (DP and Platinum map sheets) | HTTP 403 to the fetcher |
| Bulbapedia / Bulbagarden Archives | blocked to the fetcher earlier in this project (403) |
| pokemondb.net location page and maps index | encounter tables only; maps only for caves and gyms |

## What *is* reliable

- **Ends.**
  - **North: Jubilife City.** The overhead gives a 3-wide stair exit at columns 44–46 of a ~64 × 48 map.
  - **South: Sandgem Town.** The built #133 layout's north edge is open on columns 19–24, with the road on 21–22.
- **Shape (Serebii text).** "a north-facing route between Sandgem Town and Jubilife City … a fairly short route which zigzags when going north."
- **One-screen fragment (Serebii DPPt image).**
  - a 2-wide sand path that turns;
  - a sign on a small light-grass pad;
  - a 2 × 3 tree block;
  - tall grass on the east side;
  - a south-facing ledge with a tree row on it;
  - a route sign below the ledge.

  The fragment's position within the route is unknown, so it fixes no coordinates.

## Decision needed (owner)

Choose one:

1. **Provide or approve a full reference**, for example a Bulbapedia/Bulbagarden map image of Route 202 saved into the session. I'll then produce the same construction-ready package as Route 201: tile-by-tile footprints, generator, collision render, seam previews, and a reachability proof with negative self-tests.
2. **Approve a schematic Route 202.** I'd make an original-shaped zigzag between the two fixed ends, clearly labelled *not reference-accurate*. This trades the "original layout" rule for progress, so it needs your explicit yes.
3. **Keep Route 201 first** (#135 is construction-ready) and revisit Route 202 later.

My recommendation is 3, then 1. Route 201 already has a verified original geometry.
