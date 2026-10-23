# Celestic / northern Coronet: paired DEV runtime complete

PR229, branch codex/coronet-cave-art-runtime-20261023, stacked on #228 exact527ee10a201e9bbfb0b9ddc0b8491ea697ef0536. Final executable/QA source **cef64ffbdb6da7e6cf19b0f9bda6f8f695bf0b0e**; overlay source7b0c6fb9f6c2cb1d16a043dc90dfd5c5f156da73. Production baseline **c6ac2f967b02473741791eb24b5cc9b11bda3904**. Tested engine tree **c3c51b1bfe3ff4422a091a257c96ec20fc5be974**, repository tree4786b9c0672983c9374270984c9bbfd4f27615a2. Final evidence head is recorded in Issue15. Manager handles normal review/integration; this is not production registration.

## Implemented

All six already-staged maps form one traversed chain: Route210North→Celestic→211East→northern CoronetRoom1→B1F→Room2, with reciprocal returns. Reuse #228's three outdoor outputs unchanged; no reconversion. The9445-cell stage, existing8 foreign-boundary collision closures,48 outdoor bridge15 cells, six coupled warp events(three pairs) and reciprocal outdoor offsets±6/±3 are unchanged.

Cave adaptation uses only actual existing Averon General/Cave pixels, palettes and callbacks. All4232 cave map/border cells retain source C/E and full16-bit behavior/layer attrs. General primary512 records unchanged; shared secondary37 records,475slots free. Explicit roles: source922→stockCave513 floor;932→Cave741 blocked cap;933→Cave575 ladder; pond934–942→General161 water retaining shoreline geometry/full attrs; passable transition strips944–949→General207 stairs without introducing Rock Climb. Remaining used roles use current cave art. No donor artwork/palettes/music distributed. All three cave previews and actual NORMAL/RELEASE cave screenshots inspected. Two complete generations reproduce14/14 files byte-identically at engine-source527ee10a; receipt contains that source identity.

prepare_runtime.py emits40 controlled files only into clean marked exact-c6ac scratch. Temporary slots19–24 preserve production0–18. DEV section217 is a surrogate, never a permanent allocation. Separate outdoorGeneral/Rustboro and caveGeneral/Cave metadata families reuse existing asset/callback bindings; cave DEV music is existing MUS_CAVE_OF_ORIGIN. No production map, registry, global art, Pokémon encoding or save-format edits. Temporary registries from different DEV batches must not be combined blindly.

## Actual results

- Complete matching source **268/268 PASS,0skips**, local and GitHub job120182460991 at exact executable headcef64ffb. Cave-art7 plus runtime16 cases are new; all prior fixtures remain unchanged. Negative cases cover unknown art/attrs/dimensions/banks, malformed warps/seams, unsafe installation, step-on/elevation0 ladders, blocked approaches/origins and settled real-input observation.
- Actual focused native filterAveron **29/29 PASS** and unchanged backwards-save goldens **4/4 PASS**. Exact test identities are in logs: numeric registry/disabled groups, all256 met codes, existing section names, encrypted party/PC data, regional flash corruption/power-loss recovery and new compiled headers/streaming families. This is focused coverage, not the entire unfiltered native suite.
- Actual six-map static audit **0 findings**. Source tests retain every staged C/E/full attr, warp and offset. Static/source results are not gameplay acceptance.
- Graphical **mGBA0.10.5 under Xvfb**: NORMAL **46/46 PASS**, RELEASE **46/46 PASS**. Each walks all six maps, samples three cells per outdoor seam direction, executes all six warp round trips including both ladder pairs/Room2 elevation0, observes following Piplup and reachable exits, opens/closes Start menu and performs a real flash SAVE.
- Each profile: separate fresh emulator loading game-written flash **3/3 PASS**, exact saved state/follower restored; separate genuine unmodified pre-corridor flash copy **3/3 PASS**, legacy state/follower restored. Both load-only flashes remain byte-identical. Original private legacy SHA256 **44cd2e2d651128b18439e9f9763705beee6ae32e6c901fc3f24d982328512f9d** unchanged. Initial DEV entry alone is a disclosed Continue-warp fixture copy at verified walkable Celestic(9,16), layer4. Fresh Continue and legacy tests do not apply that fixture.
- Legacy Saltmere static seam warning remains: north(7,0) faces CoastalMeadow(7,31). It exactly matches both earlier accepted central-seven legacy receipts. It is not a new Coronet defect; the six-map audit is empty. The evidence publisher verifies exact legacy-baseline equality rather than suppressing the warning. No production fix is included.

