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
| main at writing | `103d05dd712bb4f0271e9c78050fa642cee0830d` (#101 egg fix and #102 QA tooling merged; #105/#106 docs) |
| Gameplay build (Q1–Q5) | source `bcfeb28d…`, ROM `e6870c30…a7f34e1`, ELF `aa2efbd9…4262d` |
| main + #101 build | `9f0efe03`: normal ROM `3072c6c0…1bfb5`, RELEASE ROM `c918e880…627c2` |
| Toolchain | arm-none-eabi-gcc 14.2.1, mGBA 0.10.5 |

## 2. Integration (P1/P2)

| Item | Verdict | Evidence |
| --- | --- | --- |
| #14/#25/#95/#96 | VERIFIED_EXISTING | merged before this session; not redone |
| #100 foreign-OT egg hatch | FIXED_AND_RETESTED, **merged #101 (`c708d6db`)** | native RED (`invalid move: 2027` in BoxMonRestorePP) on a foreign-OT egg through real `ScriptHatchMon`, control green; narrow decrypt→set OT→re-encrypt helper; GREEN incl. flash Save→Load memcmp; full suite 5331 pass / 327 = baseline; normal+RELEASE built; reviewer APPROVE. Latent (no foreign-OT egg source in Averon content today). |
| #100 battle OT/personality writes | SOURCE-REVIEWED / RUNTIME NOT DEMONSTRATED | 51 `BtlController_EmitSetMonData` call sites inspected; none writes OT_ID/PERSONALITY/ALL on a reachable path |
| #20/#71 QA stack | **merged #102 (`95ac045b`)**; #20/#71 closed as superseded | 5 files byte-identical to #71 head + GDB `\x03` fix with RED→GREEN tests (36/36); rendered-smoke green (run 39018323656); reviewer APPROVE; nothing else in #20/#71 needed |
| #97 driver (QA tooling) | **merged `4153ce5a`** at reviewed head `a9676159` | three separate read-only code reviews (two REQUEST_CHANGES, all findings fixed with mutation-checked tests); 33 offline tests; checks green. Tooling merge is not a gameplay PASS. |

## 3. Gate B gameplay (existing approved maps)

See `Averon_Codex_Handoff/qa/claude-m1-gameplay/README.md` for runs, hashes,
save chain and fixture disclosure. Verdicts are filled from reviewed evidence.

(Q1–Q5 table — filled after review.)

## 4. Native suite, builds and save handling (Claude's earlier measurement)

> **Ownership:** under the parallel plan (`M1_PARALLEL_CLAUDE_CODEX_EXECUTION_20261017.md`) the final native/resource closeout belongs to Codex (`CODEX_M1_NATIVE_CLOSEOUT_20261017.md`). This section and §5 record Claude's run on `a3d2ad99` (pre-#101 main) for reference only; Codex's final-main results supersede them.

Run on a clean worktree of main `a3d2ad99` (2026-10-17 09:05–09:21 UTC), nice'd
`make -j10`. Toolchain: arm-none-eabi-gcc 14.2.1 (15:14.2.rel1-1), host gcc
15.2.0, Python 3.14.4, mGBA 0.10.5.

| Check | Result |
| --- | --- |
| Normal build | exit 0, 234 s. ROM `0272ef0f6f3d720a9657aa4dc178067ead7f7cf49b0d103f890fbdb4405a2594`, ELF `c2b2f750a73ae13ab7379a742b4748a30fd6562a1d40c9342ca4678e41335dcd`. **0 compiler/linker warnings**; 209 `libpng warning: bKGD: invalid index` lines from graphics conversion on a clean tree. |
| RELEASE build | exit 0, 73 s. ROM `6831f6bb8b364402a7a8a9a1c83425909368a1ade4d6556f349abc5d6c7315ac`, ELF `46304537f26cefdba3b2cee3d3c823b7161ae553f3611fcb89c7a5bd0bd29636`. Only the 4 pre-existing newlib `_close/_lseek/_read/_write not implemented` link notes (same 4 in the earlier RELEASE). |
| Full unfiltered `make check` | 660 s. **5330 passed / 6105 total**; FAILED 327, KNOWN_FAILING 17, TO_DO 421, EXPECT_FAILING 9. |
| Strict baseline | `check-averon-native-baseline.py`: "failing tests in log: 327; baseline entries: 327 — OK: matches the Averon baseline" (identity match, file unchanged). |
| Averon tests | 240/240 PASS on main; 241/241 on main + #101. |
| main vs main + #101 | per-test outcome lists identical across all 6105 except the one added egg test (PASS). |

### Save compatibility (VERIFIED_EXISTING native + PASS graphical)

- Native (all PASS above): region save legacy load → upgrade, round trip of
  SaveBlock1/2/PC byte-exact, power loss at every sector write, CRC-valid
  semantic corruption, single-bit flips, mixed-slot rejection, counter wrap,
  newer-format refusal, erased/invalid-ID slots, link/Hall-of-Fame/overwrite
  paths, refused saves (trade/incremental) write nothing (`region save *`,
  `save bounds *`, `trade save refusal *`).
- Graphical: a save written by the older ROM `66b58c3a` (run17 end
  `0a7429783b43`) CONTINUEs on the current ROM (run18); every phase since
  continues through title → CONTINUE in a fresh emulator process; a save copy
  with its newest slot deliberately damaged loads the whole older slot (clinic,
  healed party, quest flags) and saves/continues normally afterwards
  (run30/31, disclosed fixture).

## 5. Resources (Claude's earlier measurement, main `a3d2ad99`)

| Budget | Normal | RELEASE | Headroom |
| --- | --- | --- | --- |
| ROM image (loadable sections) | 26,736,224 B (25.50 MiB) | 26,854,924 B (25.61 MiB) | 6.5 MiB (20.0–20.3 %) of 32 MiB |
| EWRAM | 226,484 B | 226,486 B | 35,660 B (13.6 %) |
| IWRAM statics | 28,388 B | 28,332 B | system-stack region 3,928 B (to sp_sys `0x3007E40`) |
| System stack, **measured** | 2,372 B deepest written byte in real play (field, menus, Bag, wild battles; runs 26–29) | — | ≥ 1,556 B; a lower bound, not every code path |
| SaveBlock1 | 15,568 / 15,872 B | | **304 B** |
| SaveBlock2 | 3,884 / 3,968 B | | **84 B** |
| SaveBlock3 | 68 / 1,624 B | | 1,556 B |
| PC storage | 34,144 / 35,712 B | | 1,568 B |
| Flash | 32 sectors, 14 per slot, 2 slots | | layout fixed |
| Flags / vars | 349 `FLAG_UNUSED_*`, 15 `VAR_UNUSED_*` names remain | | |
| Map data | 76 map groups (largest 123 maps); 16 Averon maps; per-map maxima 8 objects (limit 64 templates, 16 live), 4 warps, 3 coord events | | |

**Risk for Sinnoh:** ROM headroom (~6.5 MiB) is the budget for all new maps,
tilesets, graphics and music; it is finite but not yet measured against
unbuilt content. SaveBlock1/2 headroom is small (304 B / 84 B): new saved
state should come from the reserved/unused flag and var ranges or SaveBlock3,
not new SaveBlock1/2 fields. Stack has measured margin on the paths played; the
deepest battle/AI paths are not measured.

## 6. Backend matrix (C1–C3), from the passing test identities on main

| Area | Verdict | Representative passing tests (names abbreviated) |
| --- | --- | --- |
| Two regions, 8+8 badges, cap/obedience, travel, whiteout | VERIFIED_EXISTING | `region progression: *` (11), `region adapters *`, `region travel *` (7), `region save round-trips both regions` |
| Save robustness / migration / refusal | VERIFIED_EXISTING + graphical PASS | §4 |
| Map registry / IDs | VERIFIED_EXISTING | `map registry *` (3), `coast trainer reuses the unused slot without expanding save flags` |
| Field Kit / licenses / Fly / Surf / Dive / Waterfall | VERIFIED_EXISTING + graphical (Field Kit opens, Q5) | `field licenses *`, `Field Kit *` (3) + licensed/locked Field Kit (2), `Fly bounds *` (5), `native Dive/obstacle/Surf *`; Cut/Rock Smash/Strength/Surf/Waterfall/Dive/Fly rendered earlier (`qa/FIELD_LICENSE_RUNTIME_RESULTS.md`) |
| Species/forms/moves/learnsets/dex/evolution/breeding | VERIFIED_EXISTING | `every enabled species *` (5), `every evolution/form/conditional *`, `every breedable species hatches *`, `a complete national dex *` |
| Set mode, phys/special split, gimmicks off, Mega rules | VERIFIED_EXISTING | `uses Set mode even when an old save requests Shift`, `Dark physical and Ghost special *`, `rejects all excluded gimmicks for both battlers`, `Mega*` (10) and 3 more Mega tests, Primal off (2) |
| Gen 5 held EXP Share, cap, level 100 | VERIFIED_EXISTING | `EXP Share*` (9, incl. 2 lifecycle), `EXP options` (2), `six-member party respects held EXP Share and the first cap`, `with every level cap lifted … level 100` |
| Held items / Bestow / Trick / capture | VERIFIED_EXISTING | `held items: *` (19) |
| Follower lifecycle | VERIFIED_EXISTING + graphical PASS | `follower *` (8) plus 2 follower/traversal tests; doors both ways, whiteout, Continue (Q3/Q5) |
| SCRIPTED no-penalty loss, chains, no forfeit | VERIFIED_EXISTING (no story caller: POST-CONTENT) | `scripted battle *` (10), `story loss recovers in place`, `scripted loss skips the whiteout and keeps the player's money` |
| LEGEND capture/defeat/flee/retry/persistence | VERIFIED_EXISTING (no legendary placed: POST-CONTENT) | `legend *` (15) |
| QUEST reward/full Bag/retry/save | VERIFIED_EXISTING + graphical PASS | `optional event *`, `unclaimed rewards survive saving with a full pocket`, Q1/Q2 full-pocket runs |
| Party/PC/gift/OT integrity | VERIFIED_EXISTING + FIXED_AND_RETESTED (#101) | `full PC delivery *`, `foreign OT * delivery *`, `developer gift *`, `PC items *` (4), egg hatch |
| Whiteout money / heal | VERIFIED_EXISTING + graphical PASS | `whiteout money: *` (3), `native whiteout heals *` (2), Q3 |
| Wild encounters on existing tables | VERIFIED_EXISTING | `wild encounters: *` (3) |

## 7. Open owner actions and risks

(Filled at the end.)
