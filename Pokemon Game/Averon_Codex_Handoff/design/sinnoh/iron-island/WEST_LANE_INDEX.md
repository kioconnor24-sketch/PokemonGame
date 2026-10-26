# Claude west/south/central/south-east lane: batch index (handoffs 2026-10-25, 6406013875)

Labels: **SOURCE** = staged files plus source tests; **DEV** = temporary-slot ROM tested in mGBA; none of this is production. Sections are `MAPSEC_PENDING_OWNER` everywhere. No story, NPCs, encounters, items or save changes.

| PR | Branch | Batch | Status |
| --- | --- | --- | --- |
| #258 | `claude/iron-island-w1` | **W1**: Route 218 → Canalave (harbor, center, library, houses) → Iron Island (1F–B3F, 2 entrances) + Fullmoon and **Newmoon** Islands | Gate **NORMAL and RELEASE 252/252**, each + Continue 3/3. Newmoon + three-plank harbor gangway (`3fd5c974`): static 0 findings; **DEV gate 35/35 + Continue 3/3**. |
| #254 | `claude/southwest-coast-w2` | **W2**: Routes 219–221 + Sandgem seam proposal | Gate NORMAL and RELEASE 36/36, each + 3/3 |
| #255 | `claude/fuego-ironworks-w3` | **W3**: Fuego Ironworks (new) | DEV 28/28 in both builds + Continue |
| #256 | `claude/verity-cavern-w4` | **W4**: Verity Cavern (new) | DEV 14/15 in both builds; the 1 failure is the Surf-only islet |
| #257 | `claude/valley-windworks-w5` | **W5**: Valley Windworks | DEV NORMAL and RELEASE 42/42, each + Continue 3/3 |
| #260 | `claude/pal-park-w6` | **W6**: Pal Park + gate (new) | Gate NORMAL and RELEASE 35/35, each + 3/3 (Route 221 → gate → park) |
| #265 | `claude/wayward-cave-w7` | **W7**: Wayward Cave 1F/B1F (new) | SOURCE 4/4; static clean; **DEV gate NORMAL 14/14 + Continue 3/3** (eterna-cycle scene) |
| #267 | `claude/lost-tower-w8` | **W8**: Lost Tower 6F + Solaceon Ruins ×3 (Route 209) | SOURCE 6/6; static 0 findings after a derived Route 209 overlay sets the 8 pocket step cells to elevation 0 (`5823b4d3`). **DEV gate 184/184 + Continue 3/3** (the earlier 136/170 was a tooling defect: Mt. Pyre holes are one-way; fixed in #252). |
| #268 | `claude/great-marsh-w10` | **W10**: Great Marsh + gate + Pastoria houses + Center (stock Center 1F, `7b5fb8d3`) | SOURCE 4/4; static **0 findings**; **DEV gate NORMAL 174/174 + Continue 3/3** (eastern-loop scene) |
| #269 | `claude/amity-square-w11` | **W11**: Amity Square + Hearthome House1–7, + **House8–9** behind two solid door pictures (derived Hearthome map.bin, `d068e929`) + **civic interiors**: contest lobby/hall, Center, Mart (`684f5f82`) | SOURCE 6/6; static **0 findings**; **DEV gate NORMAL 149/149 + Continue 3/3** (hearthome-solaceon scene, before House8–9) |
| #275 | `claude/sendoff-spring-w13` | **W13**: Spring Path → Sendoff Spring → Turnback Cave 1F/B1F/B2F + Maniac Tunnel; Route 214 derived overlay | SOURCE 7/7; static **0 findings** (eastern-loop scene); **DEV gate 40/40 + Continue 3/3** |
| #276 | `claude/jubilife-shells-w14` | **W14**: Jubilife Global Terminal, TV, Pokétch Company and 2 condos behind production Jubilife's 7 closed doors (DEV overlay) | SOURCE 6/6; static 0 findings; **DEV gate 155/155 + Continue 3/3** after opening the halls' solid non-animated doors (`6343ec68`) |
| #270 | `claude/city-shells-w12` | **W12**: neutral shells (Veilstone, Route 213, Valor Lakefront, Solaceon, Routes 208/210S/212S) + **Veilstone civic interiors** (Pokémon Center, warehouse, department store 1F–5F + rooftop via a one-cell derived door; `3873daf5`) + Solaceon door-picture house (`efcdd649`) + Solaceon Center and Mart stock interiors (`54c07571`) | SOURCE 7/7; static 0 findings. Route 213 (74,4) left closed (sealed plateau); Veilstone (43,67) picture left closed (bottom row, no doorstep). **Veilstone DEV gate 140/140 + Continue 3/3**. |
| #285 | `claude/solaceon-depths-w15` | **W15**: Solaceon Ruins depths: A/B/C chambers on derived layouts (one ladder each) + B1F hub, B2F West/East, B3F Sanctum (loop) | SOURCE 6/6; static **0 findings** (hearthome-solaceon + W8 + W15) |
| #287 | `claude/oreburgh-gate-w16` | **W16**: Oreburgh Gate B1F under production 1F (one-cell derived 1F ladder) | SOURCE 6/6; static **0 findings** (production scene) |
| #291 | `claude/route212-mansion-w17` | **W17**: Route 212 North mansion facade opened (one-cell derived door) onto stock Cove Lily Motel 1F/2F | SOURCE 5/5; static **0 findings** (eastern-loop scene) |
| #294 | `claude/maniac-ruins-link-w19` | **W19**: Maniac Tunnel (W13) dug through to Ruins B2F East (W15) via a new 56×16 passage; branch merges W13 + W15 | SOURCE 5/5; static **0 findings** (hearthome-solaceon). No single scene holds Route 214 and Route 209, so no live crossing. |
| #297 | `claude/solaceon-ruins-entrance-w20` | **W20**: Solaceon's two warp-less cliff cave mouths → new Ruins entrance chamber → B1F hub; branch merges W19 + W12 | SOURCE 6/6; static **0 findings** |
| #252 | `claude/map-qa-elevation` | Tooling: elevation, span-aware seams, ladders, follower step-on fix, bridge start elevation (review 5641599180), **one-way holes / arrival-only warps** (`ba533bed`), **seams from a bridge use the actual elevation** (review 5644727982, `4e71ae64`), `go()` returns to the map (`68c27967`), **connection-specific edge exits** (review 5645231711, `64d0e222`), **Acro Bike rails/bumpy slopes not walkable on foot** (`8fc79e81`) | Host 72 run, 1 skipped; live W5 scene 42/42 + 3/3 at `37d52157` |

