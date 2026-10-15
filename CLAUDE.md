@AGENTS.md

## Claude Code specifics

Shared project policy lives in `AGENTS.md` (imported above) and `Pokemon Game/Averon_Codex_Handoff/development/AGENT_ROLES.md`. Keep this file for Claude-only notes; do not copy policy into it.

- **Claim before editing.** Post a `CLAIM` comment in issue #15 (format in `AGENT_ROLES.md`) before touching shared source. Work on a `claude/<feature>` branch; never push to `main`, `codex/*` or `chatgpt/*`.
- **Where to build.** On the owner's WSL host, Claude works in its own clone `/root/claude-dev/PokemonGame` and builds with the existing toolchain (`cd "Pokemon Game/engine" && make -j20 -O all`, then `make -j20 -O check TESTS=Averon`). Never touch `/root/averon/engine` or another agent's checkout. Claude Code cloud sessions have no ARM toolchain or mGBA, so use GitHub Actions there. Never report `BUILD` or `NATIVE-TESTED` without a build or test run whose output you actually read.
- **Evidence labels.** Use `DEFINED / SOURCE / BUILD / NATIVE-TESTED / EMULATOR-TESTED / DELTA-VERIFIED / BLOCKED` exactly. Manual mGBA playtesting is ChatGPT QA's job once emulator access is confirmed.
- **Skills.** The shared canonical Averon Agent Skills come from PR #19 (`.agents/skills/` plus `.claude/skills/` shims), after comparison with Codex's tooling claim. This file adds none of its own.
- **Graph and memory are hints, not authority.** Current source, live PR heads and CI outrank any code graph, note or remembered summary.
