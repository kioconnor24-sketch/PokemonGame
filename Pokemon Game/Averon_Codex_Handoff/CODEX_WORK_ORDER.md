# CODEX WORK ORDER — Pokémon Averon

Read `AGENTS.md` and `START_HERE.md` first. Take this as a multi-month-scale engineering project, **not** a request to print imaginary `.gba` bytes. Design is authored; implementation and tests are not done. All milestone records must contain source commit, commands and outputs, screenshot/log proof, regressions and open blockers.

## M0 — Real build chain (do this first)
1. Clone `https://github.com/rh-hideout/pokeemerald-expansion` using Git, and record the exact 40-character SHA in `development/ENVIRONMENT.md`. Base build should be repeatable. Use official dependencies documented for the chosen OS (GCC/arm-none-eabi, binutils, required utilities) and run the appropriate `make` target; do not substitute an `.nds` builder or browser-based app.
2. Confirm the actual base ROM build outputs a GBA file; record size, SHA-256 and compiler/make output. Verify the build does not require files or images we aren't legally permitted to possess. The finished playable custom build requires assets consistent with user ownership and redistribution rights.
3. Boot in mGBA or equivalent accurate GBA emulator; verify it reaches title, new game, overworld, first trainer battle, menu, save and reset. Save screenshot/log evidence. Check with Delta on iOS separately when user can test.
4. Document current feature flags and data coverage by reading files from the pinned repository. Copy observed symbols and example script patterns into `development/ENGINE_FINDINGS.md`; never rely on vague memory of upstream symbols.
5. Run design linter: `python3 scripts/validate_design.py`. Fix fatal issues before code changes.
**Gate:** until M0 passes, no claims of a successful game build, and no bulk content insertion.

## M1 — Saltmere vertical slice
1. Convert Saltmere and Windrow plus adjacent route R01 into actual Porymap-compatible native map data: tilesets, backgrounds, collision, priority/height, warps, NPCs, grass and sound. Review screenshots on real emulator, not just PNG mockups.
2. Script the **three indirect starter influences**: greenhouse→Snivy, workshop→Fennekin, harbor→Piplup, based only on the first meaningful visit. Later starter award shows one confirmation and provides the Pokémon; childhood rival Renn takes the type-advantage starter, Mira the third. Test any visit order, declining confirmation, closed bag/party, reset/reload.
3. Short upbeat dialogue and two local non-plot activities. Add encounter species appropriate to beginner levels (see habitat CSV). Battle with Renn.
4. Test saving mid-errand and cross-map reentry. Confirm normal overworld Pokémon follower appears or hides safely where supported.
**Gate:** build and execute this slice in emulator, with video/screenshots and tested persistence.

## M2 — First Gym + battle-system vertical slice
1. Build Alderfield, route R02, irrigation puzzle and Gym 1. Implement one actual badge; cap 15 before win and 23 after according to verified cap behavior.
2. Single challenging Set mode: confirm there is no free switch prompt before opposing team enters, including Gym, wild and boss encounters. Check AI choices on representative trainer teams; no future-button peeking.
3. Confirm traditional **held-item** EXP Share; another party member gets EXP only if actually holding item. Party-wide sharing must be absent. Test with a party of six, with and without held item, and at cap.
4. Test Mega Evolution on a dev-only legal battle, and following Pokémon with at least a starter and non-starter. Disable Z-Moves, Dynamax/Gigantamax, Tera mechanics explicitly.
5. Verify script flags, items, move category and physical/special split. Export a `.gba` test build for user to validate in Delta.
**Gate:** fully executable M2 proof. Do not begin mass map construction if M1/M2 boots break.

## M3 — Complete Averon map/gameplay production
Implement main-journey and side-route graph. Distinct settlement interiors and visuals, natural biome transitions, item opportunities, moves/field abilities. Eight Gyms at approved locations in exact order. Vesper remains Gym-free and works as transportation hub. All route shortcuts and ferry links tested with story flags. Add side activities from `design/REGION_ATLAS.md`. Establish consistent tileset/collision quality and capture the *player journey* as map screenshots and timed walkthroughs.

