---
name: averon-event-validation
description: Use when reviewing scripted story events, optional quests, flags and persistence.
---

# Validate quests and event flags

1. Read the actual script, prerequisites, reward calls and persistent flags in the current source.
2. Trace normal completion, repeated interactions, blocked prerequisites, full Bag and full party retry, save/reload, whiteout and map transitions.
3. Check flag ID collisions and preserve existing flag/save meanings. Serialize edits of shared script registries and headers.
4. Write or run deterministic positive-count native checks for covered semantics; record which cases remain only source-reviewed.
5. Request independent mGBA tests for player-facing dialog, interaction facing, collision, actual reward delivery and reloading.
6. Create a reproducible PR finding with source SHA and status PASS/FAIL/UNTESTED.

## Authority

Current code and live PRs override past notes and generated indices. Follow root/project AGENTS.md, development/AGENT_ROLES.md, WORKFLOW.md and issue #15. Preserve existing developer claims.
