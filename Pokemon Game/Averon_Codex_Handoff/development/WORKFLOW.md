# Pokémon Averon collaboration workflow — keep it clean after each session

This document is the **operating procedure**, not a second backlog. `TASKS.md` is the live queue, `PROGRESS.md` top section is the checkpoint, and `AUTHORITATIVE_BACKEND_FIRST_ROADMAP.md` records long-range engineering/design requirements.

## Session start (bounded preflight, then code)

1. Check `git status --short` to preserve local changes. Fetch/prune remote branches and inspect `main`, active PRs and current CI. Cloud, WSL and GitHub-only agents do **not** share a filesystem.
2. Read `TASKS.md`, the top of `PROGRESS.md`, and these procedures. Open other docs only if required for the selected task. Do not run broad repository audits every session.
3. Select the **first READY unclaimed** task from `TASKS.md`. Never work on files another agent owns: FIELD/PR #10 is Codex's. If ownership is uncertain, check real remote commits and leave a PR comment rather than guessing.
4. Define a one-feature executable deliverable, affected file scope, and acceptance checks. Use small isolated developer maps for systems whose final region geography is user-owned.
5. Continue the existing task branch or create a new `codex/<task>`, `chatgpt/<task>` or `contrib/<task>` branch from current `main`. Prefer direct branches off `main`, not multi-level stacked PRs.

## Programming / verification loop

- Work on real engine source, not another planning document. Reuse native Emerald Expansion mechanisms.
- Make bounded changes, run targeted source tests, then relevant native tests + a real GBA build before declaring ENGINE functionality built. Verify **nonzero executed native test count**. Full manual gameplay and Delta are distinct later acceptance tests.
- Evidence labels: **DEFINED / SOURCE / BUILD / NATIVE-TESTED / EMULATOR-TESTED / DELTA-VERIFIED / BLOCKED**. Never claim a higher validation level without performing it. Preserve one last working baseline if a change breaks a build.
- Commit and push good checkpoints; verify remote SHA. One PR per feature. Do not commit .gba/.nds ROMs, saves, build cache, tokens, copyrighted soundtracks or borrowed sprites lacking usage rights.
- PR includes purpose, ownership and changed paths, test commands/results, save/flag effects, what is untested, and next actionable step. Aim for small diff except when generated engine data legitimately requires more files.
- Re-fetch before merge. Merge only completed reviewed changes into stable `main` with appropriate CI green. No force-push to shared refs. **Do not merge unfinished PR #10 just to clear the queue.**

## Tiny end-of-session cleanup (mandatory)

1. Push valuable progress (unfinished code remains in its scoped branch), verify exact SHA; do not claim a local commit is remote.
2. Update `TASKS.md` only when owner/status changed, and the **top/current section** of `PROGRESS.md` with tested counts, pending runtime validation, and next executable step.
3. Check that new PR's files don't overlap someone else's scope; do not leave generated ROMs/secrets in Git.
4. If another PR was fully absorbed by a merge, comment where its commits live and close it; leave historic branch unless safe removal has been separately approved.
5. If blocked, state exact failure and choose the next unrelated READY task. No more than one coding PR per agent plus one integration PR.

**Weekly 10-minute review:** inspect open/blocked PRs, ownership claims, main CI, duplicated workflows and stale docs. Update existing current files instead of adding another summary. Do not run daily expensive full builds for unchanged game source.

## Roles

- **User:** final Averon geography and creative approvals, wild encounter locations, levels, map intake, Delta verification.
- **Codex Cloud/local:** FIELD first, then QUEST, LEGEND, BATTLES and REGIONS; engine/event/save files exclusively when claimed.
- **ChatGPT via GitHub:** independent data, battle/evolution/follower tests and integration/CI. It does not autonomously run when chat closes; GitHub history is the handoff.
- **Friend Codex:** separately claimed art/assets/tests only; no silent shared-header edits.

No implicit synchronization between agents. Communication is via GitHub PRs/comments and committed task/progress records.

## Failure-response decision rules

| Failure | Response |
| --- | --- |
| Token/session limit | Commit + push recoverable state; record remote SHA, exact failing/working tests and next subtask. |
| PR moved / merge divergence | Fetch/compare before integrating; do not reset or force-push another agent's history. |
| Flag/save change | Audit existing identifier allocations and add persistence/rollback tests; never casually renumber existing saves. |
| "No tests found" | Check executable runner mode, selected TESTS and test discovery; a successful compile is not a test pass. PR #9 corrected the old runner permission error. |
| Red CI | Separate environment, native compile and test failure; fix root cause rather than skipping the check. |
| ROM/RAM capacity | Measure actual build and runtime limits, keep last good ROM; do not drop Sinnoh or change level max without user. |
| Unapproved region/quest choice | Use dev fixture; mark placement PAUSED; do not fill creative gaps by guessing. |
| Missing external graphics/music permission | Pause that asset, use licensed placeholder, track permission/attribution before use. |

## Automated checks

`.github/pull_request_template.md` captures PR tests and handoffs; lightweight `averon-repo-hygiene.yml` blocks full ROM/save uploads and warns about outsized PRs. The main `averon-native-build.yml` runs actual engine compile/tests on engine changes and `main` merges, cancelling superseded runs. Legacy dedicated evolution compile is manual-only, because native engine checks now cover its source. Data/source audits stay path-filtered.

These checks are advisory to process unless a repository admin enables branch protection/rulesets in GitHub Settings. If protection is not configured, **developers must voluntarily refuse to merge red CI**. Do not claim protection is enabled without verifying it.
