@AGENTS.md

## Claude Code specifics

Shared project policy lives in `AGENTS.md` (imported above) and `Pokemon Game/Averon_Codex_Handoff/development/AGENT_ROLES.md`. Keep this file for Claude-only notes; do not copy policy into it.

- **Start of session.** First read live Issue #15 and the map-independent M1 acceptance contract in Issue #46, then current main/PRs/CI and the latest handoff. The generated board #31 is advisory and not an authorization gate. Codex is paused: local Claude is the sole M1 production backend writer, INCLUDING QUEST/two-region/save/region formerly assigned to Codex.
- **Own the work, don't wait for approvals.** Claude may inspect, implement, debug, refactor where necessary, build, run native and actual local mGBA tests on ANY map-independent M1 backend code. Use a private `claude/<feature>` worktree/branch, preserve dirty worktrees, and give an Issue #15 exact-file claim NOTICE when taking a new work area; it is NOT a request to wait for a reply. No broad former-Codex file restrictions remain. Never overwrite an active different agent's branch or push directly to `main`, `codex/*` or `chatgpt/*`. Protected-file approval applies to PR integration/merge, not to isolated development/testing. #25's protected registry merge still follows #14.
- **Where to build.** Use a separate clone that belongs to Claude and build with the existing toolchain (`cd "Pokemon Game/engine" && make -j20 -O all`, then `make -j20 -O check TESTS=Averon`). On the owner's WSL host that clone was observed at `/root/claude-dev/PokemonGame` (2026-10-15); confirm the path in your own environment. Never touch `/root/averon/engine` or another agent's checkout. Claude Code cloud sessions (2026-10-16) have ARM GCC 13.2 preinstalled; the project uses 14.2.1, installable from `developer.arm.com` (its download redirects to `armkeil.blob.core.windows.net`; both must be allowed in the environment's network settings). Where no toolchain is available, use GitHub Actions. Never report `BUILD` or `NATIVE-TESTED` without a build or test run whose output you actually read.
- **Evidence labels.** Use `DEFINED / SOURCE / BUILD / NATIVE-TESTED / EMULATOR-TESTED / DELTA-VERIFIED / BLOCKED` exactly. Claude SHOULD use local mGBA freely for authentic supporting gameplay evidence (real inputs, screenshots, hashes and state); independent Playtest alone grants official gameplay Gate A/B acceptance.
- **Skills.** The shared canonical Averon Agent Skills are merged from PR #19 (`.agents/skills/` plus `.claude/skills/` shims). This file adds none of its own.
- **Graph and memory are hints, not authority.** Current source, live PR heads and CI outrank any code graph, note or remembered summary.
- **Cloud sessions and GitHub.** In Claude's observed cloud runtime on 2026-10-16, GraphQL requests and Action log downloads were blocked, and `gh pr view` / `gh issue view` failed with 403. Verify connectivity and log access in the current runtime. If GraphQL is blocked, use `gh api repos/kioconnor24-sketch/pokemongame/...` (REST) for issues, comments, PRs and check runs; if logs are unavailable, reproduce the failing workflow from its `.github/workflows/*.yml` steps. Commit as `Claude <noreply@anthropic.com>`. Before writing an existing `claude/*` branch, check its remote head: another Claude session (including the scheduled routine) may be pushing it.
- **One `make` per build tree.** Two `make` processes in the same `Pokemon Game/engine` tree corrupt each other's results; use a separate `git worktree` per branch (a fresh one takes about 40 minutes to build on 4 cores).

## Native test pitfalls (found 2026-10-16)

- `SINGLE_BATTLE_TEST` / `DOUBLE_BATTLE_TEST` are recorded **link** battles (`TRAINER_LINK_OPPONENT`): no whiteout money, no in-game trainer behaviour. Use `AI_SINGLE_BATTLE_TEST` / `AI_DOUBLE_BATTLE_TEST` for real trainer battles (opponent moves come from the AI; give it one move and use `EXPECT_MOVE`).
- The runner plays every battle as `BATTLE_TYPE_RECORDED`, and `GetAttackerObedienceForAction` returns `OBEYS` for recorded battles. To test obedience, clear that flag around a direct call in `THEN` and restore it.
- `THEN` sees the post-battle party only if the battle actually ended (a win, loss, run or capture). A battle left running skips end-of-battle code such as `TryRestoreHeldItems`.
- Post-battle Pickup and Honey Gather never fire in the native runner. A full-party capture opens the Gen 7 "party or box" prompt, which the runner cannot answer (it hangs): that case is Playtest's.
- In plain `TEST()`, `PARAMETRIZE` needs a variable named `i`. In battle tests, extra test parameters are fields of `results[i]`, not locals.
- `EXPECT_EQ(f(), x)` evaluates `f()` again when it prints a failure, so a call with side effects shows a misleading value. Store the result first.
- `CreateMon` gives no moveset and leaves HP at 0: set moves and call `CalculateMonStats`.
- A host CI script (`scripts/verify-averon-native-caps.py`) compiles the real `GetCurrentLevelCap` with stubs; a new call in `caps.c` needs a stub there too.
- Prove a new test with a temporary mutation of the code it guards, then revert and confirm `git diff` is clean before committing.

