# Pokémon Averon — historical high-level phase roadmap (2026-10-17 checkpoint)

**CURRENT SINNOH PLAN:** [Full-region roadmap](SINNOH_MASTER_PRODUCTION_ROADMAP.md), [22 developer work packages](SINNOH_DEVELOPER_WORK_PACKAGES.md), [87-area coverage](SINNOH_FULL_AREA_COVERAGE.md), and [latest owner geography delegation](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6261800483). The rows below are a historical phase snapshot, **not current PR statuses or per-map creative-approval requirements**.

For **live status and scope**, read [CURRENT_PHASE_AND_HANDOFF.md](CURRENT_PHASE_AND_HANDOFF.md) first; for current integration priorities read [INTEGRATION_QUEUE.md](INTEGRATION_QUEUE.md) and [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). Older pre-Sinnoh dependency/PR schedules are retained in dated runbooks for history.

| Stage | Status | Evidence / next gate |
| --- | --- | --- |
| **M1: map-independent pre-Sinnoh backend** | **OWNER-ACCEPTED 2026-10-17** | [Claude consolidated signoff](M1_ACCEPTANCE_REPORT_20261017.md), [Codex native closeout](CODEX_M1_NATIVE_CLOSEOUT_20261017.md); no known M1-blocking engineering defect. Human audio listen explicitly deferred, Gym 1 evidence gap accepted. |
| **M2: next-phase design contract and technical infrastructure** | **AUTHORIZED TO BEGIN** | [Technical readiness plan](SINNOH_TECHNICAL_READINESS_20261017.md); owner decisions on geography, map IDs/sections, progression, asset resources/rights before those specific details are implemented. |
| **M2: first approved playable region slices** | **SANDGEM #133 MERGED; CLOSED-EDGE SLICE VERIFIED** | Section 216 (#132) and Sandgem maps/Center (#133, merge `ce0c505d`) are on main; Claude re-tested main NORMAL/RELEASE OFF 26/26. DEV-only entry, no natural whiteout anchor or story travel. Route201/healer44 were pending implementation at that historical checkpoint; refresh live PRs. The owner now delegates ordinary Sinnoh geography to developers, while saved ID/format and actual GitHub protections remain controlled. |
| **Expanded Averon adventure and full Sinnoh second region** | **FUTURE CONTENT BUILD** | Incremental geography, NPCs, gyms, legendary quests, dialogue and pacing; no current claim these areas are implemented or fit on ROM. |
| **Release candidate / Delta iOS compatibility** | **NOT YET VERIFIED** | Real owner device testing, finished story/world, audio listened to and documented, legal distribution and all relevant save/load/move/graphics tests. |

## Immutable gameplay/product design guardrails
Averon is the first region, Sinnoh the second. Most adventure play stays traditional, bright, exploratory and not dialogue-heavy, with sparse conspiracy hints; user decisions govern unfinished story. Use original Gen V **held-item** EXP Share, forced Set battles, level 100 cap, Mega and following Pokémon; no Z-Moves, Dynamax or Terastallization. Ordinary Sinnoh physical geography is now delegated to developers for later owner revisions. Story choices, Gym types/teams, legendary placement, saved identity policy, levels and music/art rights remain reserved.

## Integration sequence (not a blanket development gate)
1. Approve actual content/resource and section/met-location/saved-state policy before assigning permanent content IDs.
2. Establish link-time and runtime budget observations; no assumption full Sinnoh fits in ~6.39 MiB RELEASE remainder.
3. Apply small reviewed map/section/region/Fly/healer engine integrations; run targeted saves, normal/RELEASE build and unchanged-baseline comparisons as appropriate after source changes.
4. Build one approved slice; perform real mGBA checks and Save→Continue, fix defects, repeat carefully. Scale only after visible, measured successful slices.
5. Human audio review is **deferred** but cannot be bypassed for eventual release acceptance; owner Delta testing remains a separate milestone.

No bypassing protected GitHub guards, deleting history, uploading private ROM/saves or silently treating preliminary proposals as approved canon.
