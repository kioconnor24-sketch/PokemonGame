# Averon project scripts — safe navigation guide

Keep script filenames and directories stable: engine authoring programs, PowerShell wrappers, GitHub Actions, and existing tests may import or invoke them by exact relative path. **This index documents what exists; it does not authorize running mutating scripts.** See [development INDEX](../Averon_Codex_Handoff/development/INDEX.md) and [WORKFLOW](../Averon_Codex_Handoff/development/WORKFLOW.md).

| Group | Files / convention | Read before running |
| --- | --- | --- |
| WSL / build / checkout reconciliation | `build-averon.ps1`, `reconcile-shared-checkout.py` | Can affect copied source/build state; do not run against another agent's dirty engine checkout |
| Source audits | `audit-averon-*.py` | Examine a script's arguments, side effects, assumptions and input revision first; older checks can refer to historical fixtures |
| Static validation | `check-averon-*.py`, `verify-averon-native-caps.py` | May inspect or invoke existing authoring tools; do not assume every check is read-only |
| Authoring / installers | `build-averon-opening.py`, `build-averon-first-gym.py`, `build-averon-coast.py`, `build-averon-sidequests.py`, `build-averon-field-lab.py`, `install-averon-debug-tests.py` | **Writes game content or fixtures; do NOT use to create new map/layout or unapproved story content while owner freeze applies** |
| Other graphics / emulator helpers | `render-native-map.py`, `send-mgba-input.ps1`, `mgba-smoke.lua` | Inspect effects and use only for already approved assets or testing; owner screen or emulator may be affected |
| Regression tests | `test-averon-*.py`, `test-audit-averon-*.py`, `tests/test_*.py` | Choose targeted existing tests; never interpret a missing/zero-test result as pass |
| Documentation integrity | `check-repo-navigation.py`, `tests/test_repo_navigation.py` | Safe read-only local link verification; automatically runs for relevant docs PRs |

## Commands that do not build or modify game content

From the **repository root**:

```bash
python3 "Pokemon Game/scripts/check-repo-navigation.py" --root .
python3 -m unittest discover -s "Pokemon Game/scripts/tests" -p "test_repo_navigation.py" -v
```

The new [documentation integrity workflow](../../.github/workflows/averon-documentation-integrity.yml) runs the same checks on relevant pull requests. It is separate from the existing GBA/native and source checks.

## Do not reorganize these scripts by moving files

Moving a Python script can invalidate `Path(__file__).parents[...]` assumptions, hard-coded script paths, imported helpers, Windows/WSL wrappers, or GitHub Actions commands. A real relocation requires a dependency scan, compatibility wrappers where needed, tests, full game compile for authoring/source changes, and an exclusive coordination window. **No moves or deletions are part of the current cleanup.**

## Where to put results

Post build and test outcomes with the exact branch SHA and executed counts in the owning PR's HANDOFF, not new per-session log files. Reserve changes to the shared stable task queue for actual approved milestone or dependency updates.
