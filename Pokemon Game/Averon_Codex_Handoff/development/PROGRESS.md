# Engineering progress

## Current checkpoint — 2026-10-15

- Direction: BACKEND FIRST. User owns world design. Do not create final towns,
  routes, Gym puzzles, legendary locations, encounters or cap numbers.
- Branch: codex/field-licenses, PR10 targeting codex/backend-integration (PR9).
  Current field source d1395442f3e11efcd539c14590d6fda67aa4ad85 pushed; remote verified.
  Main unchanged; opening/Gym1 preserved. PR2/3/4/5/6/7/8 contributor heads
  integrated with original history. No direct developer messaging occurred.
- Task1: integrated baseline BUILT / NATIVE-TESTED locally and in clean CI. Root cause of PR5 No tests found: runner Permission denied (Git
  mode100644); restored100755 and added test-x guard. No tests skipped.
- Task1 clean CI38696580924 passed native compilation and headless tests on
  baseline3318b59c. Other source/graphics/evolution/economy checks also green.
- Task2 IN PROGRESS: native permissions for all seven field licenses, saved
  flags0x30–0x36, healthy non-egg partner selection without learned HMs,
  contextual script/Surf integration and a party FIELD KIT submenu.
  Native29/29 and layout4/4 PASS at evidence/builds/20261015T070904Z/.
  Developer-only field lab added with Cut/Rock Smash/Strength and Surf pool;
  debug Script4 entry, grant/revoke controls and return to Saltmere. No new
  final-world locations. Release preprocessing excludes its entry/grant code.
  Latest lab normal build exit0 at evidence/builds/20261015T071739Z/; no
  redundant native rerun after map-only changes. Static15 maps,201 lines and
 75-file authoring PASS. Menu/obstacle/animation traversal NOT playtested.
  Stable integrated ROM preserved separately; Task2 is not marked complete.
- Tests:26 named Averon native tests PASS, including new Linking Cord resolver
  checks for Karrablast/Shelmet and incomplete-save backup/recovery; four native
  save-layout tests PASS. Contributor source/host fixtures PASS (log
  evidence/backend-source-tests.log). Static14 maps,196 dialogue lines and
 70-file repeated authoring PASS. Optional quest overlay survives regeneration.
- Build: make-j12-Oall exit0. Local build-output/Pokemon-Averon-Test-Build.gba,
 33554432 bytes, SHA256 ea651ca5feb9e03ad06902e594841591818498b92292dbf13434d49e405db5c0.
  Stable copy: evidence/backend/averon-integrated-baseline.gba. Prior clinic
  ROM retained: evidence/m2/averon-clinic-stable.gba (b1ef8077…f5a7a8).
- Runtime limits: full first-Gym natural walkthrough, new clinic/quest UI,
  evolution animation/item acquisition and Delta remain unverified. Source
  and native resolver tests do not prove these interactions. M2 not complete.
- Ownership: Codex integration/field licenses/events/quests/scripted battles/
  region persistence; ChatGPT battle/species/evolution/forms/followers; friend
  assets/support. No overlapping species edits beyond reviewed PR7 integration.
- Next: (1) Task2 paired Dive/Waterfall fixtures and Fly destination coverage;
  (2) focused native/overworld tests for menu, cancel, follower and traversal;
  (3) Task3 reusable quest templates after Task2 acceptance. Do not invent maps.
- Existing continuation ACTIVE Oct15 07:30 EDT, then every5½hours. Automation
  prompt now carries this backend-first order. Computer/app must remain awake.
- Numeric caps, including former League76, remain provisional/unapproved.
  Preserve level100 maximum; no new cap guesses. Do not repeat setup/audits.
## Historical checkpoints (superseded by the current record above)

- Accepted remote: `a844b3b2481d5ee817f61137383f163c6d483124` on `main`;
  fetched successfully. No other branch or open PR observed at inspection.
