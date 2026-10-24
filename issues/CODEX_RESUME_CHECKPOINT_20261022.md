# CODEX_RESUME_CHECKPOINT — 2026-10-22 owner-requested stop

Stop requested by the owner after saving all recoverable work. No automatic restart or background engineering is promised. This checkpoint supplements the per-package CHECKPOINT.md files and live Issue #15; newer verified instructions supersede it.

## Saved work and integration state

Last verified main: `c6ac2f967b02473741791eb24b5cc9b11bda3904`. Manager has normally integrated northern production #206 and source packages #205, #208 and #213. Preserve them; do not reconstruct or promote older scratch registrars over main.

| Work | Branch / engineering head | State at checkpoint |
| --- | --- | --- |
| Connected Oreburgh DEV environment | `codex/oreburgh-connected-candidate-20261022` / `2c26ed624dc4f8c6ea14d1f65824af1eb56ae9fe` | [#212](https://github.com/kioconnor24-sketch/PokemonGame/pull/212), open, non-draft, source/DEV review |
| Eterna City, Route 206 and Route 211 West: five source maps | `feabcaed7951d308b4849402eee9848046a5e189` | [#213](https://github.com/kioconnor24-sketch/PokemonGame/pull/213), merged at `c6ac2f967b02473741791eb24b5cc9b11bda3904` |
| Forest and five Chateau interiors | `codex/eterna-forest-chateau-20261022` / `c0a9265c042fbb51a8d347fe49829fbb7a41a4b2` | [#215](https://github.com/kioconnor24-sketch/PokemonGame/pull/215), open against main |
| Hearthome–Solaceon: seven source maps and two adapted gateways | `codex/hearthome-solaceon-geography-20261022` / `ab6041d552766913757e4bf43efdc809f0665418` | [#216](https://github.com/kioconnor24-sketch/PokemonGame/pull/216), open, stacked on #215 |

This checkpoint is a documentation-only successor to the #216 engineering head above. The final PR/Issue handoff identifies its actual pushed commit. Manager review/merges remain pending; no self-merge was performed during wrap-up. Applicable newest checks at those engineering heads passed. Superseded cancelled file-guard and intentionally skipped weekly read-only jobs are not claimed as test passes.

## Oreburgh: actual build, native and graphical evidence

Artifacts: `Pokemon Game/Averon_Codex_Handoff/design/sinnoh/oreburgh-connected/` — recipe, hash-checked source caches, native fixture, QA launcher, detailed checkpoint, 47 evidence files including successful and failed receipts/logs and 12 actual mGBA screenshots.

Frozen runtime base `f0a8bcaa10b410245d240b6014779ba69eb31c74`; actual engine tree `4579c9085d3fc417c784317d4f1e9788eabec22e`; recipe SHA256 `9a15868d30ee3402fb290618f36b32f07fa2463ba7aa14216cbfef4b83cb8f95`. Later source-branch merges do not turn this into current-main runtime evidence.

City, Route 207 and both mine floors are connected to the existing Gate in the disposable DEV environment. Original mine event/return identities and reciprocal ±35 offsets are retained. Gate's four east-doorway cells/event are restored. One reproduced unmatched Route207/City seam cell is closed by changing collision only. Final static audit: zero findings.

GCC 14.2.1, MODERN=1, default cries OFF, generated asset cache reused:

| Profile | Linked ROM bytes | SHA256 | EWRAM / IWRAM bytes |
| --- | ---: | --- | --- |
| NORMAL | 17,410,100 | `9e81fb199833f26290bf568028c02a02eda70257a2339b70fd30cee6febf02cb` | 226480 / 28392 |
| RELEASE | 17,529,236 | `7f1b592e34775c83e168e5a75018c035620e2fe96ae9ea55b1fc69c249564686` | 226482 / 28336 |

Growth against the same frozen Jubilife baseline: +50,292 / +50,300 ROM bytes, zero RAM delta. RELEASE ROM headroom: 16,025,196 bytes. Existing newlib stub warnings are retained. This is actual compilation/linking with ELF/ROM byte verification, not a fresh clean-build claim.

Actual graphical mGBA 0.10.5, **each profile independently**: walking/warps/follower/menu/save **79/79**, fresh-process Continue **3/3**, separate upper Coronet closure **6/6**, genuine unmodified pre-corridor save load **3/3**. Old flash SHA256 `44cd2e2d651128b18439e9f9763705beee6ae32e6c901fc3f24d982328512f9d` remained unchanged after both legacy trials. Disclosed DEV-entry copies are separate from the genuine legacy baseline.

Actual focused native **29/29** and save goldens **4/4**, including all ten required runner/fixture sources listed in evidence/source-identity.json. Full source hosts **221/221**, zero skips, also verified in [Actions job 119832628998](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/39781207130/job/119832628998). This does not replace or relabel the full M1 strict native baseline.

The retained failed trials document: nonexistent music symbol caught at link; source seam collision; initially omitted native runner sources; invalid northern seed used with old DEV slots; unwalkable Muddy Slope; follower probe attempting that slope; and exact-position probe after follower placement. Corrected trials actually passed. No terrain, assertion result, engine memory or baseline was silently changed to manufacture acceptance. Existing Saltmere static warning remains disclosed separately.

## New geography and permitted art

All donor geometry is pinned to `38228bb574a3557345852b758d5f1a65eb01bb22`. Existing converter/stager is reused. Source receipts retain exact map/attribute blobs, geometry, collision/elevation, paired warps and explicit closed unbuilt exits. No donor gameplay scripts, trainers, encounters, pixels or palettes were imported.

- **#213:** EternaCity, Route206_North, Route206, Route206_South, Route211_West; **7,866 cells**. Source round-trip and 26-file repeat generation passed. Source-only, outdoor artwork not adapted.
- **#215:** EternaForest, Chateau Entrance, DiningRoom, 2F and SideRoom1/2; **8,343 cells**, 31 internal warps including 17 upstairs/self-room events. Focused **13/13**, full source **215/215**, zero skips, independently verified in [Actions job 119845805291](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/39785022798/job/119845805291). Six-map generation and both art passes reproduced byte-for-byte. Four interior previews use identical existing Averon pixels/used palette colors. Entrance uses existing Museum art with exactly four disclosed pattern substitutions affecting metatile660 at12 cells/3,072 pixels; this is not full source visual equivalence. All five physical Chateau interiors now have permitted static artwork. Forest Valor artwork remains unadapted. Guarded repair of donor SideRoom2's invalid border is documented and negatively tested.
- **#216:** HearthomeCity, Route208, both Route208/209 access interiors, Route209, SolaceonTown, Route210_South; **17,582 cells**. Geography **9/9** plus gateway-art **5/5**, full combined source **229/229**, zero skips, independently verified in [Actions job 119848029291](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/39785654226/job/119848029291). All 36 source outputs and nine gate-art outputs reproduced. Both neutral Averon gateway adaptations preserve all234 cells' collision/elevation and complete behavior/layer words. The isolated bank retains original prefixes, has 294/512 secondary records, and removes 9,072 unused primary-padding bytes. These are source artifact counts, not linked ROM savings. Outdoor art remains unadapted.

The Eterna, Forest and central packages are **SOURCE / STATIC-ART evidence only**. They have not received native ROM or genuine mGBA acceptance. Static previews are not follower, animation, warp, save or ordinary arrival acceptance. The same-map Chateau warps need coordinate-aware runtime assertions because the current shared warp helper expects map-ID changes.

## Preservation, blockers and exact resume action

- Existing permanent section/met-location IDs, map registry prefixes, save schema and main production files were not reassigned. Origins227+ still require an owner decision. Published new-area headers retain MAPSEC_PENDING_OWNER. No new permanent identity is implied by a source map or temporary metatile number.
- The frozen Oreburgh runtime uses conspicuous existing217 only as a private DEV surrogate and old temporary slots13–16. Main now has legitimate northern slots13–18. **Never merge that scratch engine or promote its saves directly into production.** First reconcile append-only current-main registration under the actual identity policy and protected-path handoff.
- Manager handles pending source review/integration. If #215 merges, refresh exact main and normally retarget #216; preserve its existing source history and recheck the new comparison. Do not rebuild the geography.
- The runtime worktree `/workspace/averon-corridor-scratch` is intentionally preserved dirty. At wrap-up all **34/34 overlay files were compared byte-for-byte with the pushed reproducible recipe**, with no unique runtime edit left only locally. Build ROMs/ELFs, private flash and caches stay local; none are uploaded. No active build/emulator or paid autonomous continuation is promised.
- Clean source worktrees retain only generated Python caches as untracked files. No substantive source edits remain uncommitted. Disk inode pressure is real (about22k free at checkpoint); reuse existing checkouts rather than create redundant full worktrees/clones. No contributor branch/work was deleted.

**Next executable task:** refresh main/Issue15 and these three PR heads first. Continue permitted-art adaptation of EternaForest's Valor family and the Eterna/central outdoor families while preserving accepted source physics and closed exits. Alternatively prepare a current-main Oreburgh DEV reconciliation that preserves merged northern registration; obtain the genuine permanent-origin decision before production promotion. Then perform real paired builds and controller-driven runtime checks on each newly integrated source state. Keep story, services, bike progression, natural whiteout, human listening and Delta explicitly unaccepted until actually tested/authorized.
