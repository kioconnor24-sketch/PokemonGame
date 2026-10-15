@AGENTS.md

## Claude Code specifics

Shared project policy lives in `AGENTS.md` (imported above) and `Pokemon Game/Averon_Codex_Handoff/development/AGENT_ROLES.md`. Keep this file for Claude-only notes; do not copy policy into it.

- **Claim before editing.** Post a `CLAIM` comment in issue #15 (format in `AGENT_ROLES.md`) before touching shared source. Work on a `claude/<feature>` branch; never push to `main`, `codex/*` or `chatgpt/*`.
- **Cloud sandbox limits.** Claude Code cloud sessions have no ARM toolchain (`arm-none-eabi-gcc`), no mGBA GUI and no PyPI/npm access. GitHub Actions is the compile and native-test run for engine changes. Local Python checks work. Never report `BUILD` or `NATIVE-TESTED` without a green CI run you actually read.
- **Evidence labels.** Use `DEFINED / SOURCE / BUILD / NATIVE-TESTED / EMULATOR-TESTED / DELTA-VERIFIED / BLOCKED` exactly. Manual mGBA playtesting is ChatGPT QA's job once emulator access is confirmed.
- **Skills.** Project skills are in `.claude/skills/`: `averon-repository-orientation`, `averon-build-verification`, `averon-event-validation`, `averon-playtest-handoff`.
- **Graph and memory are hints, not authority.** Current source, live PR heads and CI outrank any code graph, note or remembered summary.
