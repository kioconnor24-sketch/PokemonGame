---
name: averon-playtest-handoff
description: Hand a finished Averon change to ChatGPT QA for graphical playtesting, and file reproducible bug reports on GitHub. Use when a feature is built and native-tested and needs real mGBA verification, or when a playtest defect must be recorded.
---

# Playtest handoff and bug reporting

ChatGPT QA owns manual mGBA/graphical testing, and only after it has confirmed real emulator access. Never write `EMULATOR-TESTED` yourself unless you actually ran the emulator.

## Submit for playtest (comment on the owning PR)
```text
PLAYTEST REQUEST | PR # | branch | commit SHA (verified on GitHub)
CI: native-build / python-source-checks / engine-readiness results with run links
Native tests: command, tests run, pass/fail/skip counts
What changed for the player: <observable behavior>
Test steps: <fixture/entry point, exact inputs, expected result at each step>
Edge cases to try: full Bag, full party, whiteout, save/reload mid-event, repeat interaction
Not yet verified: EMULATOR-TESTED / DELTA-VERIFIED
```
- The ROM stays on the owner's machine. Do not attach `.gba` or save files (`file-guard` blocks them). Give the commit SHA and build instructions so QA can build or use the owner's local build.

## Bug report (on the owning PR or a linked issue)
```text
BUG | feature=<name> | source/ROM SHA=<...>
Environment/emulator version and fixture:
Exact reproduction steps:
Expected vs observed:
Screenshots/logs (safe to publish):
Severity and retest result:
```
The feature's owner fixes the defect and re-requests QA. QA reports retest results on the same thread.
