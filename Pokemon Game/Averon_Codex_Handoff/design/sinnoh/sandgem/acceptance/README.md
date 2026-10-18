# Sandgem Town + Pokémon Center 1F: mGBA acceptance (PR #133)

This is Claude's EMULATOR-TESTED evidence from mGBA 0.10.5, played with real controller input and read-only GDB observation. It is not human or third-party QA and not Delta. No ROMs or saves are committed. The maps are those in commit `38100116`; the popup flag is `1739ecf7`.

**Final head (this PR merged with `main` `8967b05b`, which contains #132): PASS.** Same-head NORMAL and RELEASE builds, source checks and the full mGBA acceptance all pass at `f3570d73`. See [Final head](#final-head-f3570d73-main--8967b05b). The earlier runs below are kept as history.

**Earlier headline:** on the **integrated tree** (this PR + Codex's #132, no shim) every acceptance step passes on both NORMAL and RELEASE cries-OFF. See [Integrated tree](#integrated-tree-133--132-no-shim) below. The shim-build run further down is kept as the first evidence.

## Disclosures

1. **Section shim (first run only; the integrated run has none).** `MAPSEC_SANDGEM_TOWN` (216) is Codex's and is not on `main` yet. These builds used a **local, uncommitted** `#define MAPSEC_SANDGEM_TOWN 216` in the section constants template. Both map headers therefore carry 216, and nothing else changes. The acceptance will be re-run on the integrated tree once Codex's reviewed change lands.
2. **DEV-only entry.** [`dev_continue_warp_save.py`](dev_continue_warp_save.py) copies a real save and sets the engine's own continue-game warp, `CONTINUE_GAME_WARP` plus `SaveBlock1.continueGameWarp` = Sandgem (15, 10), with valid checksums. No source or map is changed and no Averon map is redirected. Only the first Sandgem entry uses it. Every later step is ordinary play, saves and CONTINUEs.
3. **The hurt party is real.** Before the fixture is made, the same ROM plays a genuine wild battle in Averon and saves.

## Builds (`CRIES=off`, cries-ON stays available)

| Build | Sandgem ROM sha256 | Linked ROM used | Main baseline (`203a89cc`) | Growth |
| --- | --- | --- | --- | --- |
| NORMAL `make CRIES=off` | `2fcef531…` | 17,323,592 B | 17,320,628 B (`48c438a9…`) | **+2,964 B** |
| RELEASE `make RELEASE=1 CRIES=off` | `7c8fda92…` | 17,442,180 B | 17,439,216 B (`b62c42a3…`) | **+2,964 B** |

Both build with exit 0.

**Source checks**
- Map-registry contract: `PASS: 77 groups; 953 pinned IDs; 536 linked maps; 12 mutations detected; 1 valid extension accepted`. No existing ID moves.
- Map preflight: 80 geometry dependencies. The only errors are `Unknown map-section 'MAPSEC_SANDGEM_TOWN'` (×2), which are expected until Codex's entry lands.

## Results: identical on NORMAL and RELEASE

[`sandgem_qa.py`](sandgem_qa.py) runs in four modes; each step is a separate process.

| Step | NORMAL | RELEASE |
| --- | --- | --- |
| `damage`: a real wild battle in Averon hurts the party, then SAVE | PASS (Piplup 25/31) | PASS (Piplup 23/29) |
| DEV continue-warp lands in Sandgem at (15, 10) | PASS | PASS |
| Follower visible on arrival | PASS | PASS |
| West edge (Route 201) closed | PASS | PASS |
| North edge (Route 202) closed | PASS | PASS |
| South edge (Route 219) closed | PASS | PASS |
| Forest wall, house wall | PASS | PASS |
| Mart door without an interior: no warp, stays in the field | PASS | PASS |
| Walking the roads, including the south road and bottom road to the beach | PASS | PASS |
| Talking to a townsperson, reading the town sign | PASS | PASS |
| Pokémon Center door in | PASS | PASS |
| Nurse heals the hurt party | PASS: 25 → 31/31 | PASS: 23 → 29/29 |
| Start menu opens and closes | PASS | PASS |
| SAVE inside the Pokémon Center: success callbacks, valid newer flash | PASS | PASS |
| Fresh CONTINUE matches the inside save | PASS | PASS |
| Exit mat back to the Center door (15, 10); follower visible after the round trip | PASS | PASS |
| SAVE outside in Sandgem: 2 saves, counter advanced by ≥ 2 | PASS | PASS |
| Fresh CONTINUE matches the outside save; follower visible | PASS | PASS |

Each run's `result.json` and `events.jsonl` is under `normal/` or `release/` (`damage`, `town`, `cpc`, `ctown`), with screenshots.

**One QA-script note.** The first nurse A-press sometimes doesn't register right after the door warp. The script now retries until a script actually starts; on the passing run the conversation started on attempt 2. This is input timing in the harness, not a game defect: the nurse script itself is the shared, unchanged `Common_EventScript_PkmnCenterNurse`.

## Final head `f3570d73` (main @ `8967b05b`)

`claude/sandgem-town-maps` with `origin/main` merged in. `main` already contains Codex's #132 (section 216, `MAPSEC_NONE` 215). **No shim and no DEV warp in source.** The tree is clean apart from build outputs.

| Build | ROM sha256 | Linked size (`__rom_end`) | vs `main` `8967b05b` (measured) |
| --- | --- | --- | --- |
| NORMAL `make CRIES=off` | `f1d212fe913c0f14821f5b5d8e5880fc7a9567b742df4c94bcca5f6f78748294` | 17,323,640 B | **+2,964 B** over main's 17,320,676 B (`3f1ff795c0bd…`) |
| RELEASE `make RELEASE=1 CRIES=off` | `d330832786142b5986ae175691147d71c3487e2c1ea29a312738b110283e0efe` | 17,442,244 B | **+2,964 B** over main's 17,439,280 B (`d04d30bfc380…`) |

Both ROMs are **byte-identical** (same sha256) to the integrated-tree builds below, which proves that tree equals this head. The acceptance was still re-run from scratch here.

**Source checks at `f3570d73`**

| Check | Result |
| --- | --- |
| `check-averon-map-registry.py --mutations` | **PASS**: 77 groups, 953 pinned IDs, 536 linked maps, 12 mutations detected |
| `audit-averon-mapsec-namespace.py --check-pins` | **7 saved section values unchanged**; `MAPSEC_NONE`=215; Sandgem 216 |
| `audit-averon-map-readiness.py --group gMapGroup_Sinnoh` | 2 maps, 80 geometry dependencies, **0 errors, 0 warnings** |
| Exclusive-files guard (`check_protected_files.py`, fed live open PRs and #15 handoffs) | **PASS**: no unapproved shared-file or frozen-map changes. The 9 changed frozen/protected paths match `HANDOFF_APPROVED PR=#133` exactly |
| Source regression modules (CI list + mapsec test) and `test_averon_map*` unittests | 8/8 modules PASS; 62 tests OK |

**mGBA acceptance at `f3570d73`** (fresh process per mode)

| Mode | NORMAL | RELEASE |
| --- | --- | --- |
| `damage` | 1/1 PASS | 1/1 PASS |
| `town`: DEV entry, follower, 3 closed exits, walls, closed Mart door, roads, NPC, sign, PC in, nurse heal, Start menu, SAVE inside | **17/17**; heal 11 → 29/29 | **17/17**; heal 13 → 29/29 |
| `continue-pc` | 5/5 | 5/5 |
| `continue-town` | 3/3 | 3/3 |
| Flash verdict | no problems | no problems |

The map-name popup shows "SANDGEM TOWN". Evidence is under `final-head/{normal,release}/…`.

## Integrated tree (#133 + #132, no shim)

This is a local, unpushed test merge: `7f4a1485` = this branch at `1739ecf7` + Codex's PR #132 at `b899abb1853737bb30e5e37cd3e80a76babc4f98`. Codex's real `MAPSEC_SANDGEM_TOWN` (216) is used and **no local shim** is present (`git status` is clean apart from build outputs). The scripts, fixture and steps are the same as above; each step runs as a fresh process.

| Build | ROM sha256 | Size | vs main `203a89cc` |
| --- | --- | --- | --- |
| NORMAL `make CRIES=off` | `f1d212fe913c0f14821f5b5d8e5880fc7a9567b742df4c94bcca5f6f78748294` | 17,323,640 B | **+3,012 B** (Sandgem +2,964 + #132 +48) |
| RELEASE `make RELEASE=1 CRIES=off` | `d330832786142b5986ae175691147d71c3487e2c1ea29a312738b110283e0efe` | 17,442,244 B | **+3,028 B** (Sandgem +2,964 + #132 +64) |

**Source checks on the integrated tree**
- Map preflight: **0 errors, 0 warnings**. The two shim-era `Unknown map-section` errors are gone.
- Map-registry contract: **PASS**, 77 groups and 953 pinned IDs.
- The 7 section pins are unchanged, and `MAPSEC_NONE` stays 215.

| Mode | Checks | NORMAL | RELEASE |
| --- | --- | --- | --- |
| `damage`: real wild battle in Averon, then SAVE | 1 | PASS (Piplup 22/29) | PASS (Piplup 19/29) |
| `town`: DEV entry, follower, 3 closed exits, walls, closed Mart door, roads, NPC, sign, PC door in, nurse heal, Start menu, SAVE inside | 17 | **17/17 PASS**; heal 22 → 29/29 | **17/17 PASS**; heal 19 → 29/29 |
| `continue-pc`: fresh CONTINUE = inside save, exit mat to (15, 10), follower after the round trip, SAVE outside | 5 | 5/5 PASS | 5/5 PASS |
| `continue-town`: fresh CONTINUE = outside save, follower | 3 | 3/3 PASS | 3/3 PASS |
| Flash verdict, all saving steps | | no problems | no problems |

**Map-name popup:** with #132's section name and repaired popup bounds, arriving shows a "SANDGEM TOWN" popup ([`integrated/release/town/0009-arrived-sandgem.png`](integrated/release/town/0009-arrived-sandgem.png)).

Evidence is under `integrated/{normal,release}/{damage,town,cpc,ctown}/`: `result.json`, `events.jsonl`, save and continue JSON summaries (state only, no flash bytes), and key screenshots.

## Not covered / still open

- **Post-merge status in the SN-T02 register:** pending until this PR is merged; it goes in a separate small tracker PR.
- **No heal location / respawn for Sandgem:** a whiteout returns to the last Averon healer. That is the Codex and owner interface.
- **Town Map, Fly, routes and Averon → Sinnoh travel:** not built and not approved here.
- **Human listening, Delta:** UNTESTED.