## M4 — Story implementation
Adapt `design/STORY_BIBLE.md` and `design/DIALOGUE_GUIDE.md` carefully. No gigantic scripted dialogues. Build sequential and independent plot flags from `design/QUEST_AND_EVENT_MATRIX.md`. Required: Dorian self-interested manipulation, Nadia unfair two-mon ambush, Renn gym rigging and later forced loss, pre-finale discovery of rigging, infiltrated figures and coup, exactly two mandatory post-coup reaction windows, Threshold original experiment with filtration failure/test subject/Zygarde, villain secret lethal feedback weapon, ten-operative relay, ally healing, two upgraded Gym Leader rematches, four-mon Vale phase or true tested midbattle break, dimensional interlude, final battle and safe return. Player finds decisive clues, Calder and other allies collaborate. Every boss battle tested on win/whiteout/reload.

## M5 — Full Sinnoh
Find an **actually compatible and reusable** Sinnoh map base or reconstruct maps natively; do not assume any third-party repository is complete. Plan import in isolation before merging entire region. Add map selector, passages, Gyms (all eight), second League, Cynthia, exploration, modern NPC dialogue, major Sinnoh mythology and readable event flags. Level caps 79→95 as data targets. Maintain Pokémon party/items/progression across transition.

## M6 — Every Pokémon through Gen IX and battle mechanics
Generate a species/variant manifest *from the pinned revision* and compare with an independently vetted National Pokédex/form list; track IDs, type, ability, learnset, evolution, obtainable method, front/back sprite, icon, follower sprite and animation. Check all new/trade-only evolutions against solo Delta. The goal is comprehensive supported Gen IX data; missing form implementations are blockers rather than treated as implicitly done. Create an automated audit table showing 0 unavailable species for final completion. Mega transformation tests for relevant forms and status effects. No gimmicks excluded by user.

## M7 — Legends, extras and ultimate ending
Build quest families per `data/legendary_quests.csv`, with catch-once or release/capture resolution, postgame travel gates and unique geography. Make optional Champions' Circuit repeatable, several battle gauntlets, side character return scenes, Sinnoh and Averon secrets. Red appears only after both region stories and attainable postgame milestones, and is the final canonical trainer challenge. Keep him beatable without a level >100.

## M8 — Art, music, writing and credits
Review every biome and city in emulator. Finalize regular trainer sprite sheets, protagonist and cast, battle sprites/party followers/Overworld sprite, credits and attribution. Original friends' character likenesses are not added without user-supplied reference photos. Cynthia theme requires permission/licensable arrangement or a clearly original substitute; don't copy the original recording or melody by default. Read all dialogue aloud and edit for authenticity and pace. Implement text wrap/overflow tests.

## M9 — Whole-game verification and delivery
Complete new-game-to-Red playthrough on typical six-Pokémon team; also smoke test small/large parties, skipped optional trainers and obsessive all-trainer play. Automate map reachability with story gating, every Pokémon obtainable route, item/flag persistence, evolution, Nuzlocke edge cases, forced loss, any gym ambush whiteout and entire final boss script. mGBA: cold start, save+reset, new game, party box, audio, no crashes, tile/warp tests. Delta: a separate human iPhone run importing a legitimately built `.gba`, reaching game title and start, saving, loading, battles, later-region fast travel. Note emulator/version and any differences. Produce patch distribution artifact and READMEs; separate full ROM only in authorized owner environment with appropriate rights.

## Priority and technical risk order
Highest immediate risk: build toolchain, native map content, save/event compatibility, level-cap and follower script interaction. Later high risks: 2nd region merge, several generations' form graphics and special evolutions, complicated chained battle state, full species availability, GBA ROM size/memory limit, asset rights. Fix as prototypes rather than 'plan them away'.

## Reporting template for every coding session
- **What actually ran:** commands with exit codes, SHA-256 of built artifacts, name/version of emulator and screenshot location.
- **Implemented changes:** changed source paths, flags, tested interactions.
- **Still unverified/blocked:** list with next physical test.
- **Regression status:** save, battles, events, map warps, D-pad/follower behavior, level cap/EXP tests.
- **Next task:** one focused milestone, not broad claims of completion.
