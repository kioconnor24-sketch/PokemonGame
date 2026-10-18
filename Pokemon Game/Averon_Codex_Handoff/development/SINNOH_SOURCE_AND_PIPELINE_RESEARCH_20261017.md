# Sinnoh source findings and implemented map preflight

2026-10-17 · Codex independent engineering; recovered PR #125 continuation · **SOURCE / HOST-TESTED**

**Author the first approved Sinnoh area natively in Averon's format.** The examined Sinnoh fork has useful geometry, but incomplete content, concrete warp defects and unresolved asset permissions. No donor source/assets were imported. This change implements host validation and comparable resource deltas; it does not implement a Sinnoh map, converter, build inclusion change or new identifier.

Original baseline: Averon main `30a322038f42f23cb81aae62fd8f6496314a8db3`. Continuation recovered remote PR #125 at `2435a379`, preserving the implementation, then normally merged current main `80aac4c1` (#122/#123/#124). The original session checked #15/#26/#55 and the then-open #117/#122/#123/#124. The continuation honors their current merged/ownership state, not those old open-PR descriptions. The continuation uses merged #123 as a library; it does not edit its files or duplicate the namespace audit. Claude retains #117 and all its QA. The scheduled owner instruction authorizes Codex's disjoint technical lane despite the earlier sole-Claude workflow snapshot. Existing local checkouts were preserved; work uses an isolated main-based clone.

## Research: actual donor coverage

Inspected [LiderMorti00/Sinnoh-pokeemerald-expansion](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion) at commit **`a430af4281408b03fdf808e0f5af8d6d2965d676`**, not an assumed current or completed release.

| Observed source | Result / limitation |
| --- | --- |
| Registered Sinnoh map JSONs | **159**, across 18 initial groups; all read at the pinned SHA |
| Layout and binary presence | All 159 layout IDs resolve; Git-tree sizes show `map.bin = 2 × width × height`, `border.bin = 8 B` for each |
| Events | 360 objects, 327 warps, 274 coordinate events, 79 background events; source counts do not prove working gameplay |
| Empty content | 25 maps have no events; 79 script files are under 100 B; Hearthome's inspected script is only a map-script label/terminator |
| Missing interior coverage | Eight indoor groups from Hearthome through Sunyshore are empty; Mt. Coronet has only four registered rooms |
| Tileset dependencies | 29 unique symbols: two primary and 27 secondary; nine custom secondary bundles have geometry, attributes, PNG and palette sources, with NULL callbacks |

Early towns have substantial definitions: Twinleaf is 24×30 with four warps; Jubilife 70×64 with ten; Oreburgh 70×59 with fifteen. Later exterior geometry is more complete than events/interiors: Hearthome is 58×52 with four gate warps and no objects, while Sunyshore is 70×64 with one warp and no objects. Do not extrapolate early coverage to a complete region.

