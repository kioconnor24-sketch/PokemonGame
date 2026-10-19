# Sinnoh — executable Claude/Codex developer work packages

**Planning backlog, 2026-10-19.** Companion to the [master roadmap](SINNOH_MASTER_PRODUCTION_ROADMAP.md), [complete coverage](SINNOH_FULL_AREA_COVERAGE.md), [area register](SINNOH_AREA_REGISTER.csv), and [live Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). **Read live main/PR heads/claims first**; this backlog is not a permanent agent task lock or proof of a finished feature. Owner product direction is [6261800483](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6261800483). Short-term queue at issue #15 takes precedence for unfinished work already claimed by an agent.

## How to use this backlog without a manager bottleneck

1. Both agents refresh current main, Issue #15 claims, active PR head and changed paths. Resume *existing* live work before claiming a new work package. Mark a work item covered by accepted work rather than doing it again.
2. Claim **literal paths and scope**, not entire broad wave. Claude normally owns map source, biome art, gameplay QA; Codex normally owns compatibility, registrations infrastructure, save/travel resources and regression tooling. The split is negotiable for disjoint modules.
3. Select the highest-priority **unblocked** task, implement in a coherent PR, run relevant positive/negative/native/NORMAL/RELEASE/mGBA tests, publish exact-head evidence and merge if eligible under **live** fast-lane/peer-review rules. Do not keep finished PRs waiting for manager acknowledgment.
4. **No story/levels/encounters/trainers** at this stage. Developer-selected physical geography is allowed; technical persistent ID/encoding and protected-path changes require their own real gates. One larger current job should not monopolize shared map-index/generated files for weeks.
5. If any dependency is unresolved, record a one-line issue #15 blocker, switch to a disjoint package below and keep developing. Do not create another task-board system or claim that a GitHub comment awakens an agent.
6. Prefer substantial **batches that produce usable gameplay terrain**, not dozens of tiny documentation PRs. Still isolate saved-schema/migration, CI and broad engine changes for substantive review.

**Standard map acceptance ("MAP-QA"):** exact approved/delegated topology with source citations, authored and build-included map/entry/exit, preflight registry/collision/warp/section pins, NORMAL and RELEASE linked builds and ROM/headroom delta, real mGBA seam and warp in both directions (or explicitly closed future connections), no pockets, basic follower/menus, Save→fresh-process Continue at new site, proper healed respawn if applicable, one negative/mutation test where tool-supported, exact source+ROM hashes and DEV fixture disclosure. A successful screen or compile alone does not pass MAP-QA.

**Standard engineering acceptance ("ENGINE-QA"):** reproducible before/after defect or justified feature contract, affected native positive+negative regression, legitimate Save→flash→Continue across both regions where needed, byte IDs/old saves preserved, relevant profiles and resource measurement, current applicable CI, explicit unverified graphical limitations, exact SHA/file/evidence. High-risk production changes have the independent peer and/or owner decision required by the live contract.

## Active handoff, not repeated work