- Active branch: `codex/first-gym-verification`; repository project prefix
  `Pokemon Game/`. Shared ownership is in `TASKS.md`.
- Clinic now calls the native nurse prompt/animation/follower flow; compiled, UI runtime pending. A native flash test verifies previous-slot recovery after an incomplete newest save and successful subsequent saving.
- Implemented: Saltmere/Coastal Meadow/Windrow opening; Orchard Lane,
  Alderfield clinic/shop/irrigation Gym; Set, badge caps and Mega-only gating.
- Built: M2 `make -j$(nproc) -O all`, exit 0; `evidence/m2/build.log`.
  Local ROM SHA256 `6c037b81d10e9ef14517bdac033bffef399b7268be6f437a4406cd25fe20f983`.
- Tested in mGBA 0.10.5: Snivy errand/decline/award; native save/reload;
  follower; corrected Renn Fennekin battle; Bunnelby capture; Windrow berries;
  Orchard Lane transition; Exp. Share gift and native assignment to Bunnelby;
  Oran Berry assignment to Snivy. See `qa/OPENING_TEST_RESULTS.md`.
- Unverified: other starter branches/edge cases; M2 battle EXP/caps, Gym
  puzzle/badge/TM, clinic whiteout/PC, Mega runtime, natural balance, Delta.
- New developer fixtures replace upstream debug Script 1/2/3 with cap,
  legal Mega and six-member EXP parties. Incremental build exited 0; runtime
  tests pending. QA SHA256 `0ce5bab776eb44adab514e0589ea38b7ab9b477ddb97e640a2032fcfee22e62f`.
  Preserve the
  natural native save before selecting them; never count fixtures as balance.
- WSL `/root/averon/engine` retains local source changes and working build
  caches; no toolchain reinstall needed. Windows source and backups preserved.
- Next three tasks: build fixtures and test EXP/cap; test Gym and recovery;
  run legal Mega test. Finish these before expanding production geography.
- GitHub push verification is recorded with the resulting feature commit;
  a local commit alone does not mean remotely backed up.
- Workflow update: source coding/static checks/compilation take priority;
  manual emulator testing is deferred by user instruction. ChatGPT may attempt
  runtime tests with the local compiled artifact; capability is not established.
- Continuation scheduled in this chat for October 15 at 02:25 and 09:00 EDT.
  Then every 5½ hours anchored at 09:00 EDT. Local computer must be awake with
  app running. No paid reload, credit purchase or manual usage reset allowed.
- Remote feature checkpoint `c7049ccca24c02e6db42183c41e227923d38e45a`
  pushed and verified with `git ls-remote`. Engine tree matches accepted main:
  `2a56dd29f6c60ed5aa21b006e0388d71eb859702`; migration already preserved it.

Older entries below are historical; they do not override this checkpoint.

| Milestone | State | Evidence required |
|---|---|---|
| M0 Toolchain and reproducible untouched build | Built | Ubuntu/toolchain ready; base build exit 0; ROM running in mGBA; gameplay/save tests in progress |
| M1 Saltmere starting town + starter routes | Built | Saltmere ROM compiled exit 0; native maps/scripts authored; emulator checks in progress |
| M2 First Gym vertical slice and battle rules | In progress | Alderfield/route/Gym/clinic/shop authored; build and runtime checks in progress |
| M3 Eight-Gym Averon production maps and quests | Not started | Map review, quest log, full traversal checks |
| M4 All major story events incl. coup and finale | Not started | Save states and story event regression tests |
| M5 Sinnoh map and progression integration | Not started | Full second-region functional walkthrough |
| M6 Gen IX national dex + forms + mechanic audit | Not started | Per-species/variant manifest, capture/evolve tests |
| M7 Legendary quests, frontier/circuit and Red | Not started | Reachability/capture/flags and battle QA |
| M8 Visual/audio polishing, credits, localization | Not started | Asset ledger, screenshots, licensed/allowed audio |
| M9 Complete QA, Delta test and patch release | Not started | Emulator + iPhone Delta results and release checklist |

