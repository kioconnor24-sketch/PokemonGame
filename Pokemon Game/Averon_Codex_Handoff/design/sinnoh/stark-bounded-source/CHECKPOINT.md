# Stark bounded source — clean-main recovery, 2026-10-27

Branch: `codex/stark-clean-main-20261027`, accepted base `eec3efd4b9e053583fff97855ab1aaf13a4df7cb` (30 production Sinnoh maps). Original #308 head `42b324183e228cf21d04efb579c03fcfc0fd25cd` and its stacked branch are retained unchanged.

Recovered its 54 source paths plus five exact original rendered references required for replay. All 59 blobs were verified against the original commit before the recovery commit `491a1e50`. No inherited engine/workflow paths were copied or retargeted. The five references were absent from #328's minimal dependency extraction; recovering them fixes the demonstrated missing-file replay errors.

Actual host replay on the merged #328/#330 splitter: **4/4 PASS**. Every one of the **50 generated output hashes** matches #308. Room2's three 32×96 parts reassemble the original cells, collision/elevation and all RGBA pixels exactly. Each part pads to 5,170 cells, below 10,240; the old 96×96 proposal pads to 12,210. Other geometry/art and the two stair returns remain unchanged. The receipt now records the actual 30-map baseline engine and current projection hashes; output artifacts are untouched.

This is SOURCE evidence. No new ROM, native-game, mGBA, Save/Continue, Surf, rail or rock-climb acceptance is claimed. Pending sections remain pending; Route226 stays an external dependency. The original unsplit Room2 must not be registered alongside this alternative. No permanent IDs, production engine, save formats, plot, third-party art or Claude files changed.

Next: independent review of the clean extraction and source provenance, then eligible normal source-only integration. Continue the existing Frontier finding groups separately; do not reopen original conversions or use this source merge as runtime/production approval. #307 remains separately authorization/review blocked.