| Item | Current known checkpoint | Agent next useful action |
| --- | --- | --- |
| Route201/section217 (#150) | Owner approved geometry, 64×22, Sandgem reciprocal offsets -4/+4, endpoints closed, no encounters; was draft awaiting last Route201 fresh Continue evidence | Claude: finish real proof, confirm current checks/merge eligibility, integrate; Codex only finds material compatibility defect |
| Sandgem healer44 (#151) | Owner approved append-only ID44, exterior (15,10), nurse indoor (7,4), on-enter trigger; was draft awaiting real mGBA whiteout, negative and handoff | Claude: genuine whiteout & Save/Continue, exact-path permission, merge if eligible |
| Map QA single-step/whiteout (#152) | Merged at main 862f8205 (2026-10-19 snapshot) | Reuse, don't restart |
| Streamlined merge contract (#153) | Merged at main a7d87067 (2026-10-19 snapshot) | Follow current policy and owner geography delegation, don't build another org reset |
| Current Region Map invalid entry (#154) | Open engineering work when roadmap drafted | Codex: finish current PR before overlapping region-map work |
| Region identity experiments #134/#141 | Test-only proof, no adopted 13-bit encoding | Reuse evidence for owner decision rather than implementing a speculative migration |
| Route202 | Explicit trusted-reference shortage in #139 | Research original source thoroughly; if unresolved, queue it and do other geographically disjoint sites |

## Claude map and authentic gameplay work packages

### C01 — Complete the connected Sandgem wedge (P0, G0)
- Rebase/finish #150 and #151 without source collisions or changing owner-approved decisions. Audit actual signed handoffs, complete Route201 real Continue + healer whiteout/negative/Continue.
- On integrated main, walk Sandgem→Route201→Sandgem, Center door in/out, whiteout, menu and Save/Continue in NORMAL/RELEASE. Distinguish fixture entry from ordinary Averon-to-Sinnoh travel.
- Fix measured visual defects (broken tree halves, tile seams, collision ledges, clipping) without ad hoc geometry change contradicting agreed 64×22. Assess placeholder art accurately.
- Exit: main commit hashes, focused actual mGBA result, route physically connected; no premature "Sinnoh story ready" or "Delta tested" label.

### C02 — Design **the complete Sinnoh topology atlas** (P0, G1)
- Use all 87 rows and extra subareas in the companion coverage document. Source recognizable Diamond/Pearl/Platinum geographic relationships and specifically annotate adaptation/reuse.
- Draw a master region map/adjacency specification with settlements, Routes201–230, caves with multiple exits/floors, three lake basins, snow/coast/marsh, island ports, Battle Zone, underground layer, optional dimensional/special sites. Attach reference provenance and a clearly separate proposed adaptation layer.
- Build per-area source-backed rough dimensions, neighbor IDs, connection offsets/edge directions, warp type, elevation, landmark footprints and potential future neutral story spaces; **do not fake exact dimensions where unavailable**.
- Deliver candidate graph and dependency audit that catches dead ends, incorrect one-way connections, route splits and incomplete lakefronts; show plausible connection paths independent of eventual story scripting.
- Exit: 87/87 tracker keys represented, all missing child-site candidates inventoried, unresolved topology noted with source/question; no permanent map implementation required in this work package.

### C03 — Standardize reused GBA geography assets (P0/P1, G2)
- Inspect usable current native tilesets, collision/metatile definitions and original/properly licensed art. Define a practical biome palette set for settlement, grassland, coast, woodland, mountainous, snowy, marsh, volcanic and ruins.
- Create reusable **actual GBA-compatible** placeholder terrain/structures with stable collision semantics; maintain asset license/source and tile/palette budget. No DS copyrighted source asset import just because screenshots exist.
- Build a small validation run that detects palette mismatch, missing warp arrival, broken tree/metatile seam and sprite pressure; reuse merged map_qa instead of writing parallel harnesses.
- Exit: reusable patterns already exercised in 2 or more representative real (possibly test-only) geography scenes and no silent RAM/VRAM overflow.

### C04 — Southwest origin-to-Jubilife batch (P1, W1)
- Twinleaf Town exterior + rational safe interiors; Verity Lakefront; Lake Verity neutral basin; Route 201 planned south/west joins; route 202 only when the original-reference prerequisite is satisfied; Jubilife City and travel-important interiors.
- Site geometry may be decided by Claude under the owner's delegation, with evidence and later review. Do not copy starter, rival, Galactic or Platinum quest scripts.
- Integrate safe, navigable streets/roads with future event spaces, route boundary checks and optional interior shells. If route202 cannot be responsibly built, integrate other subareas with clearly blocked borders and continue research.
- Exit: MAP-QA on each integrated connected batch; city interiors plus old area still walkable and saveable.

### C05 — Oreburgh / Floaroma / Eterna loop (P1, W2)
- Build Route203, Oreburgh Gate, Oreburgh City/Mine and neutral museum; Route204 and Ravaged Path; Floaroma + Meadow, Valley Windworks physical complex; Route205 south/north, Eterna Forest/City, Old Chateau and Fuego Ironworks.
- Include the western crossover Route206 Cycling Road, Route207, Wayward Cave and Eterna-side Route211 corridor as graph permits.
- Recycle original Galactic physical sites as **neutral undecided facilities**. Never pre-assign narrative identities. Provide correct door/map warp links and non-softlocking alternate routes.
- Exit: route ring and selected interiors meet MAP-QA, source-provenance for material adaptations, resource delta measured.

### C06 — Central Sinnoh and ridge crossings (P1, W3)
- Route208→Hearthome; Route209→Solaceon/Lost Tower; Route210 (both halves)→Celestic; Route211 approaches; Mt. Coronet lower routes/connected caves; Route212 north/south; accessible western Route218 to Canalave and Iron Island ferry **physical terminal candidate**.
- Include Amity Square, contest-oriented interior shell, Solaceon Ruins and Canalave Library as neutral usable spaces without finalized gameplay.
- Treat Mt. Coronet as a multi-floor connected system with explicit entrance/exit graph; one "Mt. Coronet" tracker row is NOT one complete map.
- Exit: no accidental missing returns; neutral puzzle dependencies marked; cavern floors, stair transitions, upper/lower route segments tested.

### C07 — East, lakes and southeast coast (P1, W4/W5)
- Veilstone and its neutral facility reuse, Routes214/215, Route213 + Valor Lakefront/Lake Valor, Pastoria and Great Marsh, Pokémon Mansion/Trophy Garden, Spring Path/Sendoff Spring/Turnback Cave, Route222/Sunyshore, water Route223.
- Build safe terrain and environmental differences (wetlands, beaches, cliffs, city roads); no invented faction headquarters quest, Safari encounter tables or lake legendaries.
- Exit: MAP-QA per joined batch, region graph reconciled, a location can be visited/left/saved even if future content is deferred.

### C08 — Northern mountains and League circuit (P1/P2, W5)
- Routes216/217, northern Mt. Coronet passes, Acuity Lakefront/Lake Acuity, Snowpoint/Snowpoint Temple, Spear Pillar as neutral physical overlook, waterfall/coast route223, Victory Road floors, Pokémon League exterior/interiors and optional Route224 spur.
- Check snowfield movement, cave floor returns, slippery tile physics if used, intended traversal abilities and safe neutral doors. Preserve physical identities while the story is undecided.
- Exit: same real graphical evidence and performance budget per connected batch; no Gym/League battles claimed.

### C09 — Southern sea, island sites and postgame Battle Zone (P2, W6/W7)
- Routes219–221 with water/coastal topology and Pal Park adapted physical site; island routes/boats for Fullmoon/Newmoon; Fight, Survival and Resort Area, Routes225–230, Stark Mountain and Battle Frontier *campus*.
- Implement as multiple linked batches; include genuine coast/Surf transitions and port return/softlock tests before claiming reachability. A Battle Frontier building is not a working Battle Frontier ruleset.
- Exit: all relevant exterior/interior spaces source-integrated and navigable; deferred gameplay tracked honestly.

### C10 — Underground and advanced-world feasibility (P2, W8)
- Evaluate Underground/Grand Underground access, overworld layer/world-map representation, exits, save/continue and actual GBA memory/sprite/performance costs; formulate a practical single-player geographic adaptation if original DS multiplayer behaviors are infeasible.
- Evaluate Distortion World as a distinctive physical/camera/puzzle location *without* promising native DS 3D gravity. Record fidelity tradeoffs and stop for owner choice if mechanics materially redefine that area.
- Build neutral optional physical routes for Seabreak Path/Flower Paradise, Hall of Origin and other legendary-associated sites as appropriate. **No legendary quest or encounter authored.**
- Exit: measured feasibility + source-backed bounded implementation where supported; clearly labeled deferred mechanics when not.

### C11 — Whole-geography visual and collision correction (P2, W9/G5)
- Traverse every area/subarea, inventory placeholder aesthetics and incoherent landscape transitions, and fix actual clipping/ledge/tree/water/warps issues systematically.
- Verify original recognizable landmark placement and rational new routes; preserve migration/identity and original accepted maps if changed.
- Make a **single consolidated owner-facing geography review**: clickable area index/screenshots showing what was preserved/modified/recycled; let the owner request tweaks. Apply changes in safe batches rather than reopening all past PRs.
- Exit: 87/87 tracked geometry reviewed with nonempty evidence or explicitly unresolved limitation, no "source-only = playable" confusion.

### C12 — Future owner-content handoff (P3, W11; hold implementation)
- Define neutral technical slots for eventual region Gym scripts, trainer tables, area ecology, machine/story events, transport scene, rematches, legendary locations and quest callbacks.
- **Do not pick** story, rivals, NPC character dialogue, trainer teams, Pokémon level bands, encounter species/rates, items or regional badge order now. Produce concise later decision packets only when source geography is ready.
- On owner choices, execute approved gameplay in separate tested PRs and verify ordinary reachability, not DEV warp fixtures.

## Codex infrastructure and gameplay engine work packages

### X01 — Two-region save/travel identity audit (P0, G0–G2)
- Finish existing current PRs (#154 or later) first. Read all merged #123/#132/#134/#136/#137/#138/#140/#141; avoid duplicate tests.
- Verify section215 sentinel, originals 0–214, special253–255, new Sandgem216 and pending Route201217; old saves and flash PC/party/item met origins; heal44 if integrated. Add only missing tests.
- Cover revisits, battle whiteout, fallback healing, save/PC/Bag/badge region records, Save→flash→Continue, malformed records and unconfigured Fly guard. Coordinate direct production-source collision with Claude.
- Exit: ENGINE-QA with source/ROM/flash evidence; unverified DS/iOS behavior not called passed.

### X02 — Full-region ID/met-location planning (P0 critical path, G2)
- Derive actual demand by **named met origins**, not by 87 tracker rows or raw map count. Decide whether shared mapped names can preserve sensible origin displays without erasing previously saved semantics.
- Compare bounded 8-bit append-only codes, a stable grouped codebook and an expanded tagged origin scheme based on prior tested reports; calculate consumer audit/migration/rollback obligations. Do not implement a speculative "13-bit" production change.
- Present a **single owner technical decision** with alternatives, expected affected headers/save structs/PC/trade/battle/summary/TV/egg-hatch paths and exact costs; leave existing values pinned. Use bounded naming while still within safe known codebook and only after live governance permits each allocation.
- Exit: technically explicit chosen owner policy before exhaustion; implementation follows separately under high-risk review.

### X03 — ROM and live resource budget tooling (P0/P1, G2–G5)
- Get actual current main NORMAL/RELEASE OFF-default builds; track linked bytes, real free budget versus 32 MiB, differential from earlier same-toolchain build, release restoration ON footprint; track persistent save block headroom.
- Instrument/test actual heap fragmentation/high-water, field OAM/sprite usage, palette banks and stack across map loads, menus, battles, follower and transitions. Do not mistake unused linker EWRAM for heap capacity.
- Flag map working buffer \`(w+15)*(h+14) <= 10,240\`, field tile/metatile paired budgets and NPC/event limits as tests that fail on *bad cases*.
- Exit: automated or reproducible measurements with meaningful pass/fail thresholds rather than speculative tables; no sudden broad engine refactor.

### X04 — Reliable map registration and build pipeline (P0/P1)
- Verify Sinnoh map group/layout/headers/event script inclusion on CURRENT main. Identify actual build exclusion for new region maps; do not reopen already merged #126 work without a reproduced bug.
- Improve generator/preflight checks for append-only registry, duplicate names, missing maps, bad warp index, reciprocal offsets, illegal tiles, collision pockets, unreachable doors, invalid region/map UI.
- Ensure Claude can preview/compile one map without forcing simultaneous edits of global generated files. Develop test-only fixtures with clearly isolated ROM/save outputs.
- Exit: error injection tests catch at least one meaningful regression in each claimed validator; integration does not silently move old map IDs.

### X05 — Region Fly/PokéNav/Town Map architecture (P1/P2, G6)
- Analyze existing #138 refusal contract and exact UI data dependencies. Map planned region selection, destination visited flags, shared interregional transfer node, healer fallback, return warps and UI assets.
- Build testable, source-isolated framework that **keeps current Sinnoh UI entry refused** until all relevant assets and destinations exist, with negative tests for invalid IDs or wrong region.
- After physical sites and later owner travel details become available, implement a normal region selector and correct Fly destination behavior. No made-up default Fly location or phantom transfer route.
- Exit: only label region UI ready after real mGBA navigation, correct arrival/save/Continue and no cross-region destination misrouting.

### X06 — HeartGold/SoulSilver-style transport substrate (P1/P2, G6)
- Implement non-story engineering contracts for first travel, repeated round trips and last-safe-return anchor; party/Bag/PC/held items/levels persist unchanged.
- Use explicit transport point descriptors so Claude can later choose physical terminals; do not hard-code aircraft/ship names, schedules or nonexistent story flags.
- Add save/flash/whiteout/error recovery and invalid endpoint negatives, both region directions. Initial entry must not be claimed playably available while only DEV warp is used.
- Exit: engine-side route and contract tested; only future owner approved narrative script activates user-facing entrance.

### X07 — Field and environment scaling (P1/P2)
- Inspect follower/collision behavior on snow, marsh, ice, ash, bridges, Surf transitions, ledges and cave stairs, based on actual constructed geographic needs.
- Measure worst-case map-bound sprite/object allocation; fix reproducible bugs (not speculative redesign). Reuse native/graphical harness and exact targeted cases.
- Exit: technical gameplay rules stable across diverse real maps and old Averon scenes.

### X08 — Advanced optional-area feasibility (P2)
- Define practical GBA representation for Underground branching/multi-entrance maps and persistent discoveries, avoiding unapproved save-schema growth and pretending online DS underground support.
- Assess Distortion World camera/floor effects, special movement and ROM/CPU costs; provide owner options if faithful representation is beyond measured engine capability.
- Audit Battle Frontier candidate modes separately: geography can be complete while custom rulesets, streak data and prizes remain unapproved content/architecture. Don't implement five complex facilities by guess.
- Exit: clear proven subset, exact unsupported parts and owner-facing alternatives; no false feature completion.

### X09 — Comprehensive integrated reliability and old-save matrix (P2, G3–G8)
- Select actual regression matrix: brand-new game vs old save, normal vs release, new location vs home region, save before/after warp, PC/party origin, bag/held item, whiteout, trainer victory where approved, bad transfer/recovery.
- Run progressively on integrated main at major stage gates, not after every documentation commit. Repair actual failures with focused PRs.
- Keep accepted pre-Sinnoh Gym/follower/save/EXP mechanics working; name expected failure identities instead of laundering failures away.
- Exit: reproducible G5/G6 technical evidence; human audio and Delta remain separate.

### X10 — Validated improvements and second-region technical debt (P2)
- Triage any actual growing bottleneck in region/header space, map loads, memory peaks, field VRAM, build turnaround or emulator flakiness. Prefer small empirically justified fixes with failing-before/passing-after proof.
- Leave a short technical ledger *only for material risks or owner choices*; do not make new status dashboards or author arbitrary feature rewrites.
- Exit: concrete tested improvements merged; no overlapping Claude-owned map source.

## Parallel execution table (practical)

| Slice | Claude active build | Codex active independent work | Shared collision to serialize |
| --- | --- | --- | --- |
| Current Route201/Sandgem | C01 finish #150/#151 | X01 current PR and disjoint tests | healer/section test files if touched by both |
| Global atlas/early southwest | C02 + C03 + C04 | X02 codebook study + X03 measurements | region_map_sections.json / global layouts inclusion |
| Oreburgh–Eterna | C05 | X04 map pipeline | generator inputs and map-group indexes; merge one registrar per batch |
| Central/east/north | C06–C08 | X05 UI substrate + X07 environment checks | production field/region-map engine if same |
| Islands/Battle Zone/advanced | C09–C10 | X06 transit + X08 feasibility | port/connection description and saved-ID ownership |
| Whole region | C11 geographic polish / acceptance | X09 integration matrix / X10 regressions | source claim during difficult fixes |
| Later content | C12 story-slot handoff, then approved content | future gameplay platform support | owner decisions for plot/levels/encounters/transit activation |

## Future owner decisions — minimize interruptions

**Immediate/increasing-risk technical:** saved met-location codebook capacity/possible migration, assets/rights for outside imports, any truly invasive engine mechanism. Present options with validated evidence. These are not things a geographic designer should solve by silently renumbering.

**Later product choices, not physical-map blockers:** exact transport and first-entry narrative, Sinnoh story and use of former Galactic facilities, regional Gyms/badges, trainer levels, species encounters, rewards/quests, legendary encounters, advanced facility mechanics, final music/graphics/Delta acceptance. Reserve physically plausible slots and continue geography now.

**Owner iteration:** after W3 (first large contiguous geographic corridor), after W5 mainland main structure, and after W9 all geographic coverage, provide one visual cross-region review set (comparison, map/navigation images, known deviations and priority fixes). The owner can request modifications; don't wait for a design signoff on every earlier individual map.

## Handoff quality and stop conditions

End each developer session with **one** concise remote summary: exact branch/PR full head SHA, changed literal files, passed/failed/skipped checks, source/build hashes, mGBA run/evidence, owner assumptions avoided, outstanding true blocker, and next independently executable task. No invented elapsed time or schedule. Keep developing through all available tasks, but **stop only the affected lane** when a guard, actual test, rights issue, or irreversible identity decision blocks it.

The goal is a connected Sinnoh *that exists in the ROM and is testably navigable*, not a large collection of unmerged plans.