**Truthfulness guard:** base and custom content compiled and ran in mGBA;
partial acceptance passed. The complete game and Delta acceptance are unfinished.

### Current execution checkpoint

Ubuntu 26.04.1 installed after Windows restart. ARM GCC 14.2.1 and GNU Make
4.4.1 installed using upstream dependencies. Linux checkout at
`/root/averon/engine`, detached at the recorded SHA. `make -j$(nproc) -O all`
(20 CPUs) exited 0. Full log: ../../evidence/m0/base-build.log.
ROM: ../../evidence/m0/base-emerald.gba, 33554432 bytes,
SHA256 4ac97b2d70cbb550f1f912303f441b0a6f66a81816ea0b5dc824933aa5e06e1e.
mGBA 0.10.5 is running the ROM; startup/intro rendered at about 60 fps.
Native-save and first trainer battle still pending. Lua input helper prepared
at ../../scripts/mgba-smoke.lua; no game RAM writes or cheats.
User requests continuous development with frequent on-disk checkpoints;
keep testing gates but do not stop merely at a milestone boundary.

Saltmere first build now succeeds (evidence/m1/build.log). Local test ROM
evidence/m1/averon-saltmere.gba has SHA256
6f66b71ff51aea4e7d8a7af20be6bf9885ae730b4edc758c3df43150ab5af787.
Implementation source saved in engine commit 02c3cf5839, with subsequent fixes
being tested. Native static map checks pass. mGBA has loaded this custom ROM;
new-game, starter, follower, trainer and save tests remain in progress.

## Session 2026-10-14 — M0 setup

### Continuation: installer boundary resolved, restart required

- Diagnosed missing Windows administrator token even outside sandbox.
- Explicit RunAs installer succeeded: WSL 3.0.3 and VirtualMachinePlatform
  installed, exit 0. Windows requires restart. Transcript saved in
  ../../evidence/m0/wsl-admin-install.log; helper in ../../tools/setup-wsl.ps1.
- Downloaded/extracted official portable mGBA 0.10.5 and executed SDL version
  command successfully. Hash and executable path recorded in ENVIRONMENT.md.
- Confirmed upstream pin unchanged and no tracked game-code differences.
- Next: user restarts Windows, then resume Ubuntu/dependencies, build and
  real mGBA smoke tests. No ROM compiled; M1 remains Not started.

### Initial session

- Extracted original handoff; read requirements/design/data/QA (READING_LOG.md).
- Cloned official source into workspace engine/ and recorded exact pin in
  ENVIRONMENT.md. No game code or feature defaults changed.
- Static design validation passed with exit 0; evidence in
  ../../evidence/m0/design-lint.log.
- Recorded actual default caps, followers, held-item EXP Share, generations,
  gimmick flags and native script examples in ENGINE_FINDINGS.md.
- WSL installation failed twice with exit 1. Both current MSYS2 and Cygwin
  instructions explicitly report unsupported builds. Full command outcomes
  are in ../../evidence/m0/session-log.md.
- No compiled ROM; all emulator tests NOT RUN, including save, reset,
  battles, audio, warps, followers and EXP. Delta NOT RUN.
- Next task: complete host WSL/Ubuntu setup, install documented dependencies,
  compile untouched source and execute the M0 smoke-test sequence in mGBA.
  M1 remains Not started until the M0 development-emulator gate passes.

Changed project paths: root AGENTS.md/.gitignore; this progress file;
development/ENVIRONMENT.md, ENGINE_FINDINGS.md, READING_LOG.md, DECISIONS.md;
data/asset_license_ledger.csv; evidence/m0/. Original creative documents preserved.

Readiness recheck: WSL still cannot start; no Ubuntu distribution installed. Windows reports a pending component restart. Last boot was 2026-10-14 05:36:20, before the recorded WSL installation at 15:22. M0 remains blocked pending restart; no build or ROM test claimed.

