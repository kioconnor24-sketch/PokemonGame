# W25 current-baseline DEV preparation — 2026-10-27

Branch: `codex/w25-current-runtime-20261027`. Source implementation: `3906f1a12b99447f38afa2f117ba664f19896914`; combined-main source: `b8a298d9eb869f5c22d5845184e40e2826dc162b`.

Reuses #317's original two-map conversion, nine donor seam pairs and receipt without rebuilding geography. `prepare_current_runtime.compose(repo)` returns 63 source files for a disposable scene. It writes nothing and supplies no production installer. Current main's 30-map prefix is preserved, with nine temporary maps appended (39 total). The pinned 22-map profile is retained; other engine trees fail closed.

The legacy Oreburgh recipe could not append to current main: it had 19 slots and used Gate warp 1 for the east exit. Production warp 1 and block word 163 now belong to the B1F ladder. The adapter retains both, appends the temporary east exit at warp 2, and updates only the staged City's return. The old recipes/native source remain intact. Generated native expectations reflect the composed connection count and add explicit ladder checks.

## Actual evidence

- Cycling host regressions: **23/23 PASS**, including 11 new positive/negative adapter tests; tested against the 30-map production engine tree `63d0c037e0da9a93b5e1a968c078d9622b56c691`.
- Real source `World`/`static_audit` on an isolated filesystem view of the composed Eterna–Route 206–Route 207–Oreburgh City scene: **0 findings**. Report: private `w25-current-source-static.json`.
- Actual Emerald map-group generator ran on the 39-map source fixture; isolated healing JSON remained byte-identical. Generated header SHA256: `8029a69dcae0de659b18bbf4e7fc26052471aa64e51ad86cfff8002f62e78d5a`.
- **Four ARM syntax checks PASS**: both generated C fixtures, with NORMAL and RELEASE definitions, GCC 14.2.1 and the engine's APCS ABI. Used the real generated 39-map header and existing unchanged type headers. This is not linking or native execution.
- #334/#335 fixes are on main: ordinary planning and follower observation no longer treat a current arrow-warp input as a harmless step. #335 merge: `eec3efd4b9e053583fff97855ab1aaf13a4df7cb`.

## Not yet verified / next executable task

No new NORMAL/RELEASE ROM or gameplay acceptance is claimed. #317's original **32/34** traversal failures remain disclosed. Prepare a marked disposable checkout on the exact 30-map tree, install the returned source files using the existing guarded DEV process, run native checks and actual NORMAL/RELEASE builds, then rerun the original traversal and game-written Save → fresh-process Continue with main's corrected QA tools. Preserve originals and exact ROM/source/flash identities.

Workspace free space was about **260 MiB**; reuse completed scratch space and reclaim only verified redundant generated artifacts before a full build. No ROMs, saves or unlicensed art are in this change. A future production prefix/City integration requires explicit source reconciliation rather than dropping the pin or overwriting an existing map.
