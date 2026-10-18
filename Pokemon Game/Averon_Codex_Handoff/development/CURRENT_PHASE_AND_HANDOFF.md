# Pokémon Averon — operating contract
Updated 2026-10-18. This is the single current process and authority contract for Claude + Codex. The owner requested an organizational reset and delegated routine planning, coordination, review and eligible integration to the developers. This document becomes repository policy through its reviewed PR; the reset does not restart paused sessions.

## Read order and authority
1. Read this contract, refresh main, all open PR heads/files/checks, the [integration queue](INTEGRATION_QUEUE.md), and [#15 live claims](https://github.com/kioconnor24-sketch/PokemonGame/issues/15).
2. Resume your existing PR before starting another implementation. Inspect its latest handoff and relevant source, not every old runbook.
3. Explicit owner decisions govern creative scope and permanent identities. Approved source on main governs implemented behavior. Live PR/check/review evidence governs readiness. The queue is a dated index, never a substitute for rechecking GitHub.
4. Dated manager, sole-Claude, Codex-paused, M1 and freeze orders are historical evidence. Their titles, old priority statements, generated board #31 and legacy tasks.json do not create assignments. Preserve their content and links.
5. Existing approved product requirements in design records and nested instructions remain in force unless the owner explicitly revises them. A process reset does not approve draft story or change game design.

## Developer responsibilities
Claude and Codex are peer developers. Each plans bounded work, maintains claims and handoffs, reviews the other's work, diagnoses CI, and prepares eligible normal merges. Neither requires routine manager ACK to proceed on an already authorized disjoint scope.
- Codex normally leads engine/save/region/resource compatibility; Claude normally leads approved maps/content and genuine mGBA QA. These are defaults, not exclusive expertise.
- The developer who did not author the change leads review and may execute its eligible normal merge. Record the author, reviewer, exact reviewed SHA, scope and evidence in a PR review. Shared GitHub login does not establish independence.
- No author self-approval or self-merge. A read-only review pass by the author is useful but is not peer review. If a second developer is unavailable, leave review pending; advance another approved task. A manager may supply a real review, but is not a required routine coordinator.
- A rotating integration steward is chosen by a CLAIM in #15 for one integration batch. The steward refreshes the queue, checks collisions, merges one eligible PR at a time and checks main before the next dependent merge. This does not grant creative authority or permit merging the steward's own unreviewed work.
- Respect existing paused sessions and reserved work. GitHub comments do not launch agents or authorize paid execution.

## Claims and handoffs
Post one scoped claim in #15:
`CLAIM | developer | branch/PR | literal paths | intended outcome | evidence | dependencies`.
Check live PR file lists and existing claims first. File-disjoint approved work proceeds immediately. Serialize the actual collision, including generator inputs and outputs; preserve dirty worktrees and every contributor's commits. Release a claim after merge, explicit transfer or abandonment.
A protected-path change requires a genuine authorized `HANDOFF_APPROVED PR=#N PATHS=literal,comma-separated,paths` matching that PR. No globs or directory-only handoffs. Content/map approval must precede its handoff. Do not fabricate approvals; obey the existing checker and its trusted-author rules.
At a session end, push recoverable work and leave one PR HANDOFF with remote full SHA, files, changes, exact commands and PASS/FAIL/SKIP counts, source/ROM hashes, fixture use, remaining risk, next executable action, and `WAITING_ON / RESUME_WHEN` when blocked. Do not rewrite shared status docs for each test run.

## Risk and review gates
| Tier | Scope | Minimum gate |
| --- | --- | --- |
| R0 | Prose, routing, metadata | Diff and link/evidence review; applicable guards. No ARM rebuild for unchanged engine. |
| R1 | Tests/tools and isolated experiments | Peer diff review, meaningful positive/negative tests, actual nonzero counts; no implied production adoption. |
| R2 | Runtime fixes and approved map content | Peer source review; applicable exact-head CI/native checks, NORMAL/RELEASE and resource/save evidence; actual mGBA for affected visible behavior. |
| R3 | Save format/migration, permanent IDs, protected policy/workflows, release/security | Concrete owner scope decision where reserved; separate scoped peer review and compatibility/negative proof; existing protections stay enforced. |

Tier is about impact, not file extension: executable workflows are R3; a design proposal can be reviewed as a proposal without authorizing construction.

Before merging: refresh both full head and base SHAs, inspect the final diff and collisions, ensure non-draft, verify required checks and every applicable test. A new commit invalidates review of changed content. Choose newest applicable check per workflow/job; a superseded canceled run is not a current failure, but missing/pending/skipped required checks are not PASS. Where integration changes tested behavior, reconcile in the feature branch or verify a disposable combined tree and record exact revisions. Never rely only on a mergeable flag.
Use the normal PR path, preserving history. Never direct-push main, force-rewrite shared branches, bypass rules, disable guards, change failure baselines to hide failures, or merge known failures. Verify main after merge and stop the affected integration lane on a regression. Preserve the prior good commit and repair or revert through a reviewed PR.
After integration, release claims and update the queue at a real status/dependency change. Do not mark a whole feature accepted from a partial test.

## Owner-only decisions
The owner retains geography and reference deviations, route openings, plot/canon, dialogue direction, Gym/trainer rosters, encounters/legendary placement, level curves/caps, art/music rights and personal likenesses, permanent map/section/heal/flag identities, origin encoding precision/migration policy, default cry-profile adoption and final release/Delta acceptance.
Developers present a bounded recommendation with alternatives and implications. They may autonomously implement already approved details, safe generic repairs, tests and tooling; approval of one map is not approval of every route.
Current decisions awaiting the owner are listed once in the [queue](INTEGRATION_QUEUE.md). Routine review, CI repair, claim arbitration and merge eligibility belong to developers.

## Evidence and accepted baseline
M1 was owner-accepted on 2026-10-17; do not repeat it without a reproduced regression. [Native closeout](CODEX_M1_NATIVE_CLOSEOUT_20261017.md): 6,107 outcomes, 5,332 PASS and unchanged strict expected-failure identities, not 6,107 PASS. [Graphical acceptance](M1_ACCEPTANCE_REPORT_20261017.md) records accepted Gym 1 dialogue-screenshot limits. Human audio listening remains DEFERRED, NOT PASS, in [#23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23); Delta remains unverified.
#117 is merged; original cry source is retained and default remains ON. An OFF build's measured size cannot be described as default-ON capacity.
Labels are distinct: SOURCE / BUILD / NATIVE-TESTED / EMULATOR-TESTED / DELTA-VERIFIED. Record actual controller input/screenshots, source + ROM hashes, build profile/toolchain and DEV_FIXTURE use. Native fixtures do not prove ordinary story reachability, natural whiteout or human listening.
Measure meaningful ROM/RAM/save changes on actual builds; historic ~6.39 MiB RELEASE ON headroom and 84 B SaveBlock2 free are constraints, not a promise full Sinnoh fits. Preserve legacy IDs and saves. Do not commit full ROMs, ELFs, private saves, secrets or unlicensed media.

## GitHub organization and automation
- [#15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15): sole live claim/coordination hub; [#26](https://github.com/kioconnor24-sketch/PokemonGame/issues/26): design candidates; [#23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23): QA; [#55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55): evidence-backed blockers. Avoid duplicate boards/issues for the same work.
- The [reset audit](ORGANIZATIONAL_RESET_20261018.md) and [branch inventory](BRANCH_AUDIT_20261018.csv) preserve the reset snapshot. Nothing is deleted based on branch age/name. Squash-merged branches may have unreachable tips; merged PR state alone is insufficient deletion proof.
- No mass branch deletion, stale-PR auto-close, auto-merge, protection changes, scheduled paid agents or automatic restarts. Retain experiment/checkpoint branches until their unique work and evidence are accounted for.
- Active ruleset observed on 2026-10-18 requires PRs, blocks deletion/force pushes, and requires `file-guard` + `exclusive-files`; zero formal approving reviews are configured. Developer peer review remains required by this contract. Classic protection endpoint was inaccessible (403); do not infer protections absent.
- The legacy advisory-board correction is a separate reviewed automation PR. Until merged, its outputs can still be stale. #31 stays archived; automation output never authorizes work.
