# Sinnoh location IDs, saved origins and region safety

Status: tested non-content foundation; owner scheme/IDs NOT selected. Profiled production implementation `03f7a88a` (engine tree at build: `c08a2f6d842ba5e484490a10e1ef435e8d20a3a9`). Final verification adds only test-label goldens; final source SHA is recorded in the PR handoff on `codex/location-save-region-safety-20261018`, based on main `de1d350c1cb1fdd6021352ab986ce7eeb435d034`. This extends merged #123's research; #117/#125/#126 are reused, not reopened. No production section/map IDs, section JSON values, geography, assets, flags, save layouts or migration are added.

## Recommended owner decision

**For the first approved exterior/interior: use a bounded append-only scheme with a fixed sentinel, no reuse and no save-width change.** Freeze every legacy section value **0–214**, keep **MAPSEC_NONE=215**, and retain **0xFD/0xFE/0xFF** as egg/trade/fateful. Only **37** new ordinary 8-bit codes, **216–252**, are available. An interior may share its approved parent met-name; that content/ID decision belongs to the owner.

Raw216–252 can exist in edited/imported/test saves despite being unassigned on current main. Allocating one gives that formerly unknown byte a name. If preservation must include the unknown-origin text of every arbitrary legacy byte pattern, unversioned A/B cannot guarantee it; approve a version/tag policy instead. This PR allocates none, so all 256 current interpretations remain unchanged.

This is NOT a recommendation to append rows blindly. The current constants template places NONE after the JSON list. A one-row append preserves all six old #123 pins but changes NONE to216 and gives the new name the old sentinel value215. A compiled fixture detects that break. The isolated alternative preserves215 as a hole, explicitly numbers only experimental entries, and keeps a separate runtime count. **That constants-template/ID policy is demonstrated off-tree only and is not adopted by this PR.** Production constants generation and section JSON remain unchanged.

Approve/reject that initial compatibility contract, then choose the first slice's actual section assignments with its physical design. After approval, the next code step is a reviewed stable-sentinel constants generator plus explicit-ID-aware audit/preflight parsing; the legacy snapshots added here remain unchanged. No guard needs disabling. This bounded choice is sufficient for a small slice, not a claim that the complete two-region atlas fits 37 additional met names.

For the full atlas, prefer a separately approved **13-bit saved-origin project (C)** if every new named area must retain a distinct origin identity. Keep **runtime-u16 plus a durable 8-bit name mapping (B)** as the lower-format-risk alternative only if the owner accepts coarser shared met names. Do not silently retire/relabel upstream IDs: legacy/debug saves can contain them too. The 87 Sinnoh tracker rows are production areas, not an approved count/granularity of met names; do not equate either with the951 saved map IDs.

| Approach | What current tests demonstrate | Limit / required decision |
| --- | --- | --- |
| Naive A: append to current JSON | Real jsonproc output moves NONE; a preserved-NONE static assertion fails while old215 identifiers remain pinned | Rejected for the owner's full preservation requirement |
| Bounded A: fixed NONE, explicit append-only values | Actual generated name tables + production C lookup/predicate support216–252 and a215 hole;38th name collides with0xFD and fails the experimental gate |37 new distinct names; approve generator/ID contract before production use |
| B: u16 runtime IDs, unchanged8-bit saved codebook | Production lookup bodies compiled against a synthetic0x1234 entry recognize its name/REGION_SINNOH. Distinct runtime areas can share one8-bit code; direct writes lose high bits | Still only37 new met names if ALL215 old names and the sentinel/specials are preserved; owner must accept grouping. Current MapHeader/grid/TV widths are not widened |
| C: low8 bits plus5 currently unused encrypted bits | TEST-ONLY encoder survives checksums, PC withdrawal and genuine flash reload for limited fixtures; boundaries through8191 tested. Existing API/controller reads truncate0x1234 to0x34; low-byte0xFD aliases an egg marker | Physical feasibility only, NOT an integrated/approved encoding. Requires validated legacy/tag/version policy, all permutations and every consumer/protocol/summary/hatch/trade path before production |

## Implemented safe production foundation

