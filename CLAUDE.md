@AGENTS.md

## Claude Code specifics

Shared project policy lives in `AGENTS.md` (imported above) and `Pokemon Game/Averon_Codex_Handoff/development/AGENT_ROLES.md`. Keep this file for Claude-only notes; do not copy policy into it.

- **Start of session.** Read the live agent board, [issue #31](https://github.com/kioconnor24-sketch/PokemonGame/issues/31), then your own PR's newest `HANDOFF`. The board is a snapshot; issue #15, PRs and CI stay authoritative.
- **Claim before editing.** Post a `CLAIM` comment in issue #15 (format in `AGENT_ROLES.md`) before touching shared source. Work on a `claude/<feature>` branch; never push to `main`, `codex/*` or `chatgpt/*`.
- **Where to build.** Use a separate clone that belongs to Claude and build with the existing toolchain (`cd "Pokemon Game/engine" && make -j20 -O all`, then `make -j20 -O check TESTS=Averon`). On the owner's WSL host that clone was observed at `/root/claude-dev/PokemonGame` (2026-10-15); confirm the path in your own environment. Never touch `/root/averon/engine` or another agent's checkout. A Claude Code cloud session observed on 2026-10-15 had no ARM toolchain or mGBA; where that holds, use GitHub Actions. Never report `BUILD` or `NATIVE-TESTED` without a build or test run whose output you actually read.
- **Evidence labels.** Use `DEFINED / SOURCE / BUILD / NATIVE-TESTED / EMULATOR-TESTED / DELTA-VERIFIED / BLOCKED` exactly. Manual mGBA playtesting is ChatGPT QA's job once emulator access is confirmed.
- **Skills.** The shared canonical Averon Agent Skills are merged from PR #19 (`.agents/skills/` plus `.claude/skills/` shims). This file adds none of its own.
- **Graph and memory are hints, not authority.** Current source, live PR heads and CI outrank any code graph, note or remembered summary.
