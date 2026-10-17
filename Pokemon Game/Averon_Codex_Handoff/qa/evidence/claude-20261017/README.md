# Claude verification evidence — 2026-10-17

Raw text evidence behind Claude's #15 / #48 / #23 reports from the 2026-10-17
sole-integrator session. Built locally with arm-none-eabi-gcc 14.2.1 and the
repository's own `make` targets. Text only: no ROM, save, ELF or screenshot.
CI screenshots live in the Actions artifacts linked from #23.

| Folder | Tree tested | What it supports |
|---|---|---|
| `main-6d5c0967/` | main `6d5c0967` (#79, #80, #81 merged); local tree `1b8466a4` = main's | Post-merge check of #79/#80/#81: [#15 6228391457](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6228391457) |
| `main-plus-48-3faa7c1a/` | `6d5c0967` + #48 `ee6e4f5c`. Its engine and scripts trees equal main `ebcd54a9` after #48 merged | #48 READY and the integrated-main check: [#48 6228643387](https://github.com/kioconnor24-sketch/PokemonGame/pull/48#issuecomment-6228643387), [#15 6228735611](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6228735611) |
| `end-state-6a9a09c8/` | `6d5c0967` + #48 + #14 `db6baaea` + #25 `090ecbdb` + LEGEND `901a3533` | The pre-Sinnoh end state before the remaining merges: [#15 6228649047](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6228649047) |
| `q3-local/` | #71 `f34eab21` QA step + the #77 observer, local Xvfb/mGBA 0.10.2 | Q3 local runs 1–2 (base64 image lines removed): [#23 6227677736](https://github.com/kioconnor24-sketch/PokemonGame/issues/23#issuecomment-6227677736), [#23 6228214784](https://github.com/kioconnor24-sketch/PokemonGame/issues/23#issuecomment-6228214784) |
| `tools/guard_snapshot.py` | — | Rebuilds the `exclusive-files` guard input for one PR from live REST data, with manual paging because cloud sessions can't follow `--paginate` links. Run `python3 guard_snapshot.py <PR> > snap.json && python3 "Pokemon Game/scripts/coordination/check_protected_files.py" snap.json` |

Each tree folder holds:
- `full-native-check.log.gz`: the complete `make -j4 -O check` output, with no `TESTS=` filter and ANSI colour removed;
- `strict-baseline.txt`: `check-averon-native-baseline.py` on that log;
- `build-warnings.txt`: compiler and linker warnings from `make all` and `make release`, plus exit codes;
- `resource-budget.json`: `check-averon-resource-budget.py` on the normal build.

| Tree | Tests TOTAL | PASSED | FAILED | Strict baseline |
|---|---|---|---|---|
| main `6d5c0967` | 6,013 | 5,238 | 327 | 1 problem: the known `Gimmick Form Change animations work` flake (TIMEOUT → FAIL), which #48's checker accepts |
| main + #48 | 6,088 | 5,313 | 327 | OK |
| end state | 6,093 | 5,318 | 327 | OK |

Reproduce from `Pokemon Game/engine` on the same tree:
`make -j4 all`, `make -j4 release`, `make -j4 -O check > ../check.log 2>&1`, then
`python3 ../scripts/check-averon-native-baseline.py ../check.log`.