- **Fly gap guard:** zero-filled missing rows cannot replace a prepared warp with map0/0 (Petalburg). The defect is present today, not just in a hypothetical expanded table. The current table has38 absent rows from UNDERWATER_124 through DYNAMIC; two are intentional Southern Island/Frontier switch cases, leaving36 unconfigured rows. A native test failed on unchanged main (`mapGroup0` versus prepared Saltmere group75), then passed after the guard. All154 explicit existing rows are frozen as golden tests, including legitimate Petalburg healing. Existing gender, League flag/position, island/Frontier, route fallback and bounds behavior stays tested.
- **Named-section validity:** bounds plus actual populated name entry, excluding NONE, replaces the assumption that every name is below NONE. Sparse holes remain invalid; UINT32_MAX is rejected before indexing. The summary named-origin predicate remains equivalent for all 256 current met values; it also explicitly keeps0xFD–0xFF out of named-origin handling. The new higher-name capability is tested on off-tree data, not production locations.
- **Optional ROM-only engine-region metadata:** section entries may eventually declare an approved `region` enum (for example REGION_SINNOH). Generated region data and the resolver preserve the existing Kanto range/Hoenn fallback when no override exists. No production entry receives metadata in this change. Every old0..255 region result remains the same, including legacy invalid-ID fallback. Audit/preflight report explicit overrides instead of silently labeling them Hoenn; schema validation rejects numeric/unknown/ambiguous region tags before generation.
- **Separate namespaces retained:** AVERON_SAVE_REGION_* in SaveBlock3 is not enum Region and is not inferred from a met code. A test can keep saved active region SINNOH while the current existing Saltmere map still resolves to engine HOENN, exactly as before. No badges, heal IDs, destinations or regional evolution/progression decisions are changed.

These helpers enable future approved data; they do not allocate it, make the Town Map render Sinnoh, widen map-header/grid/TV storage, register a new healer/Fly destination or create a transition.

## Executed compatibility evidence

- Frozen native assertions cover **all 215 legacy section identifiers**, NONE215 and the three exact special codes; all 951 saved map IDs remain under the existing registry test. BoxPokemon stays80 B, party Pokemon100 B, encrypted payload offset32, saved met field1 B and current MapHeader section field1 B.
- Actual native APIs exercise all 256 byte values through encrypted setters/getters, PC deposit/withdrawal, personality reshuffling across the24 permutation classes and OT rekeying. Checksums remain valid. These are existing values, including unused/special codes; no new gameplay origins are allocated.
- Actual TrySavingData/LoadGameSave tests destroy live party/PC/TV/region RAM, then reload flash and compare the entire PC, party, TV records and relevant region state. They cover natural209–214 origins, NONE215, ordinary boundary216/252, specials253–255, all 256 PC codes and TEST-ONLY C payloads. Every legacy byte is read back exactly. Region state includes active region, a badge, return warp and healer.
- All215 legacy name-table labels are frozen too; six shipped display names are pinned to the existing uppercase strings, including **WINDROW HAMLET**. Sentinel/unassigned/special map-name lookups retain the current18-space fallback. No actual summary-screen rendering or graphical gameplay acceptance is claimed.
- Actual battle-controller get/set handlers preserve all 256 legacy bytes. The fixture replaces only the completion callback, not payload generation/handling. The get reply has one payload byte and leaves a canary beyond it untouched. A fresh recipient loses C's high bits, proving that merely using spare bits does NOT complete that design.
- Existing native region-save tests also pass: legacy RAM-only initialization/next-save upgrade, raw block/PC preservation, anchor/record corruption, mixed slots, counter wrap, newer-format refusal and power loss at each sector.

Current results: **10 compiled host namespace fixtures +17 namespace audit tests +47 map-preflight tests PASS;30 focused native test identities PASS.** Native counts are identities, not a claim that each loop/parameter is a separate test. The complete unfiltered M1 suite is not rerun for this bounded change; strict expected-failure baselines remain unchanged.

### What the C experiment does NOT prove

Its raw high-bit encoder/decoder is compiled only into native TEST builds and deliberately restricted to personality modulo24=0. No production MON_DATA accessor, BoxPokemon declaration, save size/version, migration or encoded origin is changed. Physical raw survival is not semantic integration. Do not assume every imported/legacy checksum-valid Pokemon has zero unused bits merely because project constructors clear them. Test/approve an unambiguous legacy interpretation or tag/version strategy before reusing those bits.

