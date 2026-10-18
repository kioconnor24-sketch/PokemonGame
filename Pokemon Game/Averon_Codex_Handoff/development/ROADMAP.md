# Pokémon Averon — high-level roadmap (owner-approved transition)

For **live status and scope**, read [CURRENT_PHASE_AND_HANDOFF.md](CURRENT_PHASE_AND_HANDOFF.md) first; for actual assignments read [TASKS.md](TASKS.md) and [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). Older pre-Sinnoh dependency/PR schedules are retained in dated runbooks for history.

| Stage | Status | Evidence / next gate |
| --- | --- | --- |
| **M1: map-independent pre-Sinnoh backend** | **OWNER-ACCEPTED 2026-10-17** | [Claude consolidated signoff](M1_ACCEPTANCE_REPORT_20261017.md), [Codex native closeout](CODEX_M1_NATIVE_CLOSEOUT_20261017.md); no known M1-blocking engineering defect. Human audio listen explicitly deferred, Gym 1 evidence gap accepted. |
| **M2: next-phase design contract and technical infrastructure** | **AUTHORIZED TO BEGIN** | [Technical readiness plan](SINNOH_TECHNICAL_READINESS_20261017.md); owner decisions on geography, map IDs/sections, progression, asset resources/rights before those specific details are implemented. |
| **M2: first approved playable region slices** | **SANDGEM #133 APPROVED; REVIEW PENDING** | Sandgem section 216 is on main (#132). Sandgem maps #133 remain open pending source review and normal integration. Later routes still need owner approval; see the [integration queue](INTEGRATION_QUEUE.md). |
| **Expanded Averon adventure and full Sinnoh second region** | **FUTURE CONTENT BUILD** | Incremental geography, NPCs, gyms, legendary quests, dialogue and pacing; no current claim these areas are implemented or fit on ROM. |
| **Release candidate / Delta iOS compatibility** | **NOT YET VERIFIED** | Real owner device testing, finished story/world, audio listened to and documented, legal distribution and all relevant save/load/move/graphics tests. |

## Immutable gameplay/product design guardrails
Averon is the first region, Sinnoh the second. Most adventure play stays traditional, bright, exploratory and not dialogue-heavy, with sparse conspiracy hints; user decisions govern unfinished story. Use original Gen V **held-item** EXP Share, forced Set battles, level 100 cap, Mega and following Pokémon; no Z-Moves, Dynamax or Terastallization. Final selection of specific region maps, story choices, Gym types/teams, legendary locations, permanent identifiers, levels and music/art remains with the owner.

## Integration sequence (not a blanket development gate)
1. Approve actual content/resource and section/met-location/saved-state policy before assigning permanent content IDs.
2. Establish link-time and runtime budget observations; no assumption full Sinnoh fits in ~6.39 MiB RELEASE remainder.
3. Apply small reviewed map/section/region/Fly/healer engine integrations; run targeted saves, normal/RELEASE build and unchanged-baseline comparisons as appropriate after source changes.
4. Build one approved slice; perform real mGBA checks and Save→Continue, fix defects, repeat carefully. Scale only after visible, measured successful slices.
5. Human audio review is **deferred** but cannot be bypassed for eventual release acceptance; owner Delta testing remains a separate milestone.

No bypassing protected GitHub guards, deleting history, uploading private ROM/saves or silently treating preliminary proposals as approved canon.
