# Stark bounded source — clean-main recovery, 2026-10-27

Branch: `codex/stark-clean-main-20261027`, accepted base `eec3efd4b9e053583fff97855ab1aaf13a4df7cb` (30 production Sinnoh maps). Original #308 head `42b324183e228cf21d04efb579c03fcfc0fd25cd` and its stacked branch are retained unchanged.

Recovered its 54 source paths plus five exact original rendered references required for replay. All 59 blobs were verified against the original commit before the recovery commit `491a1e50`. No inherited engine/workflow paths were copied or retargeted. The five references were absent from #328's minimal dependency extraction; recovering them fixes the demonstrated missing-file replay errors.

Actual host replay on the merged #328/#330 splitter: **4/4 PASS**. Every one of the **50 generated output hashes** matches #308. Room2's three 32×96 parts reassemble the original cells, collision/elevation and all RGBA pixels exactly. Each part pads to 5,170 cells, below 10,240; the old 96×96 proposal pads to 12,210. Other geometry/art and the two stair returns remain unchanged. The receipt now records the actual 30-map baseline engine and current projection hashes; output artifacts are untouched.

This is SOURCE evidence. No new ROM, native-game, mGBA, Save/Continue, Surf, rail or rock-climb acceptance is claimed. Pending sections remain pending; Route226 stays an external dependency. The original unsplit Room2 must not be registered alongside this alternative. No permanent IDs, production engine, save formats, plot, third-party art or Claude files changed.

Next: independent review of the clean extraction and source provenance, then eligible normal source-only integration. Continue the existing Frontier finding groups separately; do not reopen original conversions or use this source merge as runtime/production approval. #307 remains separately authorization/review blocked.

## Bounded rendered runtime verification — 2026-10-27 EDT

Source-only recovery #339 merged at `4e2aab1d41144234372b0bee16f26f9126e17ece`. This follow-up reuses the existing 74-map DEV scene instead of rebuilding geography. A read-only audit proves all seven staged Stark maps match source `ba0f90cf8f10b1651f54462ae863d36d7e2a3d61`: 16,192 block words, borders, warps/connections/events, every used metatile record/attribute, graphics/palette bindings and callbacks. All 191 scene payload hashes remain unchanged. Temporary engine tree: `70693ba03323ca8412afcacdfb9ab8f5efc0361f`; production engine remains `63d0c037e0da9a93b5e1a968c078d9622b56c691` (30 maps).

The bounded probe covers Outside, Room1, all three Room2 strips and Room3, plus the immediate Route227 seam and return. Genuine nonheadless mGBA 0.10.5 uses ordinary controller input and read-only state observation. Each profile starts from a separately relocated private game-written flash fixture; no item/ability grants, collision flattening or runtime RAM writes.

NORMAL ROM SHA256: `c1279decfd288888b9a53e52a8324f2fea5f5e1bb144948e74f6052ef7e6c377`; RELEASE: `6d12a0530a77f3e0ca5be1705d72c139e1075e1e699b7bf484214d2c2a5705c4`. Both are CRIES=off, built with ARM GCC14.2.1. Linked ROM: 17,517,796 / 17,636,932 bytes; EWRAM:226480 /226482; IWRAM:28392 /28336. SaveBlock headroom remains304 /84 /1556 bytes and PC1568 bytes. ROMs, ELF and private saves stay local.

This does not accept full Route227/226, Surf, bike/rail, rock-climb acquisition, ordinary story access, natural respawn, human audio or Delta. Temporary saved-section aliases can display Route201; no named Stark origin is allocated. All33 full-scene static findings and the Route228 overall FAIL3/4 remain recorded, not cleared by this narrower test. Existing native evidence completes322 unique Averon test identities across split runs on the unchanged engine tree, with the original interruption and bounded timeout preserved; it is not an uninterrupted or unfiltered full-suite result.

Actual results: **NORMAL48/48 traversal +3/3 fresh-process Continue; RELEASE48/48 +3/3, all PASS**. Focused source replay4/4 PASS. Both profiles restore Room3(7,16), party, follower, bags/money and recorded flags; fresh Continue leaves the game-written flash SHA unchanged. Start-menu return and real Save callbacks pass. Selected screenshots were visually inspected. Full checks, saved-state snapshots, source proof, resource reports and raw-log SHA256 identities are in [RESULTS.json](../../../../../../issues/evidence/stark74-20261027/RESULTS.json).

Next: retain this bounded DEV evidence; production needs approved origins, guarded registration and its own final integration proof. Full Route226/227/228 capability acceptance remains open; current source inventory records453 ocean-water cells on226, and mud/rail/water on227/228, without clearing the existing findings. Continue the final49-map W25 post-C native/rendered gate on #337, then reuse the existing South42x32 source for packet D. #307 remains undispatched.
