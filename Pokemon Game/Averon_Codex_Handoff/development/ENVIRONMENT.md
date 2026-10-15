# Build and environment record — to fill during M0

Base repository URL: https://github.com/rh-hideout/pokeemerald-expansion
Base repository commit SHA: 73b3fbeb574327cd9420c89e56bef5aa3c08fead
Local checkout: ../../engine (relative to this document); engine/ from workspace root
Host OS: Microsoft Windows NT 10.0.26200.0
Git: 2.53.0.windows.3
Toolchain: Ubuntu 26.04.1 under WSL2; ARM GCC 14.2.1; GNU Make 4.4.1; libpng/newlib installed
Base ROM provenance: USER-SUPPLIED/LOCALLY OWNED WHERE REQUIRED; NOT INCLUDED
Build command: make -j$(nproc) -O all (nproc = 20), exit 0; evidence/m0/base-build.log
mGBA emulator version: portable 0.10.5; base and custom ROM execution verified; focused acceptance remains in progress
Delta iOS build/version: NOT TESTED
ROM SHA256: 4ac97b2d70cbb550f1f912303f441b0a6f66a81816ea0b5dc824933aa5e06e1e
ROM size: 33554432 bytes; evidence/m0/base-emerald.gba (workspace-relative)
Linux build checkout: /root/averon/engine, detached at pinned SHA

GitHub feature publishing checkout: workspace `shared-repo/`, branch
`codex/first-gym-verification`; project prefix `Pokemon Game/`. Root workspace
retains the pre-migration history and active authoring source at `engine/`.
Use `scripts/reconcile-shared-checkout.py` for changed-source synchronization;
do not commit the old workspace tree directly over the differently laid-out
remote. WSL remains the persistent incremental build/test environment. Only
changed source files are copied there, retaining its compiler/build caches.
Native automated battle/script testing now executes through bundled
mgba-rom-test-hydra/mgba-rom-test, independently of the Windows GUI emulator.

Windows restart completed 2026-10-14 15:27. Ubuntu installed with
`wsl --install -d Ubuntu --no-launch`. Documented packages installed with
apt-get as the distribution root user; exit 0. Actual package log and versions
are in evidence/m0/toolchain-install.log and toolchain-versions.log.
The Linux checkout has no tracked modifications after the base build.
The old setup-boundary notes below are historical, not current blockers.

Follow the pinned revision's official build docs; do not copy out-of-date sample commands blindly. The first `make` and emulator smoke test are M0 acceptance gates.

## Setup boundary — 2026-10-14

### Latest result (supersedes original failure below)

Explicit Windows `Start-Process -Verb RunAs` successfully launched the installer
with `Administrator: True`. The earlier sandbox elevation did not provide an
administrator token. `tools/setup-wsl.ps1` captured the installation transcript
at `evidence/m0/wsl-admin-install.log` (workspace-relative paths).

WSL 3.0.3.0 installed, kernel 6.18.54.1-1. VirtualMachinePlatform enablement
succeeded. Installer exit 0, with explicit requirement to reboot Windows.
No restart initiated. `wsl --list --verbose` reports no installed distributions.
After reboot, install Ubuntu with `wsl --install -d Ubuntu`, finish first-run
account setup, then install the documented compiler dependencies. Check WSL2
startup; the pre-reboot virtualization warning is not proof of a firmware issue.

mGBA portable archive from https://mgba.io/downloads.html:
https://github.com/mgba-emu/mgba/releases/download/0.10.5/mGBA-0.10.5-win64.7z

Archive SHA256: B497A57C7D9093834DADC64F33A90F7C411439C21FDB8A0143255A45EA37563A.
Extracted to `tools/mgba/mGBA-0.10.5-win64/`.
`mgba-sdl.exe --version` executed successfully and reports 0.10.5
(26b7884bc25a5933960f3cdcd98bac1ae14d42e2); evidence/m0/mgba-version.log.
This verifies executable startup/version only, not emulation or a working ROM.

### Original attempt

Both `wsl --install -d Ubuntu --enable-wsl1` and `wsl --install` exited 1
even after elevated tool requests. Output says WSL is not installed. This
does not prove the underlying Windows account had an administrator token.
No reboot was initiated. See ../../evidence/m0/session-log.md.

Resume by completing WSL installation in an Administrator PowerShell using
the pinned `engine/docs/install/windows/WSL.md`; restart if Windows requests
it and finish Ubuntu's first-run account setup. User must handle any system
authentication. Verify `wsl --list --verbose` before attempting a build.

Pinned upstream dependency command (NOT RUN):

```bash
sudo apt update && sudo apt upgrade
sudo apt install build-essential binutils-arm-none-eabi gcc-arm-none-eabi libnewlib-arm-none-eabi git libpng-dev python3
```

Then verify compiler versions and use the documented `make -jN` command,
capturing stdout/stderr and exit code. N comes from `nproc`. Preserve the
untouched source pin for the baseline; record any Linux build-copy location.
Hash the resulting pokeemerald.gba only after successful compilation.
Install/verify mGBA and record actual title/new-game/overworld/trainer/menu/
native-save/reset evidence. Delta remains a separate user iPhone test.

Bundled Python used for design lint:
`C:/Users/kioco/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.
