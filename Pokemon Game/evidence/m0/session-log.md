# M0 execution record — 2026-10-14

## Continuation

- Outside-sandbox administrator-token check returned False; WSL absent.
- Start-Process wsl.exe with Verb RunAs returned PID 21220. No exit captured
  from that first direct launch; no success claimed from process creation.
- Transcript helper launched via RunAs (PID 2264) confirmed Administrator True.
  `wsl --install` installed WSL 3.0.3 and enabled VirtualMachinePlatform,
  exit 0. Windows explicitly requires reboot. See wsl-admin-install.log.
- `wsl --version` reports 3.0.3.0, kernel 6.18.54.1-1.
  `wsl --list --verbose` exits 1: no distributions installed yet.
- Official mGBA download initially failed sandbox DNS; authorized network
  retry succeeded. `tar -xf` extracted portable 0.10.5 successfully.
- `mgba-sdl.exe --version` ran successfully; mgba-version.log contains output.
  This is not a ROM test. Archive hash is recorded in ENVIRONMENT.md.
- `git -C engine rev-parse HEAD` remains the pinned SHA; `git diff --stat`
  empty. No game source changes or ROM build made.

## Initial session

Tool-output transcription; no build or emulator evidence exists yet.

1. Extracted the user ZIP into Averon_Codex_Handoff. Exit 0.
   ZIP SHA256: BB6F970B1BB00F700E51D9AB9CB141E0F352963F1946440309D8D0BA6AFF832E.
2. `git clone https://github.com/rh-hideout/pokeemerald-expansion.git engine`
   sandbox attempt exit 1: `getaddrinfo() thread failed to start`.
   Authorized network retry completed exit 0 (30215 files checked out).
3. `git -C engine rev-parse HEAD`, exit 0:
   `73b3fbeb574327cd9420c89e56bef5aa3c08fead`.
4. `wsl --list --verbose`, exit 1: Windows Subsystem for Linux is not installed.
5. `wsl --install -d Ubuntu --enable-wsl1`, elevated tool request, exit 1:
   Windows Subsystem for Linux is not installed; run `wsl.exe --install`.
6. `wsl --install`, elevated tool request, exit 1: same message.
   Neither attempt establishes installation success or restart readiness.
7. Bundled Python ran `Averon_Codex_Handoff/scripts/validate_design.py`, exit 0.
   Exact output saved in design-lint.log. 24 locations, 36 edges, eight Gyms,
   33 legendary arcs, 12 example habitats passed static validation.

`make` and `mgba` were not found on PATH. WSL is unavailable. Compilation,
title, new game, overworld, first trainer battle, menu, save/reset and Delta
are all NOT RUN. No generated ROM size/hash/screenshot is available.
