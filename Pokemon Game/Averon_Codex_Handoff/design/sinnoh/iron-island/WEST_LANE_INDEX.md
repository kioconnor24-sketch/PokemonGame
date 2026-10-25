# Claude west/south lane: batch index (handoff 2026-10-25)

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
| #267 | `claude/lost-tower-w8` | **W8**: Lost Tower 6F + Solaceon Ruins ×3 (Route 209) | SOURCE 6/6; static 0 findings after a derived Route 209 overlay sets the 8 pocket step cells to elevation 0 (`5823b4d3`). **DEV gate FAIL 136/170**: the Ruins and Route 209 pass, but the **Lost Tower stairs (1F→2F onward) don't trigger** (open defect). Continue 3/3. |
| #268 | `claude/great-marsh-w10` | **W10**: Great Marsh + gate + Pastoria House1–8 | SOURCE 4/4; static **0 findings**; **DEV gate NORMAL 174/174 + Continue 3/3** (eastern-loop scene) |
| #269 | `claude/amity-square-w11` | **W11**: Amity Square + Hearthome House1–7 | SOURCE 4/4; static **0 findings**; **DEV gate NORMAL 149/149 + Continue 3/3** (hearthome-solaceon scene) |
| #275 | `claude/sendoff-spring-w13` | **W13**: Spring Path → Sendoff Spring → Turnback Cave 1F/B1F/B2F + Maniac Tunnel; Route 214 derived overlay | SOURCE 7/7; static **0 findings** (eastern-loop scene); runtime gate stopped early at wrap-up (fixture start outside the batch) |
| #276 | `claude/jubilife-shells-w14` | **W14**: Jubilife Global Terminal, TV, Pokétch Company and 2 condos behind production Jubilife's 7 closed doors (DEV overlay) | SOURCE 5/5; static **0 findings** (production scene); ROM built, runtime not run yet |
| #270 | `claude/city-shells-w12` | **W12**: neutral shells (Veilstone, Route 213, Valor Lakefront, Solaceon, Routes 208/210S/212S) + **Veilstone civic interiors** (Pokémon Center, warehouse, department store 1F–5F + rooftop via a one-cell derived door; `3873daf5`) | SOURCE 5/5; static 0 findings (Veilstone + 9 civic floors). Route 213 (74,4) left closed (sealed plateau). Runtime gate queued. |
| #252 | `claude/map-qa-elevation` | Tooling: elevation, span-aware seams, ladders, follower step-on fix, bridge start elevation (review 5641599180), **one-way holes / arrival-only warps** (`ba533bed`), **seams from a bridge use the actual elevation** (review 5644727982, `4e71ae64`), `go()` returns to the map (`68c27967`) | Host 67 OK; live W5 scene 42/42 + 3/3 at `37d52157` |

## Merge order

1. **#252** is independent.
2. **#258 (W1)** goes before W3, W4, W5, W7, W8, W12, W13 and W14, which are stacked on it.
3. **#254 (W2)**, then **#260 (W6)**. W6 is stacked on both W1 and W2.
4. **#268 (W10)** and **#269 (W11)** come after #260.

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
  - **Trophy Garden:** Route 212 has no mansion to anchor it.

## Issues

- **#263:** engine `make -j` race empties `heal_locations.json`.
- **#264:** map_qa follower probe re-takes step-on warps. Fixed in #252.

## Still to run

- **Fix W8's Lost Tower stairs** (failing warps listed on #267).
- Re-run the W13 gate with the save inside Spring Path; run the W14 gate (production scene ROM `db14652c` built in `wt-prodthrow`).
- W12 runtime gate; RELEASE builds for the family-scene batches at integration.
