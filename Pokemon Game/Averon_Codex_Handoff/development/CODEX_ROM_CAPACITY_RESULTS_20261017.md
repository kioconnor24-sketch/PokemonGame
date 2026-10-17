# ROM capacity results and complete two-region forecast

2026-10-17 · Codex · Owner assignment [capacity brief](CODEX_ROM_CAPACITY_AND_TWO_REGION_FORECAST_20261017.md) · [PR #115](https://github.com/kioconnor24-sketch/PokemonGame/pull/115)

**Measured conclusion:** the RELEASE game occupies **26,854,924 B**. Disabling only Pokémon cries produces **17,438,276 B**, saving **9,416,648 B (8.980 MiB)** and leaving **16,116,156 B (15.370 MiB)** under 32 MiB. Music, effects and their sample/sequence objects remain. However, the no-cries configuration fails a native cold-start player-safety guard; it is **not production-ready**. Disabling just special Mega cries currently **fails both RELEASE and native compilation**. Neither configuration is merged or recommended for shipping without the missing fixes/review/QA.

The manifest scenarios for **remaining Averon + full Sinnoh + all postgame** require an additional **4.51 / 9.24 / 20.32 MiB including reserve**. With all cries, the expected scenario exceeds 32 MiB by **2,988,840 B**; cries-off would leave **6,427,808 B** after that scenario and reserve. These are explicit, low-confidence content estimates, not approved map counts or proof of fit. The measured small reclamation/alias opportunities do not close a multi-MiB gap. Keep 32 MiB as the production target, measure approved map batches, and decide cry policy after addressing the experimental blockers. A tiny 64 MiB Matrix mapping proof works in the bundled mGBA runner; a banked Averon game, Delta and Zenulator remain unverified.

## 1. Source, scope and evidence

Main was refreshed at **`8ed13f12f6e60a92f42daff9dba0b0c5c0df7e77`**; engine **`5d81cc8431cc4c915889b303c22aca2059b78aa3`** still equals the accepted M1 engine. Read root AGENTS, [current phase](CURRENT_PHASE_AND_HANDOFF.md), TASKS, the full brief, [readiness report](SINNOH_TECHNICAL_READINESS_20261017.md), [M1 acceptance](M1_ACCEPTANCE_REPORT_20261017.md), owner design files and all live #15 comments. No conflicting active PR/claim was found; #115 is the sole open PR at the final scan. Claude's acceptance, gameplay tooling/evidence, maps and content files are untouched.

This PR adds host reporting, experimental test-source templates, an original homebrew sentinel and this report/evidence. **No production engine/config/map/asset/ID/guard change is included.** Temporary link/config overlays were isolated and restored in the reporting worktree. The two alternative config sources are preserved on **unmerged experimental branches**, not production merge proposals:

| Variant | Exact source pin | Configuration difference from main |
| --- | --- | --- |
| All cries | `8ed13f12f6e60a92f42daff9dba0b0c5c0df7e77` | None |
| No cries, music on | [`c9ddb7f47f57ed7cae30d2ceb4f4a397b8c5000f`](https://github.com/kioconnor24-sketch/PokemonGame/commit/c9ddb7f47f57ed7cae30d2ceb4f4a397b8c5000f) | Only `P_CRIES_ENABLED FALSE` |
| Normal cries, unique Mega cries off | [`d764fc2122d4ab720488508698583ef646f013d1`](https://github.com/kioconnor24-sketch/PokemonGame/commit/d764fc2122d4ab720488508698583ef646f013d1) | Only `P_MODIFIED_MEGA_CRIES FALSE` |

Actual fresh RELEASE builds use ARM GCC **14.2.1 (20241119)**, GNU ld **2.44**, Make **4.4.1**, Python **3.12.14**, the repository tools and unchanged `RELEASE=1`/LTO settings. The four inherited newlib `_close/_lseek/_read/_write` link warnings remain; successful variants exit 0. Both failed Mega builds exit 2. The successful all-cries build exactly reproduces the previous M1 ROM **and ELF hashes**, so the comparison has a strong common baseline.

Full source/config/ROM/ELF/log hashes, sample inventory digests, native identities/counts, graph summary and the complete forecast input manifest are in [machine-readable evidence](../../scripts/coordination/codex_rom_capacity_evidence_20261017.json). Binary ROMs, ELFs, saves and generated graphics/audio remain local and are not uploaded. The accepted M1 full 6,107-result strict-baseline run is reused for unchanged production code; no duplicate full M1 suite or new graphical acceptance is claimed.

## 2. Matched actual RELEASE comparison

Occupancy is `__rom_end - 0x08000000`, corroborated by linker memory usage. Successful files are padded to **33,554,432 B**, which is not linked occupancy.

| Configuration | Linked used B | Free B / 32 MiB | Actual saving vs default B | Audio object `.rodata` B | Build |
| --- | ---: | ---: | ---: | ---: | --- |
| All cries ON, music/effects ON | 26,854,924 | 6,699,508 | 0 | 10,422,348 | PASS |
| All cries OFF, music/effects ON | 17,438,276 | 16,116,156 | **9,416,648** | 1,006,532 | PASS, safety gate fails below |
| Unique Mega cries OFF, ordinary cries ON | UNKNOWN | UNKNOWN | **NOT_MEASURED** | Not used as a linked estimate | **COMPILE FAIL** |

The no-cries differential is **9,415,816 B of `.rodata` plus 832 B of `.text`**; other loadable section sizes are unchanged. The cry blob inventory alone was 9,386,416 B, so it would have understated the actual linked saving. Do not add the audio object to its component samples or count any removed bytes twice.

| Successful actual RELEASE artifact | ROM SHA256 | ELF SHA256 |
| --- | --- | --- |
| Default | `56c902840cffb587a4add8a021260095e91cab77a2f170f6cf4f14bc333d9ea2` | `481510252e229314a4288c9db4e291aec43114e0b2596d18e013c813657d6932` |
| No cries | `923b49fc9b8429cbbae21736acd1ff3dd852410f5505dcfc3d10fdc0dbffa0d0` | `01da8b1c0c7b271e76419f31ae341da82cb9764178884ac720ddcd775795d361` |

Both retain EWRAM **226,486 B used / 35,658 B free**, IWRAM **28,336 / 4,432 B**. Those linker remainders are not free heap/stack allowances. The current saved structures are unchanged: SB1/SB2/SB3/PC free **304/84/1,556/1,568 B**, per accepted exact-engine M1 evidence.

**Music/effect preservation proof:** all **530 song sequence object files** have identical hashes across the builds; their aggregate name→hash digest is in the evidence. All **105 instrument/other blobs (642,204 B)** and **51 phoneme blobs (111,496 B)** match byte-for-byte at their linked addresses in both configurations. Cry blobs go from **1,156 / 9,386,416 B** to zero. The identical 8,134-symbol song-label fingerprint includes track labels; it is **not** a count of songs. Native tests additionally start representative title, town, route, wild battle, victory, healing, menu and door audio paths. This does not replace mixing/loop/voice-stealing tests or listening.

## 3. Audio safety: actual tests and explicit gaps

[Audio fixture source](../../scripts/coordination/codex_audio_capacity_fixture.c) is outside engine/test deliberately. It is copied only into a disposable build. The test ELF runs with **`gTestRunnerHeadless=FALSE`**: ordinary `make check` patches that flag TRUE, and `GetCryIdBySpecies` then returns `CRY_NONE` even for cries-ON. That would conceal this comparison.

| Test identity, prefix `Codex audio capacity` | Default | No cries | Boundary actually checked |
| --- | --- | --- | --- |
| `real cry lookup respects configuration` | PASS | PASS | Every enabled species, cry bounds and disabled result |
| `title town route battle victory and heal sequences start` | PASS | PASS | Six song parameters; correct actual music player and live tracks |
| `menu and door effects start` | PASS | PASS | Two effects; song header and active tracks |
| `script cry owns a valid completion player from cold start` | PASS | **FAIL** | Real production initializer → `PlayCry_Script` → pointer guard |
| `all cry modes and Mega lookup complete with valid player fixture` | PASS | PASS | Two species; bounded mode loop 0–11 (normal through weak), stop/wait and BGM-duck cleanup; supplied valid player explicitly |
| `target ABI unit costs` | PASS | PASS | Actual ARM structure sizes used below |
| **Test identities** | **6/6 PASS** | **5 PASS / 1 FAIL** | 13 parameter cases per configuration |

**Reproduced safety failure, not a fabricated gameplay crash:** `gMPlay_PokemonCry` starts NULL. In cries-off, `PlayCryInternal` never calls `SetPokemonCryTone`, so the pointer remains NULL. `IsPokemonCryPlaying` unconditionally reads `mplayInfo->tracks`; stop APIs also dereference the player. The cold-start test fails **before** making that unsafe completion call. GBA BIOS/open-bus reads are not a portable valid-player contract. The supplied-player test's success explicitly excludes this failure. Manager/blocker notice: [#55 comment 6241840293](https://github.com/kioconnor24-sketch/PokemonGame/issues/55#issuecomment-6241840293). A separate narrow reviewed null-safe policy and actual runtime QA are required before production use; no production repair was smuggled into this study.

**Mega-only configuration failure:** both real RELEASE and native compilation report undeclared `CRY_SLOWBRO_MEGA` at `src/data/pokemon/species_info/gen_1_families.h:10745` and `CRY_RAYQUAZA_MEGA` at `gen_3_families.h:13158`. The config removes these constants while those species initializers still reference them. No valid image or saving is reported. [Manager notice](https://github.com/kioconnor24-sketch/PokemonGame/issues/55#issuecomment-6241967276). The supported design intent is base cries with `CRY_MODE_HIGH_PITCH`; it is not presently a proven build option.

Despite that test's broad historical name, modes 12 (weak doubles) and 13 (excluded Dynamax) are not executed by its bounded loop. Source-reviewed wait callers include battle controllers/pokeballs, cry animation tasks for moves, script `waitmoncry`, evolution, party menus, Pokédex info and cry pages, trade and Hall of Fame. The cry page samples the mixed PCM buffer and has replay/countdown logic; silence does not automatically make the screen safe. [Upstream #4791](https://github.com/rh-hideout/pokeemerald-expansion/pull/4791) is context, not acceptance of this checkout.

| Required interaction | Evidence this session | Remaining acceptance |
| --- | --- | --- |
| Title/town/route/battle/victory/heal music and menu/door SFX | BUILD, identical linked inputs, NATIVE sequence starts | Actual transitions/loops/mixing and human listening |
| Wild entry, faint, capture, moves/scripts | SOURCE; cry-mode/stop/task API probes | Complete real battle/script flows on alternate ROM |
| Evolution and Mega transition | SOURCE; ordinary/Mega cry API probes | Complete scene transitions; partial-Mega build first needs fixing |
| Pokédex cry page and repeated play/back navigation | SOURCE only | Graphical input/reentry/exit/waveform test |
| Travel/whiteout/Save→Continue on alternate ROM | Unchanged source; no new acceptance | Focused actual graphical smoke after candidate fix |
| Human audio / Delta / Zenulator | **UNTESTED** | Deferred #23 listen and actual owner/device checks |

The owner has three decisions to consider: keep default cries unchanged; consider cries-off after safety repair and QA; or request the small compile fix and remeasurement for normal-only cries. A generic/reduced cry set would be another design, not an automatic substitute.

## 4. Hoenn dependencies and actual limited reclamation

Current linked inventory: **534 map headers, 456 layouts**, in a registry of **76 groups / 951 pinned IDs**. The tool builds a JSON warp/connection graph rooted at all 16 maps in `gMapGroup_AveronOpening`; its explicit closure contains those same 16. They are Saltmere and its four interiors, Coastal Meadow, Windrow/cooperative, Orchard Lane, Alderfield/Gym/clinic/supply, Coastal Bluffs, Field Lab and underwater lab. This is **not** a proof that all other maps can be removed: scripts, C callbacks, debug warps, dynamic layouts, tests, return/healer records and legacy saved warps/layout IDs are additional roots.

The clinic uses the existing `LAYOUT_POKEMON_CENTER_1F`; the opening also uses shared General/environment art and Hoenn music. Removing old map files or a whole tileset/audio object would break reuse. Normal inventory inputs `data/maps.o` **710,320 B**, `map_events.o` **103,692 B**, tilesets **688,440 B**, script_data **1,263,160 B** are attribution categories, not safely reclaimable totals. The same map/event object sizes were checked in RELEASE; C tilesets are redistributed by RELEASE LTO. Global script data includes current and reusable systems.

**35 linked layouts have no map-JSON layout reference.** Many are dynamically used: Mirage Island, Route 111's tower state, Sky Pillar clean floors and other script variants cannot be called unused from that query. Even the unused Battle Pike layout constant has a C caller. The tested cohort was just **UnusedCave1–14, UnusedContestRoom1–3, UnusedOutdoorArea**: no current JSON/static caller found beyond their generated registry definitions.

The local experiment removed only those generated layout payload definitions and replaced **their existing table entries with NULL**, preserving every other ID/index/header. No map source, geometry or permanent identifier was created/changed. Actual RELEASE becomes **26,851,192 B**, a **3,732 B** saving; `data/maps.o` becomes **706,588 B**. Existing source/ELF registry checks pass **951 IDs / 534 original headers / zero pointer mutations**. Source generation overlays were restored. Old-save/debug/dynamic-layout compatibility is not fully proven; **production forecast credit is 0 B** until reviewed retirement policy and relevant runtime/save tests exist.

## 5. Audio, graphics and other storage options

| Candidate, sorted by demonstrated scale | Measured benefit / bound | What was actually proved | Cost / remaining risk |
| --- | --- | --- | --- |
| Cries-off, music on | **9,416,648 B linked** | Matched RELEASE images; other audio bytes/objects retained | Feature removal needs owner decision; null-player blocker + graphical/audio QA; RAM statics unchanged |
| Unique Mega cries off | UNKNOWN | Both builds fail on two undeclared constants | Narrow source fix/review, new image measurement and Mega/cry-page QA first |
| Lossless LZ wrapping of 3 largest DPCM cry blobs | **15,989 B host-only** out of 78,173 B | Three host roundtrips byte-exact; no linked saving claimed | Requires new load/buffer-lifetime design, up to 27,648 B decoded per sample; double cries, battle heap/CPU/audio IRQ safety unmeasured; no loader implemented |
| Full Smol for 3 existing secondary tilesets | **5,592 B encoded**, not whole-ROM delta | Host roundtrips reused; new target-native byte equality, timing and heap restoration | Additional scratch and slower cold decode below; no blanket codec change |
| Identical accordion sample alias | **5,072 B linked** | Actual RELEASE **26,849,852 B**; both labels retained at one address, exact original sample bytes | Isolated assembly overlay restored; voice/pointer identity, human audio and runtime review still required |
| 18 orphan layout payloads | **3,732 B linked** | Actual build + registry checks above | Not wholesale Hoenn removal; legacy/dynamic eligibility still gated |
| Equal immutable graphics/objects | Prior NORMAL scanned-subset upper bound **118,440 B** | Exact-byte objects, aliases/overlaps excluded in prior report | Not a new measured RELEASE saving; no blanket pointer/data merge; do not add to overlapping candidates |
| Entire remaining Hoenn/scenes/music | UNKNOWN removable | Explicit dependency inventory only | Current reuse, dynamic callers, tests and legacy saved locations block deletion claims |

No candidate savings are added to the production forecast. Individual deltas are **not** a tested combined image.

All 1,156 linked cry blobs are already **type-1 DPCM**, from mono source WAVs: 391 at 10,512 Hz, 734 at 13,379 Hz, 22 at 11,025 Hz and nine at 13,000 Hz; 1,130 sources are 8-bit, 26 are 16-bit. Source PCM totals **19,126,422 B** versus linked generated cry blobs **9,386,416 B**. Existing `wav2agb -b -c -l 1 --no-pad` is real compression, not an unclaimed future saving. Lowering rates/requantizing would alter quality and requires approval/listening. Increasing DPCM lookahead searches for quality, not a different fixed-rate size budget.

The bounded extra-LZ host test uses existing generated Cetitan **27,648→19,752 B**, Mega Zygarde **26,244→22,052 B**, Mega Chandelure **24,281→20,380 B**, with exact decoded-byte equality. These are the three largest blobs, deliberately not a representative whole-library percentage. Wrapping the bytes is not enough: the current mixer needs a live decoded WaveData pointer for the full playback, potentially two cries at once. A generic loader is not authorized or implemented here.

Native cold-decode benchmark uses the current engine decoder, O2 test build, 16,777,216-Hz GBA timing with timer /64; counts include measurement overhead. Three parameter cases pass in one test identity. Output buffers match the original bytes; total free heap payload returns to **115,756 B** after each case. This is a test fixture's starting free heap, not gameplay worst-case headroom.

| Existing secondary | Fast/full encoded B | Fast/full ticks ×64 | Approx. fast/full ms | Full-mode requested scratch payload B |
| --- | ---: | ---: | ---: | ---: |
| Petalburg | 2,860 / 2,004 | 785 / 2,457 | 2.99 / 9.37 | 2,854 |
| Rustboro | 6,000 / 4,220 | 1,907 / 5,315 | 7.27 / 20.28 | 5,990 |
| Slateport | 10,096 / 7,140 | 2,440 / 7,835 | 9.31 / 29.89 | 10,170 |

Scratch payload follows the actual header/alignment formula in `SmolDecompressData`; allocator rounding/header and stack also count. Current fast mode avoids that allocation. Do not move this work into VBlank or extrapolate a universal percentage. Actual warp/loading UI, peak battle/field heap and deepest stack were not measured. Prefer shared assets and selective cold-asset encoding after budget/latency review; preserve animation indices, palettes and tile flips. Broad LTO/refactors are not a justified savings credit.

## 6. Full-game forecast: explicit incremental manifest

Read requirements in [gameplay/content](../design/GAMEPLAY_AND_CONTENT.md), [atlas](../design/REGION_ATLAS.md), [Sinnoh/postgame](../design/SINNOH_AND_POSTGAME.md), [art/audio](../design/SPRITES_AND_AUDIO.md). Every scenario retains the eight-Gym original Averon adventure and villain/dimensional climax, eight-Gym recognizable full Sinnoh/Cynthia/League, both-way gateway and local Fly/healers, legendary/mythical quests, Champions' Circuit/gauntlets, personal follow-ups, optional exploration and Red as final canonical trainer. No map, roster, dialogue, encounter or level curve is authored here.

**All counts below are provisional estimating inputs, not owner-approved designs.** They count *additional* layouts beyond the installed opening. Indoor counts include remaining Gyms (7 Averon, 8 Sinnoh), League/service/residential/story interiors. Dungeon/outdoor counts include story/legendary geography; additional postgame counts are disjoint supplements, not a second charge for Sinnoh's base Battle Zone. Scenarios vary density, unique art and music, not the required existence of entire regions/postgame. Whether the lean allowance can realize the eventual detailed design remains UNKNOWN.

### Actual unit-cost anchors

Native ARM ABI: Trainer **52 B**, TrainerMon **36 B**, MapHeader **28 B**, MapLayout **28 B**, object template **24 B**, warp **8 B**, coordinate event **16 B**, background event **12 B**. Raw layout blocks are **2×W×H B**, plus an ordinary **8 B border**. Budget another **64 B per new unique map/layout** for both 28-byte structures and two 4-byte registry pointers. Event/connection tables and script/text are separate. Every scenario dimension satisfies the current padded map-buffer bound.

| Existing actual linked example | Dimensions | Raw blocks / border B | Object / warp / coord / BG counts |
| --- | --- | ---: | --- |
| Petalburg City | 30×30 | 1,800 / 8 | 9 / 6 / 8 / 8 |
| Route 101 | 20×20 | 800 / 8 | 6 / 0 / 9 / 1 |
| Granite Cave 1F | 42×15 | 1,260 / 8 | 2 / 4 / 0 / 0 |
| Petalburg House 1 | 10×9 | 180 / 8 | 2 / 2 / 0 / 0 |
| Saltmere | 40×34 | 2,720 / 8 | 6 / 4 / 3 / 0 |
| Coastal Bluffs | 64×40 | 5,120 / 8 | 6 / 0 / 0 / 0 |

Existing linked music sequence inputs: **210 `mus_` objects / 651,184 B**, median **2,676 B**, largest **16,396 B**; **275 `se_` objects / 31,516 B**. These are within the 530 sequence objects, not additional ROM categories. New song assumptions below use 2,676/4,096/8,192 B per sequence and separately count only incremental samples. They require legal original/licensed music and instrument reuse; composition/rights/arrangement are UNKNOWN.

### Layout counts and sizes

Cells show `count × width × height`. Town counts include potential districts, not invented extra canonical settlements.

| Incremental region/category | Lean | Expected | Content-rich |
| --- | --- | --- | --- |
| Averon town/district exteriors | 16×40×34 | 20×48×40 | 28×60×48 |
| Averon routes | 34×60×40 | 40×70×40 | 50×80×50 |
| Averon dungeon floors | 55×36×30 | 85×40×35 | 130×48×40 |
| Averon interiors | 120×14×12 | 180×18×14 | 260×22×18 |
| Sinnoh town/district exteriors | 20×40×36 | 26×48×40 | 34×60×48 |
| Sinnoh routes | 35×60×40 | 45×70×40 | 60×80×50 |
| Sinnoh dungeon floors | 75×36×30 | 115×40×35 | 180×48×40 |
| Sinnoh interiors | 180×14×12 | 260×18×14 | 360×22×18 |
| Extra postgame exteriors | 10×60×40 | 20×70×40 | 30×80×50 |
| Extra postgame dungeon floors | 20×36×30 | 35×40×35 | 60×48×40 |
| Extra postgame interiors | 18×14×12 | 35×18×14 | 50×22×18 |
| **Additional layouts** | **583** | **861** | **1,242** |

Metadata budgets per map assume approximately 3/6/10 objects, 2/4/6 warps, 1/2/4 coordinate events, 1/2/3 BG events, plus event/connection structures: **168/284/440 B**. Budget **180 B** for an encounter-table set on each scenario exterior/route/dungeon; interiors zero (an intentionally conservative possible-table count, not encounter placements). Script/text assumptions **1/2/4 KiB per map** cover dialogue, events, movement, Gym/story/legend scripts; density is not measured for unbuilt content and is a major uncertainty.

Trainer assumptions: Averon **450/650/900**, Sinnoh **450/700/1,000**, extra postgame **100/200/400** new records, average **3/4/5 Pokémon**, charged **52 + 42×party-size B** (36-byte mon plus six EV bytes; custom names/other pools must fit scripts/margin). Existing unused trainer slots are not a verified replacement credit. New environmental families: Averon **10/16/24**, Sinnoh **14/20/28**, postgame **4/8/14**, charged **20/24/32 KiB each**, including compressed tile graphics, metatiles/attributes, palettes/night variants and animation allowance. This is a planning range anchored to the existing tileset inventory, not an imported asset package.

New songs: Averon **30/50/70**, Sinnoh **35/55/80**, postgame **15/25/40**. Incremental unique sample budgets total **384 KiB / 1 MiB / 2.75 MiB**. Sequences reusing the installed bank incur zero new sample cost. Character/UI art below excludes installed Pokémon/front/back/icon/follower libraries; their regional incremental cost is **0 B**. Missing future custom art/forms, exact palettes, voices and cutscene requirements remain unapproved/UNKNOWN and consume the stated art/margin budgets rather than silently duplicating every species bank.

### Per-category total growth, bytes

These categories are disjoint. Legend scene/effect art excludes maps/scripts/trainers already budgeted; reserve is unallocated uncertainty, not measured content.

| Incremental category | Lean B | Expected B | Content-rich B |
| --- | ---: | ---: | ---: |
| Unique raw layouts + borders | 915,832 | 1,668,928 | 3,438,496 |
| Layout/header/registry structures | 37,312 | 55,104 | 79,488 |
| Events/connections | 97,944 | 244,524 | 546,480 |
| Encounter tables | 47,700 | 69,480 | 102,960 |
| Scripts + text | 596,992 | 1,763,328 | 5,087,232 |
| Trainers + parties/EV data | 178,000 | 341,000 | 602,600 |
| New environmental tileset families | 573,440 | 1,081,344 | 2,162,688 |
| Additional character/UI art | 229,376 | 524,288 | 1,179,648 |
| New music sequences | 214,080 | 532,480 | 1,556,480 |
| Incremental unique instrument samples | 393,216 | 1,048,576 | 2,883,584 |
| Additional legend/late-scene effects/art | 262,144 | 524,288 | 1,048,576 |
| Engine integration / tables allowance | 131,072 | 262,144 | 524,288 |
| Existing species/followers/mechanics duplicated | **0** | **0** | **0** |
| Reserve | 1,048,576 | 1,572,864 | 2,097,152 |
| **Total additional storage** | **4,725,684** | **9,688,348** | **21,309,672** |

### Region totals and resulting 32 MiB headroom

| Increment / available after full scenario | Lean B | Expected B | Content-rich B |
| --- | ---: | ---: | ---: |
| Remaining Averon, before reserve | 1,329,232 | 2,898,832 | 6,759,992 |
| Full Sinnoh, before reserve | 1,684,248 | 3,633,312 | 8,423,896 |
| Additional postgame, before reserve | 663,628 | 1,583,340 | 4,028,632 |
| **Headroom after all content + reserve: cries ON** | **1,973,824** | **−2,988,840** | **−14,610,164** |
| **Headroom after all content + reserve: cries OFF** | **11,390,472** | **6,427,808** | **−5,193,516** |
| Mega-only cries OFF | UNKNOWN | UNKNOWN | UNKNOWN |
| Approved/verified Hoenn reclamation credited | **0** | **0** | **0** |

Expected milestone arithmetic, before final reserve: default free **6,699,508 → 3,800,676 after remaining Averon → 167,364 after Sinnoh → −1,415,976 after extra postgame → −2,988,840 after reserve**. Cry-off: **16,116,156 → 13,217,324 → 9,584,012 → 8,000,672 → 6,427,808**. A bare two-region map subtotal that omits postgame and reserve would misrepresent the owner's full-game requirement.

Confidence: **high** in pinned builds/unit sizes/byte comparisons; **low** in unapproved count/art/music/script inputs. Largest dependencies are actual layout/scene manifest, dialogue/trainer density, unique tileset art, new instrument samples and scope of late-game assets. A content-rich version can exceed even the measured no-cries budget. No exact future ROM hash or final size can be known before those assets exist. Optional new mechanics such as paused Nuzlocke are not silently implemented or guaranteed by this allowance.

## 7. 64 MiB: real mapping proof, no compatibility promise

GBA exposes a **32 MiB Game Pak ROM window**, mirrored across wait-state regions. A file offset above `0x02000000` is not an ordinary extra linear CPU address. Simply changing the linker from 32M to 64M, appending assets or booting a padded image proves nothing about reading them.

Primary source review, pinned on 2026-10-17:

- [mGBA Matrix implementation](https://github.com/mgba-emu/mgba/blob/9660a668f2093cb4aba5983f52bebf8878dc5b8b/src/gba/cart/matrix.c) and [loader](https://github.com/mgba-emu/mgba/blob/9660a668f2093cb4aba5983f52bebf8878dc5b8b/src/gba/gba.c): oversized file plus `M` at header `0xAC` selects Matrix. Writes at `0x08800104/108/10C`, command at `0x08800100`, map physical offset into the small low-ROM window in 512-byte pages. Validation limits the virtual mapping span to 8 KiB. This is not a transparent 32 MiB second bank; boot/code/asset pointers require a different packaging/streaming design.
- [Current desktop VBA-M loader](https://github.com/visualboyadvance-m/visualboyadvance-m/blob/925f226fdf88c378812ba8b8ab4c8be93b7cbd3b/src/core/gba/gba.cpp) has Matrix remapping and `M`-header detection. Source support is not a local VBA-M execution result.
- Delta main pins GBADeltaCore `869c34aeca9dd2b3fbd329092bb2743b0ae80c98`, which pins [VBA-M `453fa0de`](https://github.com/visualboyadvance-m/visualboyadvance-m/blob/453fa0decf179360926fb417725a794aa496d6e3/src/gba/GBA.h): `ROM_SIZE=0x2000000`. Its inspected loader has no Matrix handling. Do not substitute current desktop VBA-M behavior for this older core. Actual iPhone/Delta result: **UNTESTED**.
- [Zenulator's developer App Store listing](https://apps.apple.com/us/app/zenulator/id6790186767) advertises files up to 64MB. A reproducible public mapping/build protocol compatible with Averon was not established here. No installed phone app or second-bank read test was available: **UNTESTED**, not a pass or failure.
- [R.O.W.E.'s own patcher](https://belialclover.github.io/Rowe-Patcher/) links a special mGBA fork for cries and lists Delta among unsupported emulators. External host audio is a custom-core dependency, not an ordinary ROM compression feature or proven stock-Delta alternative. No R.O.W.E. assets or implementation were imported into Averon.

**Actual mapping experiment:** [original standalone ARM source](../../scripts/coordination/codex_matrix_sentinel.s), no Averon code/assets/Nintendo logo. A local 64 MiB image has distinct words at file `0x2000`, `0x02000000` and `0x03FFF000`; code stays in the first page and maps each into CPU `0x08001000`. Bundled mGBA runner returns **0** after verifying all three. Identical ordinary-`B` header negative control returns **1**. Headers have recomputed checksum; there is no copyrighted binary upload.

Positive ROM SHA256 `93242c403b437d23f7a3d362aa0c20c50341e5e71f0b1b77926c92b75534e2ce`; negative `a097249991e005c76ff00b2062916c54744e67edb8255e1b59a9eda69e400a51`. Runner binary/source hash pins and sentinel ELF/source hashes are in evidence. This is **native mapping-only evidence**, not graphical boot, a banked map/battle, save compatibility, timing, flashcart, VBA-M, Delta or Zenulator acceptance. No production linker, loader, bank-aware pointers or game code was changed. A full Averon-derived banked-map/battle/Save→Continue prototype is deliberately not undertaken: the small-window loader entails substantial architecture and device uncertainty, while the expected scenario has a much simpler conditional 32 MiB path.

| Pure storage arithmetic, **only if** 64 MiB addressability/integration/device gates are solved | Lean headroom B | Expected B | Content-rich B |
| --- | ---: | ---: | ---: |
| Baseline all cries + 64 MiB capacity, after content/reserve | 35,528,256 | 30,565,592 | 18,944,268 |
| Baseline no cries + 64 MiB capacity, after content/reserve | 44,944,904 | 39,982,240 | 28,360,916 |

These rows add exactly 33,554,432 B to the 32 MiB arithmetic. They are **not a measured 64 MiB Averon build or a recommended target switch**. DS migration likewise is not authorized/justified by a conditional size scenario.

## 8. Preparations, thresholds and next executable tasks

1. **Before committing to a cry policy:** manager independently review #115 and the two #55 findings. Keep production default unchanged. If the owner wants no cries, separately claim/fix/test the null-player policy, then actual battle/evolution/Mega/Pokédex/script transitions and deferred audio/device QA. If normal-only cries are preferred, fix the two guarded cry-ID initializers and obtain a new actual RELEASE differential first. No choice is silently made here.
2. **Before Sinnoh integration:** obtain the content/asset manifest and section/met-location policy, then per-PR source-pinned link deltas and approved first map batch. Only **37 further section codes** fit current preserved eight-bit semantics; a full collection of independently named new towns/routes/dungeons cannot be promised unique met locations under that policy. Do not widen Pokémon substructures, repurpose saved IDs or alias visible locations without approval. Existing two-region save/travel is present; non-Hoenn map build filtering, display/Fly/healer registration and numerical Sinnoh progression remain separate reviewed integration tasks.
3. **After an approved representative map batch:** replace assumptions with actual costs for at least an exterior, route, cave and interiors, plus new art/music/event density. Reforecast both complete regions and postgame. Require a **1.5 MiB expected reserve** unless the owner approves another value. Trigger re-estimation when projected growth exceeds **5,126,644 B with cries ON** or **14,543,292 B with cries OFF** (current free minus that reserve), or a content batch exceeds its declared budget. Escalate 64 MiB research only if the approved manifest still exceeds the applicable threshold after specifically verified safe reuse/optimization; require banked asset/map + battle + flash Save→Continue and actual target-device evidence before any platform decision.

**What can proceed as maps now:** separately owner-approved Averon slices and low-level placeholder/test data under genuine map/ID guards and Claude's lane, charging actual bytes per batch. This report is not a map approval and should not delay a separately authorized slice. **What waits:** final Sinnoh balance/rosters/secondary story until Averon progression settles; permanent section/Fly/healer IDs and imports until policy/rights decisions; any 64 MiB conversion until its own approval and proof.

Other hard constraints do not disappear when ROM shrinks: SaveBlock2 **84 B** free, 420 boxed Pokémon, regional save record reserved bytes/versioning, padded map buffer `(W+15)(H+14)≤10,240`, signed map/group/return boundaries, 1,024 field tiles, primary/secondary palette partition, 64 software sprites/16 live objects/16 total OBJ palette banks. Keep region-scale data in ROM and share existing working sets. Unknown worst-case heap/stack/sprite/palette/CPU peaks require focused measurements on actual approved scenes, not growth proportional to region count.

## 9. Reproduction and handoff

Work branch **`codex/rom-capacity-20261017`**, PR #115. Two source-only experimental branches above remain unmerged and must not be mistaken for eligible release changes. Default source, strict failure baseline, protected checks, Claude files and permanent IDs are unchanged. Relevant blockers are documented in #55; no newly demonstrated critical defect in accepted default gameplay is claimed.

In a clean disposable worktree with the supported toolchain active, each source pin builds using `make -j8 -O RELEASE=1`. Record build status before hashing; **never reuse a prior `.gba` after a failed build**. Then:

```sh
python3 ../scripts/coordination/codex_rom_capacity.py . pokeemerald-release.elf pokeemerald-release.gba --output /tmp/capacity.json
# From Pokemon Game/scripts/coordination:
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_codex_rom_capacity.py
```

For native audio, copy the fixture to `engine/test/averon_codex_audio_capacity.c` in the disposable checkout. In engine:

```sh
make -j8 -O pokeemerald-test.elf TEST=1 TESTS='Codex audio capacity' TEST_SRCS='test/test_runner.c test/test_runner_battle.c test/test_runner_args.c test/averon_codex_audio_capacity.c'
/workspace/.onboarding/mgba-rom-test pokeemerald-test.elf > /tmp/audio.log 2>&1
```

Use the locally executable supported runner path for your environment. Inspect nonzero `:P/:F` results; the raw runner can exit zero even when a test fails. Do not patch headless TRUE. The no-cries safety failure is expected evidence, not permission to alter the production expected-failure baseline. Fixtures are not registered in production/native CI.

For the Smol probe, stage the three raw/fast/full files under `/tmp/averon-sinnoh-compression` using the exact gbagfx/compresSmol commands in [readiness §9](SINNOH_TECHNICAL_READINESS_20261017.md#9-reproduction-and-references), with filenames used by the fixture. Copy the compression fixture to `test/averon_codex_compression_capacity.c` and substitute that file/filter in the native command. Three parameter results must be byte-exact, heap-restored and logged; default test ROM is O2, not a shipping RELEASE latency certification.

For cry LZ research, copy each listed existing generated `.bin` into `/tmp/averon-cry-lz`, run `tools/gbagfx/gbagfx sample.bin sample.bin.lz`, decode to `sample.decoded.bin` and `cmp` against input. No production mixer consumes those wrappers. For the accordion trial, preserve both symbols by replacing only the duplicate label/payload with `.global DirectSoundWaveData_sc88pro_accordion_duplicate` and `.set DirectSoundWaveData_sc88pro_accordion_duplicate, DirectSoundWaveData_sc88pro_accordion`; compare a fresh RELEASE to default and restore. For orphan trial, remove the 18 named generated layout definitions and NULL only their corresponding generated table entries, build/measure/check registry, then restore; never edit or delete their map inputs/IDs as part of reproduction.

For Matrix: assemble the provided source, link at `0x08000000`, objcopy locally. Pad to 67,108,864 B with zeroes, place the three documented little-endian words, set header `0xBD=(-sum(bytes[0xA0:0xBD])-0x19)&255`; run `mgba-rom-test -S 3 -R r0 file.gba`. Replace `M` at `0xAC` with `B`, recompute checksum and expect exit 1. No full game/platform inference follows from exit 0.

**Next concrete action for manager:** review the measured report and source-only probes, choose whether to authorize the small experimental audio-config repairs, and obtain the first approved content/ID/budget contract. The technical assessment is complete; alternate gameplay/device acceptance, production removals and a banked game remain explicitly open.
