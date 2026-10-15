# Pokémon Averon

Source for the Pokémon Emerald Expansion-based **Pokémon Averon** Game Boy Advance project. The eventual owner-tested `.gba` targets Delta iOS; do not publish complete copyrighted ROMs. Native source lives in [Pokemon Game/engine/](Pokemon%20Game/engine/).

## Live development entry points
- [Task queue / ownership](Pokemon%20Game/Averon_Codex_Handoff/development/TASKS.md) — which task to work on next, and who owns it.
- [Current progress checkpoint](Pokemon%20Game/Averon_Codex_Handoff/development/PROGRESS.md) — read latest section at **top**, not historical entries.
- [Codex + ChatGPT workflow](Pokemon%20Game/Averon_Codex_Handoff/development/WORKFLOW.md) — branches, handoffs, CI, merges, and daily hygiene.
- [Backend-first roadmap](Pokemon%20Game/Averon_Codex_Handoff/development/AUTHORITATIVE_BACKEND_FIRST_ROADMAP.md) — engineering requirements and longer-term stages.
- [Instructions for coding agents](AGENTS.md).

`main` includes the early playable content / Gym 1 and integrated backend contributions (PRs #1 and #9). **PR #10 is unfinished, Codex-owned field-license development** and should remain separate until tested. Recheck GitHub: these references may be superseded by newer work.

**Scope:** full original Averon plus full second-region Sinnoh; lively traditional Pokémon adventure, reusable quests and events, modern mechanics and following Pokémon. The user is designing the geography; agents must not invent or lock final towns, level caps or legendary placement.
