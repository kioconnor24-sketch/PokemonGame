# Organizational reset audit — 2026-10-18
Scope authorized by the owner: audit and organize GitHub, delegate routine developer planning/coordination/review/integration to Claude + Codex, preserve code/history/evidence, and use reviewed PRs for repository changes.

## Snapshot and methods
Main `8967b05b951c63dca9ffa39325ac53f240e3d9ba`; 11 open PRs (#133–#143), four open issues (#15/#23/#26/#55). #117 is already merged at `456a45016446c8b103f373b2d7b6fe082cd757c7`; no cries implementation needs reopening.
Read live repository metadata, all open PR metadata, exact-head check runs, submitted reviews and inline comments, PR handoffs, all #15/#55 comments, 125 PR records across two pages, and 143 branch refs across two complete nonempty pages plus an empty third page. Direct ancestry was checked from fetched Git commit objects. Review-thread resolution was not independently queried; no inline review comments existed on the open PRs. No production build or gameplay test was rerun for this documentation/operations audit.
The prior ChatGPT reference contained user intent but its assistant responses were unavailable content references. No missing assistant plan was treated as evidence or instruction.

## Findings and remediation
| Finding | Remediation |
| --- | --- |
| Root/nested entrypoints, TASKS, roles and workflow disagree about Codex pause, map freeze, PR #117 and manager authority | One operating contract at existing CURRENT_PHASE_AND_HANDOFF path; short redirects at active process entrypoints; dated historical banners; original replaced authority texts copied under archive/reset-20261018 |
| Latest developer checkpoints are richer than top-level status | Exact full-head queue with observed checks, proposed cross-reviewers, owner-only decisions and concrete integration blockers |
| No submitted reviews on any of the 11 open PRs | Keep review pending; assign peer-review roles in queue; green CI is not approval |
| #133 body still describes draft/shim work despite ready metadata and final evidence | Queue records current ready status and final handoff; update its stale description through GitHub metadata hygiene |
| #143 runtime fixture verification incomplete | Preserve draft and genuine 4/6 first-run disclosure; require committed 6/6 rerun |
| Old board generator writes closed #31 from stale M1/sole-Claude registry | Separate R3 automation PR proposes live read-only PR summary with no issue writes or agent execution; do not claim active until merged |
| Old branch names look stale | Exact SHA/PR/ancestry CSV, retain all branches and code; no mass deletion |
| Protection metadata can mislead | Active [ruleset](https://github.com/kioconnor24-sketch/PokemonGame/rules/25210165) requires PR + file-guard/exclusive-files, blocks deletion/force; no bypass actors. Classic protection GET returned 403. No settings changed |

## Branch inventory
[CSV](BRANCH_AUDIT_20261018.csv) covers all 143 pre-reset branches: main 1; open-PR 11; other ancestor tips 78; merged-PR but nonancestor tips 34; unmerged/experimental tips 19. Counts precede new reset branches.
A nonancestor tip may reflect squash integration; it is not automatically abandoned work. Ancestor status does not prove all branch evidence can be discarded. Every row's action is retain. No code/history/branch deletion is proposed in these PRs.

## Completed versus pending
This audit and queue are a reviewable repository proposal until merged. Live issue #15/#26/#55 and archived #31 navigation updates can take effect independently and explicitly identify the pending PR links. Original issue bodies are preserved in a linked audit comment before editing; historical comments/edits remain.
No source PR, doc PR or automation PR is auto-merged by the reset. No protection is weakened, baseline changed, agent restarted, paid API configured or new creative decision made.
The doc and automation PRs require real peer review of their exact heads and passing applicable CI before adoption. This is a developer review gate, not a new owner permission queue. Source PRs remain available for scoped peer review in the [queue](INTEGRATION_QUEUE.md).
Owner decisions remain Route 201 geometry/deviations/section/connections/grass, Route 202 reference versus schematic/defer, Sandgem permanent respawn allocation/coordinates, future origin format/precision, audio default adoption and release/human/Delta acceptance. Review/testing/normal merge work does not require another owner creative approval.
