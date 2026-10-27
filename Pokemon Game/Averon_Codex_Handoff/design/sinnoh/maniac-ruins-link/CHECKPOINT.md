# W19 Maniac Tunnel → Solaceon Ruins link: checkpoint

OFF-ENGINE staging. The branch is a merge of my own W15 (`2072b44b`, #285) and W13 (`f8b4dfa3`, #275), unchanged, plus this folder. The DS anchor is that Route 214's Maniac Tunnel is dug through into the Solaceon Ruins.

## Maps (3)

| Map | Change |
| --- | --- |
| ManiacTunnel (W13, re-staged) | One cell: a down-ladder at (16,4). One warp appended; the Route 214 exit stays warp 0. |
| SolaceonRuins_B2F_East (W15, re-staged) | One cell: an up-ladder at (24,16). One warp appended; the W15 ladders keep their indices. |
| ManiacTunnel_B1F (new, 56×16, W1 cave kit) | A long dug passage with four outcrops and an up-ladder at each end. |

## Graph

`Route 214 → ManiacTunnel → B1F passage → Ruins B2F East`, which joins the whole W15 network (and through it Route 209's three chambers). Both ladder pairs are reciprocal index-for-index.

## Tests run

- `test_sinnoh_maniac_ruins_link.py` 5/5. The W13 (7/7), W15 (6/6) and W8 (6/6) suites also pass on the merged tree. The tests cover:
  - a reproducible build;
  - one changed cell and one appended warp per re-staged map;
  - reciprocal ladders, plus a one-way negative;
  - every ladder reachable on its floor, with the floor closed.
- Static map_qa (#252 `64d0e222`) on hearthome-solaceon + W8 + W15 + W19: the Ruins B1F/B2F East/B3F, the passage and the tunnel, **0 findings**.
- **No live run across the join.** Route 214 (eastern-loop) and Route 209 (hearthome-solaceon) live in different Codex scenes, and no single scene holds both. W13's side was already exercised live (40/40), and the Ruins side is in the W15 gate.

## Not included

No objects, Unown condition, story or sections (MAPSEC_PENDING_OWNER).
