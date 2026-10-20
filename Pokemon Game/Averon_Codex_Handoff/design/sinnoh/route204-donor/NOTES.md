# Route 204 + Ravaged Path: staging notes (off-engine; claim #15 6284624908)

**Credit:** layouts by LiderMorti00 ([Sinnoh-pokeemerald-expansion](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion)),
rev `38228bb5`, owner-reported permission in #15 6274520543. Converted by `build_route204.py`; hashes are in
`route204-convert-receipt.json`; renders are `route204-built.png` and `ravaged-path-built.png`.

## Static `map_qa` result

Run in a throwaway tree, with the staged maps registered locally only; no IDs were allocated.

| Map | Result |
| --- | --- |
| Ravaged Path | **0 findings**. Both exits are mutually reachable. |
| Route 204 | **1 finding:** `exit-unreachable` between its two cave doors, (11, 31) south half and (19, 24) north half. |

The Route 204 finding is the intended geography, as in DPPt: the halves are joined **through Ravaged Path**. Both
directions are flagged; there is no ledge between the halves.

The audit and the runtime driver's `go` are per-map. Accepting this batch therefore needs batch-level
(cross-map) reachability in `map_qa`, not a geography edit.

## Open before production

1. **`map_qa`:** treat two exits as connected when another map in the batch links them, both statically and at runtime.
2. **Door collision:** the north cave door (19, 24) carries the collision bit in the donor. Check in mGBA whether it can be entered, and clear the bit as a documented access fix if not.
3. **IDs and sections:** none allocated. The ends stay closed until Jubilife (Codex #184) and Floaroma exist.
