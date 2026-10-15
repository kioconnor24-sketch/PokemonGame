# POKÉMON AVERON — AUTHORITATIVE BACKEND-FIRST PRODUCTION ROADMAP
## Implementation contract for Codex and collaborating developers

**Prepared:** 2026-10-15. **Status:** Production plan; NOT a certification that the features below already work. **Owner of geography, route flow, towns and broad creative direction:** the user. **Engine:** the existing Emerald Expansion-derived GBA source in Pokemon Game/engine/. **Output:** real .gba built and eventually checked in Delta iOS. **Worldbuilding policy:** work on mechanics and reusable systems while the user designs the map; do not independently finalize new towns, Gym layouts, route placement or geographic sequence. Preserve the opening already authored; avoid throwing away working source.

This roadmap supersedes *unverified scheduling and numeric design assumptions* in older handoff documents. It does NOT erase established story/gameplay locks. The roadmap is a queue of deliverables with proof requirements, not permission to claim everything is implemented.

## A. Ground truth and project definition

Repository: https://github.com/kioconnor24-sketch/PokemonGame

The current Codex gameplay feature branch is codex/first-gym-verification (PR #1), whose observed head when this plan was written was 0466c38240335c1e152897eae3360bcd5deeec41. Fetch its NEWEST head before editing. All project files live under Pokemon Game/. The main branch and multiple feature branches are NOT interchangeable.

Other contributions awaiting review (do not assume merged):
- PR #2: species/encounter/evolution-source inventories; based on main.
- PR #3: two early optional quests and world-progression audit; based on main.
- PR #4: nine-generation species graphic references and actual Pokémon graphic/follower asset-path checks; based on main.
- PR #5: source configuration and persistent-flag auditing, restored missing native compresSmol build-tool source, host-compiled real C cap checks, GitHub compilation and resource reports; based on Codex branch.
- PR #6: real trainer-party and six-group experience-growth source analysis; based on Codex branch.
- PR #7: adds Linking Cord item evolution for Karrablast→Escavalier and Shelmet→Accelgor; verifies that all 30 parsed trade-evolution paths have nontrade alternatives; based on Codex branch. Item OBTAINABILITY and in-game item-use tests are still required.

Verified at different checkpoints: a clean native ARM build produced a 32 MiB GBA binary after PR #5 restored compresSmol; PR #7 with evolution changes also native-compiled. The clean build linker reported EWRAM 86.37%, IWRAM 86.60%, ROM 79.64% used. This is a *build/linker snapshot*; it is not proof of runtime heap headroom, endgame fit, or Delta playability. Codex's progress log records 24 named early-game native tests plus four save-layout tests passing on a prior feature snapshot, while full first-Gym natural gameplay acceptance remains outstanding. Newer PR #5 GitHub workflow compilation passed, but the additional bundled headless-runner step failed with "No tests found": investigate test discovery and exact runner arguments instead of calling it a C compilation failure.

Existing documented sequence: M0 native setup, M1 Saltmere opening, M2 Alderfield Gym 1, M3 rest of Averon, M4 conspiracy story, M5 Sinnoh, M6 National Dex, M7 postgame/legends/Red, M8 art/audio, M9 QA. The roadmap below reorganizes this into *backend-first tracks plus subsequent user-led world production*; it does not mean M3-M9 are already achieved.

### Immutable gameplay / creative requirements

- Original Averon world and complete second region Sinnoh; **Red is the final canonical trainer battle**, after Sinnoh and the postgame. Optional repeatable Champions' Circuit is not the ending.
- Eight Averon Gyms, with 6 and 7 in the northern mountain/snow zone and Gym 8 in southern volcanic islands; separate remote Averon League; capital Vesper is NOT a Gym.
- Starter assignment from the first meaningful ordinary visit: greenhouse→Snivy, workshop→Fennekin, harbor→Piplup; rival Renn receives type advantage, Mira takes remaining starter. Existing early-game source must be preserved.
- One fair challenging difficulty; permanently Set battle style; Gym/story level caps; 100 absolute maximum; held-item Generation V EXP Share only (NOT team-wide); smarter AI without reading player decisions it could not know.
- Physical/special move split, Fairy type, supported modern moves/abilities/evolutions, Mega Evolution, regional forms and following Pokémon. NO Z-Moves, Dynamax, Gigantamax battle mechanic, Terastallization, Primal Reversion or Ultra Burst without explicit user decision.
- Single-player accessibility of all intended Gen I–IX National Dex species and required evolution items/forms by endgame; no compulsory trade or unsupported Delta multiplayer dependency.
- Field traversal licenses that do NOT consume Pokémon move slots; Cut/Surf/Strength/Rock Smash/Waterfall/Dive/etc. unlocked appropriately through game progress.
- Traditional Pokémon adventure feel, lively everyday NPCs and sidequests, sparse and selective conspiracy foreshadowing, deep but restrained rival arc. Keep established Threshold / Team Vantage layers, coup, forced Renn defeat with no penalty, post-raid gauntlet + ally heal, dimensions, and Sinnoh continuity.
- The user is actively shaping the final Averon map. Existing atlas and gym-type/location details outside the locked essentials are **provisional**. Do not quietly substitute a self-designed full region.

### Numeric level curve: explicitly NOT LOCKED

Old cap numbers for Averon Gyms (15,23,31,39,47,55,62,69), its first League (76), later Sinnoh caps and Red 100 are present in legacy documents/source but are NOT approved as final balance. The user specifically objected to 76 for the first Averon League. Design a NEW full two-region + postgame experience curve from actual encounters/EXP economics, studying HeartGold/SoulSilver as structural inspiration alongside Platinum and Black 2/White 2. Their Gym/Champion ace levels are NOT player hard caps. Do not change actual level-cap numbers merely to substitute another guess. Keep the cap *machinery* functional and the final maximum at 100 while postponing numeric tuning.

## B. Task status vocabulary and discipline

Every deliverable must be tagged with ONE of:
- DEFINED: requirement exists only in design documents.
- SOURCE: native code or assets exist, but functionality is not compiled.
- BUILD: integrated native ARM game build passes, checksum/size recorded.
- NATIVE-TESTED: an appropriate bundled headless test executes and passes (record exact test names and counts).
- PLAYTESTED: the actual user-facing action has been exercised in a running emulator and persistence demonstrated where appropriate.
- DELTA-VERIFIED: separately exercised on an iPhone running Delta; never infer this from mGBA.
- BLOCKED: include the precise dependency and what can still be done independently.

A source audit is not game implementation. A successful build is not gameplay validation. A defined Pokémon is not necessarily obtainable. A conventional graphics file exists does not prove the corresponding sprite renders in game. A remembered local commit is not pushed unless the remote SHA is checked.

A deliverable is DONE only at its appropriate acceptance tier, with tests and reproducible commit recorded. Deliver substantial functionality before polishing low-risk reports.

## C. Immediate priorities: BACKEND BASELINE (B0)

These are first because independent developers are currently writing to different branches.

**B0.1 Establish one truthful integration baseline**
- Fetch main, newest Codex PR #1, and PRs #2–#7; read AGENTS.md, CODEX_WORK_ORDER.md, development/PROGRESS.md and TASKS.md.
- Capture current HEADs, major code paths, overlapping files and parent relationships. Make a precise merge/dependency matrix. PRs #2–#4 target older main; #5–#7 target Codex's Gym branch. No blind merges or force pushes.
- Assign file ownership by feature; commit to separate short-lived branches and open/refresh PRs. Merge into a verified integration branch in a tested order, then stable main after review. Avoid leaving useful code isolated indefinitely.
- Detect generated-source files that Codex's map generator will rewrite. Keep source generators and generated outputs consistent; ensure re-running build-averon-coast.py cannot silently erase someone else's native edits.
**Gate:** fresh clone + documented toolchain can build the same integrated source; tests have traceable SHAs; opening remains playable.

**B0.2 Fix missing graphics build tool and CI test selection**
- Review restored compresSmol files in PR #5 against pinned upstream SHA 73b3fbeb574327cd9420c89e56bef5aa3c08fead; retain attribution/provenance.
- Review PR #5 GitHub headless-test failure "No tests found". Codex's recorded local command is make check -j12 TESTS="Averon"; inspect test-runner matching, case, shell argument selection, binary execution permissions and test build flags. Do not turn a real failure green by skipping the tests.
- Keep separate CI stages for (1) source/lint, (2) real ARM build, (3) native tests, (4) eventual emulator smoke. Cache safe build artifacts where possible; do not upload a publicly distributable copyrighted ROM.
**Gate:** reliable green build + named tests on the integrated HEAD, not only a historical branch.

**B0.3 Define a tiny reusable dev testing surface**
- Keep or add a dev-only test map and menu/warp with isolated triggers for mechanics, no invented permanent region geography.
- Provide deterministic fixtures: species/forms/held items, fixed trainer parties, flags, scripted battle win/loss, field obstacles, save/reload, ferry/region transition stand-ins.
- Build flags must keep debug fixtures unavailable in release builds. Confirm debug access cannot accidentally award one-time story progress.
**Gate:** representative mechanics can be reproduced in seconds without replaying the full story.

## D. Backend workstream B1: Pokémon, data and battle functionality

**B1.1 Freeze an engine-supported species/form manifest**
Input: the pinned expansion's true species constants, enabled generation families, form tables, items, abilities, learnsets, graphics linkage, and a separately vetted complete Generation IX National Dex reference. List each species and form with engine ID, method/form condition, base stats/types, moves, abilities, required assets and obtainability status. Distinguish unsupported recent additions or cosmetic variants; do not fabricate them. Treat actual compiled enabled data separately from eventual location in Averon/Sinnoh. Reuse PRs #2 and #4; add tests for duplicate IDs, missing referenced data, and invalid forms.
Gate: every *supported and in-scope* species has a truthful data/asset record; missing implementations are itemized, not marked done.

**B1.2 Stabilize battle mechanics using existing engine**
Verify permanent Set for all trainer, wild, scripted and multi battles. Verify physical/special split, Fairy matchup, selected updated moves/abilities/status changes, trainer held items, legal Mega use (only appropriate Stones, battle reset to ordinary form), ability/form transitions and no forbidden gimmick access from enemy, menu, bag, AI or scripted battles. Reuse existing tests; add targeted ones for actual gaps only. Verify trainer AI is strategically challenging but cannot inspect future choices. Avoid reimplementing all Emerald Expansion move logic.
Gate: controlled native and emulator proofs for a representative cross-generation matrix, with no incompatible gimmick buttons.

**B1.3 Gen V held Exp Share and global cap enforcement**
Verify EXP only to participants and the Pokémon holding the item. Check 1–6 party members, fainted/nonparticipants, EXP buffs, items, gifts, catches, daycare and max level 100. Hard cap applies to Rare Candies, evolution timing, bonuses and any alternative level-gain path. Check save/reload at cap and no overflow or corrupt party. Keep the CAP MECHANISM independent of final level numbers. Reuse PR #5's real C cap-function tests and Codex tests.
Gate: repeatable tests for main EXP/cap paths; no unavoidable grind designed into final placement later.

**B1.4 Single-player evolution and form completeness**
Integrate PR #7's Linking Cord changes after its successful native build evidence is reviewed. Check every trade evolution destination has a nontrade source method AND that its item/method will be obtainable somewhere in the eventual game. Audit special evolution cases (region, weather, nature, move known, held item, friendship, party composition, time-of-day, spinning, damage/hits, etc.) and form-changing items/events. Keep basic evolution item sources for general economy; don't place late rare items in starter shops without user-approved balance.
Gate: isolated real item-use and edge-case evolution tests; complete source coverage table, obtainability to be finalized after world content.

**B1.5 Following Pokémon and sprite safety**
Verify lead party Pokémon following via existing engine config and working code; follower sprite/animations across generations; missing assets fallback (no crash), shinies and forms, water/flying/large sprites, party switching, trainer interactions, bikes, Surf, stairs, warps, narrow paths, doors, cutscenes and save/reload. Audit full graphics includes and actual loaded sprites (PR #4 is only first-pass source evidence). Reduce known event-object-slot and palette conflict risks. Fix crashes/sprite corruption rather than designing a new follower engine.
Gate: native/emulator matrix with at least a set of small/large/alternate-form/fainted follower test cases and stable transitions. Complete every rare form art only if remaining gaps are proven.

**B1.6 Gym-independent encounter/item data primitives**
Make wild encounters support habitat tables, fishing, surfing, caves, time-of-day only if safely enabled; provide data schema and validation, not actual final species placement without map. Wild ability, held-item, encounter species checks and nontrade play compatibility should be reusable.
Gate: a test route can exercise encounter modes; no final biome encounter tables claimed yet.

## E. Backend workstream B2: overworld, progress and save

**B2.1 Move-slot-free field licenses — a major missing feature**
Audit existing badge-unlock field_move.c, party menu, relevant field effects, item use and overworld collision. Implement a field-toolkit/license abstraction that permits Cut, Rock Smash, Strength, Surf, Waterfall, Dive and Fly/other required traversal with progression flags and relevant contextual prompts **without mandatory learned HMs**. Battle moves remain teachable normally. Choose an interface that fits GBA menus and sound. Avoid duplicating field effect animation code; reuse native callbacks. Ensure Surf and followers interact safely. Distinguish permission (license obtained) from whether the tile action is currently legal.
Gate: all planned traversal actions work on isolated test obstacles with no compatible HM in the party; unavailable license cannot bypass gate; party empty/fainted, save/reload, bikes and follower edge cases safe. Final license locations/order remain world-design dependent.

**B2.2 Persistent event-state registry and safe scripting**
Centralize allocations of flags/variables, story phase, Gym flags, quest IDs and dedicated states. Apply PR #5's collision checker. Never reuse previously claimed early quest flags (0x2A–0x2F in PR #3) without integration review. Create helpers and invariants for one-time rewards, full bag/party retry, absent key items, repeated dialogue, cancel, save/reload and whiteout. Event reentry must be idempotent; avoid softlocks and repeated reward exploits.
Gate: reusable tested one-time gift, item reward, multi-phase state and NPC visibility examples with explicit ID allocations.

**B2.3 Save/persistence and backwards compatibility**
Test fresh saves and old developer saves on the pinned engine with follower, party, forms, dex, flags, items, Gym states and options. Document save-structure layout and expansion strategy; reserve region-specific progress without changing save semantics carelessly. Build versioning/migration only where actual schema changes require it. Test menu saves, real flash cycles, power/reset, whiteout, PC, bank and full party, from both regions when content exists. Distinguish linker free RAM from runtime allocations.
Gate: native save-layout tests and emulator reset/restore with canonical fixtures; no data loss or infinite cutscene on reload.

**B2.4 Multi-region engine architecture**
Plan two independent regional maps and identifiers, Gym badges and badge-dependent field licenses, Pokédex/filter states, travel unlocks, safe ferry/rail/warp return points, home/heal/whiteout location, region-dependent forms/evolutions, fly map selection, correct current-region UI and postgame gating. Preserve party, items, trainer records, PC and global progress when traveling. Start with TWO TEST MAPS acting as Averon and Sinnoh; do not populate the real Sinnoh region without geography/source permission review. Use one safe transition with save/reset/follower tests.
Gate: reversible simulated region transition with distinct badges/flags, no save corruption or trapping; final world travel geometry later.

**B2.5 Optional Nuzlocke feature: DEFER**
It appears in an existing design document as an optional new-game toggle, but is not required for stabilizing core story. Keep in the backlog until player confirms this mode remains desired, and core saves/caps/forced scripted losses already work. If implemented: per-zone encounter log, faint handling, legal exceptions and no-penalty forced Renn fight, persistence and fail-safe toggling.
Gate: independent compatibility and user approval; **must not block map development**.

## F. Backend workstream B3: reusable storytelling, scripted battles and unique encounters

**B3.1 Small, reusable quest-state engine**
Do not create a large separate quest operating system unless the native script/flag engine cannot suffice. Use compact templates/helpers for: offered→accepted→objective→ready→rewarded; branch/cancel/retry; journal entry only if UI fits; item and Pokémon gifts; NPC text/appearance changes; multi-visit location objectives; optional unrelated slice-of-life quests. Leverage PR #3 rather than rewriting. Provide two dev-map example quests. Do not author the rest of Averon's quests without their locations.
Gate: save during every quest stage, full bag/party, repeated interaction, whiteout, receiving reward exactly once.

**B3.2 General battle-event toolkit**
Reusable scripted trainer challenge functions for clean win/loss branches, intentional unwinnable rival fight (zero loss penalties and restore at Pokémon Center), battle immediately after Gym without heal, short sequence of ~10 single-Pokémon operatives preserving party HP, ally-provided heal, stronger Gym leader rematches, boss phase transition and scripted return location. Avoid implementing the whole political finale until locations/dialogue are finalized. Prefer proven cutscene-based phase changes to risky midbattle battle-engine interruption.
Gate: dev test stages demonstrate lose, whiteout, heal, resume, save and flag safety; no Nuzlocke penalty for the intentional loss if mode retained.

**B3.3 Repeatable battles and tournament infrastructure**
Templated boss/NPC rematches, reusable tournament bracket/match setup, entry restrictions, reward-once vs repeatable rewards, safe defeat/retry, partner dialogue hooks and persistence. The Champions' Circuit is optional and repeatable, not required for Red. Final NPC lineups and storyline scene timing follow later.
Gate: one noncanonical test bracket of several matches can complete, fail and restart without corruption or duping rewards.

**B3.4 Legendary/mythical encounter service**
Implement reusable persistent capture/defeat/flee/blackout/retry states, single-owned legendary encounters, optional conditional shrine/cave/weather/seal triggers, multi-location backtracking and late unlocks. Ensure no unrepeatable encounters become permanently lost through a failed battle unless explicitly designed. Develop a DEV MAP fixture with one normal static encounter and one multi-stage secret quest; do not make an all-legendaries-in-one-room player area. Do not generate final quests or placements until world geography is approved. If villain owns a legendary temporarily, resolve that with separate story flags and final player obtainability.
Gate: catch, defeat, run, full party, save before/after and repeat-interaction tests; no duplicate mythical gift.

**B3.5 Narrative technical scaffolding, not final writing**
Persist story chapters, official Gym flags, allies, conspiracy evidence, command overthrows, coup state and post-coup world-state changes. Test turning NPC/spawn/warp/shops/transport state on and off without softlocks. Do not write full NPC dialogue in advance or force foreshadowing onto unrelated scenes. The established Threshold logic and toned-down rival arc must remain intact when final scenes are authored.
Gate: fake story-state switches drive test NPC behavior; scene timing remains under creative review.

## G. Backend workstream B4: National Dex, economy, performance, compatibility

**B4.1 National Dex attainability ledger**
Maintain data fields: species/form, pre-evo/evo method, earliest allowed milestone, one guaranteed obtainable source, alternate method if applicable, encounter requirement, region, key item, repeatability and special legendary quest. Mark statuses: engine-supported, asset-supported, source-planned, world-placed, game-tested. No complete NatDex claim before all final maps/rewards exist. The user wants eventual access to every in-scope species; do not force unrelated wild species into the wrong habitats to satisfy a checkbox.
Gate now: complete normalized ledger; gate after world: zero unobtainable target species.

**B4.2 EXP and difficulty modeling (without deciding levels prematurely)**
Use PR #6's verified trainer-party and real experience-growth data. Extract actual wild and trainer encounter experience formulas, trainer density, optional fight fractions (~65–80%), party sizes 3/4/6, species growth curves, holding EXP Share vs not, and capture replacement timelines. Compare official games' progression, notably Johto League ~50 as opponent ace, Kanto Blue ~60, Red ~88, Platinum Cynthia ~62 and B2W2 Normal Iris ~59; do not turn these into automatic hard caps. Simulate full two-region progression in increments as maps are planned and filled; the user signs off major boss and player cap bands. The present source only defines about 10 Averon trainer entries, not the endgame.
Gate now: simulator with actual engine formula and parameterized route data; gate later: all-region no-forced-grind acceptance with distinct team sizes.

**B4.3 Graphics/asset and licensing ledger**
Use PR #4 source-and-folder reports and verify linkage of required battle front/back/icon/follower/form sprites. Assign unresolved art to a real backlog. Support user-provided, authorized photos for friend-based custom trainer pixel art later; generate proper palette-constrained sprite sheets and test in-engine. Catalog community rights and attribution. No final Cynthia soundtrack copying without distribution permission; an original alternative is acceptable only after creative review.
Gate now: reliable coverage report and missing-asset classes; final sprite creation and music decisions deferred until character/location assets are approved.

**B4.4 ROM/RAM budgets and performance**
Use clean linker reports as starting snapshots (ROM 79.64%, EWRAM 86.37%, IWRAM 86.60%). These figures are not equivalent to available heap at runtime or proof full Sinnoh fits. Profile and set guard thresholds based on measured peak RAM stack/heap and graphics/OAM/palette behavior. Prefer storing immutable tables/graphics in ROM, local streaming and reuse/compression; reduce duplicated unused vanilla content after confirming it is truly unused. Do not move sensitive IWRAM routines indiscriminately. If 32 MiB space is exhausted, verify proven hardware/emulator/Delta compatibility of any larger-ROM strategy before committing to it. Do not cut the second region based on current RAM percentages.
Gate: build/linker measurement after each major new subsystem; later representative emulator gameplay profiling. Never promise arbitrary additional capacity.

**B4.5 Delta/release support**
Build a reproducible .gba for owner-authorized local use; do NOT commit generated copyrighted ROMs to public GitHub. Provide version/checksum, clean-build instructions and eventually a legally appropriate patch, credits, and save-compatibility notes. Separate iPhone Delta smoke acceptance from desktop emulator/headless tests, especially save reset, audio, battle, text, follower, region ferry and large content.
Gate: explicit user-executed Delta tests; release only with full-game completion and asset rights addressed.

## H. What is explicitly PAUSED while the user designs the world

**PAUSE finalizing or bulk generating these items:**
1. Unapproved Averon map geography, exact route graph, town footprints, decorations, final tilesets and interiors beyond working opening.
2. Building final remaining Gyms #2–#8 and their puzzles/cutscenes; retain the approved north/northern Gym 6+7, southern volcanic Gym 8 and separate League constraints. Existing Breakwater is a provisional geographic idea until user approves its place and shape.
3. Final locations of legendaries, hidden dungeons, unique islands, legendary key chains and quest triggers.
4. Biome-specific final encounter species distribution, encounter rate, fishing/surf/dive tables and route items; develop schema and sample fixtures only.
5. Final trainer teams, levels, Gym ace levels, exact cap numbers and final experience pacing; build analysis systems now.
6. Final town-by-town dialogue, local cast placement, scripted plot scene staging and custom friend sprites requiring reference photos.
7. Full Sinnoh imported map art/content or wholesale fan-game map copying without user direction, technical inspection and rights review. Two-region data framework CAN proceed.
8. Final Champions' Circuit rosters, legendary placement, Red entrance scene and final soundtrack arrangement.
9. Massive optional cosmetic animation work, optional Nuzlocke mode and social/link features unless real blockers arise.
10. Endgame asset polishing and entire-game manual playtesting before most content exists.

**NOT PAUSED:** any technical item whose test can use a developer map, source-built native fixtures, or existing opening, including field licenses, flag registry, legendary capture infrastructure, scripted losses, follower stability, test harnesses, save stability, region boundary test, and the National Dex source manifest.

If the user submits partial map plans, incorporate the approved portion in the next *content* milestone without fabricating the rest. The story/plot remains intermittent in a lively Pokémon world and should not dominate ordinary routes.

## I. Complete game production path AFTER backend readiness and/or user map delivery

**W0 — Map design intake and freeze**
- User specifies region-scale coastline and landforms, relative town placements, Gym city association, path loops, shortcuts, transport, landmarks, progression gates, regional biomes and major secrets. Accept sketches/photos/diagrams with approximate topology; there is no need for exact native map tile measurements yet.
- Convert user material into an authoritative, versioned WORLD_MAP_SPEC: stable location IDs; node adjacency; planned warp links; travel unlock flags; separate biome and settlement art notes; staged NPC/story/event requirements. Flag uncertainty as OPEN rather than guessing.
- Contradictions in old REGION_ATLAS.md or route CSV are reconciled explicitly, with the newest approved user map taking precedence for provisional geography. Maintain nonnegotiable north/volcanic/League/Sinnoh rules.
**Gate:** user signs off initial topological route network, not every house interior.

**W1 — Integrate backend into first playable district**
- Merge reviewed PRs, preserve Saltmere/Orchard/Alderfield content as appropriate to the accepted map; finish any remaining Gym1 game flow and save/whiteout acceptance without delaying every other independent task.
- Create developer transportation to test later systems without story spoilers; keep dev map excluded from release.
**Gate:** playable opening→Gym1→next-route exit, native build and save/reset; user walkthrough feedback recorded.

**W2 — Build Averon by geography-first production batches**
- For each batch, implement a contiguous district: outdoor route(s), main settlement, interiors, biome identity, trainers/wild battles, story-neutral sidequests, field-toolkit gates, items, shortcuts, ambient dialogues, mapping collision/height/audio and local optional secrets.
- Embed the next approved Gym when the route network reaches it; don't skip gameplay to create eight generic gyms in one pass.
- Add story only where approved (ordinary Team Vantage crimes at first, gradual clues, later real conspiracy/coup). Preserve naturalistic character pacing.
- Prefer Porymap/Poryscript-compatible native map data, existing decompiled map/tileset patterns and small reusable helpers. All warps need reciprocal or intentionally one-way handling, tested return and safe spawn.
**Gate per district:** native build, static connectivity/encounter correctness, scripted reward reentry, at least one user-facing smoke traversal and state-persistence test. Track playable towns/routes, not just commits.

**W3 — Full Averon story and first championship**
- Integrate Renn/Calder/other allies, rigged Gym history, corrupt leaders, multi-phase villain finale and dimensional interruption in correct sparse pacing; 10-operatives relay + ally heal; no-penalty forced loss; short mixed public reactions after coup.
- Only after actual levels/encounters exist, rebalance badge gates and first League using full-game EXP simulation. Do not retain League 76 simply because it is in older data.
**Gate:** full fresh-save Averon→League run, story forks, recovery/persistence and no unfair grind.

**W4 — Full Sinnoh as real second region**
- With source rights and compatibility cleared, produce real recognizable Sinnoh route/city/dungeon graph including all eight Gyms, Mt. Coronet and League/Cynthia; normal overworld exploration must remain substantial, not a series of teleport rooms.
- Wire cross-region badges, transport and global party/items; add revised continuation-level economy, Sinnoh-specific quests and mythological discoveries; no forced reset to level five.
**Gate:** complete in-order and backtracking playthrough, bidirectional region travel, save cycles, all eight badges and League.

**W5 — Late postgame, completion and Red**
- Fill missing NatDex obtainability, unique multi-location mythical/legendary chains, secrets, returning character quests, Champion Circuit as OPTIONAL repeatable content and Red as last canonical trainer encounter.
- Finish trainer team balance, rare item availability, high-level progression to approximately 100, legal assets and original/credited music.
**Gate:** no permanent softlocks, full single-player catch/evolve path for target species, Red finish from realistic six-mon save.

**W6 — polish, performance, patch, full QA**
- Full Game Boy Advance ROM and RAM profiling (plus battle/overworld worst cases), text overlap, portrait and follower animation, map collision, all flags, credit/asset audit, multi-route replay.
- Full 3/4/6-mon and 65–80% optional trainers test scenarios, no excessive leveling jumps.
- Full-game desktop emulator playthrough and separate iOS Delta acceptance; documentation and appropriate patch release.
**Gate:** reproduce the release ROM/patch with checksum and clear blockers resolved.

## J. Assignment matrix (coordinate, do not independently duplicate)

- **User / creative director:** final world-map topology, town identities, which roads/biomes touch, landmarks, location ordering, exploration loops, broad tone and later visual sign-off. User does NOT need to write code or define every individual house.
- **Codex on primary computer / integration owner:** one working feature integration branch and early-Gym regression; B0 clean build/headless tests; B2 field licenses, persistent events, save and two-region runtime; B3 quest and scripted battle templates. Once user map is approved, produce actual route/town native scripts from the accepted map.
- **ChatGPT / battle-data owner:** B1 source/battle mechanics fixes and follower compatibility; PR #2/#4/#6/#7 integration review; species/evolution/form audits, Gen V EXP/caps regressions, numerical EXP research, targeted compatibility repairs. Coordinate same-file edits in caps and species tables before updating them.
- **Friend's Codex / isolated supporting track:** B4 graphic/follower files and species asset linkage, encounter data schema, licensing ledger and tools, independent runner/test fixtures; review PR #4. Use independent branches and request integration into correct baseline.
- **Shared principle:** tasks are assigned by FILE/SYSTEM ownership. If a developer finishes a subsystem, hand back proof and pick another nonoverlapping workstream. There is no implicit direct communication among isolated AI instances; the GitHub PR, TASKS.md and status file are the coordination mechanism.

Suggested owner rule: only ONE person edits shared native event IDs, caps, main Gym scripts or generation species table at a time; others open reviewable PRs or supply proposed patches. Before commits, fetch active Codex branch and compare file hashes. NO automatic merging of review PRs and no force pushes.

## K. Development operating procedure and acceptance

Each session:
1. Fetch current branches/PRs. Read only relevant status/diffs and the current next-queue; don't restart entire background research.
2. Pick ONE bounded coding deliverable (several related source files, not a vague engine rewrite). Identify owner, dependency, acceptance test and expected touched files.
3. Check existing native Emerald Expansion implementations and test coverage. Use existing code rather than inventing symbols, code or data. Make the change in a feature branch; preserve clean release baseline.
4. Compile incrementally. Run named targeted tests and impacted smoke path. For source-only work report SOURCE rather than BUILT. If a test fails, debug or log blocker and switch to independent work; don't skip tests to manufacture success.
5. Record paths, command outputs, counts and actual SHA. Commit/push and verify remote head; keep full copyrighted ROMs out of public git.
6. Review for resource usage, save compatibility, merge conflict and legal sprites/music as relevant.
7. Update exactly one concise status ledger with the next three ready tasks. Don't author multiple redundant 30-item progress spreadsheets.
8. Start the next highest-priority UNBLOCKED backend task; do not wait for the whole Averon map or generate geographic fiction to stay busy.

### Definition of backend readiness for user-map implementation

At minimum:
- Clean reproducible ROM build + native test suite on integrated HEAD, not just separate PRs.
- Set mode, approved gimmick gating, held-item EXP Share, level-cap code and evolution mechanics reliably exercised.
- Starter and follower transitions work at representative test points.
- Field-license actions work without learned HMs in dev fixtures.
- Quest/one-time gift/legendary/static encounter/forced loss/gauntlet templates work and save safely.
- Two-region boundary fixture preserves persistent state.
- Complete source-level supported-species/form/asset ledger and known missing entries.
- Memory reports and repository integration status readily visible.
- Story and geography hooks configurable from future map data.

**Backend-ready does NOT mean:** complete National Dex obtainable, every species drawn perfectly, the final level curve approved, all quests authored, all 16 Gym teams finalized or the entire Sinnoh region ready.

### Nonblocking priority queue for next coding sessions

P0-1 Review current PRs #1–#7 and create one clean integration order; fetch latest Codex head.
P0-2 Fix CI "No tests found" headless test-selection and produce a named, passing native suite on the integrated branch.
P0-3 Integrate/restored compresSmol source and PR #7 solo trade evolutions carefully; preserve a passing clean build.
P1-1 Implement field-license traversal prototype for Cut/Rock Smash and Surf on dev maps, test no required move slot.
P1-2 Build a small persistent quest-state/reward-retry and one-time legendary encounter framework, with save tests.
P1-3 Implement robust forced-loss / no-penalty recovery and staged gauntlet fixtures in dev area.
P1-4 Create reversible two-region test-map crossing with independent badge/region progress and shared party/items.
P1-5 Fill in remaining source-level Gen I–IX species/form/follower gaps that evidence shows are real blockers.
P1-6 Exercise all evolution item methods in native tests; record which items still need user-approved locations.
P1-7 Expand real battle and follower regression coverage; test dev surface in emulator.
P2-1 Build an EXP model and obtainability ledger ready to accept future route/Gym design; NO guessed numeric cap changes.
P2-2 Establish runtime memory profiling and meaningful resource regression thresholds.
P2-3 Review optional features and asset licenses only after the essentials above.

If parallel contributor is already doing the next item, take the next nonoverlapping one. The user may supply a partial map at any time; include user-approved geography in W0/W1 without interrupting independent backend work.

## L. Instructions that Codex should interpret literally

- Do not stop after producing an audit or planning page. Implement, test and push real usable code where feasible.
- Do not equate "everything I listed" with finishing the entire two-region game in one coding session. Implement meaningful increments with verifiable evidence, and carry forward precise outstanding tasks.
- Do not overwrite user's map decisions or independently invent the rest of the Gym route.
- Do not prematurely lock level 76 at first League or substitute another unsupported number.
- Do not delete Sinnoh based on the ROM/RAM snapshot. Treat storage/heap limits as measured engineering risks and optimize responsibly.
- Do not throw out working starter/first-Gym source to create a fresh game.
- Do not consume huge allowances with repeated manual emulator navigation, but do not skip native/emulator acceptance when it is genuinely required.
- The best proof of progress is working reusable backend systems NOW and playable districts AFTER the user provides the map, not hundreds of lines of documentation.
