> **OCTOBER 18 PHASE 2 MAP HANDOFF GATE:** The historical unconditional map freeze has been replaced in the manager's scoped policy PR by an **exact per-PR/file signed handoff requirement**, not a blanket removal of protection. Any new/changed permanent map, layout, tileset or reference-map file must have its **literal, exact path** in an Issue #15 `HANDOFF_APPROVED PR=#NUMBER PATHS=comma-separated-file-paths` comment by an authorized owner/collaborator. A directory/glob approval, unrelated PR handoff or informal discussion is insufficient. Existing protected source such as `engine/data/event_scripts.s` must be independently covered in the same exact PR handoff. The handoff must follow concrete owner-approved geography, initial section/ID policy and permitted in-repo asset choices. Do not post approval for unapproved content; the CI check continues to fail closed. No workflow/CI requirement is disabled.
>
> **CURRENT OWNER-APPROVED PHASE (2026-10-17):** Pre-Sinnoh M1 is accepted, the next development phase is authorized, and human audio listening is **deferred / unverified**. For current ownership/scope read [CURRENT_PHASE_AND_HANDOFF.md](CURRENT_PHASE_AND_HANDOFF.md), [TASKS.md](TASKS.md) and live [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). The dated pre-Sinnoh freezes, sole-Claude/Codex-paused routing and pending-Gate-B paragraphs **below** are historical only. **DO preserve** the actual PR/CI/file-guard/protected-path/source-provenance rules below: owner approval is not a bypass of safeguards or approval of undesigned maps, IDs or story.
>
> ---

> **LATEST OWNER EXECUTION POLICY — BACKEND FIRST, NO IDLE WAITING:** [BACKEND_TO_SINNOH_EXECUTION.md](BACKEND_TO_SINNOH_EXECUTION.md) is the detailed authoritative ownership matrix, map-independent completion inventory and fallback ladder. Any older text suggesting Codex must stop TWO-REGION until QUEST merges, Claude must wait to begin LEGEND or a legal disjoint mechanics task, or that every ACK is permission, is historical/superseded. New Sinnoh/Averon maps remain frozen. At each blocked file, QA case or merge, continue fallback within your existing session and revisit only after the documented observable trigger. Do not turn 'backend complete' into endless audit-only work. GitHub comments do not launch agents.

# Pokémon Averon — permanent GitHub operations handbook

