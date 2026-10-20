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

## Throwaway mGBA check (2026-10-20)

This is a NORMAL-only run in an uncommitted throwaway tree: maps registered locally, section shown as ROUTE 201,
no IDs allocated. ROM `bb6e7cc6…`, 0 compiler warnings. The tooling is `claude/map-qa-batch` @ `c547ddfd`.

**Result: 25/25 PASS, 0 static findings.** The batch-aware audit joins Route 204's halves through Ravaged Path.
- **Warps:** all four, both ways, with the follower visible after each arrival and an exit still reachable.
- **Edges:** both north and the south closed edges block.
- **Menus:** Start menu and SAVE work.

The first runs found the unenterable north cave door, now fixed in `ACCESS_EDITS`. They also showed that the driver
routed through an unreachable door, which `c547ddfd` fixes.

**Rerun with the builder's production headers** (staged map.json/scripts.inc, installed by `--engine` with
stand-in sections in a throwaway on main `eadd5ef1`; ROM `eedc3429…`, 0 warnings):

| Check | Result |
| --- | --- |
| Static | 0 findings |
| NORMAL mGBA | **25/25** |
| Save → fresh Continue | **3/3** |
| `negative-route204-warp-swap` | **FAIL as required**: static `exit-unreachable`, and the warp 1 round trip fails |

That negative points Ravaged Path's north exit at the south door. It also stranded the player in the wrong half, so
the north-edge checks failed too.

**Not run:** RELEASE. It belongs to the production PR, once IDs are approved.

## Corridor throwaway check (Route 204 + Ravaged Path + Floaroma Town + Floaroma Meadow)

Installed with stand-in sections in an uncommitted throwaway on main `eadd5ef1`, using the region-aware driver from
`claude/map-qa-regions` `498fc37e`. ROM `d26e051b…`, 0 warnings.

| Check | Result |
| --- | --- |
| Static, whole corridor | 0 findings |
| NORMAL mGBA | **48/48** |
| Save → fresh Continue | **3/3** |

The runs covered the Route 204 ↔ Floaroma seams both ways, all Ravaged Path and Meadow step-on warps with the
follower, and the closed edges.

Earlier corridor runs found and fixed:
1. dead-end seam cells, now Route 204 bushes;
2. a one-tile nook reachable only from Floaroma, now bushes on both sides;
3. a driver that walked toward an edge reachable only through the cave, now region-aware routing.

## Open before production

1. **`map_qa` batch reachability:** done on `claude/map-qa-batch`.
2. **Door collision:** done. The north cave door's collision bit is cleared, and the door was verified in mGBA.
3. **IDs and sections:** none allocated. The ends stay closed until Jubilife (Codex #184) and Floaroma exist.
