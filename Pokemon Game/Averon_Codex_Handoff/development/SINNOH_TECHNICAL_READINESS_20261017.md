# Sinnoh technical readiness assessment

2026-10-17 · Codex · **Planning and read-only measurements; not permission to create content.**

**Conclusion:** a second region is technically plausible within the current 32 MiB cartridge, using shared species/audio assets and a bounded working set. It is **not yet demonstrated to fit**: there is no approved Sinnoh asset manifest or map-count/size specification to measure. The first preparations should be a resource/identifier budget, a saved map-section/met-location compatibility decision, then explicit map-generator and region/Fly integration. Broad engine refactoring, a larger ROM format, removal of existing features, and blanket recompression are not justified by this assessment.

Claude retains final M1 acceptance and its report. This document allocates no map, encounter, story, trainer, permanent ID, or new mechanic. It changes no engine, asset, generator, workflow, save format, or Claude-owned file. No critical existing defect was reproduced; the gaps below concern future content integration, not newly discovered M1 failures.

## 1. Exact baseline and evidence boundary

Assessed main: **`9ae0b32a4b53e552c82bf67f5dfd7a9742a0a3bb`**, complete engine tree **`5d81cc8431cc4c915889b303c22aca2059b78aa3`**. There were no open PRs at the initial scan. Existing M1 conclusions and actual measurements are in [Codex native closeout](CODEX_M1_NATIVE_CLOSEOUT_20261017.md), its [exact native/build metadata](../../scripts/coordination/codex_m1_evidence_20261017.json), and [Claude's separate acceptance report](M1_ACCEPTANCE_REPORT_20261017.md). Claude's graphical conclusion was CONDITIONAL-YES with human audio listening and the Gym 1 text-frame PARTIAL decision still explicit; this assessment does not decide either.

The already completed final native run on main `4f8f987b` has 6,107 results / 5,332 PASS and exactly matches the unchanged strict 327-failure-identity / 329-result baseline. Its engine tree equals assessed main. The actual normal and RELEASE artifacts revalidated at `4f8f987b` have the same production inputs as assessed main. This documentation-only assessment does **not** rerun the full suite or call it a new build. New work here consists of reading actual ELF/map data, linked-object/sample byte comparisons and temporary host compression experiments on existing assets.

Reused local toolchain: ARM GCC 14.2.1 (20241119), GNU ld 2.44, Make 4.4.1, Python 3.12.14. Exact artifacts, each ROM padded to 33,554,432 bytes:

| Artifact | SHA256 |
| --- | --- |
| NORMAL ROM | `e09381d08f29178328c364257502e86cd59ab744b291120390b344ce16ed2e5c` |
| NORMAL ELF | `31efd1c9553d33b773d3d13bfeb584c2d8ff215a9238b1c1d7f8bb002a7d4067` |
| RELEASE ROM | `56c902840cffb587a4add8a021260095e91cab77a2f170f6cf4f14bc333d9ea2` |
| RELEASE ELF | `481510252e229314a4288c9db4e291aec43114e0b2596d18e013c813657d6932` |

A padded 32 MiB file does not mean the ROM is full. Use linked loadable size. Conversely, debug ELF file size and repository PNG/WAV totals are not cartridge usage.

## 2. Capacity that is actually available

| Resource | Current NORMAL | Current RELEASE | Meaning for a second region |
| --- | --- | --- | --- |
| ROM linked used | 26,736,200 B | 26,854,924 B | RELEASE is 118,724 B larger here; LTO is not an automatic space saving |
| ROM remaining | 6,818,232 B | **6,699,508 B (6.389 MiB)** | Shared budget for all remaining project content and code, including future Averon work |
| EWRAM used / remaining | 226,484 / 35,660 B | 226,486 / 35,658 B | Linker remainder is not the current free heap |
| IWRAM used / remaining | 28,392 / 4,376 B | 28,336 / 4,432 B | Remainder includes stack needs, not a new static allocation allowance |
| Static system-stack span | 3,928 B | 3,984 B | Calculated from linked end to `sp_sys`; not measured deepest execution |
| SaveBlock1 used / limit | 15,568 / 15,872 B | same | **304 B free** |
| SaveBlock2 used / limit | 3,884 / 3,968 B | same | **84 B free**, tightest save block |
| SaveBlock3 used / limit | 68 / 1,624 B | same | 1,556 B across the existing sector chunks, not a license to change schema |
| PC storage used / limit | 34,144 / 35,712 B | same | 1,568 B free; 14 × 30 = **420 boxed Pokémon**, plus party |

Source limits: [linker](../../engine/ld_script_modern.ld), [heap](../../engine/include/malloc.h), [field map](../../engine/include/fieldmap.h), [sprites](../../engine/include/sprite.h), [hardware definitions](../../engine/include/gba/defines.h), [storage](../../engine/include/pokemon_storage_system.h), [flash layout](../../engine/include/save.h).

- The existing **115,968 B heap** (`HEAP_SIZE=0x1C500`) is already inside linked EWRAM. Its free/largest contiguous block at runtime is unmeasured here; do not add it to the 35,658 B linker remainder. Map count should primarily grow ROM, not permanently resident RAM: retain one active layout, primary/secondary tilesets and normal transient battle/menu allocations.
- Hardware VRAM is 96 KiB; tiled modes normally divide it into 64 KiB BG and 32 KiB OBJ. Engine field tiles are **1,024 4bpp tiles = 32 KiB**, shared by primary and secondary: Emerald primary 512, secondary budget 512. FRLG-style primary is 640, leaving 384. Metatiles likewise total 1,024, normally split 512/512; each uses eight tile entries. These are per-loaded-pair limits, not whole-region limits.
- BG palette hardware has 256 entries/512 B. Field maps currently load **13 four-bit banks**, split 6 primary + 7 secondary (FRLG 7 + 6). This is not 13 new available banks; UI, effects and day/night behavior still matter. Each bank is 32 B and a 4bpp tile has one transparent index and up to 15 visible colors. Existing palette arrays may physically store 16 banks even though only the relevant ranges load.
- Hardware has 128 OAM entries, but this engine has **64 software sprite slots**, **16 live object events**, and **64 saved object templates per map**. A sprite can use subsprites/OAM entries, so these counts are not interchangeable. The player, follower, NPCs, weather/effects, icons and menu transitions consume the same finite resources. Sixteen OBJ palette banks/512 B is the total; `FreeAndReserveObjectSpritePalettes` reserves a state-dependent subset. No claim of 16 free simultaneous NPC palettes.
- `sBackupMapData` already occupies **20,480 B**. The authoring condition is **(width + 15) × (height + 14) ≤ 10,240 cells**, from `InitMapLayoutData`, not simply width × height. For illustration, 100×75 fits (10,235 cells), 100×76 does not (10,350). Prefer appropriately sized connected areas later, rather than expanding this global buffer.
- Save flash is 32 × 4 KiB with two 14-sector save slots and the existing special sectors. Region state already uses an 8-byte anchor and 64-byte record; it does not need a new save block for Sinnoh badges/return/healer. The record stays wholly inside logical sector 0's 116-byte SB3 chunk. Its reserved bytes are validated zero: they are **not** unversioned scratch space. Existing 68 B SB3 usage leaves only 48 B before the first chunk boundary, despite 1,556 B total headroom.
- Do not add a PC box casually: its 30 existing 80-byte boxed records alone cost 2,400 B, already beyond the 1,568 B PC headroom before names/wallpapers/alignment. Availability of all species does not imply storing every species simultaneously. Any different storage requirement is a separate owner decision and compatibility project.
- Source contains 349 `FLAG_UNUSED_*` and 15 `VAR_UNUSED_*` macro names. These are **not audited free allocations**: aliases, references, temporary/special and daily-reset ranges must be excluded. Persistent story/visit bits need a reviewed ledger; never use a daily/temporary bit just because its name says unused.

Dynamic high-water for heap/stack/OAM/palettes is not newly measured. Claude's older real-play stack measurement of 2,372 B is separately attributed on an earlier source and bounded paths; it does not certify worst-case AI, double battles, decompression or new tilesets. Keep that evidence and add focused measurements only when approved technical work or content warrants them.

## 3. What occupies ROM, and what reuse can realistically save

Fresh reads of the actual NORMAL ELF and link map, not repository directory sizes:

| Loadable section / linked input | Bytes | Interpretation |
| --- | ---: | --- |
| `.text` | 2,348,792 | Code |
| `script_data` | 1,263,160 | Registered script data |
| `.rodata.compound_string` | 367,628 | Compound strings |
| `.rodata` | 22,754,408 | Most assets/tables, includes the input rows below |
| `data/sound_data.o` `.rodata` | **10,422,348** | Voicegroups, tables and samples; not all song sequence objects |
| `data/maps.o` `.rodata` | 710,320 | Existing enabled layout/group/header data |
| `data/map_events.o` `.rodata` | 103,692 | Existing map events |
| `src/tilesets.o` `.rodata` | 688,440 | Most tilesets; other graphics/animations also live elsewhere |

Do not add overlapping section/input rows. An additional 2,208 B of ROM carries initialized RAM data; the section sum alone need not equal linker used size because of alignment.

A second pass matched generated sample bytes **against the ELF at linked labels**, handling inactive preprocessor branches and aliases. It found 105 instrument/other blobs totaling **642,204 B**, 1,156 cry blobs totaling **9,386,416 B**, and 51 phoneme blobs totaling **111,496 B**. These are existing assets, not future Sinnoh requirements. In particular, adding locations for already-enabled Pokémon does **not** require duplicating their battle/follower art or cries. Cry output is already DPCM-compressed in `audio_rules.mk`; promising another universal “50% compression” would be false.

Sized-object inventory corroborates existing coverage: 1,476 `gMonFrontPic_` symbols total 1,580,344 B; 1,466 back-pic symbols total 895,136 B; 1,699 `gObjectEventPic_` symbols total 1,575,744 B (followers and other objects together). These are prefix inventories of sized linked objects, not counts of unique species or an exhaustive asset classification.

**Deduplication measurement:** hashing equal-size ROM `STT_OBJECT` byte ranges (size ≥16), coalescing aliases by address and excluding overlapping candidate ranges gives **118,440 B of candidate redundant bytes** in NORMAL. It is only an upper bound for that scanned subset, not proven removable bytes or a whole-ROM bound. There are 807 equal-byte groups before overlap exclusion. Examples: identical 912 B Floette follower sheets across five colors (3,648 B potential); 1,196 B Florges sheets across four colors (3,588 B); two 2,304 B Man2/DevonEmployee sheets (2,304 B). Differences in palette pointers can remain intentional even when pixels match.

Separately, exact linked sample bytes expose the accordion/accordion_duplicate pair at **5,072 B each**, with 5,072 B candidate redundancy. Do not sum unlike inventories blindly. Relocations, alignment, address identity, symbol visibility, tag ownership, generated references and release LTO can constrain realizable savings. A future dedup PR must preserve logical identities, palettes and all callers, then prove actual linked delta and relevant graphics/audio behavior. Nothing was deduplicated here.

## 4. Compression research and actual bounded experiment

Existing build already supports LZ77, `.smol`, `.fastSmol`, and `.smolTM`; these are not proposed new codecs. `src/decompress.c` dispatches compatible data headers. Do not route Smol through a raw BIOS LZ call, decompress from an unreviewed interrupt path, or treat map block arrays as compressed merely by changing a suffix.

Host experiment: existing Petalburg/Rustboro/Slateport secondary PNGs were converted only into `/tmp`, using their actual 159/498/504-tile crop arguments. Each raw buffer was compressed with current `gbagfx` LZ and `compresSmol` fast/full modes, then **all nine outputs were host-decompressed and compared byte-for-byte** with the raw input. No asset/map source or production binary changed.

| Existing secondary | Raw 4bpp | Current fastSmol encoding | Full Smol | LZ77 | Full vs fast reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Petalburg | 5,088 B | 2,860 B | 2,004 B | 2,300 B | 856 B |
| Rustboro | 15,936 B | 6,000 B | 4,220 B | 5,564 B | 1,780 B |
| Slateport | 16,128 B | 10,096 B | 7,140 B | 8,136 B | 2,956 B |
| Total | 37,152 B | 18,956 B | 13,364 B | 16,000 B | **5,592 B (29.5%)** |

The fast sizes match the corresponding linked sized symbols. This demonstrates lossless host encoding and a small size opportunity, **not GBA decode speed, door/warp latency, peak stack/heap or a universal percentage**. Current fast encodings were selected for loading performance. Benchmark future cold-load assets before selectively preferring full Smol; retain fast formats for demonstrated hot paths. `test/compression/smol.c` provides existing native codec tests, but those were not newly rerun for this prose assessment.

Practical options, in recommended order:

| Option | Expected resource effect | Required proof before implementation |
| --- | --- | --- |
| Share existing species/follower/cries, reusable interiors, common primary art and compatible music samples | Avoid duplicate additions; no existing gameplay loss | Asset/reference manifest and per-PR actual link delta; maintain logical map identities |
| Author new tile art with duplicate/flip reuse and palette discipline | One 4bpp tile saved = 32 raw B and one resident tile slot; compressed saving varies | Remap every metatile/animation/tile-index consumer; render/collision checks; no automatic reorder of existing tiles |
| Alias narrowly proven equal immutable data | Small measured candidates above, no promised MiB gain | Exact-byte/source/address-use review, normal/RELEASE deltas, palette/audio regression |
| Select full Smol for future cold assets | Three-asset example saves 5,592 B vs fast | Target-GBA latency and scratch-space measurements; native roundtrip plus rendered transitions |
| Reuse MP2K instrument banks; bounded new MIDI sequences | Usually much less growth than adding a new bank per song | Track/instrument/loop audit and actual song + sample link deltas; human listening |
| DPCM/rate/loop edits to new samples only if necessary | Potential sample reduction, unmeasured here | Audio-quality approval, driver compatibility, loop/pitch and CPU tests; no blanket change to existing cries |
| Remove unused code/data only after reference proof | Unknown; link already uses `--gc-sections` and RELEASE LTO | Link reachability including assembly/pointer tables, native baseline and gameplay equivalence |

Do not claim savings from feature-removal switches such as `FREE_MYSTERY_GIFT`, `FREE_RECORD_MIXING_HALL_RECORDS` or `PHONEMES_SHARED`. They alter existing features/audio or save layouts and are not safe budget credits. Do not upgrade the entire upstream engine or introduce ROM banking/64 MiB assumptions to make an unmeasured plan fit.

## 5. Pipelines and integration bottlenecks

| Pipeline now | Future technical preparation after approval |
| --- | --- |
| Porymap-compatible `data/maps/*/map.json`, `map_groups.json`, `layouts.json` and raw layout bins → `tools/mapjson` → generated ASM/constants → linked maps | Preserve existing group/index/layout values; append only through an approved ID ledger. Validate dimensions, event counts, warp pairs, connections, masks, enabled headers and layout pointers. Do not edit generated headers as source |
| `map_data_rules.mk`: current Emerald groups explicitly filter out maps whose `region` is not `REGION_HOENN`; layouts likewise select Emerald vs FRLG | Separate **build inclusion** from gameplay/display region. Define a narrow supported Sinnoh inclusion rule before any real map import. Merely writing `REGION_SINNOH` would currently exclude a map. Do not globally enable all FRLG groups or change existing IDs |
| `src/data/tilesets/{graphics,metatiles,headers}.h`, raw metatile/attribute bins, PNG/PAL, callbacks; `INCGFX` converts/caches compiled graphics | Track actual primary/secondary compatibility, 4bpp tile count, metatile count, palettes, night variants and animated reserved indices. Pin Porymap version/config; proposed automatic packing must preserve palette and animation indices. Raw map bins/metatile arrays have direct-pointer consumers; compressing them needs a separately justified loader change |
| `graphics_file_rules.mk`, `spritesheet_rules.mk`, `tools/gbagfx`, `tools/compresSmol`; existing graphics/path audits | Add reporting of **linked**, not just on-disk assets. Current audit scripts explicitly do not prove every asset is linked/renderable. Preserve size/alignment/transparent indices and ownership/licensing; do not import fan-hack art/music |
| MIDI → `mid2agb` with mandatory `sound/songs/midi/midi.cfg` entry → ASM/song table; WAV → `wav2agb` → sample/voicegroup data | Reuse verified instruments, track song IDs append-only, record samples once. Engine initializes 5 Direct Sound channels, with driver maximum 12 and 16 tracks/player; track count ≠ simultaneous sample voices. More songs need ROM, whereas denser arrangements can cause CPU/voice-stealing problems. New mixer/rate/voice-count changes require separate justification |
| Existing registry native tests plus `check-averon-map-registry.py` pins 76 groups / 951 IDs / 534 linked headers | Current pins intentionally reject changes; update append-only expectations only inside the future reviewed integration. The map freeze and protected-file guard must remain genuine; owner approval must be reflected through normal guarded policy, never disabled to pass a content PR |

Current source has 800 layout definitions, including disabled-version content. Current 76 groups leave 52 possible signed-byte group slots; largest group contains 123 entries, leaving five before the 128-entry bound. Counts are not approval to use any slot. Saved `WarpData` and healer group/map fields are signed bytes. Save validators also bound regional return coordinates and warp indices to 127, so map authors must respect those return/arrival interfaces, not only the unsigned JSON event types. There is no need to widen group IDs merely to support a second region.

## 6. Two-region readiness: existing platform vs work still needed

| Boundary | Existing verified platform | Required before future Sinnoh is playable |
| --- | --- | --- |
| Saved identity, 8+8 badges | `averon_region_save.c`: active region, canonical Averon badge flags + Sinnoh byte; legacy/future/corrupt/torn-slot behavior native-tested | Keep format/offsets/semantics unless a real new requirement needs migration; no second full set of save blocks |
| Travel, return, healer, whiteout | `AveronRegion_BeginTravel` validates destination, records departure, uses target return/healer/arrival and sets escape warp; registered special | Authorize and register real destinations and healer/NPC records, then prove inter-region roundtrip, invalid/disabled destinations, escape/whiteout and Save→Continue. A symbolic region test is not Sinnoh geography |
| Caps / obedience / badge consumers | `averon_region_progression.c` accepts a 9-stage regional profile; current Sinnoh profile is **NULL**; fallback is existing behavior | Owner decides numerical progression and badge-consumer policy. Profile storage is 18 const bytes (9 caps + 9 obedience), plus linkage/alignment, no saved field required. Default `AVERON_BADGE_RULE` remains Averon; no silent change |
| Field licenses and visited Fly | Field Kit permissions and bounds/visited behavior are tested for existing destinations | Define owner-approved regional/global license policy; extend visited-bit ledger, heal destinations, Fly eligibility/filter/selection and region map art/labels together |
| Display/section identity | `include/regions.h` classifies Kanto ranges vs Hoenn fallback; `RegionMapType` has Hoenn/Kanto/Sevii, no Sinnoh display branch | Explicit region/section resolver and Sinnoh UI table integration. The engine's `REGION_SINNOH` enum is different from saved `AVERON_SAVE_REGION_SINNOH`; do not interchange integers or infer support from an enum name |
| New saved state | Two-region record already covers badges/returns/healers; normal flag/var APIs and SB3 exist | Allocate only approved persistent quest/visited bits, preserving daily/temporary semantics; add old/new/corrupt/torn-write tests for any schema change |

**Highest compatibility risk: map sections / Pokémon met locations.** The current generated JSON has **215 section entries**, IDs 0–214; `MAPSEC_NONE` is 215. `mapsec_u8_t` and Pokémon `metLocation` are eight-bit; `0xFD/0xFE/0xFF` are reserved met-location meanings. Preserving existing values **including NONE** leaves at most **37 other numerical codes** below those reserved meanings (216–252). This is a capacity calculation, not an allocation. Naively appending to the existing implicit enum would shift NONE; widening just `mapsec_u8_t` would not automatically fix the separate `u8 metLocation` field/substructure and every saved consumer.

First obtain the owner's intended number of distinct named sections/met locations. If it fits, review an append-only generator strategy with explicitly stable existing constants/sentinel; still allocate nothing until approved. If it exceeds this space, compare a separately represented runtime/UI section with an explicit legacy-sized met-location mapping against a versioned all-consumer/save migration. Aliasing different named areas is a visible semantic choice requiring owner approval. Widening Pokémon substructures can pad **all four** secure substructures; do not estimate one byte per Pokémon. PC and flash headroom make an unaudited widening especially risky. This is a future design gate, not a current corrupted-save reproduction.

The current Fly table `sMapHealLocations[][3]` uses **u8** columns although saved regional healer fields are u16; the UI eligibility switches and `GetRegionMapType` are Hoenn/Kanto-specific. New healer IDs and section tables need an end-to-end width audit, not simply a new record entry. Existing bounds tests should remain intact.

## 7. Resource estimate: a planning envelope, not a promise

No approved content manifest exists, so a fixed “full Sinnoh costs X” would be invented. Use measured units and a provisional envelope for **all remaining content**, to be replaced by actual linked deltas. One possible cap set is:

| Growth category | Proposed envelope | Basis / uncertainty |
| --- | ---: | --- |
| Layout blocks and borders | 1.0 MiB | Raw block cost ≈ `2 × width × height` per unique layout. Illustrative 100×60×60 + 300×20×20 layouts = 960,000 B before borders; this is arithmetic, not a proposed geography/map count |
| Headers, events, scripts, text and trainer data | 0.5 MiB | Separate from raw blocks; actual event/script density can dominate |
| New shared tilesets/metatiles/palettes/animation | 1.0 MiB | Reuse families; a pair's uncompressed tile ceiling is 32 KiB, while compressed ROM size varies; no one-unique-set-per-map assumption |
| Additional UI/object/battle graphics | 0.5 MiB | Reuse existing species/followers rather than duplicating their libraries |
| New music sequences and net new samples | 1.5 MiB | Shared banks; new high-rate/long samples can exhaust this quickly |
| Integration code, tables and uncertainty within work items | 0.5 MiB | Measure normal and RELEASE; not a guaranteed optimization credit |
| **Total proposed growth** | **5.0 MiB / 5,242,880 B** | Leaves **1,456,628 B** of current RELEASE ROM as an unassigned reserve |

This is a suggested review trigger, not an owner-approved budget. No candidate dedup/compression savings are credited. Other future Averon assets consume the same envelope. Exceeding a category means re-estimate shared assets and requirements before adding engine complexity; even staying below it does not prove RAM/timing/visual safety.

Working-memory target: avoid new always-resident region-scale arrays; keep layout buffer, object pools and both save layouts unchanged. A 32-destination visit bitmap would cost 4 B if a new one were truly required, but IDs/versioning/flags are separate approved choices; shared existing persistent bits might avoid a new field. Sprite/palette budgets are per scene and need peak observations, not proportional growth estimates per total map count.

## 8. Prioritized implementation plan after owner approval

| Priority / separate scoped deliverable | Estimated engineering effort* | Resource expectation | Exit evidence |
| --- | --- | --- | --- |
| **P0: approve content/resource contract and ID compatibility strategy** | 1–2 focused sessions after owner inputs | Reporting only; 0 runtime/save growth | Approved section/met-location count strategy, intended Fly/visit/healer counts, asset rights and provisional ROM reserve; no actual IDs/maps assigned here |
| **P1: linked-asset and per-change budget reporting using existing tools** | 1–2 sessions | Host tooling only, 0 GBA runtime growth | Hash-pinned normal/RELEASE reports, disjoint object/sample accounting, largest linked contributors, map/palette/tile/section limit diagnostics and nonzero negative fixtures |
| **P1: targeted runtime capacity measurements on existing approved gameplay** | 1–2 sessions, coordinated with Claude's finished acceptance | No permanent save/ROM change required for a temporary measurement build; instrumentation must be disclosed | Heap free/largest block, stack canary, object/sprite/OAM/palette peaks during maps, follower, Field Kit/Fly, battle/menu/whiteout and decompression; actual toolchain/ROM source; no fabricated worst-case guarantee |
| **P2: map inclusion + stable section/display identity integration** | 2–4 sessions, larger if saved-width migration is necessary | Mostly ROM tables/code; no intended SB1/SB2 growth; size unknown until implementation | Approved build-inclusion contract; retained current generated numeric IDs/sentinel; disabled maps stay null; no-map/native fixtures and exact old-save/OT/met-location roundtrip; protected review where applicable |
| **P2: region-map/Fly/healer/progression registration** | 2–4 sessions after owner policy/destination inputs | Profile18 B; UI/table/art sizes TBD; no automatic new save field | Visited vs unvisited, wrong/invalid region, return/whiteout/heal/escape, retained badges/caps/obedience, Save→Continue; native + actual graphical acceptance of approved content later |
| **P3: smallest measured asset optimization, only if the budget needs it** | 1–2 sessions per scoped experiment | Upper-bound candidate savings above; target actual measured reduction, 0 promised gain | Normal/RELEASE before/after hashes/sizes; exact pixels/indices/palettes/sample loops unchanged; native relevant tests and decode/load latency/visual/audio checks |
| **P4: owner-authorized content batches** | Cannot estimate before manifest | Charge each batch against actual remaining ROM and per-scene limits | Owner's map/content approval first; then one bounded playable batch at a time, regression/warps/collision/save/follower and human QA. This assessment does not start P4 |

*Sessions are rough effort bands, not deadlines or guaranteed completion times. Save-width migration or new asset-rights requirements invalidate those estimates. P1 reporting and P0 analysis can be separately authorized without unfreezing maps. Protected files and freeze checks remain active; later actual changes require exact claims, review, applicable CI and genuine approval records. An owner decision to build maps is not permission to weaken those controls.

Preserve gameplay while optimizing: prefer additions sharing immutable content; retain audio/visual fidelity and all current features; change one measured bottleneck at a time. Do not tune AI, sprite-pool constants, save layout or codecs speculatively. A genuinely critical existing failure discovered during future preparation must get an exact reproduction and manager notice, not an unbounded refactor.

## 9. Reproduction and references

Measurements were read from `/workspace/averon48-build-repo/Pokemon Game/engine` artifacts already built at `4f8f987b`; planning branch is main-based. All experiment outputs stayed in `/tmp`, no new map JSON/layout/generated asset input was created. Relevant commands, with the toolchain activated:

```sh
arm-none-eabi-size -A pokeemerald.elf
arm-none-eabi-nm -S --size-sort --radix=d pokeemerald.elf
# Read linked .rodata contribution lines in pokeemerald.map.
# Save/budget reporters are the existing scripts linked by the M1 metadata.
```

Example exact host roundtrip for one existing source (repeat crop counts 498 and 504 for Rustboro/Slateport; compare all three formats):

```sh
tools/gbagfx/gbagfx data/tilesets/secondary/petalburg/tiles.png /tmp/petalburg.4bpp -num_tiles 159 -Wnum_tiles
tools/compresSmol/compresSmol -w /tmp/petalburg.4bpp /tmp/petalburg.fastSmol false false false
tools/compresSmol/compresSmol -d /tmp/petalburg.fastSmol /tmp/petalburg.fast.decoded.4bpp
cmp /tmp/petalburg.4bpp /tmp/petalburg.fast.decoded.4bpp
tools/compresSmol/compresSmol -w /tmp/petalburg.4bpp /tmp/petalburg.smol
tools/compresSmol/compresSmol -d /tmp/petalburg.smol /tmp/petalburg.decoded.4bpp
cmp /tmp/petalburg.4bpp /tmp/petalburg.decoded.4bpp
tools/gbagfx/gbagfx /tmp/petalburg.4bpp /tmp/petalburg.4bpp.lz
tools/gbagfx/gbagfx /tmp/petalburg.4bpp.lz /tmp/petalburg.lz.decoded.4bpp
cmp /tmp/petalburg.4bpp /tmp/petalburg.lz.decoded.4bpp
```

Exact host tool SHA256: `gbagfx` `70de5c3116fddf4a72f93df392c4f98d5547830cf45ed0db6faf242932b8f2c6`; `compresSmol` `7185f7e67994f8a449840cf7ea1b79c2d5df64946fdec666958e624010487d3f`. Temporary JSON capture hashes: ELF/inventory `fed320ba0735827f9a989be4721a115c1fe975e4ec9cbc92d24bf0ad7fa5efb2`; linked samples `e686eb97c638ad73f1ae632ce2d22ab74d93820d6ab687501094aab6c1e28344`; compression `4170fe1e1ac0978fce80877f2a7a3237bc9ff3a6a01e6257bbcb09494e673914`. These hashes identify local capture files, not publicly hosted artifacts; durable selected measurements are in the tables above. ELF parsing used ELF32 section/symbol tables, compared bytes at section-relative symbol addresses and excluded duplicate aliases/overlaps; assembly sample ranges were verified separately against generated blobs. No removal of a candidate was attempted.

Read primary references on 2026-10-17; local assessed source governs compatibility, not the latest upstream version:

- [Tonc hardware](https://gbadev.net/tonc/hardware.html): cartridge/RAM/video hardware capacities; [Tonc regular backgrounds](https://gbadev.net/tonc/regbg.html): tile reuse, screen entries, palette/flip bits. Supports reuse as a method, not a claim that this project's art can be reordered freely.
- [Upstream Expansion 1.13 compressor notes](https://github.com/rh-hideout/pokeemerald-expansion/releases/tag/expansion%2F1.13.0): Smol/fastSmol/SmolTM tradeoffs, wrapper calls and interrupt caveat. No universal upstream compression percentage is used as this project's capacity estimate.
- [Porymap tileset editor](https://huderlem.github.io/porymap/manual/tileset-editor.html) and [project files](https://huderlem.github.io/porymap/manual/project-files.html): existing PNG/palette/metatile/header editing contracts. Porymap was not installed/run here; future importer/editor compatibility must be pinned and tested, not presumed from documentation.

**Deliverable status:** assessment and nine host lossless roundtrips complete; proposed preparations remain unimplemented and approval-gated. No new gameplay acceptance, M1 decision or Sinnoh content approval is implied.
