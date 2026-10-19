# Pokémon Averon — current agent operating contract
**OWNER-APPROVED NEXT PHASE, 2026-10-17.** The authoritative status, approved scope, responsibilities and unresolved limits are in [CURRENT_PHASE_AND_HANDOFF.md](Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md). Read it **before** any older 2026-10-15/16/17 M1 runbooks, GitHub board snapshots, or previous handoffs. The owner accepted pre-Sinnoh Milestone 1, authorized proceeding to the next phase, accepted the Gym 1 missing-text evidence gap as non-blocking and **deferred human audio listening** to later QA.

## Start every new session
1. Refresh `main`, open pull requests/checks, exact issue/PR heads and [Issue #15 — live ownership hub](https://github.com/kioconnor24-sketch/PokemonGame/issues/15).
2. Read the [current-phase handoff](Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md), then applicable [technical Sinnoh planning](Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_TECHNICAL_READINESS_20261017.md), [final M1 QA](Pokemon%20Game/Averon_Codex_Handoff/development/M1_ACCEPTANCE_REPORT_20261017.md), and the exact code paths you will change.
3. Claim **specific new files and scope** in #15 as a nonblocking notification; check no other developer owns a conflicting worktree/path. Coordinate real protected overlap rather than stopping unrelated work. Follow [WORKFLOW](Pokemon%20Game/Averon_Codex_Handoff/development/WORKFLOW.md).

## Current lanes (not a blanket release to invent content)
- **Codex:** independent technical foundation; resource/section-ID/ROM/RAM/save checks; later owner-approved map/region/Fly/healer integration and narrow engine fixes proven by real tests.
- **Claude:** owner-approved playable region slices and local graphical mGBA gameplay evidence, controller input, Save→Continue, visible follower/dialogue/menu behavior. Before individual design approval, safely improve supporting tools or review the scoped integration contract, not unapproved map/story data.
- **Manager / reviewers:** architectural and integration review, file-claim arbitration, accepted PR merge, resource and QA evidence triage. One canonical live coordination hub is #15.
- **Owner:** final authority on geography, story, trainers/Gyms, levels, map/section/flag identifiers, new assets and phase production decisions. Phase 2 **may begin**, but it does not make unknown specific creative choices approved.

## Correctness and evidence rules
- **M1 is complete; do not redo it.** Codex's 6,107-result full regression (5,332 PASS + existing expected failures), identical strict baseline, builds and save tests; Claude's Q1–Q5 visual evidence, conditional audio caveat, and Gym 1 badge persistence are preserved in the M1 reports. Source hashes and limitations matter. No new full suite for doc-only changes if exact engine tree is unchanged.
- Track the Game Boy Advance cartridge and save constraints: RELEASE ~6.39 MiB ROM headroom; **84 B** free SaveBlock2; map-section/met-location constraints; unknown maximum dynamic sprite/palette/stack occupancy. Measure every meaningful new linked asset/code increment. Don't infer a full Sinnoh build fits from a planning estimate.
- **Audio listening remains DEFERRED, NOT PASS**, tracked at [QA #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23); retain genuine screenshots, input traces, ROM/source hashes and DEV_FIXTURE distinctions. Do not assert independent human QA or Delta iOS compatibility without proof.
- Do not alter existing protected-file guards, disable workflows, rewrite failure baselines, bypass CI or normal review, or push to shared `main` outside the reviewed PR process. If approval exposes a prior obsolete guard, revise it in a **separate reviewed policy PR**, not by bypassing it. Never force-push shared work, trample dirty worktrees or reopen merged fixes.
- Do not upload copyrighted ROMs/unlicensed sprites or music, actual user save files, private images, credentials or custom friend likenesses. Use asset rights/provenance approvals before inclusion.
- Claim labels truthfully: `SOURCE`, `BUILD`, `NATIVE-TESTED`, `EMULATOR-TESTED`, `DELTA-VERIFIED` are different. An unimplemented area of map/story work is `POST-CONTENT`, not an M1 failure.

## Important scope distinction
Averon is the original custom region and Sinnoh the full second region. Technical preparation and approved content work are now allowed **in principle**; new map geometry, routes, story, Gym order/rosters, progression numbers, legend locations or permanent IDs require concrete owner approval. Existing map/ID guard protections continue until separately updated through reviewed normal process.

## Historical references
Older [M1 parallel plan](Pokemon%20Game/Averon_Codex_Handoff/development/M1_PARALLEL_CLAUDE_CODEX_EXECUTION_20261017.md), [sole-Claude plan](Pokemon%20Game/Averon_Codex_Handoff/development/CLAUDE_SOLE_M1_EXECUTION_20261017.md), prior #15/#46 comments, old #24/#31 taskboards and PR handoffs remain valid *historical evidence only*. They are not current agents' work orders. GitHub comments do not auto-start agents.
