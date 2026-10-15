---
name: averon-build-verification
description: Compile Averon engine changes and verify executed native regressions, save layout and exact ROM provenance.
---

Read the recorded ENVIRONMENT and active PR HANDOFF. Reuse the persistent WSL
checkout; `scripts/build-averon.ps1 -Sync <changed engine paths> -NativeTests
-SaveLayoutTests -Jobs 12` is the desktop wrapper. Sync the actual changed source,
including new files, rather than rebuilding stale WSL inputs. In Linux use
`make check -j12 TESTS=Averon`, `make check -j12 TESTS=test/save.c`, and
`make -j12 -O all` as appropriate. A selected suite with zero executed tests fails.

Record pass/fail/skip counts and linker ROM/EWRAM/IWRAM sizes. Those are not peak
heap measurements. Preserve the last successful ROM on failure. After committing,
verify compiled inputs against committed source, ROM size/SHA256 and remote SHA.
Keep binaries/saves local. Compilation and native mGBA tests do not establish
graphical or Delta acceptance. Do not run ARM builds for prose-only changes.
