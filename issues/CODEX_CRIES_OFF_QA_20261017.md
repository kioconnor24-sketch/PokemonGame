> **Historical (superseded, Claude 2026-10-18).** This is Codex's checkpoint from before the takeover. Its blocker and status notes are out of date. RELEASE saves are now verified without `gSaveAttemptStatus`, and the RELEASE gameplay runs exist. For the current evidence and status, see `Pokemon Game/Averon_Codex_Handoff/qa/claude-cries-off/README.md` and the PR #117 description. The text below is unchanged.

# Active Codex audio integration gaps — 2026-10-17

PR117 fixes natively reproduced NULL player calls and silent unpaired BGM ducking. Both RELEASE configurations build and native audio passes. It is not merged. See `Pokemon Game/Averon_Codex_Handoff/development/CODEX_REVERSIBLE_CRIES_EVIDENCE_20261017.md` for exact hashes and counts.

Actual observer blocker: Claude normal-build driver reads gSaveAttemptStatus after SAVE. In RELEASE LTO, disassembly shows stores to this write-only production global removed; it reads0 even after visible saved-game text and a complete disk flash slot. Original run FAILED, not relabeled PASS. Codex will observe actual save-success callbacks and fresh Continue using its separate wrapper. No protected save source change warranted.

Outstanding gates: complete new-ROM cries-OFF graphical battle/capture/faint/evolution/Mega/Pokédex/script/music/follower and fresh Save→Continue coverage; independent source review; final applicable CI. Human listening and Delta remain UNTESTED, per policy. No unsafe merge or baseline/protection bypass.
