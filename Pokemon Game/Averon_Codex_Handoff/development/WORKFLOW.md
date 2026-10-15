# Pokémon Averon — permanent GitHub operations handbook

**Goal:** keep the repository organized with tiny cleanup at every coding session, not periodic major cleanups. Applies to Codex and Claude as peer co-lead developers, both ChatGPT agents, and other contributors. This is the only active *process* manual. For the division of responsibilities, read [AGENT_ROLES.md](AGENT_ROLES.md) and the live [team hub #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15).

## 1. Only one authority for each kind of information

| Concern | Authority | When updated |
| --- | --- | --- |
| Accepted gameplay source | `main` + passing relevant GitHub Actions | Verified PR merge |
| Active task claim and work | OPEN PR, touched-file list, latest HANDOFF comment | Each coding session |
| Next task / dependencies / user blockers | `TASKS.md` | Priority or ownership milestone, NOT each session |
| How to work together | This document and root `AGENTS.md` | Rarely |
| Integrated evidence | Top/current section of `PROGRESS.md` | Integrated milestone |
| Full approved design / backlog | Backend roadmap and approved design files | User/technical decision |
| History | Closed PRs and archived checkpoint sections | Never treated as live direction |

**Anti-conflict rule:** no agent edits TASKS.md or PROGRESS.md just to record another test or token-session restart. Record all working results on the *same* PR. Only the integrator updates shared tracking docs when a task really changes ownership, is blocked long-term, or merges. This avoids recurring collisions like PR #10 vs. the cleanup work.

## 2. Deterministic session start (2–5 minutes, then code)

1. Preserve dirty checkout first. Fetch latest `main` and remote PR state, inspect checks, compare relevant changed files. Local/cloud instances do not share filesystem or chat history.
2. If your own PR is open, resume it. Read its latest HANDOFF and fix applicable red CI. Don't create another PR for the same task merely because a session ended.
3. Otherwise read TASKS.md in priority order; take the first READY task with satisfied dependencies and no file overlap with an active PR. Respect the currently claimed Codex and Claude scopes; check current PRs and the shared claim thread before modifying any overlapping source. Old branch/ownership references elsewhere in this file are historical.
4. Define a single executable target: expected player behavior, source files, test assertions, and known blockers. Claim by opening a draft PR after the first meaningful commit. Larger independent features may use a GitHub engineering Issue template, but Issues aren't mandatory for tiny fixes.
5. Branch from fresh `main`: `codex/<feature>`, `claude/<feature>`, `chatgpt/<feature>`, or `contrib/<feature>`. Continue an existing PR on its existing branch. Avoid stacked PRs unless a real technical dependency makes them necessary.
6. If no task is READY and nonoverlapping, report the exact blocker instead of inventing geography/story, making extra plans, or silently interfering.

**WIP limit:** one coding PR per agent and at most one integration/operations PR. Two agents needing the same `flags.h`, save code, event scripts, or shared asset file must **serialize** the work and communicate in the PR.

## 3. Development and verification

Make a bounded actual source change, then targeted checks. Use real upstream engine APIs, not guessed names or fake placeholder ROMs.

| Work type | Required evidence before describing as complete |
| --- | --- |
| Docs/CI instructions | Changed file review and PR hygiene; don't waste ARM compilation for prose |
| Python audits and scripts | Relevant source tests; explicitly verify nonzero tests ran |
| Engine C, gameplay maps/scripts, moves, species, trainers | Real GBA compile, relevant native test(s) with nonzero count and applicable CI |
| Save layout, progression flags, region travel | Above plus save/load, compatibility, whiteout, rollback/regression cases |
| Following sprites/visual field effects/unique story battles | Emulator gameplay for actual rendered acceptance; test fixtures only prove covered semantics |
| Final game milestone/release | Whole journey + save/reload + separate owner-run Delta iOS acceptance |

Use evidence labels **DEFINED / SOURCE / BUILD / NATIVE-TESTED / EMULATOR-TESTED / DELTA-VERIFIED / BLOCKED**. No test selected or 'No tests found' is a failure, not a green pass. Run inexpensive targeted tests while iterating; reserve full build for a meaningful final change rather than repeating it without modifications. Don't upload full ROMs, saves, secrets, compiled output, or art/music without redistribution rights.

For changes to persistent flags, vars, badge data or save structures: inspect existing allocation, preserve old saves and add explicit save/reload regression coverage. Do not silently renumber identifiers.

## 4. Review, merge and keep main green

- PR = one feature; explain task ID, owner/file scope, base, exact commands/pass/fail/skip counts, save compatibility, remaining emulator/Delta gaps and next action. Use the PR template.
- Always fetch latest base/head before merging. Inspect diff for accidental generated binaries, duplicate integration and overlapping active PRs. Relevant CI must succeed, even if not enforced as a required check by GitHub.
- Prefer normal PR merge preserving history for complicated engine changes; merge completed verified work only. Don't merge unfinished field licenses simply to make the PR list shorter. No force-push on shared branches, no normal direct `main` commits.
- Once merged: release active PR ownership, update TASKS priority only if changed, and write **one** new PROGRESS integration checkpoint. Close superseded PRs with a preservation note only after verifying their commits are already reachable from main. Avoid deleting any unmerged source.
- If an agent added old copies of TASKS/PROGRESS in its feature branch, reconcile them against current `main`; do not restore outdated task directions.

## 5. End-of-session HANDOFF (a PR comment, not a new file)

```text
HANDOFF — task ID, timestamp
PR / branch / verified remote commit SHA:
Implemented this run:
Changed files, possible collision:
Build and tests: exact commands; # passed, failed, skipped:
Evidence: SOURCE / BUILD / NATIVE-TESTED / EMULATOR-TESTED / DELTA-VERIFIED
Unverified interactions / blockers:
Next single concrete action:
```

Every session leaves pushed recoverable work or an exact blocker, not a mysterious private workspace. If blocked, take an unrelated READY task next time; don't consume tokens repeating the same unsuccessful guess. PR comments replace constant shared-doc rewrites.

## 6. Ownership, schedules and maintenance

See [AGENT_ROLES.md](AGENT_ROLES.md) and the live [team coordination issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) for current names, claims, and priorities; these supersede older Codex-only assignment descriptions.

- **User:** creative map/locations, final level curve, final story, major design approvals and release/Delta acceptance.
- **Codex — co-lead developer:** primary owner of current QUEST PR #14 and subsequent TWO-REGION engine/save/progression work; default shared-backend integration coordinator, not Claude's manager.
- **Claude — co-lead developer:** equal authority to implement substantial independent game systems, tests and engine improvements; owns its explicitly claimed file-disjoint work. May lead major scripted battle, legendary or other backend milestones after coordinated handoff.
- **ChatGPT QA:** actual gameplay/emulator acceptance when authorized execution access is confirmed; otherwise evidence review and reproducible test plans, with honest blocked status.
- **ChatGPT architecture/review:** read-only PR, dependency, regression and resource analysis by default, plus scoped validation/docs changes when claimed.
- **Other contributors:** specifically scoped code/assets/tests with verified permission and nonoverlapping files.

Do not presume direct AI-to-AI communication, shared local files, or automatic invocation by GitHub comments. GitHub is the durable claim, PR, bug and handoff surface. Two developers may work concurrently only on nonoverlapping files or agreed independent interfaces; serialize high-risk shared source.

**At each session end:** push, verify SHA, update PR handoff, check generated/secret files absent. **At each merge:** confirm builds, release claim and close truly redundant PR. **Weekly:** the read-only `averon-repo-hygiene.yml` checks last main build, inactive PRs and branch protection; it reports warnings in GitHub Actions. It doesn't merge, delete or self-fix code. Run repository maintenance only on a concrete warning; no weekly mass refactors or extra docs.

**Cost control:** light PR hygiene runs on every PR; full native build runs for relevant engine changes and main pushes; specialized audits are path-filtered; don't run multiple equivalent ARM builds on the same unchanged source. Count playable validated features and green baselines, not generated files or number of commits.

## 7. Failure playbook

| Problem | Action |
| --- | --- |
| Token/session limit | Push checkpoint, add HANDOFF, next scheduled session fetches and resumes same PR |
| Agent source collision | Pause one claim; compare exact PR file lists, serialize changes, preserve both branches |
| PR diverged from main | Fetch/compare; reconcile safely in feature branch, never force-reset another agent |
| Native 'No tests found' | Check mGBA runner execute bit and test filters; require positive executed count |
| Red CI / broken main | Hold merges, preserve last known-good commit, distinguish toolchain/compile/test error and fix in separate PR |
| Flags/save corrupted | Stop migration, test old save compatibility, restore last green code until fixed |
| ROM/RAM usage grows | Measure real resource reports; optimize before introducing speculative hardware hacks |
| User map/story decision missing | Mark PAUSED, use developer-only fixture or take independent task |
| Missing art/music rights | Do not copy the external asset; use authorized placeholder |
| PR unchanged >14 days | Weekly workflow warns; don't auto-close (AI usage may be exhausted) |

## 8. One-time GitHub owner controls (cannot be enabled by markdown)

Owner: repository **Settings → Rules → Rulesets** (or Branches protection) → create a branch ruleset targeting **main**. Require PR before merge; block force pushes and deletion. Do not require a second reviewer if the owner works alone. Require the always-running check **Averon PR hygiene / file-guard** once its name is verified in GitHub; native build uses path filters and must NOT be globally required, or docs-only PRs may get stuck. Agents must voluntarily enforce passing applicable native checks.

Optional Settings → General → Pull Requests → **Automatically delete head branches** for merged PRs. Unmerged work stays; don't prune historic branches unless each head is reachable from main. Until GitHub shows a live protecting ruleset, this is a documented standard, **not a technical guarantee**. Cloud scheduling/AI usage is separate from GitHub Actions.

## 9. When map design is approved

The user provides district topology/entry exits, travel gates, route landmarks and Gym order. Convert **one** district at a time to a separate playable map PR with collision/warp/save/backtracking acceptance. Work through Averon, full Sinnoh, postgame and ultimate Red battle without destabilizing the backend fixture tests.

This process should remove most routine cleanups; it cannot guarantee zero bugs, zero human approvals or unlimited AI execution.