Evidence: [map registry](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/data/maps/map_groups.json), [layouts](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/data/layouts/layouts.json), [layout blob metadata](https://api.github.com/repos/LiderMorti00/Sinnoh-pokeemerald-expansion/git/trees/5bb71f859b38880ac8cbed33b940081a7718256b?recursive=1), [Hearthome map](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/data/maps/HearthomeCity/map.json), [Hearthome script](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/data/maps/HearthomeCity/scripts.inc), [Sunyshore map](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/data/maps/SunyshoreCity/map.json).

### Compatibility and definite conflicts

The donor documents the same Emerald 16-bit cells: low ten bits metatile, two collision bits, four elevation bits. This makes geometry adaptation **plausible**, not byte-identical or playable proof. Metatile numbers depend on exact primary/secondary definitions, attributes, graphics, palettes and behavior meanings. Its nine custom sets include Jubilife, Hearthome, Celestic, Veilstone, Canalave, Snowpoint, Sunnyshore, Valor and Pasos. Existing symbols such as General/Petalburg also cannot be assumed byte-equal to Averon's versions. See [encoding](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/include/global.fieldmap.h), [tileset declarations](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/src/data/tilesets/headers.h) and [metatile source references](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/src/data/tilesets/metatiles.h).

- The donor **prepends 18 groups before Hoenn**. Copying its registry would renumber Averon's saved map identities. Keep existing ordered registries and regenerate local output after any approved append; never copy donor generated headers/tables.
- Two definite zero-based warp bounds errors: [OreburghCity](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/data/maps/OreburghCity/map.json) warp 9 targets [Flat3_F1](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/data/maps/OreburghCity_Flat3_F1/map.json) warp 0, but that target has no warps. [Route218](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/data/maps/Route218/map.json) targets [Route211_East](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/data/maps/Route211_East/map.json) warp 1, but only warp 0 exists.
- Three warps depend on Hoenn interiors: Sandgem's lab points to Birch's lab; Oreburgh's museum to Lilycove Museum; Veilstone's store to Lilycove Department Store. Their presence does not establish native Sinnoh interiors.
- Early events use `VAR_SINNOH_STORY`, `VAR_SINNOH_HAS_POKEMON`, `MUS_DPP_*` and reused Hoenn flags. For example [Twinleaf](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/data/maps/TwinleafTown/map.json) reuses `FLAG_HIDDEN_ITEM_ROUTE_113_TM_DOUBLE_TEAM`; [Oreburgh Mine](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/data/maps/OreburghMine_B1F/map.json) reuses `FLAG_ITEM_ROUTE_110_DIRE_HIT`. These would couple unrelated state if copied.
- Donor Twinleaf connects south to Route220 as well as north to Route201. Exact donor topology is not owner-approved Averon geography. Keep physical/event-space review separate from its Barry/Rowan/Platinum-like progression and our unresolved original story.

A future lawful, justified converter would operate on **one approved map and its dependency closure**, with explicit metatile remapping that preserves collision/elevation and rejects unmapped indices. It would translate map/layout/warp/script references to an approved destination ledger and regenerate output. No whole-hack merge, automated spelling corrections, upstream engine replacement or converter is justified now.

### Source and permission status

GitHub's [repository metadata](https://api.github.com/repos/LiderMorti00/Sinnoh-pokeemerald-expansion) returned `license: null`. No root LICENSE/COPYING file or asset-specific license in the inspected tileset tree was found. The inherited [README](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/README.md) and [credits](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion/blob/a430af4281408b03fdf808e0f5af8d6d2965d676/CREDITS.md) do not establish a grant for the Sinnoh maps/custom assets or guarantee the donor owns them. This is an unresolved provenance finding, not a legal conclusion that every file is unusable.

Before copying, obtain authorship/source and explicit reuse terms for geometry, each custom tileset/graphic, any code additions and music separately, including required attribution and third-party restrictions. The owner decides whether those terms are acceptable. No maintainer was contacted in this session. Until then, native authoring with existing accepted Averon assets avoids this dependency; further fan-project hunting is lower value than a first approved native slice. Prior references to Crossroads/upstream regional metadata in the manager handoff remain architecture references, not cleared asset libraries or solved met-location storage.

Research used read-only GitHub file/tree APIs at the pinned commit; all 159 map JSONs were fetched in bounded batches. A public Git lookup failed once and an oversized API batch failed; switching to small connected-API batches completed the inventory. At the original checkpoint, binary connector output did not supply a trustworthy raw-byte sample. The verified-byte follow-up below now resolves geometry/record decoding for three maps; **donor compilation/rendering/walkability and gameplay remain unverified**. File sizes and source declarations support format compatibility only.

### Verified byte follow-up: three candidate exteriors

The continuation obtained **Git-verified blobs** at the same donor SHA using a filtered bare repository under `/tmp`, never inside Averon or committed to this PR. `git show` bytes were checked against their canonical `blob <size>\0<data>` SHA1. This resolves the earlier binary-transport uncertainty **for these three examples only**. API content had failed both declared size and Git SHA checks (Twinleaf declared1,440 B versus decoded1,690 B); those bytes were rejected, not diagnosed as donor corruption.

| Donor map | Blocks / border | Referenced block metatiles | Different native definitions | Missing native indices |
| --- | ---: | ---: | ---: | --- |
| TwinleafTown24×30 |1,440 /8 B |60 |47 |none |
| SandgemTown34×32 |2,176 /8 B |115 |99 |none |
| JubilifeCity70×64 |8,960 /8 B |251 |157 |862–870 (9) |

All referenced IDs resolve **against the donor's own** metatile/attribute banks. Comparison with Averon's equally named banks shows why geometry is not drop-in: Twinleaf/Sandgem bind General+Petalburg, Jubilife binds General+Rustboro (not merely a bundle named Jubilife). Counts of differing definitions compare both the16-byte tile record and2-byte behavior attributes; graphics, palette appearance and animation equivalence are **not** implied by matching records. Jubilife also uses9 metatiles absent in Averon's Rustboro bank. Reuse, if rights and owner design are approved, requires explicit metatile/behavior remapping or native reconstruction, plus approved asset dependencies; copying map.bin alone is invalid.

Block Git SHAs: Twinleaf `9a05b953e1cb7eacac5389b42b91019a5c4e56ce`; Sandgem `1edcc525f71a1095ec6daed242bf2aebc1733561`; Jubilife `12595aaa72d215853f86582e1d7433f34b47bc4b`. Metadata still reports `license:null` and last push2026-10-04; no new reuse permission established. No donor code/asset was imported into Averon, no maintainer contacted, no donor ROM built or gameplay claimed. The159-map coverage/incomplete-interior inventory above remains pinned research; this is not a second whole-repository survey.

## Implemented: selected-map readiness audit

[audit-averon-map-readiness.py](../../scripts/audit-averon-map-readiness.py) checks a selected batch without generating or editing engine files:

- Map/layout identity, unambiguous registration, current Emerald header/layout inclusion and mixed filtered-group hazards. It hashes build/generator source and rejects changed filter/padding contracts pending review.
- Positive layout dimensions, the actual padded buffer limit `(width+15)×(height+14) ≤ 10240`, exact raw block/border sizes, tileset roles, matching metatile/attribute records and referenced low-ten-bit metatile bounds.
- Actual C symbol references for primary/secondary data, including `gTileset_Building` → `gMetatiles_InsideBuilding` → `primary/building`; no CamelCase folder guessing.
- Warp coordinates, target registration/inclusion/layout, numeric or target-defined symbolic indices, arrival and return-index bounds; cardinal connection edge overlap, reciprocal direction and inverse offset checks. Intentionally one-way/dynamic returns remain explicit review warnings. Dynamic, shared or unresolved symbolic events and indirect returns explicitly require manual review.
- PNG header/chunk CRC and tile-footprint checks, actual graphics-symbol bindings and converter tile-count/VRAM limits, all16 declared JASC palette sources with16 RGB colors. Primary and FRLG tile splits come from fieldmap.h independently of metatile capacities. These are source checks, not pixel conversion or animation proof.
- Reuse of merged #123 section definitions,6 saved-value pins and engine-region mapping; unknown sections, changed pins, reserved MAP_DYNAMIC slots, signed group/map capacity and Sinnoh/header-section namespace mismatch are diagnosed without allocating numbers.
- SHA256/size inventory of selected geometry/visual dependencies and byte-identical candidates. Candidates are informational; nothing is deleted or deduplicated.

The report **does not prove** linked conditional C symbols, converted pixel/animation validity or scene-level palette occupancy, scripts, licensing, collisions, pathfinding or emulator behavior. Select all maps in the approved slice for full geometry checks; unselected targets get only registration/layout inclusion/arrival checks. The CLI refuses report output inside the engine tree. The existing registry pin checker remains authoritative for saved-ID stability; Merged #123 remains the authoritative met-location audit and is reused directly; its source/pin hashes are recorded.

From repository root (replace this existing-map example with approved map names later):

```sh
python "Pokemon Game/scripts/audit-averon-map-readiness.py" \
  --engine "Pokemon Game/engine" --map Saltmere --map SaltmereGreenhouse \
  --json /path/outside-engine/map-readiness.json
python "Pokemon Game/scripts/check-averon-map-registry.py" \
  --engine "Pokemon Game/engine" --mutations
```

The existing 16-map Averon opening batch passes with zero errors/warnings. The baseline also has 20 raw-size anomalies in **unused, unreferenced** legacy layouts; this tool intentionally validates selected content rather than making those old unused layouts a new gate.

## Implemented: comparable linked growth in the existing reporter

[check-averon-resource-budget.py](../../scripts/check-averon-resource-budget.py) retains its old API/CLI and adds `--profile`, `--source-revision`, `--baseline`, and optional `--linker-map`. A comparison requires matching nonempty caller profile labels, matching capacities and a valid complete prior report. It emits signed used-byte deltas for ROM/EWRAM/IWRAM from **linker output**; padded ROM file size is never growth. Metadata is explicitly caller supplied, not verified source/configuration provenance. Use the same toolchain/options/profile for comparable batches.

```sh
# Produce the previous report with the same profile; omit --baseline that time.
python "Pokemon Game/scripts/check-averon-resource-budget.py" \
  --log release.log --rom pokeemerald.gba --json current.json \
  --profile release-cries-off-experimental --source-revision COMMIT \
  --baseline previous.json
```

With `--linker-map current.map`, the same reporter also records stable named ROM input objects, normalizing build-directory prefixes. A baseline carrying the same inventory yields signed per-object growth/removal, sorted by magnitude. Discarded/output sections and RAM VMA are excluded; absolute toolchain/LTO partition paths, initialized-RAM load bytes and alignment remain an explicit **unattributed residual**. Do not sum partial object attribution as a second ROM total or interpret changed temporary LTO filenames as new game assets. Missing paired inventories never fake a mass removal. Malformed inventories/bytes or totals inconsistent with linked usage fail.

A static integration check reused two retained matched GCC14.2.1/LTO **experimental OFF** build logs/maps (old study source8ed13f12+isolated OFF, versus d84f6d52; neither is current main). It correctly reported **+272 linked B**, **556 stable objects with0 attributed changes**, and **+272 unattributed B**. No ROM was rebuilt, no audio/gameplay retest performed and no new production capacity certified. Synthetic tests additionally prove new asset growth, removals and residual arithmetic. Keep separate OFF working-budget and ON restoration baseline reports; never compare unlike profile/toolchain/options labels or treat unmerged OFF as accepted production.

```sh
python "Pokemon Game/scripts/check-averon-resource-budget.py" \
  --log current-release.log --linker-map current-release.map --json current-off.json \
  --profile release-cries-off-experimental --source-revision SOURCE_SHA --baseline previous-off.json
# Repeat on a comparable ON build with its own previous-on.json baseline.
```

Run this existing reporter after each meaningful content build. No CI/build hook was added, because that would overlap the build/audio lane and require separate workflow review. Cries-OFF remains an **experimental intended profile** until #117 is accepted; no new capacity saving or accepted OFF build is claimed here.

## Smallest next production changes and effort savings

1. **Owner selects one real exterior plus linked interior**, approves rough footprints/exits, accepted temporary-art source and the section/met-location contract. The 37 spare byte values are **named sections/met locations**, not a 37-map ceiling. No allocation is made here; old map IDs, section values and saves remain unchanged.
2. Author using existing native JSON/layout tooling and shared tilesets. Keep a small replacement manifest beside the approved asset work: `role, source/terms, 16×16-metatile footprint, palette/tileset, collision/elevation, placements, replacement status`. Reuse one terrain/building family per compatible biome, rather than importing another asset copy per map. Preserve door/ledge/collision footprints when surface art changes; biome appearance still needs owner/rendered review. No new asset library/speculative manifest is created by this research.
3. Make the narrow mapgen inclusion change **with the approved slice**. In current source it is `tools/mapjson/mapjson.cpp` that filters non-Hoenn headers; `map_data_rules.mk` invokes that generator. Layout inclusion separately uses `layout_version` and border-file presence. Preserve null disabled groups and positional IDs; do not blanket-enable FRLG content or hand-edit generated output. Map-section sentinel/storage and any obsolete protected map guard need their own properly reviewed changes, never bypasses.
4. Use the existing normal-build debug warp menu (`src/debug.c`, `DebugSelection_SetWarp_OnComplete`; R+START via `include/config/debug.h`) after checking valid linked header/warp targets. It is disabled on RELEASE; no new teleport framework or permanent debug map is needed. Menu/source presence is not new emulator testing.
5. Run the preflight, saved registry pins, actual GBA build and comparable linked growth report; then genuine mGBA motion/collision/warp round trip/follower/menu/SAVE→fresh CONTINUE. Only that evidence can advance the area register. Final Gym teams/story/events and interregion Fly/healer policy follow their real dependencies, not this tooling change.

Highest-value next Codex task after those decisions: implement the first approved **native** Sinnoh exterior/interior with narrow build inclusion and measured resource growth. Claude's immediate lane remains finishing #117's RELEASE gameplay acceptance after the separately reviewed clinic fix; no audio takeover is implied.

## Verification boundary

The original session used bundled Python with Windows sandbox temporary files redirected to its `work/` directory. The continuation uses Python3.12 on Linux and temporary reports outside engine/. The initial resource test attempt failed on default-temp permissions; workspace temp resolved it without changing assertions. Negative geometry/ID cases exist only in memory, never as new production map files. See the PR HANDOFF for exact final commands/counts and remote SHA.

No GBA/native/emulator/Delta test was rerun for these host-only changes. `engine/` is unchanged, so no new build/ROM/save or cries acceptance is claimed. Original-session WSL discovery returned access denied; no privileged installation or system change was attempted. Existing M1 evidence remains historical, not a result of this session. The area CSV retains every pending production status.


## Continuation validation / next executable task

Preflight tests **40 PASS**, existing resource tests **18 PASS**, event-capacity tests **4 PASS** (62 focused host tests). All16 existing opening maps pass the enhanced preflight deterministically, with0 errors/warnings. Registry remains76 groups/951 saved IDs/534 linked headers;10 mutation controls detected; all6 #123 saved section pins unchanged. No area CSV status advanced. The tool identifies Sinnoh build exclusion and section routing as unresolved contracts; it does not authorize them.

Code progress is on the **existing PR125**, not a replacement. No engine/map/asset/save/guard/CI source edits by Codex, no new builds needed for these host changes, no #117 files or Claude QA touched. Source SHA and exact final commands/check status are in the PR HANDOFF. Next: independent review of125, then an owner-selected real exterior+interior with rough dimensions/exits, accepted placeholder rights/footprints and permanent section/met-location policy. While those content decisions are pending, this validator and partial growth reporter are usable on existing or proposed staged source without making permanent IDs.
