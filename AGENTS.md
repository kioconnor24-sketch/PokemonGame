# Pokémon Averon — instructions for every AI developer

Apply these rules to **both co-lead developers (Codex and Claude)**, both ChatGPT agents (playtesting QA and architecture/review), and any future contributor, regardless of model or conversation history.

**Four-agent role and ownership contract:** Read [AGENT_ROLES.md](Pokemon%20Game/Averon_Codex_Handoff/development/AGENT_ROLES.md) and the shared [team coordination issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). Codex and Claude are **peer lead developers** authorized to implement substantial features on their own nonoverlapping branches. Codex currently owns the active QUEST PR's code/build/native testing and is the default shared-backend integration coordinator, not Claude's manager. **Manual mGBA/graphical playtesting belongs to ChatGPT QA after verified emulator access, not Codex right now.** Outstanding graphical acceptance remains pending until actually performed. ChatGPT architecture/review handles independent engineering and PR oversight.

**On every session start:** fetch/check live GitHub `main` and open PRs, their changed files and newest `HANDOFF` comments; then read [WORKFLOW.md](Pokemon%20Game/Averon_Codex_Handoff/development/WORKFLOW.md), [TASKS.md](Pokemon%20Game/Averon_Codex_Handoff/development/TASKS.md), the current heading of [PROGRESS.md](Pokemon%20Game/Averon_Codex_Handoff/development/PROGRESS.md), and project-specific [AGENTS.md](Pokemon%20Game/AGENTS.md). Read only relevant portions of the long roadmap. Treat older task priority/owner references as historical when contradicted by current owner decisions in issue #15 or live PRs.

**Source of truth:** `main`/current PR heads/CI = actual code; latest claimed PR + HANDOFF = work ownership; `WORKFLOW.md` = procedure; `TASKS.md` = stable queue and dependencies; `PROGRESS.md` = integrated milestones. Owner-approved newer changes in issue #15 take precedence over outdated queue snapshots until the integrator synchronizes them.

**Work selection:** resume your existing unfinished PR first. Otherwise claim a high-value, genuinely unowned, file-disjoint task in issue #15 or a dedicated linked issue. A CLAIM must identify affected paths, dependencies and test gate **before any shared source edit**. Codex and Claude must not edit each other's claimed files; serialize saved flags, badge/save code, event registries and shared generated inputs. Do not invent user-owned maps or final level/story choices.

**Each coding session:** implement an actual scoped change, run appropriate positive-count tests and real GBA builds for engine changes, push/verify remote SHA, and leave a concise HANDOFF comment on the same PR. Do not repeatedly edit shared `TASKS.md`/`PROGRESS.md` as session logs. For major release claims, distinguish BUILD / NATIVE-TESTED / EMULATOR-TESTED / DELTA-VERIFIED.

**Safety:** no routine direct `main` pushes, no force-rewriting shared history, no silent merge of unfinished work, no uploaded ROM/save binaries, tokens or unlicensed sprites/music. CI/native tests are not graphical emulator or Delta acceptance. GitHub comments don't themselves awaken other agents. User decisions supersede old documents.

This branch preserves an unmerged Codex tooling trial for comparison only.
PR #19 is the recommended canonical skill set; do not merge this competing set.
See [preserved trial results](Pokemon%20Game/Averon_Codex_Handoff/development/CODEX_TOOLING_TRIAL.md).
