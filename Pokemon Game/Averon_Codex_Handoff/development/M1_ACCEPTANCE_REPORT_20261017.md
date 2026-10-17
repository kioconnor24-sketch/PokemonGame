# M1 ACCEPTANCE REPORT — pre-Sinnoh backend (consolidated, 2026-10-17)

**Status: FINAL CONSOLIDATED REVIEW — FOR OWNER ACCEPTANCE.** Combines Codex's
native/backend closeout (`CODEX_M1_NATIVE_CLOSEOUT_20261017.md`, merged #109)
with Claude's graphical Q1–Q5 evidence (`qa/claude-m1-gameplay/`, merged #110).
Reviews are by AI agents (Codex, Claude and Claude read-only subagents). **None
is third-party human Playtest.** Sinnoh work has not started.

## 0. Final answers

| Question | Answer |
| --- | --- |
| All assigned pre-Sinnoh backend engineering complete? | **Yes.** Every P0–P4 item in `M1_EXHAUSTIVE_REMAINING_WORK_20261017.md` is done, verified on current main, or classified POST-CONTENT / OWNER_DECISION below. No open engineering PR. |
| M1 ready for owner acceptance? | **Yes, with one human check outstanding** (a short audio listen, §0.3). |
| Genuine blocking defects? | **None.** The only reproduced defect (#100 foreign-OT egg hatch) is fixed and merged (#101). No new production defect was found by Codex's 6,107-result run or by 59 graphical runs. |
| What needs owner approval? | (1) audio listen result, (2) accepting Gym 1's missing dialogue screenshots as non-blocking, (3) accepting the known limitations in §0.4, (4) M1 acceptance itself, (5) authorizing Sinnoh map/content production. |
| Can Sinnoh begin after approval? | **Yes.** No technical blocker. Planning constraints in §0.5 apply (SaveBlock2 has 84 B free; ROM ~6.5 MiB free). |

**BACKEND_READY: YES** — backend engineering is complete and verified
(§0.1–§0.2). M1 *acceptance* still waits on the owner's audio listen and the
approvals above; those are human checks and decisions, not engineering work.

### 0.1 Native/backend verification (Codex lane; cross-checked by Claude)

- Codex's final unfiltered native run on main `4f8f987b` (engine tree
  `5d81cc84…`): 6,107/6,107 results, PASS 5,332, strict comparison exit 0 —
  all 327 normalized failing identities / 329 results match the unchanged
  baseline (`averon-native-test-baseline.txt` SHA256 `18af720b…`, last changed
  before M1 closeout; Claude re-hashed it from main). Normal and RELEASE builds
  exit 0, 0 compiler warnings (RELEASE: the 4 inherited newlib stub notes).
  Save batch 30/30 PASS, including Codex's new torn-PC-sector composition test.
- Claude re-checked: main `9ae0b32a`'s engine tree equals tested `4f8f987b`'s
  (`git rev-parse … :Pokemon Game/engine` = `5d81cc84…`); `103d05dd` →
  `4f8f987b` engine diff is the single new test file; cited CI runs
  39057987968 and 39018184673 concluded success.
- **Independent Claude run on main `9ae0b32a`:** CROSSCHECK_PLACEHOLDER
- ROM hashes differ between Codex's and Claude's environments for the same
  source (Codex normal `e09381d0…`, Claude `3072c6c0…`; both GCC 14.2.1).
  Each environment reproduces its own hash exactly (Claude: two worktrees at
  different paths, and a clean rebuild of run17's source reproduced
  `66b58c3a…`). Graphical evidence is tied to Claude's ROM hashes; native
  evidence to Codex's. Not a defect; noted for release reproducibility.
- Resources (Codex, actual ELFs): ROM 25.50 MiB used / 6.82 MiB free (normal);
  EWRAM 35,660 B free; IWRAM 4,376 B free; SaveBlock1/2/3/PC free
  304 / **84** / 1,556 / 1,568 B. Claude's measured dynamic stack high-water in
  real play: 2,228–2,372 B of 3,928 B (lower bound, quest build; its IWRAM
  static end `0x3006EE8` equals current main's, so the stack region is the same). Peak sprite/palette use not measured.

### 0.2 Graphical Gate B (Claude lane)

Q1, Q2, Q3, Q4 (DEV_FIXTURE), Q5, Q1/Q2 full-Bag retry (DEV_FIXTURE) and
corrupt-newest-slot fallback (DEV_FIXTURE): **PASS** (§3). Gym 1: PARTIAL
evidence, **not blocking** (§0.3). Current-main applicability: justified, with
Continue/Q3/Q4/Q5 rerun on the main ROM.

### 0.3 Gym 1 and audio decisions

**Gym 1 (recommendation: accept; does not block backend acceptance).** Proven:
an ordinary Elio battle won on the current-quest ROM (run52 try3, last foe
fainted on screen), `FLAG_BADGE01_GET` and the TM flag set immediately after,
trainer card badge 1 in the same run, the save written (flash hash changed),
and a fresh Continue showing badge 1 (run53); run17 also won on the older ROM.
Gym script and reward are covered natively (`Gym TM requires a badge and is
granted only once`, `Gym TM01 reward resolves to Work Up`, `Gym reward
normal/link flash preserves full-Bag retry and nonduplication`). Dialogue
rendering itself is proven elsewhere (Q1–Q5 dialogue frames). Missing: a
screenshot of Elio's post-battle lines and the badge/TM message text (captured
as empty boxes). That is a presentation-evidence gap with no functional
consequence. No Gym replay was run after the owner's instruction.

**Audio (needs a human; not verified by Claude).** Claude measured only that
mGBA's mixed output is non-silent: per-second RMS 2,200–3,200 during wild
battles, 1,300–2,400 in the field, audible during the whiteout/clinic window
(run23 `audio-report.json`, `audio-by-state.json`). Nobody has listened. A
human should play the current main ROM with sound for ~10 minutes and confirm:
title music; Saltmere/Alderfield field music; music changes on a map change;
wild battle music start and loop; trainer/Gym battle music; victory fanfare;
low-HP warning beep; whiteout transition; clinic healing jingle; menu
cursor/select, door and save sound effects; Pokémon cries; and no crackle,
dropouts, wrong pitch/tempo, stuck notes or silence. Record PASS/FAIL per item
on Issue #23.

### 0.4 Known limitations (accepted scope, not defects)

- DEV_FIXTURE paths: Q4's Field Lab and PC are reached only through the debug
  menu (no natural lab entrance — POST-CONTENT); full Bag pockets were made
  with debug Fill; corrupt-slot test used a deliberately damaged save copy.
- Not exercised: full-party capture swap UI; live peer-to-peer trade; a status
  condition at whiteout (status clearing is native-tested); legacy
  Ruby/Sapphire link and Berry Blender save concerns (no reachable reproduction).
- Opening/starter: covered natively (`starter awards respect party capacity`,
  `first accepted errand survives all six household orders`, `opening and Gym
  progression survive two native flash save and load cycles`); the natural
  save chain began with the real opening, but no opening frames are in the
  packaged evidence.
- SCRIPTED/LEGEND have no story caller yet (registered macros, native tests):
  POST-CONTENT.
- Driver artifact: caught Pokémon in the test save are nicknamed "A".

### 0.5 Sinnoh readiness (technical vs content)

No technical blocker. Constraints to plan around: SaveBlock2 has 84 B free and
SaveBlock1 304 B — new saved Sinnoh state should use the 349 unused flags / 15
unused vars, SaveBlock3 (1,556 B free) or the region record, not new SB1/SB2
fields; ROM has ~6.5 MiB for all new maps, tilesets, graphics and music; map
registry has 52 signed group slots left. Everything else for Sinnoh is
content/owner work: maps, Gyms, routes, encounters, story/canon, trainers,
graphics, music, level curve, natural Field Lab access, legend/scripted scenes.

## 1. Source and build identity

| Item | Value |
| --- | --- |
| main at writing | `9ae0b32a4b53e552c82bf67f5dfd7a9742a0a3bb` (engine tree `5d81cc84…` = tested `4f8f987b`; #107/#108/#109/#110 merged) |
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
| #107 Codex torn-PC-sector test | VERIFIED (Codex) | merged `4f8f987b`; 242/242 Averon CI |
| #109 Codex native closeout | VERIFIED (Codex; cross-checked §0.1) | merged `9ae0b32a` |
| #108 / #110 | merged `6140a397` / `d50de2ce` | driver follow-up; graphical evidence + this report |
| #97 driver (QA tooling) | **merged `4153ce5a`** at reviewed head `a9676159` | three separate read-only code reviews (two REQUEST_CHANGES, all findings fixed with mutation-checked tests); 33 offline tests; checks green. Tooling merge is not a gameplay PASS. |

## 3. Gate B gameplay (existing approved maps)

See `Averon_Codex_Handoff/qa/claude-m1-gameplay/README.md` for runs, hashes,
save chain and fixture disclosure. Verdicts are filled from reviewed evidence.

Final verdicts after three separate read-only reviews (Claude subagents, **not
third-party Playtest**); the last covered runs 47–59 and current-main
applicability. Current-quest build: source
`bcfeb28d`, ROM `e6870c30…`, ELF `aa2efbd9…`.

| Case | Verdict | Scope | Evidence (runs) | Remaining gap |
| --- | --- | --- | --- | --- |
| Gym 1 | **PARTIAL** | ordinary play, save copy of the pre-badge save | run52 try3 win (last foe down, Elio sprite), badge + TM flags, trainer card badge 1; save proved by flash hash; run53 Continue card badge 1; run17 older-ROM win; run48/52 try1–2 genuine losses → clinic | no frame shows Elio's defeat, badge or TM text (empty boxes, capture timing); not replayed per owner |
| Q1 | **PASS** | ordinary play | run51 opening request; run35 Hiker/researcher dialogue, Bag 0 → Great Ball ×2, repeat; run36/38 Continue Bag ×2; run39 gate message + block | — |
| Q1 full pocket | PASS | DEV_FIXTURE (debug Fill) | run26 refusal → TOSS 999 → +2 once; run37 Continue Bag ×2 | — |
| Q2 | PASS | ordinary play | run20 walk, boy hint, tree, artist +3, repeat; run38 natural Continue Oran ×3 | Oran 0 before is a memory read |
| Q2 full pocket | PASS | DEV_FIXTURE (debug Fill) | run28 refusal → TOSS 999 → +3 once; run29 Continue Oran ×3 | — |
| Q3 | **PASS** | ordinary play on copies of the pre-Q3 save (+ natural run23) | run41/47 defeat text, full whiteout text (run47), nurse, party screens, save box + "saved"; run42/44 Continue in clinic, full HP numbers; follower after one step | status clearing not exercised (no status at the loss; native-tested); PP is a memory read |
| Q4 | PASS | DEV_FIXTURE (lab + PC via debug menu) | run22 refusal, PC deposit → 5, one Wobbuffet, repeat; run40 Continue party screen | gift path changed on main (#96) → rechecked in run56/57 |
| Q5 | PASS, audio needs a human listen | ordinary play | run25 collision, menus, Field Kit, NPC, follower through clinic door both ways; run23 audio non-silent in field/battle/clinic | audio quality not judged |
| Corrupt newest slot | PASS | DEV_FIXTURE (damaged save copy) | run30/31 older whole slot loads, saves, continues | discriminator is state, not picture |

**Applicability to current main** (game code `103d05dd` = `4153ce5a`):
Gym map, Alderfield/Coastal Bluffs maps, trainer data and battle code are
unchanged since run17's source. Main's other non-test engine changes since
`bcfeb28d` are the SCRIPTED/LEGEND registration includes and `pokemon.c` OT
re-keying (`GiveCapturedMonToPlayer`, used by `givemon` and captures). Minimal
current-main runs: run54 (natural save on the main ROM: Bag, party, Q5
checks; its Q3 loop stopped on a too-strict driver check after a legitimate
evolution, not saved), run58/59 (genuine loss, whiteout, clinic, save, fresh
Continue) and run56/57 (Q4 gift through the changed function). Final reviewer:
**applicability JUSTIFIED** — the quest-build evidence applies to current main
for GYM1, Q1/Q2 rewards, full pockets and corrupt fallback by unchanged source
(save.c, quest scripts, Gym/maps/trainers/battle code unchanged), and Q3, Q4,
Q5 and Continue were rerun on the main ROM.

## 4. Native suite, builds and save handling (Claude's earlier measurement)

> **Superseded by §0.1 / Codex's final closeout.** Under the parallel plan (`M1_PARALLEL_CLAUDE_CODEX_EXECUTION_20261017.md`) the final native/resource closeout belongs to Codex (`CODEX_M1_NATIVE_CLOSEOUT_20261017.md`). This section and §5 record Claude's run on `a3d2ad99` (pre-#101 main) for reference only; Codex's final-main results supersede them.

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

## 7. Graphical lane conclusion (Claude) and open items

**Graphical half: CONDITIONAL-YES.** Every Q1–Q5 case is PASS on genuine
emulator evidence except Gym 1, which is PARTIAL only for missing on-screen
defeat/badge text (the win, badge, save and Continue are proven). The
quest-build evidence applies to current main (`103d05dd` game code; main
`6140a397` adds only QA tooling), and the main ROM itself passed Continue from
an older-ROM save, Q3, Q4 and Q5 runs. Gameplay audio is non-silent across
field, battle and clinic, but **a human must still listen** to judge it.

Tooling: #97 merged (`4153ce5a`), follow-up #108 merged (`6140a397`); #101,
#102 merged; #20/#71 closed as superseded.

Open, for the owner:
1. **Audio listen** (owner or human tester) — not something Claude can judge.
2. **Gym 1 text frames** — accept PARTIAL, or ask for one Gym replay with
   longer per-message waits (owner asked not to repeat it now).
3. **Backend half** — Codex owns the final native suite, saves and resources
   (`CODEX_M1_NATIVE_CLOSEOUT_20261017.md`); §4–§5 here are Claude's earlier
   reference measurements only.
4. **POST-CONTENT** (not M1 failures): natural Field Lab access for the Q4 gift,
   real story/legend callers, Sinnoh maps.

**BACKEND_READY** is the owner's combined call after Codex's closeout. Sinnoh
work has not started and waits for the owner's approval.
