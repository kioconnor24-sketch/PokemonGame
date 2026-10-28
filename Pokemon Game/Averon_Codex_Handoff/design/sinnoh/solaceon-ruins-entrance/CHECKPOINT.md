# W20 Solaceon Ruins entrance: checkpoint

OFF-ENGINE staging. The branch is W19 (#294, which carries W15 and W13) merged with my W12 (#270), unchanged, plus this folder.

## DS anchor

Solaceon Town's east cliff (Codex's hearthome-solaceon, read-only) draws two cave mouths: (55,19) on the ledge and (54,23) at the foot. Both are walkable `MB_NON_ANIMATED_DOOR` cells with no warp. W12 had opened only animated doors.

## Maps (3)

| Map | Change |
| --- | --- |
| SolaceonTown-dev-overlay (W12's, re-staged) | Two warps appended, one per mouth. W12's warps and derived map.bin are unchanged. |
| SolaceonRuins_Entrance (new, 30×20, W1 cave kit) | Two Granite Cave mouths back out (one per cliff door), a central outcrop, and a down-ladder. |
| SolaceonRuins_B1F (W15, re-staged) | One cell: an up-ladder at (21,4). One warp appended. |

## Network now

Solaceon Town (2 mouths) → Entrance → Ruins B1F hub, which connects to:
- Route 209's chambers A/B/C;
- B2F West/East → B3F Sanctum;
- B2F East → Maniac Tunnel B1F → Maniac Tunnel → Route 214 (W19).

## Not opened

Solaceon's 4-wide houses draw the door picture 593 beside the end piece 529. No door of the family is ever drawn next to 529, so the horizontal pair is unattested and they stay closed.

## Tests run

- `test_sinnoh_solaceon_ruins_entrance.py` 6/6. On the merged tree, W12 7/7, W19 5/5 and W15 6/6 also pass (24 in total).
- Static map_qa (#252 `8fc79e81`, rail-aware) on hearthome-solaceon + W8 + W15 + W19 + W12 + W20: Solaceon Town, the Entrance, B1F, Route 209 and Route 210 South, **0 findings**. Both mouths are reachable on foot, including the ledge.
- No ROM or mGBA claim yet.
