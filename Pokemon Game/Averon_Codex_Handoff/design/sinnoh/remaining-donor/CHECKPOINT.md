# Remaining pinned donor geography — SOURCE ONLY, 2026-10-23

Directive: Issue15 comment6373183781. Branch `codex/sinnoh-donor-reuse-20261023` starts at main `d855ff86785a744264788ff39815cc70581e4c94`; the inventory also inspects exact live #230/#231/#235/#236 heads. Existing production19 + separately staged49 maps were excluded. No completed geography was reconstructed.

**Implemented:**91 additional registered donor maps,67,285 cells, through the existing `eterna-cycle/stage_batch.py` and `sinnoh-donor-map-pilot.py`. Includes the remaining Sunyshore/League/Battle Zone/southern sea geography, LakeValor/LakeAcuity, southern Coronet, Windworks and the unstaged donor interiors. `selection.json` is the exact named list with source dimensions/blob/SHA256. No donor pixels, palettes, music, scripts, objects, encounters, saved IDs or production registrations copied.

Actual converter identity roundtrips91/91. Sanitized candidate headers retain57 internal warps and30 directed connections;2,915 explicitly receipted closures seal unbuilt external doors/edges and final nonoverlapping seams. Each closure changes collision bits alone; all map metatile/elevation bits remain intact. `source-receipt.json` records every changed cell, original technical header, source hash, warp compaction and dependency. 456 complete output files independently regenerated twice, all byte-identical to each other and the committed output.

## Real source defects reproduced and narrowly repaired

- First bulk attempt failed closed: Route221 has the identical `left -> MAP_ROUTE220,offset4` connection twice. Route220 has one reciprocal right connection at-4. The wrapper removes exactly one duplicate under an exact before-list guard; donor source stays unchanged. Before/after are in `neutral_header_corrections`. Route220's separate original up connections to Twinleaf/Route219 are not rewritten: Twinleaf is outside this source-only cluster and its external edge remains closed.
- Attribute preflight found16 interiors using Building468/469/476/477 beyond the donor primary bank's8 records. **Every invalid reference is in the four-cell border, zero in the actual interior geometry.** The unmodified stager rejected this dependency. The existing hash-guarded `repair_border` substitutes the pinned JubilifeCity_Mart border `[1,1,1,1]`, which uses the same Building primary and preserves all border collision/elevation bits. Every original border hash, invalid dependency and before/after word is recorded in `selection.json`/`border_substitutions`; the original undefined behavior/layer values are not claimed preserved. No guessed attributes or global bank changes. All final used map/border attributes resolve.
- The unregistered `LAYOUT_FUEGO_IRONWORKS` metadata exists but its map.bin has **no Git tree entry** at the pinned revision. That declaration is not reusable geometry. Hoenn/FRLG VictoryRoad layout names likewise do not establish Sinnoh VictoryRoad sourcing. The ledger keeps these as gaps.

Focused source tests **8/8 PASS**: all91 actual outputs/source identities; reconstruct exact original hashes by unwinding closures; every used attribute;16 guarded border repairs and changed-source rejection; exact duplicate-connection repair/negative cases; warp bounds/order/no gameplay; reciprocal/final fixed-point seams; invalid selection before output. Ledger tests **11/11 PASS**. First complete source run **448/448 PASS** before two added ledger boundary cases; final complete count and CI recorded in the PR/handoff.

Reproduce (fresh off-engine outputs only):

```sh
python3 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/remaining-donor/stage_remaining.py' --donor /path/to/pinned-donor --out /new/off-engine/output
python3 -m unittest discover -s 'Pokemon Game/scripts/tests' -p 'test_sinnoh_remaining_source.py' -v
```

Pinned donor revision: `38228bb574a3557345852b758d5f1a65eb01bb22`. A partial Git clone may lazily fetch missing exact objects and therefore require network access on the first reproduction. The output contains neutral collision schematics, not final graphics or geographic gameplay acceptance. Placeholder header music is not final music. No NORMAL/RELEASE/native/mGBA/Delta test is claimed for this new batch. Production remains19maps; origins227+ remain owner-only. Next: adapt connected shared graphics families with permitted Averon assets, then build/test coherent disposable clusters before real production integration. Preserve #230/#231/#235/#236 rather than reconstructing their work.
