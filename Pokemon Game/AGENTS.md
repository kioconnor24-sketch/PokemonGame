# Averon workspace — current operating rules

**Use current GitHub state, not old historical handoffs.** First read `Averon_Codex_Handoff/development/TASKS.md`, then the top of `development/PROGRESS.md`, then `development/WORKFLOW.md`. Relevant design and engine references remain in `Averon_Codex_Handoff/AGENTS.md`, `CODEX_WORK_ORDER.md` and the authoritative backend roadmap, but their historical M0–M2 directions do not override the current task queue.

As of 2026-10-15, `main` includes PR #1 (opening/Gym 1) and PR #9 (backend/tooling/native tests and earlier contributor work). PR #10, `codex/field-licenses`, remains an unfinished Codex-owned gameplay branch, retargeted to `main`. Fetch newest remote state before coding; **do not touch field-license source unless Codex explicitly transfers it**.

User designs final Averon map, settlements, routes and exact quest locations. Eight Averon Gyms, northern Gyms 6–7, volcanic-island Gym 8, full second Sinnoh, Red ultimate canonical opponent; keep traditional cheerful adventure tone with sparse conspiracy scenes. Level 100 max, held-item Gen V EXP Share, forced Set, Megas and following Pokémon; no Z-Moves, Dynamax or Terastallization. No fixed first-League level-76 cap; no guessed level curve. Optional Nuzlocke is paused.

Agents must work on claimed feature branches, prevent file overlap, run targeted tests, compile relevant game changes, distinguish SOURCE/BUILD/NATIVE-TESTED/EMULATOR-TESTED/DELTA-VERIFIED, and push verified commits with exact handoff. Do not publish ROMs or save data. Cloud Debian setup and old Windows/WSL paths differ; inspect the actual environment. Never silently skip failing tests.