**Goal:** keep the repository organized with tiny cleanup at every coding session, not periodic major cleanups. Applies to Codex and Claude as peer co-lead developers, both ChatGPT agents, and other contributors. This is the only active *process* manual. For the division of responsibilities, read [AGENT_ROLES.md](AGENT_ROLES.md) and the live [team hub #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15).

## Current owner directive: parallel development first

**The owner has clarified that frequent Codex/Claude waiting is harming progress.** See [the owner-directed concurrency correction in #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6206878015). This section supersedes older *one-PR-per-developer*, "wait for prerequisite merge before coding" and broad "blocked task" language below **only for independently owned development**. It does **not** waive the creative freeze, shared-source claims, independent QA, protected branch checks or final merge criteria.

- **Develop now, integrate later.** A prerequisite such as QUEST means a downstream feature cannot claim *integrated/playable/merged* status until the upstream feature passes its required checks. It does **not** stop coding, negative native tests, synthetic in-memory fixtures, code review, or branch-local GBA builds for a file-disjoint, approved module. In particular, Codex can harden TWO-REGION's isolated pure branch while #14 awaits graphical QA; Claude can extend SCRIPTED-BATTLE's owned files and build a separately claimed, unplaced generic engine module while #14 awaits integration.
- **No artificial global one-PR limit.** Maintain one **primary** development PR per lead and preferably just one secondary disjoint coding PR when it materially advances the game. An additional narrowly scoped, independent track is permitted **without waiting for another lead's merge or manager permission**. Each feature gets its own branch, exact path claim, tests, and handoff. Avoid duplicate implementations or churn; don't treat this as permission to start every backlog item.
- **Claims are notifications when disjoint.** The developer posts exact paths/functions/IDs, checks the current claims/PRs, then starts an already-approved file-disjoint feature immediately. No need to wait for an "ACK" from another agent if no protected overlap and no reserved creative/architecture decision is involved. Questions are asynchronous; send a directed `AGENT_MESSAGE` and work on independent files meanwhile.
- **Serialize only the collision.** Before touching `event_scripts.s`, `config/battle.h`, `flags.h`, `vars.h`, `save.c`, shared save/badge/region/overworld interfaces or the same generator input/output, obtain the exact exclusive handoff. If that file is busy, do not edit *that file*, but keep implementing/tests in owned nonconflicting files. A temporary integrator branch can rehearse the combination; don't manually copy another agent's commits into `main`.
- **Merge/QA gates remain real.** QUEST #14 needs independent game QA evidence to merge; #25's existing approved two shared-line edits do not permit a simultaneous protected-file merge while #14 is open. Codex and Claude may still prepare and test both modules independently. The `exclusive-files`, `file-guard`, applicable native, save and runtime checks are unchanged. Build results cannot be relabeled as gameplay or Delta acceptance.
- **Creative freeze remains absolute.** No new/temporary production maps, regional geography, story scenes, trainer teams, legendary species/placements, art, saved identifier allocations or other owner-reserved content without separate specific approval. Only already-approved generic mechanics and test data may proceed.

**Block the smallest thing possible:** a protected-file edit, an integrated merge or an actual creative decision—**never an entire developer's coding session** merely because another PR is not merged.

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
3. Otherwise read TASKS.md and the live issue board; start an independently claimed file-disjoint development task even if its *merge* dependency is pending. Only integration and protected-file writes wait for their gates. Respect the currently claimed Codex and Claude scopes; check current PRs and the shared claim thread before modifying any overlapping source. Old branch/ownership references elsewhere in this file are historical.
4. Define a single executable target: expected player behavior, source files, test assertions, and known blockers. Claim by opening a draft PR after the first meaningful commit. Larger independent features may use a GitHub engineering Issue template, but Issues aren't mandatory for tiny fixes.
5. Branch from fresh `main`: `codex/<feature>`, `claude/<feature>`, `chatgpt/<feature>`, or `contrib/<feature>`. Continue an existing PR on its existing branch. Avoid stacked PRs unless a real technical dependency makes them necessary.
6. If one integration or file is blocked, continue any specifically approved, disjoint implementation/testing first. If no safe work exists, report the precise blocker instead of inventing geography/story.

**WIP guidance, not a hard cap:** prefer one primary coding PR plus one useful disjoint secondary track per developer. Do not start redundant work, but do not stop merely because a different PR remains open. Exact protected-file edits still need one writer and a scoped handoff.

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

Every session leaves pushed recoverable work or an exact blocker, not a mysterious private workspace. If a specific file, QA case or merge is blocked, keep progressing your own disjoint tests/code during the same session; don't repeat the same unsuccessful guess. PR comments replace constant shared-doc rewrites.

## 6. Ownership, schedules and maintenance

See [AGENT_ROLES.md](AGENT_ROLES.md) and the live [team coordination issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) for current names, claims, and priorities; these supersede older Codex-only assignment descriptions.

- **User:** creative map/locations, final level curve, final story, major design approvals and release/Delta acceptance.
- **Codex — co-lead developer:** primary owner of QUEST #14 **code, builds, native/automated checks, fixes and integration preparation**, and subsequent TWO-REGION engine/save/progression work; **not responsible for manual mGBA/graphical playtesting right now**. Default shared-backend integration coordinator, not Claude's manager.
- **Claude — co-lead developer:** equal authority to implement substantial independent game systems, tests and engine improvements; owns its explicitly claimed file-disjoint work. May lead major scripted battle, legendary or other backend milestones after coordinated handoff.
- **ChatGPT QA:** **designated owner of manual gameplay/mGBA graphical acceptance**, including QUEST #14, after actual emulator execution access is confirmed; otherwise post the exact access blocker and reproducible test plans. Codex fixes reported defects. The user alone may reassign fallback manual playtesting.
- **ChatGPT architecture/review:** read-only PR, dependency, regression and resource analysis by default, plus scoped validation/docs changes when claimed.
- **Other contributors:** specifically scoped code/assets/tests with verified permission and nonoverlapping files.

**QA gate:** Codex need not manually playtest while an assigned independent QA agent is being established. An unverified visual/interactive milestone remains `EMULATOR-TESTED: PENDING`; keep its PR unmerged until an actual tester supplies required runtime evidence or the owner explicitly changes the gate. Continue nonconflicting work instead of duplicating QA.

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
