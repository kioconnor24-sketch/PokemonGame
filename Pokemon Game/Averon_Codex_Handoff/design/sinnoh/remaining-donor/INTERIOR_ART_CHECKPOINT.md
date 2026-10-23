# Shared permitted indoor test art — 2026-10-23

Stacked on source PR #237@86713bdfca4afbb8839c4fffd30c2ef11db50908. No #237 source map, border, header, source receipt or protected inventory file changed. All42 selected Building-primary maps retain at least one real source portal in the sanitized batch; exact names/dimensions/anchor order are pinned in `adapt_interior_art.py`. This is the next art-construction task after91 actual source maps, not another converter.

Reuses the merged central gate packer unchanged, over5,811 cells. Stock Building/Shop floor/wall/counter/mat templates replace foreign graphics with neutral test art. Retained stairs/doors are marked with mats; neutral counters represent blocked source furniture. Every map collision/elevation/full16-bit behavior/layer word is preserved. Source geometry/header/portal arrays remain byte-identical. Both Building metadata prefixes are the real8-record bank, not padded published art; Shop prefix unchanged; isolated secondary331/512 records,181free. Tile/palette closure and rendered pixels are verified. All89 generated files reproduced twice byte-for-byte; final representative EternaFlat1F2 and Windworks previews inspected.

This is **test art**, not faithful donor/final room appearance, services/story, natural accessibility, engine integration or runtime acceptance. Orange stock flooring/neutral counters are intentional proxy visuals. No donor pixels/palettes/music copied and no existing shared General art replaced. Rooms without retained source portals are excluded rather than inventing portal coordinates. Two other gates currently have no retained source portals and are not represented as functioning travel.

Focused tests **5/5 PASS**: every42-map cell/source attribute; exact anchors; canonical existing asset hashes; real bank prefixes/capacity; full pixel rendering/tile/palette closure; missing/reordered/out-of-bounds/non-neutral portal fixtures rejected before creating output. Initial asset-hash assertion compared CRLF working palette bytes against canonical committed LF bytes and failed; corrected the test to use the existing `verified_file` canonical-Git + working-copy verification. No asset or hash baseline was changed to hide a mismatch. Complete host suite **455/455 PASS, zero skips** (59.217s). Final-head CI remains independently recorded in the PR.

Reproduce with new off-engine output:

```sh
python3 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/remaining-donor/adapt_interior_art.py' --engine 'Pokemon Game/engine' --out /new/off-engine/output
python3 -m unittest discover -s 'Pokemon Game/scripts/tests' -p 'test_sinnoh_remaining_interior_art.py' -v
```

Current source PR #237 has450/450 host PASS (also independently downloaded Actions job120628313786), but its three new inventory files under development/ require a genuine owner-reserved exact-path handoff; do not self-author that marker, relocate to evade protection, or merge failing checks. Issue15 comment6373678700 records exact paths and head. This art branch changes disjoint nonprotected paths and continues engineering while that handoff is pending. Next: bounded disposable linked two-floor room cluster tests using this actual source/art; final visual refinement and production identities stay separate. Four specific Twinleaf house floors now have paired build/native/mGBA evidence in ROOM_RUNTIME_CHECKPOINT.md; the remaining38 candidates retain static test-art status.
