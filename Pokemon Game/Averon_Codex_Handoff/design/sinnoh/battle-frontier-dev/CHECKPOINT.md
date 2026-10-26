# Bounded Battle Zone / Frontier / Stark DEV scene
Tested code ba42d7cbff9469a43380498926ad6b0f9beb00db. BASE f57a79eaf8060bd1da4c412e703345f560dad30a, exact engine tree c2e26cce0a00af43251e0672fef708c796b7a918. Fresh main was fetched: only accepted QA fixture changes since the prior snapshot, engine/contract unchanged. Source script works in shallow checkouts using pinned engine-tree identity, not an unavailable side-branch object.

## Implemented
44 unique temporary maps combine existing #295 towns/rooms, #298 bounded Frontier, nine Battle Zone exteriors and #274 Stark source. Original19 Sinnoh names/slots and all other groups/layouts/disabled entries stay unchanged. Temporary scene has63 Sinnoh entries; no production group/section/healer/flag or saved format changes.
191-file deterministic overlay,808558 bytes before filesystem allocation. Surrogate existing section217 applies only to disposable test headers; source MAPSEC_PENDING_OWNER data unchanged. No original map reconstructed, Claude source or engine/workflow file edited.
Real preflight found source Stark Room2 also96×96/padded12210>10240. The DEV assembler derives three32×96 strips, preserving every original cell/C/E and mechanically remapping both stair returns. Actual Room1 is64×32. Every selected layout now fits the unchanged native buffer.
49597 source cells/border records validated against full native attribute words. Prefix/attribute/graphics compatibility allows six source bank roles to share four actual banks:4230→2412 raw secondary metadata bytes (1818 saved UNLINKED; not measured ROM savings). Graphics/palettes/callback bindings reuse the existing engine definitions.

## Actual evidence
9/9 HOST PASS14.008s. Covers original groups/layouts/disabled registry prefix, exact Room2 recomposition/capacity/return targets, closed44-map header graph, bank-prefix sharing, full export replay, dirty-source/invalid target/ordinary branch refusal, shallow checkout, ignored asset/path escape guards.
Installer filesystem replay uses actual immutable blobs and explicitly STUBBED target Git state. It is not a real marked Git-checkout/ROM test. Real-current-repo install was correctly refused. A genuine fresh-base install/build remains pending.
Actual existing host mapjson executable, with matching current mapjson.cpp/json11.cpp/mapjson.h source, executed47 successful commands: baseline groups, overlay groups, layouts and44 map headers/events/connections.970 original numeric map constants unchanged; generated healer data matches the baseline control. No ROM/native-game/mGBA/Save/Delta result claimed.
DEV_EXPORT_EVIDENCE.json and HOST_MAPJSON_EVIDENCE.json record tested source SHA, exact input/output/tool/source hashes, temporary coordinates, aliases and generator results. Generated assembler is local host-tool evidence, not a linked GBA build.
Development failures preserved privately: wrong assumed Room1 dimensions refused before output; real oversized Room2 corrected by exact split; standalone host-tool view initially lacked original map paths/required defines/src-data output area. Final verifier supplies a read-only map view and isolated healer baseline control. Initial enum parser was corrected to the real num|(group<<8) format. No live engine mutation.

## Reproduce and next executable action
From source checkout:
- python prepare_scene.py --repo SOURCE_REPO --out NEW_OUT
- python verify_mapjson.py --repo SOURCE_REPO --bundle NEW_OUT --tool BUILT_MAPJSON --out NEW_VERIFY
- PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s 'Pokemon Game/scripts/tests' -p test_sinnoh_battle_frontier_dev.py -v

On a host with space, create an exact-BASE throwaway branch named codex/battle-frontier-runtime-scratch-*, mark engine/.map_qa_throwaway, then invoke SOURCE_REPO's prepare_scene.py --repo THROWAWAY --install. Installer rejects other branches, wrong HEAD/tree, dirty engine, existing untracked output or paths escaping engine. Build actual NORMAL/RELEASE, focused native and legacy-save checks, then genuine doors/stairs/seams/followers/Save→fresh Continue. Header connectivity is not ordinary-foot/Surf/rail/rock-climb acceptance.
~8MiB scratch prevents safe real full build here. Existing CI workflows have no arbitrary overlay preparation hook, so dispatching them unchanged would compile an unrelated ROM. No pointless native workflow dispatched.
ci-workflow.proposal.yml is INACTIVE, manually dispatched NORMAL/RELEASE build + NORMAL focused native, contents:read, logs/JSON only; never ROM/ELF/save upload. YAML parsed locally; NOT executed or authorized. Proposed eventual path: .github/workflows/averon-battle-frontier-dev.yml. Current operating contract reserves GitHub Actions authorization to owner and independent workflow review; do not activate without those gates.
This package is test preparation, not production integration, saved-origin approval, linked resource measurement or final geographical acceptance. Higher effort is not currently needed for the completed exporter; full DS dynamics remains separately deferred.

Owner subsequently explicitly authorized the exact proposed workflow path/content and publication of scoped approval (PR305 comment6407941960). The active-path copy has identical operative YAML; only its comment changes. Independent workflow review remains mandatory. GitHub requires default-branch discovery, so an identical CI-only bootstrap PR is necessary; do not merge the geography stack to enable the workflow. Dispatch the reviewed source branch, not bare main which lacks the assembler. No CI run has been dispatched yet.