## Actual resources

GCC14.2.1(20241119), MODERN=1; RELEASE adds RELEASE=1. Cries OFF by production default, original sources retained. Existing newlib stub warnings remain in build logs. Occupancy uses linked __rom_end, not32MiB padded length.

| Profile | Linked bytes | Growth vs c6ac | Free/32MiB | EWRAM/IWRAM | ROM SHA256 |
|---|---:|---:|---:|---:|---|
| NORMAL |17432828|39484|16121604|226480/28392|3ef9056857f7e99fcf2f26fcb967bb40d0e6a88fa1c1ff6faea4560437e0f17a|
| RELEASE |17551948|39484|16002484|226482/28336|2dc41db923035524376fd701fd14e78e3447b58248896055caf6f84bc8691e58|

RAM unchanged from matching baseline. runtime-evidence/source-identity.json records toolchain, all40 installed hashes, exact code/engine/ELF/ROM/asset identities and legacy baseline. EVIDENCE_INVENTORY.json hashes all53 actual evidence files, including20 rendered screenshots. Text files normalize only trailing newlines; private raw originals remain intact. No ROM/ELF/private saves or donor reference image uploaded.

## Preserved failures / corrections

Initial source negative fixture removed nonexistent attribute1:16-case ERROR, fixed to remove an actual key. Initial real NORMAL **FAIL29/34**: four native step-on ladders were approached as standing/facing warps, plus bad entry fixture. First helper replay refused legitimate elevation0 before emulator launch; corrected native zero-transition predicate. Second diagnostic **FAIL36/41**, intentionally interrupted: follower reversal stepped back onto an arrival ladder, triggering another warp. Corrected by leaving to ordinary floor before reversible probes, with settled observations. Next completed run **FAIL45/46** isolated initial Celestic(8,16) as source-blocked: escape to(9,16) worked; reverse correctly collided. The earlier motion-only hypothesis was wrong. Corrected fixture to verified(9,16), regress blocked origins. No terrain/event/game-memory/engine/ROM changes produced final passes. All three failed receipts/events, prelaunch traceback and original host error remain published, clearly FAIL; interrupted diagnostics are not completed traversal.

## Reproduce / boundaries / next

Run adapt_cave_art.py --engine ENGINE --out NEW_OFF_ENGINE_DIR. Invoke this branch's prepare_runtime.py --repo CLEAN_MARKED_EXACT_C6AC_SCRATCH --install and retain receipt. Build make -j4 MODERN=1 and make -j4 MODERN=1 RELEASE=1. Exact native sources/filter/compiler commands are in logs. Existing map_qa.py fixture-save may enter a private copy of real flash at MAP_CELESTIC_TOWN9,16. Run run_runtime_qa.py with matching --engine/--rom/--scratch/--out/--profile/--recipe. A second new process uses --expect saved-coronet-six.json against game-written flash. Independently load original legacy flash with existing map_qa.py --expect. Preserve original flash and source identities.

DEV-only: no natural story arrival, production saved origin, healer/whiteout, comprehensive bridge/Acro Bike/Surf/animation, human audio, Delta or complete canonical Coronet acceptance. Original water/terrain behavior is preserved and permitted art inspected; field progression is not invented. Origins227+, protected production promotion and external south210/west211/216 integration remain separate gates.

NEXT: newest Issue15 comment6354992423 directs #226's existing eight outdoor art adaptations, then12-map eastern current-main DEV tests. Reuse four completed gateways,17warps,97elevated cells and340boundary closures; do not restage. Manager reviews #229 while independent permitted-art work proceeds.
