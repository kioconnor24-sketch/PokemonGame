# Repository preservation audit — 2026-10-19

Codex. Engineering completed first: #162 merged `bc55711215126fc5f6f95e3ea2875f92ceb356ab`; #163 pushed with8/8 focused and301/301 full native PASS, actual NORMAL/RELEASE builds and independent source review requested. This is the owner's subsequent **non-destructive** branch/workflow/distribution audit. No branch, release, asset, historical comment, workflow or policy is deleted/changed by this PR. Main for this frozen audit is `bc55711215126fc5f6f95e3ea2875f92ceb356ab`.

## All165 branch snapshots, with squash-aware proof

The dated157 count is superseded by **165 live branches** captured before this audit branch was created, with145 PR receipts. Full inputs/SHAs/explicit active and retained lists are in [JSON](CODEX_BRANCH_RECOVERY_INPUTS_20261019.json); exact per-branch classifications, proof SHAs, changed paths and deletion recommendations are in [CSV](CODEX_BRANCH_RECOVERY_AUDIT_20261019.csv). The audit branch itself is outside that frozen count. Refresh live heads/claims before any later removal.

| Classification | Count | Disposition |
| --- | ---: | --- |
| ACTIVE | 5 | Retain main, current engine PR and Claude's current map/respawn/Twinleaf branches |
| HISTORICAL_CHECKPOINT | 13 | Retain explicit proof/checkpoint branches and attached worktrees |
| INTEGRATED_WITH_NO_UNIQUE_WORK | 131 | Precisely the CSV rows with `deletion_candidate=True`; eligible **recommendations only**, no deletion performed |
| UNIQUE_UNMERGED_WORK | 4 | Preserve literal unmerged differences; may be superseded, never automatically restore them |
| UNKNOWN | 12 | Preserve; receipts/history insufficient for safe removal despite measured feature-path differences |

Of131 recommendations,73 tips are directly reachable in main history and **58 are proven using squash/merge receipts**, not rejected merely for nonancestry. A squash proof requires the exact PR head, its integration commit reachable from main, and all feature-path contents **and modes/deletions** present at that integration snapshot. Later intentional main edits do not erase the earlier integration receipt. Missing objects, combined/conflicted results, post-merge branch work, protected/default/active branches and explicit checkpoints never authorize deletion. The tool never fetches/pushes/deletes/merges or changes refs; the audit separately fetched remote heads into a local frozen namespace, without pruning old refs.

Four literal unmerged candidates require preservation, not another automatic integration attempt:

- `chatgpt/emulator-smoke-playtest`, PR20, `e46beacf003fe8052697751cef44539b2d22747a`: QA controller differences.
- `manager/combined-build-manual-only-20261016`, PR69, `ac541660e12a64468fdec1cc63304f5af9d10691`: existing manual-only combined-build proposal/tests; reuse rather than recreate.
- `manager/pr48-full-native-proof-20261017`, PR82, `1ee7b36a08d7d6e3acd562d04799a22cda391425`: historical workflow absent from current main.
- `manager/qa-clinic-heal-contract-20261016`, PR71, `f34eab2184c40a7f6ab1bd74274c3058c7c0fdc9`: QA controller differences.

`UNIQUE_UNMERGED_WORK` here means literal feature-path differences backed by an unmerged PR, **not proof the feature is missing from today's game**. Current replacements/acceptance must be compared before recovering code. UNKNOWN rows likewise are not assignments to restore obsolete engines. Active/checkpoint rows deliberately bypass deletion analysis; their zero path counters do not certify an empty diff. No mass cleanup command is supplied.

Reproduce on a clone containing the pinned commit objects:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s 'Pokemon Game/scripts/tests' -p test_averon_branch_recovery.py -v
PYTHONDONTWRITEBYTECODE=1 python3 'Pokemon Game/scripts/audit-averon-branch-recovery.py' \
  --inputs issues/CODEX_BRANCH_RECOVERY_INPUTS_20261019.json \
  --csv /tmp/branch-recovery.csv
