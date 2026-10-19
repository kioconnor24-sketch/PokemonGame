> **Exact temporary ownership clarification, 2026-10-17:** Owner transferred paused Codex's reversible cries safety/audio **PR #117** to **Claude**, now the sole active writer of those paths and `qa/claude-cries-off/`; see [manager's current restart](CHATGPT_MANAGER_ACTIVE_HANDOFF_20261017.md) and [Claude's audio runbook](CLAUDE_CODEX_CRIES_TAKEOVER_20261017.md). Any Codex restart must check live #15 claims and be assigned disjoint work. The manager reviews source/CI/gameplay evidence and may merge only an independently reviewed, actually eligible PR, without racing Claude. Story owners must read the [provisional dossier](../design/STORY_DEVELOPMENT_WORKING_DOSSIER_20261017.md) before implementing any rival/villain/Sinnoh beats. The role table below describes general lanes, NOT permission to resume overlapping current work.

# Pokémon Averon — current responsibilities

**Owner approval 2026-10-17:** M1 pre-Sinnoh backend accepted; Phase 2 permitted with audio listening postponed. [Current-phase operating guide](CURRENT_PHASE_AND_HANDOFF.md) is authoritative. Older sole-Claude / Codex-paused / four-agent M1 matrices are historical, retained in earlier Git commits and dated runbooks.

| Actor | Active role | Primary caution |
| --- | --- | --- |
| **Owner** | Approves specific playable slice/map plans, story/canon, Gyms, level curves, saved IDs, asset rights; accepted M1 and deferred audio. | Generic phase go-ahead **does not** finalize unspecified creative or technical ID decisions. |
| **Codex** | Technically complex map/section/save/ROM/RAM/budget architecture and the eventual approved integration, one scoped PR at a time. | Avoid duplicating completed M1 or Claude's content/QA branch; do not silently allocate permanent IDs. |
| **Claude** | Approved playable content development and real local mGBA graphical QA/verification with persisted saves and visual evidence. | No independent human-audio PASS from nonzero RMS, no unapproved map/story writing or invented visual evidence. |
| **ChatGPT manager/reviewer** | Coordinates disjoint claims, examines source/CI/resource/acceptance, performs eligible normal integration, resolves true blockers and updates canonical status at milestones. | Do not invent dependencies, bypass protections, or call a native-only test graphical proof. |
| **Other QA/human tester** | Optional independent gameplay/Delta and deferred soundtrack/effects listening. | A historic Playtest agent is not automatically active; QA authority and actual tested device must be explicit. |

## Where work happens
- [#15 ownership and collaboration](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), [#26 future roadmap](https://github.com/kioconnor24-sketch/PokemonGame/issues/26), [#23 graphical/audio QA](https://github.com/kioconnor24-sketch/PokemonGame/issues/23), [#55 problem desk](https://github.com/kioconnor24-sketch/PokemonGame/issues/55).
- [Current task queue](TASKS.md), [roadmap](ROADMAP.md), [technical Sinnoh planning](SINNOH_TECHNICAL_READINESS_20261017.md).
- [Workflow and GitHub protections](WORKFLOW.md), [root rules](../../../AGENTS.md), [Claude-specific rules](../../../CLAUDE.md).

**Concurrent work:** exact file-disjoint new claims may proceed without arbitrary approval delays; protected/shared modifications require coordinated review and CI. Claims are notifications, not permission to bypass authorizations for specific content. Historical PR/issue evidence and accepted M1 reports remain intact.