## Merge order

1. **#252** is independent.
2. **#258 (W1)** goes before W3, W4, W5, W7, W8, W12, W13 and W14, which are stacked on it.
3. **#254 (W2)**, then **#260 (W6)**. W6 is stacked on both W1 and W2.
4. **#268 (W10)** and **#269 (W11)** come after #260.
5. **#285 (W15)** comes after #267; **#287 (W16)** after #258; **#291 (W17)** after #270; **#293 (W18)** after #268.
6. **#294 (W19)** after #285 and #275; **#297 (W20)** after #294 and #270.

## Owner decisions

Production files are untouched in all of these; each is a DEV overlay or proposal only.

- **Proposed connections:**
  - Sandgem ↔ Route 219 (−3);
  - Route 205 South/North ↔ Windworks.
- **Proposed openings:**
  - Lake Verity's cave mouth;
  - the doors and mats on Codex's staged maps (Route 206, Route 209, Pastoria, Hearthome and the W12 maps).
- **Neutral portals:**
  - Canalave Harbor ↔ Iron Island / Fullmoon Island;
  - the Route 209 tower and ruins portals.
- **Art and sections:**
  - Valley Windworks turbine art;
  - all section IDs.
- **Not built, by design:**
  - **Flower Paradise:** Floaroma Meadow's NE tunnel is solid trees in production;
  - **Trophy Garden:** the fenced garden behind Route 212 North's mansion is solid in the source (the mansion itself is W17).

## Integration manifest: maps outside Claude's own new maps that each batch touches

All are DEV-only overlays (header append and/or a same-size derived map.bin); the engine and Codex's files are unchanged.

| Map (owner of base) | Batch | Header change | Derived cells |
| --- | --- | --- | --- |
| CanalaveCity (Codex canalave-west) | W1 | warps appended | pier-house door (525 → 537) |
| OreburghGate_1F (**production**) | W16 | 1 warp appended (Codex's east-exit restore appends after) | (18,5) ladder |
| JubilifeCity (**production**) | W14 | 7 warps appended | 4 hall doors: collision 1 → 0 |
| Route206 (Codex eterna-cycle) | W7 | warps appended | none |
| Route209 (Codex hearthome-solaceon) | W8 | 4 warps + 4 coord triggers | 8 pocket steps: elevation 2 → 0 |
| HearthomeCity (Codex hearthome-solaceon) | W11 | 4 mat warps + 9 door warps | (20,19), (21,30) door pictures → door |
| SolaceonTown, Route208, Route210_South (Codex hearthome-solaceon) | W12 | door warps appended | Solaceon (11,11) picture → door |
| VeilstoneCity, Route213, ValorLakefront, Route212_South (Codex eastern-loop) | W12 | door warps appended | Veilstone (18,10) picture → door |
| Route212_North (Codex eastern-loop) | W17 | 1 warp appended | (24,38) picture → door |
| PastoriaCity (Codex eastern-loop) | W10 | door/gate warps appended | none |
| Route214 (Codex eastern-loop) | W13 | 1 warp + 1 connection appended | tree rows cut (rows 20–21, x ≥ 30) |
| Route221 (Claude W2) | W6 | gate warp | — |
| LakeVerity (**production**) | W4 | 1 warp | cave mouth |
| Route205_North/South (Codex route205-donor) | W5 | connections | — |

Needed at integration for every new map: a layout ID (new blockdata) or stock layout reuse, a map ID in the Sinnoh group (owner-gated, no 227+ origin values) and a section decision. Overlays that share a map with a Codex DEV change (Oreburgh Gate east exit, Route 209 restorations) are appends, so they merge by concatenating warp lists in the documented order.

## Known external blocker

- Codex's eastern-loop Route 212 South: rail rows (MB_HORIZONTAL_RAIL, row 11 x 27–59 and row 22) are a collision on foot, so Route 212 North (W17's mansion) is unreachable from Pastoria. Reported on #15 (6406549902); W17's live gate is deferred.

## Issues

- **#263:** engine `make -j` race empties `heal_locations.json`.
- **#264:** map_qa follower probe re-takes step-on warps. Fixed in #252.

## Still to run

- #252: awaiting manager re-review of `64d0e222` (the multiple-same-edge routing fix).
- W15/W16/W17 and the W11/W12 door-picture additions: DEV mGBA gate at the connected-batch integration gate.
- RELEASE builds for the family-scene batches at integration.
