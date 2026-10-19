# Sinnoh resume regression and invalid-section repair — 2026-10-19

## Source and reproduced defect

Implementation: [PR #154](https://github.com/kioconnor24-sketch/PokemonGame/pull/154), source **`82d5d8d7f7e61c085ccf2174800ad8e557e5a1bd`**, engine tree **`fff133a3da2b11cf4f0f5646706775d91915e076`**. Base `a7d87067cef500afc0e8ee1ea1ba26d9a5cd9f6d`; later main `862f8205` changes QA tooling only, with the same baseline engine. #148 is already merged and is not repeated. Codex independently reviewed #153 at `fa6a3ce54fb6fcbc5b15ca087f2ed2d655f133b7` and normally integrated governance as `a7d87067`; the owner fast lanes govern subsequent work.

**Actual native RED:** unchanged main reports `IsRegionMapAvailableForSection(MAPSEC_NONE) == TRUE`. `GetRegionForSectionId` deliberately retains a Hoenn display fallback for unknown identifiers, and the availability predicate had trusted that fallback. The final regression against the original production function fails **1/1**, before opening UI or dereferencing invalid map metadata. This is an API/invalid-metadata defect; no ordinary-player Petalburg misrouting or existing approved-map regression is asserted.

The only production change is an existing `IsRegionMapSectionIdValid` check in `src/regions.c`, plus its header include. Invalid/unallocated/NONE/special-origin aliases cannot authorize a map grid. Valid legacy sections and explicit Sinnoh behavior retain their meanings; region/name fallback itself remains unchanged. No map, permanent ID, save format, workflow, or Claude-owned path is changed. This runtime fix retains peer review, rather than being misclassified as Fast Lane B.

## New native coverage

All new code is in `engine/test/averon_sinnoh_resume.c`, separate from Claude's Route201/respawn tests. Four test identities pass through the actual mGBA native runner. With two linked Sinnoh maps, the function runner executes **104 parameter combinations**:

- Two real layout-boundary cases, each checking valid corners, out-of-bounds/mixed coordinates and indexed-warp limits.
- Two flash reload/resume cases, preserving encrypted party/PC data and both badge banks, rebuilding the runtime map header, refusing Fly/Town Map/PokéNav, and travelling both ways using persisted return targets.
- **60 interrupted-return/control cases**: two endpoints × two flash-slot parities × cut positions0–14. The56 interrupted cases recover the complete older Sinnoh state; four completed controls recover the complete newer Averon state. Region record, heal/escape/location warps, badges, money, party and the **last PC slot** are checked together.
-40 invalid 8-bit section cases (NONE and217–255 on this source), checking all three UI paths and raw u32 API values256/0xFFFFFFFF.

Endpoints and the healer are read from production tables. After section217/healer44 integrate, this matrix adds Route201 and exercises the real Sandgem healer without new allocations or copied implementations. Future expected combinations are not claimed as already executed here. Claude's existing ID/name/summary and successful healer flash tests are not duplicated. Previously merged #134/#136/#137/#140/#141 already cover all256 origins, legacy identifiers, permutations/hatching, generic outbound travel, legacy-format flash migration and save failure paths.

**Full focused Averon suite: 288/288 PASS**, including these four identities and the existing legacy/save/storage tests. No expected-failure baseline was altered. This is not a new unfiltered M1 closeout or a load of a private owner save. Test setup uses engine calls and real emulated flash; it does not prove ordinary story access, a graphical fresh-process Continue, walking into the Center, or battle-driven whiteout. Those acceptance gates remain with the map/respawn author.

One initial fixture assertion compared unused WarpData padding after decoding a return warp; it was corrected to compare the five defined fields. It is not counted as a production defect. An initial launcher/path/discovery error and missing test header were fixed before the final RED/GREEN runs; no zero-test preparation run is reported as PASS. Flash/region snapshots still compare actual saved bytes where byte identity is meaningful.

Exact-head CI also passed **288/288**: run39213804857/job117932908699, artifact12168818486, zip SHA256 `5cd629bbee24f5f75ea927ef4fa20a1a65e3b50cf065aa6cb4ddd5bb2090dfeb`. CI ROM SHA256 `f49b009175a3e6fa6e600e4a22b8c6d56876513ab56cd7fa73697ea02d32add9`; its GCC13/newlib4.4 differs from the local toolchain. All applicable file-guard/exclusive-files/production-config/route checks passed at82d5d8d7; weekly read-only audit is inapplicable/skipped. Recheck later-head checks before integration.

## Actual NORMAL/RELEASE and control builds

Local GCC14.2.1 (20241119), binutils2.44, newlib4.5.0.20241231; MODERN ordinary builds with no CRIES argument/environment override: **OFF default**. Each control overlays only the original `regions.c` while retaining the final test file, which is excluded from production linkage. `git diff BASE -- src include data` was empty during control builds. Candidate source was restored in a finally block. Both profiles were then rebuilt and reproduced their candidate ROM hashes byte-for-byte. Six actual builds, sequentially; no full ROM/ELF/save uploaded.

| Profile/source | Linked ROM | ROM free | EWRAM / IWRAM | Warnings |
| --- | ---: | ---: | ---: | ---: |
| normal-control | 17,323,760 B | 16,230,672 B | 226,480 / 28,392 B | 0 |
| normal-candidate | 17,323,776 B | 16,230,656 B | 226,480 / 28,392 B | 0 |
| release-control | 17,442,936 B | 16,111,496 B | 226,482 / 28,336 B | 4 |
| release-candidate | 17,442,912 B | 16,111,520 B | 226,482 / 28,336 B | 4 |

**Observed linked delta:** NORMAL **+16 B**, RELEASE **−24 B** with LTO. No RAM or SaveBlock growth. Release's four newlib syscall notices also occur in its control build; no new warning. These are exact measured pairs, not promises of the same optimizer delta on later content.

ROM SHA256:

- normal-control: `6fc04ed737c033e5a74c7441966df83d766124ac6decdeab6bd3a86429949d2d`.
- normal-candidate: `3563dfded2ceb22a785b5b0f5be815d036da547a883b4b2c35e906b9fbe86cc7`.
- release-control: `d2e49d11414e023ec78e87082ed49c75ea21b85c3449f5f443a3eb18c195fbaf`.
- release-candidate: `eccbb982aa8e63e2dda95d0a901a16c7b4c0f2ca35abc269659b771c3c931acc`.

Every measured ELF retains free space: SaveBlock1 **304 B**, SaveBlock2 **84 B**, SaveBlock3 **1,556 B**, PokémonStorage **1,568 B**. BoxPokemon/party sizes and encoding are untouched. Cries sources remain retained; this work makes no audio change. Runtime stack/VRAM/palette peaks and human/Delta acceptance are not established by linker measurements.

## Registry, capacity and integration status

Source audits on82d5d8d7 pass: registry **77 groups /953 pins /536 linked maps**, **12 negative mutations detected**, **1 valid extension**; Sinnoh preflight **2 maps /80 geometry dependencies /0 errors /0 warnings**; section pins preserved. There are **36** ordinary codes217–252 before Route201, **35** after its approved217 allocation. NONE215 and specialFD–FF remain fixed. The registry reports51 signed group slots available; the current two-entry Sinnoh group has126 remaining map-number slots before signed8-bit limits (125 after Route201). Additional future groups/IDs require approval; this does not authorize construction or an expanded origin encoding. Layout buffers and asset budgets impose independent limits.

Advisory source checks of #150/#151 found no reproduced defect: JSON comparisons preserved every existing section, all43 healer rows, group order and old map slots; only approved appends were added. #150/#151 remain author-owned Fast Lane B work until their exact handoffs, real acceptance and final checks are complete. Codex's advisory check is not a waiting gate. Old-ROM downgrade after saving healer44 remains unsupported as disclosed by its owner-approved packet.

Next: when Claude integrates those sources, refresh actual main and run this matrix against the real section217/healer44 tree. Until then, an explicitly labeled temporary combined-source native experiment may provide early engineering evidence without adopting maps or claiming gameplay acceptance. #154 itself still needs the retained independent runtime-source review. No new manager approval service or organizational reset.

## Reproduce

From `Pokemon Game/engine`, using the recorded source and toolchain:

```sh
make -j4 -O check TESTS="Averon Sinnoh resume" ROMTEST=/workspace/.onboarding/mgba-rom-test
make -j4 -O check TESTS="Averon" ROMTEST=/workspace/.onboarding/mgba-rom-test
make -j4 -O RELEASE=0 all
make -j4 -O RELEASE=1 all
```

The ROMTEST override identifies this environment's actual runner; elsewhere use the bundled executable. Run resource-budget/save-headroom tools on each actual log/ROM/ELF as documented in #148. Default-OFF source/ROM hashes above refer to82d5d8d7; documentation-only follow-ups do not relabel those measurements as a later main build.
