# Sinnoh map construction — master checklist and production contract

**Status:** owner-approved *workflow/priority split* (2026-10-17); **NOT** approval of any specific new map geometry, saved ID, storyline, art source, trainer roster, or production asset. This is the canonical **map-construction checklist**; the companion [area register](SINNOH_AREA_REGISTER.csv) is the canonical **per-area status inventory**. For actual source of truth about accepted engine behavior, use `main` and the relevant test PR.

**Purpose:** build **actual, permanent Sinnoh geography** as the prototype and production world; never build a disposable extra test region. Sinnoh is the **full second playable region** after Averon in the game, even if we *author* its maps first. Preserve its recognizable geography while allowing owner-approved deviations from the original Diamond/Pearl/Platinum story. No automatic cloning of Team Galactic scripts, blocked routes, rival events, or licensed material.

**Audio scope:** plan and budget with **cries-OFF as the intended working build**, while retaining *all* cry sources/definitions and a reproducible cries-ON option. PR [#117](https://github.com/kioconnor24-sketch/PokemonGame/pull/117) has since **merged**: the reversible ON/OFF build paths and Claude's native/RELEASE emulator evidence are available, but the unchanged `CRIES=default` still selects ON, and human listening, Delta iOS and final OFF adoption remain unverified/separate. Normal music and other sound effects must remain. Do not reopen the completed ROM capacity study or require human audio/Delta acceptance before beginning disjoint map authoring; still fix genuine runtime blockers before claiming affected gameplay accepted.

## 0. How to use this checklist (no extra bureaucracy)

- **One page, one CSV and existing GitHub hubs**: this document owns process-level checks; [SINNOH_AREA_REGISTER.csv](SINNOH_AREA_REGISTER.csv) tracks each place; [#15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) remains the only file-claim/owner-decision hub; [#26](https://github.com/kioconnor24-sketch/PokemonGame/issues/26) remains the phase roadmap; [#23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23) and [#55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55) retain gameplay QA and real blockers. Do **not** create a separate issue per street, asset, or speculative subplot.
- All CSV `SN-*` keys are **tracker-only identifiers**, NOT GBA map IDs, sections, flags, event vars, Pokémon met-location values, or reserved saved identifiers. Existing names and routes are an **inventory for coverage/review**, not owner approval of exact scale, paths, locations or original game plot.
- **Statuses** for each CSV row: `Adaptation=UNDECIDED|PRESERVE|MODIFY|REDESIGN`; `LayoutApproval=PENDING|APPROVED`; `Structure=NOT_STARTED|IN_PROGRESS|EMULATOR_PASS`; `VisualAssets=UNSOURCED|PLACEHOLDERS|FINAL_REVIEWED`; `Gameplay=DEFERRED|IN_PROGRESS|EMULATOR_PASS`. Record tested ROM SHA, screenshots/run/evidence URL, and linked PR before marking any `EMULATOR_PASS`. A parent location may expand into subrows (e.g., a separate cave floor or city interior) once approved; no invented technical map count ahead of design.
- Update a row **on meaningful progress**, not on every developer session. Do not mark `EMULATOR_PASS` on the strength of map JSON, a compiler return code, synthetic fixtures, or someone else's unrelated ROM run. `Gameplay=DEFERRED` is intentional, **not** evidence of a blocker.
- Follow live #15 exact-file claims and [October 18 parallel assignments](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6251950630): #117 audio, #125 preflight and #126 map-generator inclusion have all merged; Codex now owns disjoint save/section/Fly engineering and Claude owns Sinnoh art/approved map authoring and emulator evidence. Issue comments cannot remotely launch Claude. Keep new map source claims disjoint from active PR #117 audio files, and make normal reviewed PRs. Work must respect existing map/file guards; do not weaken them.

## 1. The **only mandatory gates** before permanent Sinnoh map work

- [ ] **Owner approves the first real Sinnoh slice**: choose an actual exterior + linked interior, intended rough layout/footprints, and approximate exits. This must be an area of the future game, not a fabricated test area. Do not assume Twinleaf or another location is chosen without approval.
- [ ] **Approve an ID/save compatibility contract** before allocating permanent section/met-location numbers: existing section IDs `0..214`, `MAPSEC_NONE=215`, and `0xFD..0xFF` special Pokémon met-locations stay stable. The reported 37 spare byte codes are **section/met-location** headroom, NOT a limit of 37 new maps (951 map IDs were already registered). Decide how many *named* sections are needed; if over capacity, choose an explicitly save-compatible runtime UI section vs legacy 8-bit met-location conversion, or an evidenced versioned migration. No anonymous aliasing or blind `u8` widening, and no speculative SaveBlock2 layout growth (84 B spare in the audit).
- [ ] **Check asset provenance for the first slice's temporary art** and approve reuse or original placeholders. Gameplay/map reference images are not automatically redistributable assets.

**Do not delay map drawing for:** final Sinnoh story or villain, fully developed Averon, eight Gym scripts, final encounter tables, complete two-region Fly/ferry/whiteout UI, full ROM forecast, final tileset art, human cry listening, or postgame balancing. **A minimal map build inclusion path must work for the first slice**; it may be implemented *with* that slice, not as a separate region-sized project. Existing `map_data_rules.mk` filters out non-`REGION_HOENN` maps, so simply labeling a new map `REGION_SINNOH` will not work.

## 2. Sinnoh geography/adaptation contract (repeat for each area)

- [ ] Review the **Sinnoh original's functional geography**: entrances, landmarks, terrain, iconic orientation, route neighbors, traversal flow and visual identity. Research/reference is permitted; copying an unlicensed ROM, tileset, script, or copyrighted music into this repo is not.
- [ ] Assign **PRESERVE**, **MODIFY**, or **REDESIGN**, with a one-sentence rationale and owner approval of any material change. Preserve recognizable Sinnoh; do not reproduce original story-specific gates by default.
- [ ] Approve **structural topology before drawing**: map footprints, elevation, traversable connections, intended shortcut branches, portals/doors, access to healing and safe future event footprints. Keep reasonable dimensions for final graphics so placeholders won't force map rework.
- [ ] For story-dependent sites (e.g., Valley Windworks, Spear Pillar, a repurposed faction facility), map neutral **physical space only**; record `RESERVED_EVENT_SPACE` or `PENDING_STORY` in the register. Don't script Team Galactic, Arceus Plates, Vale, the rival, or permanent story flags based on provisional lore.
- [ ] Plan environmental variety and ecology now: grass/water/caves/forests/snow/islands, landmarks, exploration detours and plausible habitat spaces, **without** picking exact species/levels/rosters/item rewards before progression is ready.
- [ ] Record geographically relevant owner decisions in the area register and source PR; unresolved story decisions are explicitly **not** map blockers unless geometry truly depends on them.

## 3. Shared placeholder system (build once; reuse)

- [ ] Create **one small, legally sourced/original, GBA-compatible** placeholder set for terrain/buildings, biome variants, NPCs, Gym/interior objects and reserved event landmarks. Reuse existing engine palettes/metatiles/tilesets where practical. Do not create a unique throwaway graphics library for every map.
- [ ] Maintain a single replacement manifest per used placeholder: `token / role / source-license / width-height & tile footprint / palette & tileset / collision semantics / final asset owner or TBD / placement(s) / status`. Store with map/asset work, not speculative giant spreadsheets.
- [ ] **Fixed now:** walking collision, ledges, doors, warp coordinates, map dimensions/levels, route connection geometry, basic safe healer access where applicable, renderable 4bpp tiles/palette behavior. **Replace later:** surface art, NPC identities/schedules, dialogue, nonessential effects, wild/trainer tables, quests, named items and music.
- [ ] **Visually distinguish biomes even with placeholders.** A generic tile carpet is useful for testing collision, but cannot count as visual completion.
- [ ] When real art replaces a placeholder, revalidate metatile indices, palette slots, sprite dimensions, animations, collision, lighting and warp sightlines; replacement is a *goal* to be low-rework, not a guarantee of no map change.
- [ ] All rights and attribution must be reviewed before importing third-party Sinnoh source maps, art, audio or fan-hack packs. An external Sinnoh-on-Emerald project is a **reference candidate**, never an assumed drop-in.

### Implemented supporting tools (not completed map production)

- [x] **SOURCE/HOST tooling:** [selected-map preflight and comparable linked-resource deltas](SINNOH_SOURCE_AND_PIPELINE_RESEARCH_20261017.md) now check geometry, PNG/palette dependencies, metatile bounds, warp arrival/return indices, reciprocal edge geometry, saved-section pins (reusing #123) and current build inclusion; the existing resource reporter compares matching profiles and partial named-object contributions with explicit LTO/padding residuals. The 16 existing Averon opening maps pass. This does not certify converted pixels, collision/gameplay or change any area-register status. Preflight42 + resource18 + event-capacity4 host tests pass; no new map or permanent identifier is approved by this check.
- **Research only:** the same report pins the Sinnoh donor's 159 map definitions, incomplete coverage, concrete warp conflicts and unresolved asset terms. No third-party map/asset is imported; native construction remains the actionable path pending specific owner decisions.

## 4. **First real Sinnoh slice** — implement and retain

- [ ] Create approved first exterior plus a **real connected interior**, using final-ish map dimensions and approved, tracked placeholder assets.
- [ ] Implement only required append-only map/layout/header registration and narrow Sinnoh build inclusion. Preserve old registry values, `MAPSEC_NONE`, disabled maps, and the guarded mapping tests. No blanket enable of all FRLG content, generated-header hand edits, or temporary production IDs.
- [ ] Verify actual GBA compilation in the **working OFF profile when technically available**, and record build command, source/ROM hashes and true linked bytes. Where PR #117 is not integrated, label any separate OFF trial **experimental**.
- [ ] In a genuine mGBA graphical playthrough, verify rendering, motion, walk/collision/ledge behavior, door/warp round trip, following Pokémon if active, menu, save, fresh-process Continue at the intended point, and safe exits. Any blocked RELEASE path is reported honestly and tested via an alternative build only with that limitation stated.
- [ ] Record exact area register stage/evidence. **Keep this slice as the first part of the final Sinnoh world**; no separate proof-of-concept region to throw away.
- [ ] Before larger imports, review whether the new source/map pipeline actually works on this engine. If a third-party import fails, choose a local native reconstruction rather than endlessly retrying a mismatched importer.

## 5. **Every subsequent approved map batch** — the same concise checklist

- [ ] Update topological neighbors in the register; secure scoped approval of changed/expanded layouts before assigning identifiers.
- [ ] Implement one logically connected and reviewable batch (route + its town/interiors, cave floors, etc.). Prefer shared tileset families to duplicated assets; reserve plot/event spaces but avoid unfinished forced transitions.
- [ ] Verify mapgen inclusion, all connected warps (including return direction), safe spawn/healer interfaces when present, no traps, collisions/ledges, palette/metatile ceilings, enabled header and map IDs, and NPC/follower object pressure. Keep within the engine's known scene-level tile, palette and object constraints; test actual peaks when approached.
- [ ] Run targeted checks/CI plus authentic mGBA walking/warp/saving evidence for the newly playable path; do not rerun all M1 regressions solely for an unchanged tree.
- [ ] **Measure ROM on every meaningful build/content batch**, not in a separate forecasting phase: hash + source commit, `CRIES=off` linked bytes (only when that profile is integrated/safe), used/free vs 32 MiB, signed delta from prior comparable build, major new contributions and remaining *Averon + Sinnoh + postgame* reserve. Note placeholder-vs-final-asset uncertainty. Keep optional cries-ON restoration cost visible without making ON a day-to-day map prerequisite.
- [ ] Record build/runtime regressions and blocked areas once with the next alternative action; if stuck, develop an independent approved neighboring area, not an infinite debug loop.
- [ ] Update register `Structure`/`VisualAssets` only when evidence supports the change; record exact PR/screenshot/ROM source evidence. **Visual complete is not gameplay complete.**

## 6. What **waits until Averon gameplay/story is completed enough to define dependencies**

- [ ] **Final Sinnoh Gym/leader/trainer roster and level tuning** against the actual end-of-Averon team, badges, items and available mechanics.
- [ ] **Story-dependent missions and locked access**, including exact rival/antagonist return, Team Galactic replacements, faction buildings, scene triggers and legendary/Arceus events (all unresolved choices remain provisional).
- [ ] **Final encounters, rewards, sidequests and economy**, except early ecological spaces and any independently owner-approved self-contained content.
- [ ] **Canonical entry from Averon**, return voyage, complete inter-region Fly/visited network, global badge and Field Kit policy, healer/whiteout fallback across regions, and final Save→Continue travel proof. The existing two-region save and generic travel foundation may be independently tested beforehand; defer **finished destination-specific integration**, not all infrastructure.
- [ ] **Full Sinnoh story progression and flags**, Cynthia/Champion sequencing, quest-related map changes, Battle Zone/postgame/Circuit and ultimate Red gating, complete pacing/balancing.
- [ ] **Final audiovisual polish and actual owner Delta iOS acceptance** after a playable integrated release candidate. Preserve deferred human audio check as untested, not PASS.

These are **integration dependencies**, not bans on drawing approved towns/routes, using neutral loreless interiors, refining scenery, or developing independent map tooling now.

## 7. Definition of finished and owner-facing progress

**An area is not one binary checkbox:**
- **INVENTORIED:** named for planning only (all initial rows). **APPROVED:** owner accepts the specific physical design and adaptation.
- **STRUCTURAL / EMULATOR_PASS:** a real map on a reproducibly built GBA ROM with correct movement, connections, warps, and successful save/reload; temporary art and no scripted story are explicitly allowed.
- **VISUAL / FINAL_REVIEWED:** approved final art is integrated with real rendered acceptance and no broken collision/warp readability.
- **GAMEPLAY / EMULATOR_PASS:** the area's *approved* encounters, access rules, events, progression and rewards pass meaningful actual gameplay tests (often **after Averon**).

Report **counts by stage**, not misleading overall percentages or a bare `map complete`. A tracker row is a geographic coverage unit, **not necessarily one physical map file**. Never count pending/nonapproved locations as built, and never infer a release candidate from completed structural geography.

**Global Sinnoh geographic construction is ready for integration** when all owner-required core areas have tested structural paths, their registered connections/return routes work, relevant graphical/runtime memory limits and ROM headroom are measured, and unresolved story hooks remain clearly marked. **Sinnoh's full playable story is ready only after** Averon-derived progression and integrated acceptance. Preserve the wider project's final 32 MiB/Delta compatibility constraints and the cry source library.

### Context / source references

- [Current phase and owner approval](CURRENT_PHASE_AND_HANDOFF.md) | [technical map IDs, asset, save, Fly and build study](SINNOH_TECHNICAL_READINESS_20261017.md)
- [Sinnoh recognizable geography and postgame requirements](../design/SINNOH_AND_POSTGAME.md) | [provisional cross-session story ledger](../design/STORY_DEVELOPMENT_WORKING_DOSSIER_20261017.md)
- [Cries retention owner policy](CRIES_OFF_REVERSIBLE_OWNER_POLICY_20261017.md) | [GitHub workflow](WORKFLOW.md)
