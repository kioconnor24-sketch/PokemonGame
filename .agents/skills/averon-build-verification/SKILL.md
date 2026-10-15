---
name: averon-build-verification
description: Use after a scoped engine or tooling change when build confidence is needed.
---

# Verify builds and native tests

1. Identify branch, exact head SHA, changed files and build instructions from repository workflow; do not invent build commands.
2. Run actual target Game Boy Advance build for engine changes. Record exit code, produced artifact metadata, and build warnings/errors.
3. Run relevant native/host test suites, confirm nonzero test discovery and exact pass/fail/skip counts. Check save ID/layout when affected.
4. Inspect CI for same commit; distinguish local results from CI results.
5. Do not label a change EMULATOR-TESTED without an actual runtime session, nor DELTA-VERIFIED without an owner-run iOS test.
6. Do not commit ROM, save, linked binaries, credentials, or unauthorized copyrighted assets.

## Authority

Current code and live PRs override past notes and generated indices. Follow root/project AGENTS.md, development/AGENT_ROLES.md, WORKFLOW.md and issue #15. Preserve existing developer claims.
