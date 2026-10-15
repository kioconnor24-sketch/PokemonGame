# Preserved Codex trial — superseded entry point

Do not adopt this entry point: use the reviewed CLAUDE.md from PR #18 with
the canonical skills from PR #19. This file is retained only for comparison.

Read AGENTS.md and its linked AGENT_ROLES/WORKFLOW and live issue #15. They are
the canonical policy and claims; this file does not define a competing workflow.
Claude and Codex remain peer co-leads. ChatGPT QA owns manual playtesting.

Shared reusable workflows live in `.agents/skills/averon-*/SKILL.md`.
`Pokemon Game/scripts/setup-agent-skills.ps1` exposes the same directory to
Claude's `.claude/skills` without copying policy. Read relevant skills only.
Graphify is an optional local navigation aid; inspect current source when results
are incomplete, stale or surprising. No strict graph gate or lifecycle hook is
required. See `Pokemon Game/Averon_Codex_Handoff/development/CODEX_TOOLING_TRIAL.md`.
