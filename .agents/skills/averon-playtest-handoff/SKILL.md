---
name: averon-playtest-handoff
description: Use to hand a new compiled ROM from Codex or Claude to independent ChatGPT QA.
---

# Prepare ROM runtime acceptance

1. Identify owning PR, branch, remote commit SHA, exact tested ROM SHA256, build timestamp and build command. Confirm the ROM matches the requested source, not merely a local filename.
2. Supply an owner-authorized local delivery path or archive containing a playable .gba, build manifest, QA cases and no secrets. Do not commit or publicly upload copyrighted full ROMs/saves to GitHub.
3. Include reproducible start state/save fixtures where distribution is authorized, relevant map/event prerequisites, clear controls and known blockers.
4. QA actually launches ROM in mGBA, captures screenshots and tests real interactions. Report observed results, not hoped-for results.
5. Record BUILD, NATIVE-TESTED, EMULATOR-TESTED and DELTA-VERIFIED independently. Reserve DELTA-VERIFIED for owner-run iOS test.
6. Send findings to owning PR with repro, ROM/source hash, severity and evidence; developer responds on their claimed branch.

## Authority

Current code and live PRs override past notes and generated indices. Follow root/project AGENTS.md, development/AGENT_ROLES.md, WORKFLOW.md and issue #15. Preserve existing developer claims.
