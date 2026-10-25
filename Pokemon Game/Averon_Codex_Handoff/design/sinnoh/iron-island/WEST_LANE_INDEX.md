# Claude west/south lane: batch index (handoff 2026-10-25)

Labels: **SOURCE** = staged files plus source tests; **DEV** = temporary-slot ROM tested in mGBA; none of this is production. Sections are `MAPSEC_PENDING_OWNER` everywhere. No story, NPCs, encounters, items or save changes.

| PR | Branch | Batch | Status |
| --- | --- | --- | --- |
| #258 | `claude/iron-island-w1` | **W1**: Route 218 → Canalave (harbor, center, library, houses) → Iron Island (1F–B3F, 2 entrances) + Fullmoon Island | Gate **NORMAL and RELEASE 252/252**, each + Continue 3/3. Fullmoon: SOURCE + static 0 findings. |
| #254 | `claude/southwest-coast-w2` | **W2**: Routes 219–221 + Sandgem seam proposal | Gate NORMAL and RELEASE 36/36, each + 3/3 |
| #255 | `claude/fuego-ironworks-w3` | **W3**: Fuego Ironworks (new) | DEV 28/28 in both builds + Continue |
| #256 | `claude/verity-cavern-w4` | **W4**: Verity Cavern (new) | DEV 14/15 in both builds; the 1 failure is the Surf-only islet |
| #257 | `claude/valley-windworks-w5` | **W5**: Valley Windworks | DEV NORMAL and RELEASE 42/42, each + Continue 3/3 |
| #260 | `claude/pal-park-w6` | **W6**: Pal Park + gate (new) | Gate NORMAL and RELEASE 35/35, each + 3/3 (Route 221 → gate → park) |
| #265 | `claude/wayward-cave-w7` | **W7**: Wayward Cave 1F/B1F (new) | SOURCE 4/4; static clean (the cave joins Route 206's existing south section) |
| #267 | `claude/lost-tower-w8` | **W8**: Lost Tower 6F + Solaceon Ruins ×3 (Route 209) | SOURCE 5/5; static: Lost Tower clean. **Solaceon Ruins unreachable** because of Route 209's own pocket elevations (reported to Codex). |
| #268 | `claude/great-marsh-w10` | **W10**: Great Marsh + gate + Pastoria House1–8 | SOURCE 4/4; static **0 findings** |
| #269 | `claude/amity-square-w11` | **W11**: Amity Square + Hearthome House1–7 | SOURCE 4/4; static **0 findings** |
| #270 | `claude/city-shells-w12` | **W12**: 24 neutral shells (Veilstone, Route 213, Valor Lakefront, Solaceon, Routes 208/210S/212S) | SOURCE 3/3; static: every door joins an existing region. Route 213 (74,4) is left closed (sealed plateau). |
| #252 | `claude/map-qa-elevation` | Tooling: elevation, span-aware seams, ladders, follower step-on fix | Verified in mGBA by the W1 gate; hold released |

## Merge order

1. **#252** is independent.
2. **#258 (W1)** goes before W3, W4, W5, W7, W8 and W12, which are stacked on it.
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
  - **Newmoon Island:** there's no third harbor gangway;
  - **Flower Paradise:** Floaroma Meadow's NE tunnel is solid trees in production;
  - **Trophy Garden:** Route 212 has no mansion to anchor it.

## Issues

- **#263:** engine `make -j` race empties `heal_locations.json`.
- **#264:** map_qa follower probe re-takes step-on warps. Fixed in #252.

## Still to run

- W10 runtime gate on the eastern-loop scene (running).
- Runtime gates for W7, W8, W10, W11 and W12 on Codex family scenes. They need those families' builds.