Current sources still have one-byte met setters, daycare/egg-hatch locals and controller REQUEST_MET_LOCATION_BATTLE payloads; summary retains an8-bit cached field. MapHeader, region-map grids and TV records have separate8-bit constraints. Full C adoption needs all permutations, real hatch/trade/controller/summary paths and compatibility/refusal policy; these remain **NOT IMPLEMENTED**, not secretly PASS. B likewise needs an approved immutable runtime-to-met codebook and coverage for TV/other saved consumers. No speculative implementation of either format is included.

## Builds and exact resources

Paired actual builds used the SAME installed ARM GCC14.2.1 (20241119), ld2.44, newlib4.5 and Make4.4.1; default cries ON throughout, without reopening audio work. Baseline source was `de1d350c`; feature production source was `03f7a88a`. Later test/report-only changes leave production source/data unchanged. All four makes exited0. Logs and full binary hashes are recorded here; binaries remain local.

| Profile | Baseline linked ROM B | Feature linked ROM B | Delta B | Feature remaining B | EWRAM / IWRAM B |
| --- | ---: | ---: | ---: | ---: | --- |
| NORMAL | 26,736,188 | 26,736,516 | +328 | 6,817,916 | 226,480 / 28,392 (both unchanged) |
| RELEASE | 26,855,128 | 26,855,696 | +568 | 6,698,736 | 226,486 / 28,336 (both unchanged) |

The ROM artifacts are each 32 MiB padded images; padding is not linked usage. NORMAL logs have 0 warnings. Both paired RELEASE logs contain the same 4 existing newlib `_close`/`_lseek`/`_read`/`_write` warnings and 0 errors (case-insensitive warning scan).

ROM SHA256:
- BASE NORMAL: `7792b7ebbdea0426313657d77f69ed07b1406fad6e791199e25ed5e1a32de8ff`
- BASE RELEASE: `c6c64c11569d1e69172e967c84b8d4a72f3ac91b18997e3483eec3377f399e7c`
- HEAD NORMAL: `cdadd7b4800a3c3f323fad4a25cb13f50e7e5f693fddfd668008e258eeef6c80`
- HEAD RELEASE: `d658b213cb2f8644844b86f7e97535aeea07186657ff3cc15e773f042db59439`

Feature NORMAL ELF SHA256 `00df33f567e0fe809a76a47b03488befd1ce31db37dd3a6376a1a5986887f52c`; RELEASE ELF `bd65e3eda0ab7f9b525dc41f50bd46481dfc56d2903c96c150f8de17c6ce58f0`. Both linked ELFs passed the existing registry check:76 groups,951 pinned IDs,534 original linked headers;10 source mutations and3 ELF pointer mutations detected. Current #123 six pins pass, and opening preflight remains16 maps/165 dependencies/0 errors/warnings. Claude separately owns #129 registry support; it is complementary, not duplicated here.

Save footprints are EXACTLY unchanged: SaveBlock1 **15,568 B /304 B free**, SaveBlock2 **3,884 B /84 B free**, SaveBlock3 **68 B /1,556 B free**, PokemonStorage **34,144 B /1,568 B free**. The base/head linked-ELF headroom reports compare equal. These are static footprints, not new worst-case stack/sprite/palette measurements.

Local test/build evidence is complete; CI and independent source review are separate live PR gates. No self-merge.

## Owner checkpoint and next executable action

1. Review/integrate the safe guardrails and tests through the normal PR process; protected-source checks and independent review remain required.
2. Approve/reject bounded A with **all 0–214 fixed, NONE215 fixed, specials fixed, no reuse, at most37 additional names**. This is the requested precise initial choice, not a new general-preparation milestone.
3. Alongside Claude's physical proposal, approve the actual first exterior/interior, footprints/exits, legal placeholders and exact IDs/section attribution. Codex then implements the approved constants/audit contract; Claude owns map art/construction and authentic graphical QA.
4. Before the37-name budget is exhausted, decide whether full distinct origins justify an approved C encoding project or whether B's coarser names are acceptable. Neither is permanently selected here.

No complete ROM/save, new production map/ID, asset or unapproved story is published. Human audio, Delta and new Sinnoh graphical acceptance remain outside this technical evidence.
