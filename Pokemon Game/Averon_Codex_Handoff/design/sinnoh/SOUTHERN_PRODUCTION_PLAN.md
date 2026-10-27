# Southern and central production plan (C48)

Written 2026-10-27 against main `eec3efd4`, with packet C (#337) pending. This is a design document only. It installs nothing, and it allocates no section, slot or ID.

## Where production ends

Production Sinnoh slots 0–29 cover Twinleaf, Sandgem, Verity, Jubilife, Route 201–205, Floaroma, Valley Windworks and Oreburgh Gate. Packet C (#337) would add Oreburgh City and its ten interiors at slots 30–40. Every exit beyond that is closed:
- Route 207 and the mine at Oreburgh;
- Route 205 North;
- Route 218 and the Eterna side.

Anything further south or central has to join physically through one of those exits. No new portals.

## The physical chain, map by map

Owner of each staged map, and the evidence it has so far:

| Step | Maps | Staged by | Evidence |
| --- | --- | --- | --- |
| 1 | Route 206 (Cycling Road), Route 207 | Codex `eterna-cycle`, `oreburgh-connected`; W25 join #317/#336 | #336: 39-map DEV NORMAL traversal; the mud-planner fix is in progress |
| 2 | Mt. Coronet 1F South (Route 207 ↔ Route 208) | Codex `remaining-donor` (#237 ledger; reused by #248) | source only; anchors kept closed until integration |
| 3 | Route 208, its gate, Hearthome, Route 209 and its gate, Solaceon, Route 210 South | Codex `hearthome-solaceon` | #227: NORMAL/RELEASE 55/55, Route 208 upper bridge 87/87 |
| 4 | Solaceon houses, Mart, Center | Claude W12 `city-shells` | static |
| 5 | Lost Tower, Solaceon Ruins A/B/C, B1F hub, B2F W/E, B3F sanctum, Entrance | Claude W8, W15 (#285), W20 (#297) | static 0 findings; C46 live gate queued (see below) |
| 6 | Maniac Tunnel and its B1F → Route 214 | Claude W13, W19 (#294) | W13 live 40/40; whole-join C46 live gate queued |
| 7 | Hearthome ↔ Route 212 gate ↔ Route 212 North/South | Claude W24 `central-joins`; Codex `eastern-loop` and `route212-foot-crossing` | W24 live on the composed scene |
| 8 | Pastoria, the Great Marsh gate, Great Marsh ×4, Pastoria houses | Codex `eastern-loop`; Claude W10 (#268), W18 (#293) | static 0 findings; C46 live gate queued |

Every step above is already staged, so no new site is needed. The one exception is steps 1–2: they become production work only once Codex's W25 lane lands.

## Traversal limits (measured, not assumed)

- **Route 207 mud: Oreburgh → Mt. Coronet is not walkable.**
  - On Codex's oreburgh-connected Route 207, the only cut between the Oreburgh seam (south edge) and the Coronet 1F South door cell (52,5) is the two `MB_MUDDY_SLOPE` cells (18,14)/(18,15). Without them, foot reach from (9,31) is 250 cells and the door's approach (52,6) is not among them; with them it is 904 cells and the door is reached.
  - Native `ForcedMovement_MuddySlope` slides a player on foot south, so this edge works downhill only.
  - The on-foot way into Coronet 1F South is from the north, Eterna → Cycling Road/Route 206 → upper Route 207, which is W25's join. The southbound slide to Oreburgh closes the loop one way.
  - Production must label the uphill direction BIKE-DEPENDENT and not flatten the donor terrain.
- **Route 209 has 4 mud cells.** The C46 Solaceon gate walks them with `mud_qa` (down seams last).
- **Surf:** none of the chains above needs Surf. Route 212 South's crossing is the single source-pinned ground cell from `route212-foot-crossing`. Routes 219–221 and Pal Park (W6, southwest-coast) do need Surf to reach from Sandgem, so they stay out of these packets.
- **Bike:** Cycling Road (step 1) is the bike route. The W25 lane decides how its entry is handled. Nothing in steps 3–8 needs a bike.

## Proposed packet order

Each packet appends slots after the previous one. It needs:
- an owner exact-path handoff;
- the exact-head NORMAL/RELEASE gate with Save → fresh Continue;
- a re-pin of the Codex DEV families to the new prefix.

| Packet | Content | Lane | New sections needed |
| --- | --- | --- | --- |
| D | Route 206 (+ North/South), Route 207, Mt. Coronet 1F South | Codex (W25) | Route 206, Route 207, Mt. Coronet |
| E | Route 208 (+ gate), Hearthome, Route 209 (+ gate), Solaceon + interiors, Lost Tower, Solaceon Ruins network, Route 210 South | Codex outdoors + Claude interiors/ruins, one combined installer like packet C | Route 208, Hearthome, Route 209, Solaceon, Solaceon Ruins, Lost Tower, Route 210 |
| F | Route 212 gate/North/South, Pastoria + houses, Great Marsh gate + 4 areas | Codex outdoors + Claude marsh/houses | Route 212, Pastoria, Great Marsh |
| G | Route 213/214, Valor Lakefront, Veilstone, Maniac Tunnel ×2 | Codex outdoors + Claude tunnel | Route 213, Route 214, Valor Lakefront, Veilstone, Maniac Tunnel |

Packet E depends on D, because Coronet 1F South is the only physical way into Route 208. F depends on E, through Hearthome's Route 212 gate. G closes the loop: Pastoria → Route 213 → Valor → Route 214 → Maniac Tunnel → Ruins.

Section values are an owner decision. The current request is #15 6444910204, item 2. It proposes 228–236 for the first sections; the full order above would need more.

## What Claude does next, without a decision

- Run the C46 live DEV gates: the Solaceon network (13 maps on hearthome-solaceon + eastern-loop) and the Great Marsh network (14 maps on eastern-loop). Post the results on #285/#294/#297 and #268/#293.
- Once packet D's shape is known, draft packet E's installer from those staged sources, following packet C. This uses Codex modules read-only, appends only, closes exits honestly and includes its own location test.
