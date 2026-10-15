---
name: averon-playtest-handoff
description: Package a locally compiled Averon ROM and precise evidence for independent ChatGPT QA testing without publishing ROMs.
---

Verify the source commit, clean intended inputs, successful build, ROM size and
SHA256. Copy the ROM to a distinct source-named local artifact; preserve previous
working ROMs/saves. Package it with a provenance manifest and bounded QA steps:
starting save/position, debug fixture access, inputs, expected behavior and edges.
Keep all ROMs and saves out of public GitHub, Releases, attachments and artifacts.
The owner can attach the local ZIP directly to ChatGPT where supported.

Post a HANDOFF on the existing PR with source/remote SHA, code changes, exact test
counts, local artifact/hash, outstanding rendered/Delta checks and one next task.
Never infer that another chat can run an emulator from its GitHub connection or
that a GitHub comment woke it. Only actual screenshots/logs establish gameplay.
