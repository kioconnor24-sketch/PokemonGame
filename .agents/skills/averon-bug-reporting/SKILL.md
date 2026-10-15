---
name: averon-bug-reporting
description: Report reproducible Averon gameplay or engineering defects with exact source/build context for the owning developer.
---

Check the active CLAIM/PR and existing reports to avoid duplicates. Report on the
owning PR or a linked issue: source SHA, ROM SHA256, environment/emulator version,
starting state, exact map/coordinates and inputs, expected/observed behavior,
severity, frequency and safe screenshot/log references. Separate confirmed defects
from suspected causes and unperformed checks. Never upload ROMs, saves or secrets.

Give one actionable reproduction and acceptance test; let the owning developer
change its claimed source. After a fix, retest the exact scenario on the new build
and record its SHA. Static/native tests cannot close a visual defect by themselves.
