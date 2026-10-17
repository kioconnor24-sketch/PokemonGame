# M1 ACCEPTANCE REPORT — pre-Sinnoh backend (Claude, 2026-10-17)

**Status: DRAFT FOR OWNER DECISION.** Written by Claude, the sole active
executor. Gameplay verdicts are Claude's own QA, with a separate read-only
reviewer pass by a Claude subagent. **They are not third-party or independent
Playtest approval.** Sinnoh work has not started and waits for the owner.

Legend: **PASS** (verified this session with evidence) · **VERIFIED_EXISTING**
(already-merged tests, re-run green this session) · **FIXED_AND_RETESTED** ·
**PARTIAL** (exact missing fact stated) · **POST-CONTENT** · **OWNER_ACTION**
(ready, blocked only by a GitHub write the host denied to Claude).

## 1. Source and build identity

| Item | Value |
| --- | --- |
| main at writing | `a3d2ad99b27c52eb9acb2e15268ebd953a7a8222` (docs-only since `27f91919`) |
| Gameplay build (Q1–Q5) | source `bcfeb28d…`, ROM `e6870c30…a7f34e1`, ELF `aa2efbd9…4262d` |
| main + #101 build | `9f0efe03`: normal ROM `3072c6c0…1bfb5`, RELEASE ROM `c918e880…627c2` |
| Toolchain | arm-none-eabi-gcc 14.2.1, mGBA 0.10.5 |

## 2. Integration (P1/P2)

| Item | Verdict | Evidence |
| --- | --- | --- |
| #14/#25/#95/#96 | VERIFIED_EXISTING | merged before this session; not redone |
| #100 foreign-OT egg hatch | FIXED_AND_RETESTED, **OWNER_ACTION to merge #101** | native RED (`invalid move: 2027` in BoxMonRestorePP) on a foreign-OT egg through real `ScriptHatchMon`, control green; narrow decrypt→set OT→re-encrypt helper; GREEN incl. flash Save→Load memcmp; full suite 5331 pass / 327 = baseline; normal+RELEASE built; reviewer APPROVE. Latent (no foreign-OT egg source in Averon content today). |
| #100 battle OT/personality writes | SOURCE-REVIEWED / RUNTIME NOT DEMONSTRATED | 51 `BtlController_EmitSetMonData` call sites inspected; none writes OT_ID/PERSONALITY/ALL on a reachable path |
| #20/#71 QA stack | **OWNER_ACTION to merge #102**, then close #20/#71 as superseded | 5 files byte-identical to #71 head + GDB `\x03` fix with RED→GREEN tests (36/36); rendered-smoke green (run 39018323656); reviewer APPROVE; nothing else in #20/#71 needed |
| #97 driver | in review | see §6 |

## 3. Gate B gameplay (existing approved maps)

See `Averon_Codex_Handoff/qa/claude-m1-gameplay/README.md` for runs, hashes,
save chain and fixture disclosure. Verdicts are filled from reviewed evidence.

(Q1–Q5 table — filled after review.)

## 4. Backend matrix (C1–C3)

(Filled from the full-suite test identities.)

## 5. Resources

(Filled after final build.)

## 6. Open owner actions and risks

(Filled at the end.)
