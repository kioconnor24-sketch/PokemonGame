# Pokémon Averon — Full Sinnoh production roadmap

**Status:** master production *plan*, 2026-10-19. **No future build, integration or gameplay acceptance is claimed by this document.** Owner product direction: [Issue #15 comment 6261800483](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6261800483). Owner streamlined integration direction: [Issue #15 comment 6261313794](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6261313794). **Read the [live issue hub](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), current main and PRs at execution time; any SHA/status here is a snapshot, not merge authorization.**

**Companion execution documents:**
- [Sinnoh developer work packages](SINNOH_DEVELOPER_WORK_PACKAGES.md): large Claude/Codex tasks, work allocation, readiness criteria, fallback work and sequencing.
- [Sinnoh complete area coverage](SINNOH_FULL_AREA_COVERAGE.md): reconciliation of every entry in the existing 87-row [area register](SINNOH_AREA_REGISTER.csv), additional sublocations, and scope/technical flags.
- Existing [map construction checklist](SINNOH_MAP_BUILD_TRACKER.md), [technical readiness](SINNOH_TECHNICAL_READINESS_20261017.md), [saved-location analysis](SINNOH_LOCATION_ID_COMPATIBILITY_20261018.md), [operating contract](CURRENT_PHASE_AND_HANDOFF.md), and [Issue #23 QA](https://github.com/kioconnor24-sketch/PokemonGame/issues/23) remain relevant. This roadmap supersedes their **planning priority or per-map creative preapproval language where the newer owner decision differs**, but does not erase findings, evidence, technical safeguards, signed handoffs, or protected-branch rules.

## 1. Product definition and absolute boundaries

1. **Full second region:** construct an explorable, interconnected, recognizable Sinnoh with every main settlement, Routes 201–230, the three lakes, Mt. Coronet, the League, Battle Zone, optional/postgame destinations, Underground, and major interiors/subareas. Core world and optional areas are separate acceptance tracks; "all geography exists" does not equal "all gameplay implemented."
2. **Adaptation style:** start from Pokémon Platinum's functional geographic topology; improve, selectively expand or redesign terrain, visual character, access and reused locations. Story-specific Diamond/Pearl/Platinum buildings are **physical-site candidates**, not permission to reuse Galactic plot or stage another faction. Reuse geography while assigning a neutral placeholder purpose; the owner can later repurpose it.
3. **Owner review after geography:** Claude and Codex should make reasonable source-grounded ordinary geographic decisions and build the world incrementally, then accept owner-directed revisions. Do not keep requesting approval of routine layout, house placement, tiles, or route footprints. Preserve the previous decisions already used in Sandgem/Route 201; no quiet overwrite. Material departure from recognized Sinnoh should be explicitly annotated for later owner review, not silently treated as canon.
4. **No story now:** write *no definitive* Sinnoh plot, villain scheme, dialogue arcs, quest flags, rival developments, scripted legendaries, Gym rosters, trainer rosters, reward inventories, chronology, or level curves. Build neutral spaces and placeholder door/staging slots, not event chains. Reserve Averon's unresolved villain/Threshold/rival choices. Sinnoh's eventual Cynthia and Red placement, main quest and postgame must be integrated only under the owner's later content direction; **Red remains the intended ultimate end-of-game battle after the Sinnoh/postgame adventure**.
5. **Pokémon generations 1–9:** world design should support eventual appropriate ecological representation and availability across these generations, subject to existing species/mechanics assets and technical reality. Record potential habitat **types** (grassland, marsh, cave, coast, forest, snowy peak, volcanic, etc.), not species/levels/abilities/encounter rates yet. Do not assert the full species catalogue is currently compiled/playable.
6. **Johto→Kanto-like continuation:** enter Sinnoh after Averon's principal adventure, using the **same team, levels, moves, held items, PC, Bag and progress**. No reset, dynamic trainer scaling or regional level restriction. A conventional second-region Gym/adventure framework is the eventual design, but no Gym battle progression is authored in this geography phase. Preserve the planned level-100 endpoint late in postgame; **no level numbers or curves assigned now**.
7. **Region transfer:** plan a meaningful first journey, subsequently convenient unrestricted repeat transportation, region-specific Fly/map views, and an interregional transfer interface/destination. No arbitrary weekday schedules. **Physical method, terminals, unlock timing/quests and exact locations are unresolved**; only design reversible interface footprints and testable neutral technical seams. Don't enable unfinished Fly/town-map screens or invent a ferry plot.
8. **Gameplay style:** most of the eventual playthrough remains an ordinary lively Pokémon adventure, not a relentlessly ominous conspiracy. Existing features (following Pokémon, traditional held EXP Share, Set-style battles, Mega Evolution where implemented) must be preserved; exclude Z-Moves, Dynamax and Terastallization as requested.
9. **Legal/technical limits:** use original, properly licensed or permissible re-created GBA-compatible assets. Public Sinnoh diagrams are *research/reference* and not automatically redistributable assets. Reusing DS-only Platinum files/music/sprites without rights is not authorized. Avoid claims of full DS-style Underground, Distortion World gravity or five Platinum Battle Frontier facilities before feasibility/testing and owner review.

## 2. Authority and safe autonomy

**Owner delegates normal *physical geography* decisions to the developers**, including researched topology, ordinary footprints, safe interiors, environmental art placement, benign navigation signage, and candidate reuse of story buildings. That delegation **is not** approval of story, events, battles, encounter tables, level curves, legendary encounters, legal asset imports, invented mechanics, or final release.

- The [operating contract](CURRENT_PHASE_AND_HANDOFF.md) and newest [Issue #15 product direction](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6261800483) govern actual risk/merge review together. An independently reviewed governance update should reconcile any old per-map owner-approval wording. **This design roadmap alone never bypasses GitHub protected-file handoffs, guards, checks, or review tier.**
- **Map IDs vs Pokémon met-origin IDs are distinct.** Assign new technical map/header slots only with append-only verified registry preservation and existing pinned-ID safeguards. Never guess/reuse old IDs. Saved met-location/section naming is a separate constrained codebook; the owner must choose any wider/migrated scheme before production adoption. Don't burn remaining codes unnecessarily just to represent every interior.
- Legacy met names **0–214**, MAPSEC_NONE **215**, egg/trade/fateful **253–255** remain fixed. Existing Sandgem section **216** is in main; owner-approved Route 201 section **217** is in active PR #150 pending integration at the recorded checkpoint. That leaves **35** spare ordinary 8-bit codes **218–252** *after* #150 merges, not enough evidence for unlimited individually named areas.
- Never reinterpret an old save, silently group met origins in a way that changes their meaning, enlarge a save struct, move ID meanings, or introduce a migration under routine map autonomy. The separate owner decision on a full-region met-name strategy is **an early technical-critical-path decision**, not a per-route layout gate.
- Proposed world layouts are reviewable and revisable, but every merge remains a real source change. Maintain normal branches/PRs, exact-path ownership, original protections and meaningful tests. Author self-merging is only permitted within the *actually current* owner fast-lane criteria. A future autonomous geography authorization does not turn high-risk refactors, ID migration or governance changes into R0.
- Story/encounter/level deferral is explicit: do not "fill in" under the excuse that the full map plan is approved.

## 3. Current checkpoint and truth labels

As of the roadmap preparation, existing Milestone 1 was owner-accepted; Sandgem Town and its Pokémon Center were on main, with separate graphical QA evidence. Production Route 201 and healer 44 were active **draft** PRs #150/#151; the graphical seam/whiteout harness #152 and streamlined operating-policy PR #153 subsequently merged (verify live main). The route design is owner-approved but **production completion is not presumed**. A partial transition reached using a DEV fixture is **not** normal story reachability. Human-audible audio acceptance and Delta iOS acceptance remain unverified.

Track each implementation dimension independently:

| Label | Minimum evidence |
| --- | --- |
| REFERENCED / PROPOSED | Original geographic references + rationale/uncertainty, topo/geometry sketch, no production claim |
| SOURCE-INTEGRATED | Registered final production files and existing IDs/compat checks verified in an actual main commit |
| BUILT | Exact NORMAL and RELEASE binary/source SHA, applied toolchain, linked ROM growth and budgets |
| NATIVE-TESTED | Relevant native assertions and negative cases, with measured pass/fail/skip, no expected failures hidden |
| EMULATOR-TESTED | Real mGBA input/screenshots for walk/collision, seam/warp both ways, follower, menu, Save→fresh-process Continue and healing where applicable; DEV fixtures disclosed |
| GEOGRAPHY-ACCEPTED | Connected structure and visuals accepted as implemented, owner revision backlog handled or expressly deferred; does **not** imply story, species or levels |
| GAMEPLAY-ACCEPTED | After future content approval: legitimately reachable complete gameplay and all applicable authentic tests, not fabricated scripted results |
| DELTA / HUMAN AUDIO | Independently measured/played on target iOS/human ears; not inferred from normal mGBA/source passing |

Keep the actual [area register](SINNOH_AREA_REGISTER.csv) as source of current stage. Its old \`LayoutApproval=PENDING\` entries reflect historical per-area workflow and **must not falsely be relabeled APPROVED**: if necessary, introduce a separately governance-reviewed \`delegated layout / owner revision pending\` status or record the delegated decision link in \`OwnerDecisionLink\`. No status promotion just for publication of this roadmap.

## 4. Production strategy

**Hybrid: full-region topology first; permanent implementation in connected, playable geographic batches; gameplay content later.**

Why: comprehensive topology catches roads/ridges/lake connections and interior multiplicity before too much map work is baked in. Small production batches make real maps playable/testable early, contain merge conflicts, expose RAM/ROM limitations, and permit later owner revisions without a monolithic rebuild. They must be *real eventual Sinnoh geography*, not a discardable mock region.

Use one **master topology graph** with each area-register key, external adjacency, directed ledges, water/Surf/strength/etc. as neutral traversal placeholders, entrance/return portal types and off-map ferry points; a **shared coordinate/scale reference**; a **tileset/biome/palette reuse plan**; and a **neutral interior/asset inventory**. Exact play locks must remain unscripted until story/field mechanics are approved. The topology should show full physically traversable potential and separately annotate *currently inaccessible* edges—not invent progression gates.

**Representative geographic implementation batches**, with dependencies and detailed area assignments in the companion documents:

| Stage | Region wave | Major geography and useful purpose | Start condition |
| --- | --- | --- | --- |
| W0 | Existing wedge | Sandgem Town, Center, Route 201, whiteout, old-save and seam verification | Resolve #150/#151 with real evidence |
| W1 | Southwest origin | Twinleaf, Verity Lakefront/Lake Verity, Route 202, Jubilife and early community subareas | Topology + trustworthy Route 202 source; do not approximate its deferred layout |
| W2 | Oreburgh and northwest | Routes 203–207, Oreburgh City/Gate/Mine, Route 204/Ravaged Path, Floaroma/Meadow/Valley Windworks, Eterna Forest/City, Old Chateau, Fuego, Cycling Road/Wayward Cave | W1 junctions or separately closed edges |
| W3 | Central and west | Routes 208–212 and 218, Hearthome, Solaceon, Celestic, Canalave; Amity Square, Lost Tower, Solaceon Ruins, Mt. Coronet lower crossovers, Iron Island | Central road graph and shared cave/interior toolchain |
| W4 | East/south wetlands | Routes 213–215, Veilstone, Pastoria, Lake Valor + Lakefront, Great Marsh, Trophy Garden/Pokémon Mansion, Spring Path/Sendoff/Turnback | Shore/coast/marsh assets and matching paths |
| W5 | North and League coast | Routes 216–217, Snowpoint/Acuity, Snowpoint Temple, Mt. Coronet upper floors/Spear Pillar; Routes 222–224, Sunyshore, 223 coast, Victory Road, League and 224 optional branch | Snow/vertical/Surf/cave tooling; map graph can be staged independently of battle events |
| W6 | Sea and island postgame | Routes 219–221, Pal Park reuse, Fullmoon/Newmoon Islands and transports, relevant port/interior sites | Water/boat interface, safe return paths |
| W7 | Battle Zone | Fight/Survival/Resort Areas, Routes 225–230, Stark Mountain, Battle Park/Frontier physical campus, rematch areas | Main regional travel surface ready; no promised five-facility mechanics yet |
| W8 | Advanced optional worlds | Underground/Grand Underground; Distortion World; Flower Paradise/Seabreak Path; Hall of Origin, optional ruins and legendary-site *physical spaces* | Explicit feasibility per feature; neutral map shell may precede eventual gameplay |
| W9 | Completeness and art pass | All 87 tracked sites + submaps, missing interiors, alternate biomes, placeholder replacement and cross-world spatial review | Every wave has a connected source build |
| W10 | Two-region transport and UI | First-arrival interface, reversible repeat transit, regional map/Fly selection and transfer point (without plot scripting) | Owner later selects terminal/transport details and persistent technical policy |
| W11 | Future gameplay-content pass | Gyms, trainers, encounters, quests, ecology balance, game economies, legendary interactions, optional minigames | **Blocked on later owner story/progression/level/encounter decisions**; geography work proceeds independently |
| W12 | Whole-game acceptance | Ordinary Averon→Sinnoh reachability, badge/field systems, party/Bag/PC, save/whiteout, scene UX, postgame, sound/Delta and regression | All relevant features implemented; no synthetic fixture substituted for acceptance |

**These are geographic engineering waves, not mandatory story order or level order.** Connected W2–W7 subareas may be built in parallel once scoped and claimed. No fixed durations are invented. Read the coverage file for area-by-area mapping and the work-packages file for actionable developer assignments.

## 5. Technical critical path and gating decisions

### Early, high-impact systems

A. **Identity/codebook strategy.** Audit real named-section demand (not simply number of maps), including old Pokémon met-location preservation. Reuse the researched bounded 8-bit, grouped runtime section and 13-bit experimental options; do not casually widen bytes. Produce an owner decision with tradeoffs/irreversible effects **before** the current 8-bit code budget becomes insufficient. Source-backed production map compilation continues where unblocked.

B. **32 MiB ROM and transient hardware ceilings.** Update measured OFF-default and ON-restoration linked-used and remaining bytes on each major batch. Historical readiness estimate was ~6.39 MiB RELEASE spare and SaveBlock2 ~84 B free, **not a current verified build and not evidence the whole region fits**. Track future Averon and postgame reserve too. Observe map working buffer condition \`(width+15)*(height+14) <= 10,240\`, field tiles/metatiles/palettes, 16 object events and 64 software sprite slots; watch actual high-water heap/stack/palette usage. Never add more PC boxes, raise ROM size or rewrite save layouts casually.

C. **Map tooling and asset provenance.** Build a repeatable source pipeline for authored geometry, collisions, warps/return points, gates, tilesets and map group registration. Source original/reference documentation; assets must be created/cleared separately. Plan forest/coast/marsh/cave/snow/volcano biome families with palette/metatile limits. Do not rely on one throwaway GBA tileset to certify final visual character.

D. **Transit/region map/Fly.** Separate persistent region state from visual map region and met-origin code. Region-specific Town Map/PokéNav/Fly currently refuse unsupported Sinnoh paths safely; continue refusal until the full correct UI/destinations have tests and physical sites. Architect user-facing transfer with verified reversible source/destination, one-time introduction followed by repeat transport, save/whiteout fallback and old-save behavior. Exact plot and transport mode undecided.

E. **Field traversal and specialized areas.** Surf/waterfall/strength/caves/ledge/ice/snow/ash as applicable must match actually implemented features and terrain; defer unsupported puzzles mechanically rather than fake acceptance. Underground/Distortion World/Battle Frontier have scoped **feasibility spikes** first, with separate owner choices on faithful/adapted implementation if GBA limitations require tradeoffs.

### Checks by risk

| Change | Gate |
| --- | --- |
| Reference research, topology proposals, documentation/QA-only | Fast Lane A per live operating contract |
| Source-only independent tests/tooling | Fast Lane A if genuinely isolated from production and all applicable checks pass |
| Ordinary geography/connections after delegated owner direction | Confirm current owner/delegation + existing GitHub protected-path handoff and risk tier; bounded eligible Fast Lane B **only if the live policy actually authorizes this exact scope**; otherwise targeted peer review. Do not self-expand Fast Lane B by reading a plan as code approval |
| Saved IDs, save/runtime schema, broad engine, CI, guards, security, release | Owner policy decisions where applicable, independent meaningful review, native/compatibility/negative tests, normal SHA-pinned PR merge |
| Actual graphics/connected player behavior | NORMAL/RELEASE builds, real mGBA, Save→fresh Continue, exact ROM/fixture evidence |
| Story, encounters, battles, levels, legends and final player experience | Later owner-approved design + actual gameplay acceptance |

Use **minimum sufficient verification**, not full suite reruns for an unchanged documentary diff. Failure on an applicable required check means stop that merge; switch to a disjoint task. An author can merge eligible PRs without manager approval, but not bypass saved-ID/guard governance.

## 6. Milestone exit gates

**G0 — Existing slice trustworthy:** #150 and #151 merged (if eligible) with true Route 201 fresh Continue, healer ID44 real whiteout and negative test, source and ROM evidence, Sandgem/Route201 seam both directions on main. Any limitation disclosed.

**G1 — Atlas designed:** all 87 register entries appear in a verifiable geographic graph; port/coast/cave/underground links and additional subareas listed; cross-map route topology and boundaries checked. Story sites neutral. Source references and uncertain adaptations identified; no known missing settlement/route category.

**G2 — Authoring platform safe:** linked profile budget and ID/codebook strategy documented; pipelines preflight map group/section pins, collision/edges/warps, resource measurement. Tests demonstrably catch broken/negative fixtures. No unauthorized persistent IDs.

**G3 — Mainland structural coverage:** all mainland towns/routes/lakes/caves/staging interiors compiled, physically reachable from a developer entry where appropriate, with safe reciprocal connections or intentional closed boundaries and normal Save/Continue. Incomplete scripted content labeled as such.

**G4 — Postgame geography:** Battle Zone, optional islands/sea, Victory Road/League outer/internals, side paths and ruins present and return-safe; advanced exceptions honestly documented. No pretend completion of Battle Frontier's mechanics.

**G5 — Complete geographic QA:** each of the 87 tracked locations and all approved child maps has a source commit, linked ROM measurement, graphical inspection and safe traversal result. Unbuilt exception != PASS. Owner review/revision requests resolved or tracked.

**G6 — Multi-region platform ready:** tested legitimate first-arrival/return route once owner transit specifics exist; visited area display/region selector/Fly/whiteout, Save→Continue and legacy saves work. No region confusion.

**G7 — Full gameplay (later, separate):** after the owner chooses story, levels, trainers, Gym logic, encounters and quests, implement and accept actual primary/optional progression with native and graphical evidence.

**G8 — Whole game/release (last):** real full-run test, late postgame and Red final battle when scripted, save/compat matrix, legendaries only as owner-designed, legally usable assets, audible checks, performance and real Delta iOS smoke. Never call this complete from source-only or emulator-only evidence.

## 7. Execution and dependency rules

**Primary critical path:** G0 playable wedge → G1 coherent topology + G2 map/identity/toolchain readiness → geographically independent W1–W8 source batches → G3/G4 → G5 physical completeness → G6 completed transit mechanics → G7 owner-authored gameplay → G8 release.

**Parallelization:**
- Claude drives original-reference geography, map source/tilesets, warps/collision/follower mGBA QA, field visuals, owner revision passes, and approved production content. Do not force all 87 sites into one source branch.
- Codex drives section/met-origin compatibility, heap/ROM/stack/capacity checks, save/region/Fly/transport plumbing, native coverage and build tooling. Independent work proceeds while Claude maps.
- Cross-review **only where risk policy actually requires it**. Shared generated registry files must be claimed/serialized by integration batch. Neither agent needs a ChatGPT manager ACK to continue disjoint work or perform a valid author merge.
- At every wave boundary refresh live main and PR heads, reconcile ID allocation, leave one reproducible command/evidence log and actual remaining blocker(s). Do not rewrite the entire roadmap for every commit.
- If a location needs a future story decision, build a safe, neutral physical shell and mark the event slot reserved. If its very geometry fundamentally depends on story, propose two source-grounded variants and do another independent area.
- If Route 202 references are still insufficient, source them; in parallel proceed with independently reachable topology/candidates and approved connected areas. Do not fill the gap using unsupported invented Platinum coordinates.
- No self-scheduled paid agent restarts, mass branch deletion, rewriting preexisting accepted M1 work, or pretending PR commentary automatically launches a coding session.

## 8. Evidence and ownership cadence

For each substantial connected batch record: (1) exact area keys/submaps; (2) source reference + justified deviations; (3) planned and actual adjacency/portals including blocked edges; (4) exact PR/head/main and literal changed paths; (5) native and negative results; (6) NORMAL/RELEASE ROM/source hash and linked growth; (7) genuine mGBA screenshots/event log, path walk, real warps and fresh Continue; (8) saved identity impact; (9) known placeholders and no-story/levels status; (10) next callable task. Preserve the [existing 87-row register](SINNOH_AREA_REGISTER.csv) as operational progress tracking, not an abstract checklist.

Review cadence: one small focused PR per connected batch or one cohesive technical system; after green eligibility merge, move immediately to the next unclaimed area. Maintain a short weekly physical-coverage/technical-risk snapshot **only when it reflects meaningful changes**, never a new management ceremony.

### Final acceptance question

A geography milestone is useful only if a player can actually explore a recognizable, richly varied Sinnoh **without accidental softlocks**, and an engineer can save/continue, return to Averon when that system is later enabled, and add approved gameplay without reconstructing the terrain. A completed outline or all-green source CI is not equivalent to this result.

---
**Reference evidence, not automatically distributable game assets:** existing Sinnoh register and production records above; external [Sinnoh location inventory](https://bulbapedia.bulbagarden.net/wiki/Sinnoh), [Platinum location catalog](https://bulbapedia.bulbagarden.net/wiki/Category:Platinum_locations), and [Battle Zone geography](https://bulbapedia.bulbagarden.net/wiki/Battle_Zone). The 87-row tracker is an inventory index, **not** a claim of only 87 actual game maps; each exterior, floor, house, special layer or gameplay venue may expand into child maps after research.