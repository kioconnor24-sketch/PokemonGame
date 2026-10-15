# Pokémon Averon — instructions for every AI developer

Apply these rules to Codex Cloud, local Codex, ChatGPT and guest agents, regardless of model or conversation history.

**On every session start:** fetch/check real GitHub `main` and open PRs; then read [WORKFLOW.md](Pokemon%20Game/Averon_Codex_Handoff/development/WORKFLOW.md), [TASKS.md](Pokemon%20Game/Averon_Codex_Handoff/development/TASKS.md), and the current heading of [PROGRESS.md](Pokemon%20Game/Averon_Codex_Handoff/development/PROGRESS.md). Check the active PR's latest handoff. Read only relevant portions of the long roadmap and project-specific [AGENTS.md](Pokemon%20Game/AGENTS.md).

**Source of truth:** live `main`/PR heads/CI = actual code state; `TASKS.md` = priorities and dependencies; each active PR and its latest handoff = ownership/working progress; `WORKFLOW.md` = procedure; `PROGRESS.md` = integrated milestones, not a daily journal. Historic handoffs and cached branch names cannot override live GitHub.

**Work selection:** resume your existing unfinished PR before taking the first READY, unclaimed, nonoverlapping task. Codex owns active [field-license PR #10](https://github.com/kioconnor24-sketch/PokemonGame/pull/10) until it changes status. No other agent may overwrite its event/field-move/save sources. Use scoped branches/PRs and developer fixtures instead of inventing user-owned maps.

**Each work session:** implement a testable change; run checks appropriate to the files; push and verify remote SHA; add a concise HANDOFF comment to that PR with tests and the next executable action. Do **not** edit shared TASKS.md or PROGRESS.md every session; the integrator updates them only at real milestone/ownership changes.

**Safety:** no routine direct `main` pushes, no forced shared-history rewrites, no silent merge of unfinished work, no uploaded ROM/save binaries, tokens or unlicensed sprites/music. Build/native tests do not constitute emulator or Delta verification. User decisions supersede documents. GitHub Actions cannot autonomously perform coding fixes.
