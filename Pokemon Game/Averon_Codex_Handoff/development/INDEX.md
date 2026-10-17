# Pokémon Averon — current documentation index

**Authoritative current read:** [CURRENT_PHASE_AND_HANDOFF.md](CURRENT_PHASE_AND_HANDOFF.md). Milestone 1 is owner-accepted; next-phase technical preparation and specifically approved content development may proceed. The human audio listen is deferred and not considered PASS. Older instructions that say "M1 unfinished", "Codex paused", or "all maps forbidden" are historical.

| Need | Source |
| --- | --- |
| **Current phase / owner decisions / agent ownership / risk limits** | [CURRENT_PHASE_AND_HANDOFF.md](CURRENT_PHASE_AND_HANDOFF.md) |
| Active concrete task queue | [TASKS.md](TASKS.md) · [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) |
| Dependency and production phases | [ROADMAP.md](ROADMAP.md) · [future backlog #26](https://github.com/kioconnor24-sketch/PokemonGame/issues/26) |
| Tested M1 native and build facts | [CODEX_M1_NATIVE_CLOSEOUT_20261017.md](CODEX_M1_NATIVE_CLOSEOUT_20261017.md) · [machine-readable details](../../scripts/coordination/codex_m1_evidence_20261017.json) |
| Tested M1 graphical/owner acceptance | [M1_ACCEPTANCE_REPORT_20261017.md](M1_ACCEPTANCE_REPORT_20261017.md) · [Q1–Q5 evidence](../qa/claude-m1-gameplay/README.md) |
| Sinnoh resource, save/section and mapper study | [SINNOH_TECHNICAL_READINESS_20261017.md](SINNOH_TECHNICAL_READINESS_20261017.md) |
| QA, **deferred audio** and new graphical issues | [Issue #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23) |
| Cross-agent problem reporting | [Issue #55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55) |
| Safe development / review / merges | [WORKFLOW.md](WORKFLOW.md) · [root AGENTS.md](../../../AGENTS.md) · [CLAUDE.md](../../../CLAUDE.md) · [AGENT_ROLES.md](AGENT_ROLES.md) |
| Current source / results | [main](https://github.com/kioconnor24-sketch/PokemonGame/tree/main) · [PRs](https://github.com/kioconnor24-sketch/PokemonGame/pulls) · [Actions](https://github.com/kioconnor24-sketch/PokemonGame/actions) |

## File groups

- **Game source:** `Pokemon Game/engine/` (stable paths; changes require compile/native/ROM evidence).
- **Tools and verifiers:** `Pokemon Game/scripts/` (some paths consumed by guarded workflows; don't move blindly).
- **Visual/QA packages:** `Pokemon Game/Averon_Codex_Handoff/qa/`; provenance does not imply human QA.
- **Design/data drafts:** `design/` and `data/`; provisional until owner explicitly approves.
- **Historical M1 development records (retained):** `BACKEND_TO_SINNOH_EXECUTION.md`, `CLAUDE_SOLE_M1_EXECUTION_20261017.md`, `M1_PARALLEL_CLAUDE_CODEX_EXECUTION_20261017.md`, `M1_EXHAUSTIVE_REMAINING_WORK_20261017.md`, `CHATGPT_MANAGER_*HANDOFF*.md`, `PROGRESS.md`, `READING_LOG.md`, `NEXT_AGENT_COMMANDS.md`, and issue/PR timelines. These preserve past constraints/provenance, **not** fresh assignments.
- **Research and creative working papers:** `ENGINE_RESEARCH.md`, `ENGINE_FINDINGS.md`, `LEVEL_CURVE_RESEARCH.md`, `CHATGPT_QUESTS_AND_PROGRESSION.md`, etc. Do not silently promote speculative ideas to canon.

## Hygiene policy

Old paths, QA screenshots, commits, and issue threads remain in place. Close outdated work items with a link to the signed-off evidence instead of deleting their history. One current owner hub (#15) and one QA hub (#23) avoid multiple contradictory task queues. Update this index only at real milestone transitions; put per-session tests/handoffs on the owning PR or issue.
