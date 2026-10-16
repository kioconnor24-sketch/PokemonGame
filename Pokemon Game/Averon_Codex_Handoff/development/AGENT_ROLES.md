# Pokémon Averon — four-agent engineering roles and GitHub coordination

**Approved by the project owner on 2026-10-15.**
**Shared live team hub:** [GitHub Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15)

This is a permanent onboarding reference for separate Codex, Claude, and ChatGPT sessions. Each session MUST inspect the current `main`, open PRs, issue claims, and latest PR HANDOFF before starting. Historical task queues or old README/AGENTS role claims cannot override live ownership or the owner's newer direction. See [WORKFLOW.md](WORKFLOW.md) for the established PR/CI rules.

**Updated owner instruction — parallel development:** Codex and Claude can develop independent, approved, file-disjoint modules simultaneously even while QUEST QA or other PR merges are pending. Prefer one primary and one secondary coding PR each. A claim on unclaimed, nonprotected files is a notification, not a request to wait for acknowledgment. Only overlapping protected-file edits and integration into main are serialized. Preserve the owner hard freeze, required QA, CI, review, and branch protection. See [current workflow policy](WORKFLOW.md#current-owner-directive-parallel-development-first) and [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6206878015). Earlier one-PR and blanket dependency waiting instructions are superseded only for independent development.

## Four roles: two lead developers and two independent reviewers

| Actor | Authority and responsibility | Current / initial work | Boundaries |
| --- | --- | --- | --- |
| **Codex — co-lead gameplay/engine developer and default shared-backend integrator** | Owns end-to-end implementation, native builds, regression tests, gameplay fixes and integration of shared engine/progression components | Finish QUEST implementation, compilation, automated/native verification, and repair any QA-reported bugs on [PR #14](https://github.com/kioconnor24-sketch/PokemonGame/pull/14); after the separate QA agent confirms real graphical acceptance, integrate and lead TWO-REGION developer-fixture foundation | Owns its active feature files; initially QUEST, then region identification, independent regional badge/save progression, Fly, cross-region travel, heal/whiteout. Must not overwrite Claude's claimed code. |
| **Claude — co-lead gameplay/systems developer** | **Full peer developer**, authorized to design, implement, build, test and own substantial game features and review Codex's work | Claim an independent, genuine coded gameplay/data/move/evolution/follower/battle-mechanics defect or feature; build-test and ship a dedicated PR. Later may lead SCRIPTED-BATTLE, LEGEND or other large modules when ownership/interfaces allow | Does not edit files claimed by Codex, particularly current QUEST and near-term region/save/badge/Fly fields. Shared C headers, persistent IDs or event scripts are serialized by explicit GitHub agreement. |
| **ChatGPT QA — gameplay playtester** | Real player-facing testing, visual bugs, controls, map collisions, dialogue/events, save/reload and repeatable regression scenarios | **Own** actual graphical/mGBA QUEST playtesting, collision/NPC/visual/regression checks and fix verification **once confirmed emulator access is available**; post findings on PR #14 | Read-only on normal production source unless assigned isolated QA tooling. ChatGPT browser GitHub connection alone does not allow it to control Windows mGBA. No fabricated `EMULATOR-TESTED` claims. |
| **ChatGPT review — independent architecture and coordination** | Inspect source dependencies, review pull requests, audit save compatibility/resource risks, coordinate task boundaries, challenge weak tests | Review current QUEST PR and the two-region architecture; review Claude PRs independently | Read-only on major gameplay sources by default. May submit focused doc/test-tooling PR without conflicting with active coding. |

**The two development leads are peers.** Claude is not confined to audits, utility scripts, or minor contributions. Either can own a substantial complete feature within a clear claim. Codex is the **default integration coordinator for shared engine/save changes**, NOT Claude's manager. One designated integrator merges shared work at a time, with normal PR review and owner/repository acceptance. The owner can reassign integration responsibility.

**Owner:** final Averon world map, story choices, numeric level curve, major feature approvals, and final Delta iOS testing. No agent may fabricate final geography, Gym teams, postgame maps or level caps.

## User-approved immediate priority

1. **QUEST**: Codex finishes code/build/native checks and fixes QA-reported defects on PR #14. **ChatGPT QA owns manual graphical emulator acceptance** when actual emulator execution is available. Do not require Codex to personally playtest right now. Keep PR #14 marked emulator-acceptance pending and unmerged until actual QA evidence exists or the owner explicitly changes the acceptance gate.
2. **TWO-REGION**: Codex implements two-region identity; 8+8 independent badges; reversible travel via *temporary* fixtures; correct Fly, healing, whiteout and persistence; save compatibility; builds/native tests and emulator checks. Do not construct real Sinnoh yet.
3. **SCRIPTED-BATTLE**, verified mechanics/data/follower deficiencies, **LEGEND**'s missing encounter semantics, comprehensive integration QA, then owner-approved full world production. Exact later owners are decided by file disjointness and dependencies.
4. **Claude proceeds in parallel** on a disjoint, independently testable real coding assignment from gameplay mechanics or Gen I–IX data/asset integration. It must not just write a duplicate broad audit.

This priority update supersedes the older LEGEND-before-TWO-REGION queue only insofar as authorized by the owner. Follow the `WORKFLOW.md` rule: the integrator changes `TASKS.md` on a milestone/priority change, not per chat session. Always recheck live status.

## How agents communicate through GitHub

**No agent-to-agent automatic communication is assumed.** GitHub is the durable system of record; a chat's local state and installed plugins are not shared with other chats.

### Every session starts with

1. Fetch current `main`, list open PRs/issues, inspect their current SHAs, checks, and changed files.
2. Read repository-root and project-local `AGENTS.md`, `development/WORKFLOW.md`, `TASKS.md`, this file, and the current PR's latest HANDOFF.
3. Resume your own unfinished PR. Otherwise claim a bounded unowned task **in [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) or a linked task issue** before touching source.
4. Compare expected paths and shared identifiers with all active coding PRs. Negotiate overlap in issue/PR comments **before editing**.

### Claim and develop

Post a comment:

```text
CLAIM | agent=Codex/Claude | task=<name> | branch=<name>
Expected code files/directories:
Dependencies / interfaces that overlap other PRs:
Player-observable acceptance:
Build and native/emulator test gate:
```

Use feature branches like `codex/<feature>` or `claude/<feature>`, from fresh `main` when independent; one coding PR per developer. Allow a single separate integration/ops PR at most. Avoid stacking on another PR unless the dependency is explicit and coordinated.

**High-risk shared files** (e.g., `engine/include/constants/flags.h`, `vars.h`, `save.c`, `global.h`, event script registries, region/badge APIs, shared species tables and generated data) are serialized, not edited simultaneously. An explicit handoff or file-disjoint interface contract is needed. Source generators and outputs must remain in sync.

### Report evidence and review

Each feature PR must contain:
- User-observable behavior and scope.
- Actual changed files and dependency links.
- Commit SHA verified on GitHub.
- Successful real GBA compile for engine/source changes.
- Named native test commands with **nonzero** tests and exact pass/fail/skip counts.
- Save compatibility, resource measurements and emulator gaps when applicable.
- Latest `HANDOFF` comment with next executable action.

QA posts defects on the *owning PR* or a linked GitHub issue:

```text
BUG | feature=<name> | source/ROM SHA=<...>
Environment/emulator version and fixture:
Exact reproduction steps:
Expected vs observed:
Screenshots/logs (safe to publish):
Severity and retest result:
```

Architecture reviewer and the opposite development lead may submit independent source-grounded reviews. The responsible feature owner fixes defects. The designated integrator reviews current head, applicable CI and test evidence before merging. No silent automatic merges.

Update `PROGRESS.md` only for integrated milestones; `TASKS.md` for approved priority, ownership, or dependency changes. Avoid repeating session handoffs across many files.

### Manual emulator testing ownership

**Owner clarification (2026-10-15):** Codex does not need to personally perform graphical mGBA playtests now. ChatGPT QA is the assigned manual tester, **not automatically an operational tester**: capability must be confirmed before any runtime claim. Codex still runs compiler checks, automated/native suites and any noninteractive test harnesses it develops, then fixes the QA agent's confirmed defects. A completed build or native test never substitutes for required graphical acceptance. If QA cannot access an emulator, explicitly mark `EMULATOR-TESTED: PENDING / ACCESS BLOCKED` and do not merge an unverified interactive milestone as fully accepted. Codex may prepare distinct unblocked tasks while waiting. The owner must approve any fallback reassignment.

### Evidence tiers and limitations

Use exactly the relevant status: **DEFINED**, **SOURCE**, **BUILD**, **NATIVE-TESTED**, **EMULATOR-TESTED**, **DELTA-VERIFIED**, or **BLOCKED**. Compiling or a native test does not equal running a graphical game. Delta must be tested separately on iOS. Never publish copyrighted ROMs, saves, unauthorized sprites/music, or secrets to a public repo.

**Automation caveat:** GitHub Actions can run builds and tests; GitHub comments cannot independently wake/command every assistant. Codex, Claude and both ChatGPT sessions must be configured to open/check live GitHub on each run, or use separate supported scheduling.

## Concrete startup directions

- **Codex:** own QUEST #14 implementation, builds, automated/native tests and QA-bug fixes. **Manual mGBA/visual playtesting is NOT Codex's assigned responsibility right now**; wait for ChatGPT QA's actual emulator evidence, without marking untested interactions as passing or merging an incomplete acceptance. Continue only genuinely nonoverlapping useful work while awaiting QA, then claim TWO-REGION after QUEST integration. Respect Claude's file claim.
- **Claude:** connect its own GitHub access; read this document and Issue #15; claim real, meaningful, independent gameplay coding work; implement and test it through a reviewable `claude/*` PR. It may later own major scripted-battle or legendary features, not just data work.
- **ChatGPT QA:** designated owner of QUEST manual/mGBA playtesting and graphical acceptance. First confirm actual local app or executable emulator control; test the ROM and post exact source/ROM SHA, pass/fail observations, reproduction evidence and retest outcomes on PR #14. If access fails, report the exact blocker instead of inventing results. Only the project owner can explicitly reassign manual playtesting as a fallback.
- **ChatGPT review:** inspect both co-leads' PRs, maintain evidence-based dependency analysis, flag real integration hazards without duplicate coding.

**Success:** two peer developers shipping distinct, compatible, tested implementations; two independent ChatGPT agents testing/reviewing; one stable `main` and one truthful shared record of what is actually playable.
