# Route 202: reference status (C3)

**Status: RESOLVED (2026-10-19).** A full original DPPt overhead of Route 202 was obtained and hash-verified. The construction-ready candidate built from it is in [`ROUTE202_CANDIDATE.md`](ROUTE202_CANDIDATE.md): generator, plan JSON, renders, a Sandgem seam preview, and a reachability proof with negative self-tests. Junctions D and E in [`../SINNOH_JUNCTIONS.md`](../SINNOH_JUNCTIONS.md) can now be filled in from that document.

## Sources used (geometry only; not committed)

Both URLs and SHA-1 values come from the Bulbagarden Archives MediaWiki API (`action=query&list=allimages&aiprop=size|url|sha1`), and the downloaded files hash to the same values.

| File | Size | SHA-1 | Role |
| --- | --- | --- | --- |
| [`Sinnoh_Route_202_DP.png`](https://bulbapedia.bulbagarden.net/wiki/File:Sinnoh_Route_202_DP.png), `https://archives.bulbagarden.net/media/upload/3/39/Sinnoh_Route_202_DP.png` | 592 × 416 | `deffab27d40d430ae1dedac8958d2929f78edcdd` | primary reference: every footprint |
| [`Sinnoh_Route_202_Pt.png`](https://bulbapedia.bulbagarden.net/wiki/File:Sinnoh_Route_202_Pt.png), `https://archives.bulbagarden.net/media/upload/0/09/Sinnoh_Route_202_Pt.png` | 610 × 452 | `67674efa0c162974728964ba3a5988138fef0126` | cross-check: topology, and Jubilife's stairs above the north clearing |

Both are foreshortened 3D renders: 16 px per tile across, about 12.3 px down. The candidate document states which footprints are measured (flat ground: sand, ledges, tall-grass edges) and which are ±1 (trees, signs, NPCs).

## What changed since the blocked note (2026-10-18)

- **Reachable source.** The earlier search could not reach Bulbapedia or Bulbagarden Archives (HTTP 403 to the fetcher). The archive's API and file URLs are reachable with a plain browser user agent, and the files' hashes are checked against the archive's own record.
- **Superseded content.** The earlier one-screen Serebii fragment and the text description ("a fairly short route which zigzags when going north") are superseded. The full overhead shows that zigzag:
  1. west along the south strip;
  2. north through the south-west grass;
  3. east along the cross path;
  4. north through the east field;
  5. back west along the upper paths.
- **Sandgem's north edge** was re-measured from the built `map.bin`: open on x 19–24, road 21–22. The old note was right.
- **Jubilife's stairs** (x 44–46 in SINNOH_JUNCTIONS.md) are not re-measured here. The Platinum overhead confirms only that they land on Route 202's north clearing.

## Remaining owner decisions

These are listed in `ROUTE202_CANDIDATE.md` section 6:
- the geometry;
- Route 202's **section ID**, which is not owner-approved and not allocated or named by this work;
- the Sandgem connection;
- keeping the north edge closed until Jubilife exists.