```

**10/10 temporary-Git native-host tests PASS**: true squash, changed combined result, later main replacement, post-merge work, active/protected/checkpoint priority, missing object, ancestral history, unmerged-but-accounted scope, executable mode, and deletion mismatch. Actual165-row audit completed with zero Git errors. These are Python/Git tests, not GBA native tests; existing source CI syntax checks do not automatically discover this new module. Unknown/missing evidence stays nondeletable. Machine inputs and CSV are included rather than requiring trust in a branch name or an ancestry-only summary.

## All21 current workflow definitions;22 registered with GitHub

GitHub reports22 active registrations, but main contains21 workflow files. The extra registration is `.github/workflows/averon-pr48-full-native-rehearsal.yml`, preserved on the unmerged PR82 branch. Its API state does not establish that it executes on main. Do not disable/delete anything on that assumption.

| Workflow file stem (`.github/workflows/*.yml`) | Current scope / finding |
| --- | --- |
| `averon-agent-board` | Read-only PR/claim/daily advisory; no stale board writes or agent restart. Ordinary nonclaim comments yield skipped jobs. |
| `averon-combined-build` | Generic validated two-PR/main-only manual runner already exists; stale14/25 defaults and exact comment trigger remain. See bounded proposal below. |
| `averon-coordination-tests` | Host routing/guard tests; explicitly still reads legacy tasks.json and asserts historical HARD FREEZE output. Keep that fixture consumer intact until reviewed replacement. |
| `averon-documentation-integrity` | Link-checker fixtures and relative links; retain independent docs coverage. |
| `averon-engine-readiness` | Source/config/event/cap function checks; does not replace full native ROM regression. |
| `averon-evolution-native-build` | Manual historical evolution build; no routine trigger cost. Review archival purpose before retiring. |
| `averon-graphics-audit` | Host graphic/species/path/follower audit; keep asset-specific checks. |
| `averon-integration-rehearsal` | Manual disposable integration; no routine build duplication. |
| `averon-level-economy` | Host trainer/evolution/source economy audit; relevant only on matching paths. |
| `averon-map-registry-contract` | Fast source ID/capacity mutations, not a second full GBA build. Keep. |
| `averon-native-build` | Actual NORMAL ROM, save headroom and full Averon native filter on engine changes; retain production/negative coverage and main integration verification. |
| `averon-optional-agent-pilot` | Manual plus explicit variable/secrets gate. No automatic restart; no settings changed or pilot launched. |
| `averon-qa-observer-unit` | QA observer/controller unit cases; current retained historical fixture consumer. |
| `averon-quest-support-q3` | Special-purpose graphical Q3 support; preserve old evidence, review current relevance/branch condition before future edits. |
| `averon-release-config-parity` | Preprocessing/host production configuration mutations. **Not an actual RELEASE ROM build**; retain alongside real feature-specific RELEASE evidence. |
| `averon-rendered-playtest` | Real graphical observer/smoke on QA paths/manual; preserve honest gameplay boundary. |
| `averon-repo-hygiene` | Required file-guard plus independent weekly read-only audit. Weekly SKIP on PR events is intentional, not failed coverage. |
| `averon-scripted-core-rehearsal` | Fast preflight fixtures on changes; expensive manual path still insists PR25 is open, so obsolete after integration. Archive/generalize only through reviewed CI change. |
| `averon-shared-file-guard` | Required exact-path/protected-source gate using trusted main; retain unconditionally. |
| `averon-solo-evolution` | Targeted host evolution reachability audit; not duplicate native execution. |
| `averon-source-checks` | Syntax plus selected explicit host suites. Newly added regression modules are not automatically all discovered; any expanded wiring needs time/coverage measurement and reviewed CI change. |

Observed latest100 API runs:36 queued,1 running,63 completed; **13 combined-build and10 advisory runs skipped**. These are bounded snapshot counts, not monthly costs. Queued does not mean PASS, and the queue's cause is unverified. Do not bypass required checks or remove their coverage to make the list shorter.

Highest-value reviewed follow-up: reuse PR69's existing manual-only implementation/tests; remove only combined-build issue-comment fanout, set safe explicit main-only0/0 defaults, retain arbitrary distinct same-repo open PR inputs and exact SHA pinning. `run_combined_build.sh` already validates numeric inputs, same-repo/open state and fetched head equality; no competing integration runner is needed. Keep its read-only permissions, no remote writes and no ROM/save uploads. Run/adapt the preserved positive/negative dispatch tests and obtain independent CI review. This PR proposes that change, **does not adopt it**.

Do not treat all PR→main reruns as waste: integration may combine other source. Consider compiler/tool caches with toolchain/TEST/RELEASE/CRIES-aware keys, not cached acceptance or private saves. Measure before consolidating host jobs. Protect `file-guard`, `exclusive-files`, actual production regression and security boundaries.

## Practical template, tasks.json and navigation proposals

Current PR template still leads with a TaskID and gives every PR emulator/Delta checkboxes. Proposed compact replacement: problem/result; risk tier + actual path claim; exact source/head; applicable tests with pass/fail/skip and explicit unverified limits; required owner identity/protected handoff/peer review only when applicable; next executable action. Do not imply Delta is routine approval for a host-tool PR, or that smaller text waives graphical requirements for gameplay changes. No template/governance change is made here.

`tasks.json` is **not unused**: `averon-coordination-tests.yml` loads it into a synthetic snapshot, passes it to `render_board.py`, then asserts historic freeze/routing strings. The live advisory says this legacy registry is not authority. Safe next treatment is a historical label plus preserved fixture/consumer provenance, with a separately tested governance/CI update before moving any path. Deleting/moving it now would break a real consumer.

Issue15/26/55 headers retain old reset/M1 snapshots; prepare a minimal dated navigation banner linking [current contract](../Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md), [master roadmap](../Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_MASTER_PRODUCTION_ROADMAP.md), live PRs and latest developer handoff, identifying old reset PR144/145 as merged. Preserve the old bodies/comments and owner decisions; no policy rewrite or new board. These are proposed navigation corrections, not silently edited owner instructions.

## Public release and provenance — actual facts and limitation

Public `v1.0`: release413284705, published2026-10-14T23:59:34Z by repository owner, empty description, target field`main`; tag actually pins `97aa51dc2c282c5c3f933f13d94411fa4a706a90`. Attachment642074913, `Pokemon.Game.zip`, **745541366 bytes**, API digest `sha256:568e9022eb134aa9ef23f8a54a4a049d2d435a49c2302169ab7c2799739fe848`, zero downloads at scan. That is pre-M1 history, not this session's tested build. Empty metadata establishes no intended purpose or rights.

A bounded HTTP Range request for ZIP central-directory metadata returned **HTTP501 Not Implemented**. No full745MB download was attempted. **Archive contents and digest were not independently verified**; do not call it a source-only snapshot or a confirmed game ROM from its filename. Next owner/distribution action: inspect the central directory in an environment that supports it and clarify provenance/intended distribution; recommend holding further distribution approval until reviewed. Do not delete or alter the release/asset without the owner's decision.

Repository metadata is public, description/homepage/license fields are null. Engine README identifies RHH pokeemerald-expansion1.17.1 and inherited pret decompilation; CREDITS/tool-specific licenses exist, but no root/engine-wide license grant was found. The asset ledger has only **one inherited-baseline row**, explicitly saying redistribution rights are not established. Credits/source availability are not a blanket grant for all graphics/music/third-party material. This is an evidence/provenance gap, not a new legal conclusion or permission to remove assets.

Three committed `.gba` files are explicitly included by existing multiboot assembly, rather than new complete Averon builds. Preserve until separately reviewed:

| Source resource | Bytes | SHA256 |
| --- | ---: | --- |
| `engine/data/mb_berry_fix.gba` | 15348 | `f3d87e14688faf0190b33e071607887c7783462b45f92f1cb7135eec56260740` |
| `engine/data/mb_colosseum.gba` | 163840 | `d133d340ce7507932bcb3a83f9ee1dd9905072763d493b66db20e1bde4304572` |
| `engine/data/mb_ereader.gba` | 12512 | `e50d06841b3485282bf772f1cfe2988da2bb476eb26ff5337b467af8a60bdf07` |

Main has34044 tracked blobs. Largest is historical `Pokemon Game/evidence/m0/base-build.log`,4644473B, SHA256 `e6369e732b8f72e0efbbefdd1de686a521216613f780b4477c1d8560c1629a61`; other large items include upstream tutorial GIFs, bundled native runner and generated Pokémon data. No private-key/.env filename candidates matched the current guard pattern; **no comprehensive content secret scan is claimed**. Preserve hashes/provenance and scope any compression/artifact/archive cleanup separately; do not blindly delete logs, binaries or duplicate-looking evidence.

## Next executable work

All audit inputs,165-row recommendations, tool and10 passing tests are reviewable together. This is isolated R1 host tooling/evidence, with no CI/governance/release changes. After latest applicable checks, normal Fast Lane A integration is eligible. Separately: obtain peer review/current CI for #163 and integrate normally when eligible; reuse PR69 for a scoped tested manual-trigger CI proposal; inspect the12 UNKNOWN branches without restoring old features; preserve Claude's active maps and run bounded compatibility tests after their actual integration. No saved-origin encoding,218 allocation, story or performance acceptance is implemented by this audit.
