# Sinnoh parent-section authoring safety

Codex, 2026-10-19. Base `bd705ed5b0987b7a7dcc071d553d5bd89cdcb2d4`. Owner tasks10/12: make physical-map expansion safe without assigning one saved origin per interior. Extends the merged preflight; no new maps/layouts, permanent IDs, source data, engine/save format, Claude QA or CI changes.

## Reproduced boundary

Previously a declared `REGION_SINNOH` header using an existing Hoenn/Kanto section produced only `section-region-mismatch` **warning**, leaving exit0. Runtime origin/name/UI region is resolved from the section, so the build-inclusion marker alone does not make the encounter origin Sinnoh. A new focused test actually failed on unchanged source: **1 identity /3 failing subcases**, using existing `MAPSEC_SALTMERE`, `MAPSEC_PALLET_TOWN` and `MAPSEC_DYNAMIC` in in-memory map documents. No shipped map was changed or alleged broken.

Promote that mismatch to an **error**. A declared Sinnoh header using unnamed `MAPSEC_NONE` is also an error. Unknown section references were already errors and stay so. Outside declared Sinnoh, the legacy NONE review warning remains unchanged. The existing explicit mismatch test is strengthened from expecting a warning to requiring an error; the generator-inclusion positive fixture now supplies an actual existing Sinnoh section. No runtime resolver fallback, legacy ID meaning or displayed name is changed.

## Existing approved parent sharing still works

The positive fixture uses **two distinct existing physical map identities** and one existing parent section216, changing documents only in memory. Both source audits pass with one named origin and correct Sinnoh metadata; no second saved code is needed. The tool does not approve transplanting those real Averon maps or assigning Sandgem's name to unrelated geography. Real interiors must use their geographically correct owner-approved parent. A generic unrelated place-name fallback is not a capacity solution.

The checker cannot infer geographic parent meaning, story suitability, source rights, encounters or owner authorization from a matching region. Those still require the existing content/source review and protected handoff. No13-bit format, migration, grouping of already saved origins or final full-region codebook is adopted. Future runtime/met-location architecture changes require separately reviewing this current section-to-region contract.

## Executed tests

From repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s 'Pokemon Game/scripts/tests' -p test_averon_map_readiness.py -v
python3 'Pokemon Game/scripts/audit-averon-map-readiness.py' \
  --engine 'Pokemon Game/engine' --group gMapGroup_Sinnoh --strict-connections
python3 'Pokemon Game/scripts/audit-averon-map-readiness.py' \
  --engine 'Pokemon Game/engine' --group gMapGroup_AveronOpening --strict-connections
```

Final **56/56 host identities PASS** (53 retained, with two positive/severity assertions correctly tightened, +3 new identities). New cases cover the3 wrong-region legacy sections, Sinnoh-vs-Hoenn NONE severity, and two physical maps sharing one approved parent origin. Initial full run exposed the old warning expectation; it was updated to the stronger error contract, not removed or relaxed. All fixture edits remain in memory.

Real strict source scans: **3 Sinnoh maps /82 dependencies /0 errors /0 warnings** and **16 Averon maps /165 dependencies /0 errors /0 warnings**. `git diff --check` PASS. This is SOURCE/host evidence, not a GBA build, map linkage certification, natural travel or graphical acceptance. Existing source CI compiles the module but does not automatically run this56-test suite; the counts above are actual local runs. No redundant native rebuild is claimed for a host-only severity change.

R1 isolated validation/test work: normal Fast Lane A after final-head applicable checks. Next map batches can reuse correct approved parents and use strict seam checks, while preserving existing IDs/saved origins and running actual builds/native/MAP-QA/Save→fresh Continue. Long-term distinct named-origin capacity remains a separate owner decision.
