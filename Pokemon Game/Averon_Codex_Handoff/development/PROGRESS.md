# Engineering progress (accurate as of design handoff)

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

**Truthfulness guard:** untouched base ROM compiled and booted in mGBA. Averon content is not implemented yet; gameplay/save acceptance is in progress.

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
