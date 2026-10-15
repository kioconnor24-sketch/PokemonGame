---
name: averon-build-verification
description: Build the Averon GBA ROM and run the right automated checks, and report results with correct evidence labels. Use when changing engine C, scripts, maps, trainers or tests, or before claiming BUILD or NATIVE-TESTED.
---

# Averon build and test verification

Commands below are copied from `.github/workflows/averon-native-build.yml` and `averon-source-checks.yml`. Re-read those files if they may have changed.

## Where each check can run
| Check | Needs | Cloud sandbox | CI | User WSL |
| --- | --- | --- | --- | --- |
| Python syntax: `python3 -m compileall -q "Pokemon Game/scripts"` | python3 | yes | yes | yes |
| Script tests: `python3 "Pokemon Game/scripts/test-averon-quest-flow.py"` (same for `test-averon-sidequests.py`, `test-audit-averon-*.py`); `python3 -m unittest discover -s "Pokemon Game/scripts/tests" -p "test_averon_*.py" -v` | python3 | yes | yes | yes |
| ROM build: `make -j$(nproc) -O all` in `Pokemon Game/engine` | `arm-none-eabi-gcc`, binutils, newlib, libpng | **no** | yes | yes |
| Resource budget: `python3 "../scripts/check-averon-resource-budget.py" --log <build.log> --rom pokeemerald.gba --json <out.json>` (run from `engine/`) | build log + ROM | no | yes | yes |
| Native tests: `make -j4 -O check TESTS="Averon"` in `engine/` (bundled headless runner `tools/mgba/mgba-rom-test`) | built toolchain | no | yes | yes |

## Rules
- A pass needs a **nonzero** test count. CI fails on "No tests found" or "0 tests run"; so must you.
- Engine C, maps, event scripts, trainers, species: real GBA compile + named native tests + CI.
- Save layout, flags, badges, region travel: also save/load, whiteout and old-save compatibility tests.
- Cloud sandbox cannot compile. Push a draft `claude/*` PR and read the Actions result (`gh api repos/kioconnor24-sketch/PokemonGame/commits/<sha>/check-runs`). Quote exact pass/fail counts from the logs, not from memory.
- Build and native tests are `BUILD` / `NATIVE-TESTED`. They are not `EMULATOR-TESTED` or `DELTA-VERIFIED`.
- Report ROM/RAM usage from the budget script. Static figures do not prove peak runtime heap use.
- Never upload a built `.gba`, save file or secret.
