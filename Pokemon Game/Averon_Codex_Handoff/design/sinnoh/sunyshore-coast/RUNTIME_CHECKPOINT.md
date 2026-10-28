# Five-map coast DEV checkpoint — paired evidence complete, geometry blocker remains

Base d96ae4041cb955918801eea5dfb300f517000474 plus32 exact recipe files, actual engine tree eb74029471ea632cbd58f8cbabdbf348ed12d11c. Public runtime-evidence/inventory.json hashes82 evidence files plus its own inventory; source-identity.json is a generated tree, not a production commit. All original19 map slots and saved structures retained. Only temporary19–23/217 surrogate; no production install or227+ allocations.

Actual NORMAL+RELEASE each: coast/gateway/follower/readonly foot-flags/menu/Save44/44; fresh Continue4/4; original legacy flash3/3; two independent upper/lower League copied-flash cases6+4 each. Total142/142 positive GUI checks. Four elevated city spans(28,11),(25,33),(23,44),(30,45) reached, actual player/follower layers3/4 observed, screenshots show upper walkway and lower occlusion. All68 original elevation15 cells host-preserved, not every tile/plane visually accepted. League fixtures are not natural Surf/Waterfall arrival. Source Route223 has zero dry walkable cells under existing foot rules, so no fake on-foot sea test or capability grant.

**Explicit negative failures:** two separate NORMAL cases6/7 each reproduce original Route222 ledges36/37,16 jumping onto collision1 boulders36/37,17. Actual failed checks/events/screens preserved. Existing generic QA labels ordinary navigation PASS while retaining both static findings; do not turn that into geometry acceptance. Source-preservation directive is honored; PR241 remains draft pending a reviewed narrow correction, never an unsafe merge.

Curated native29/29; unchanged strict SaveBlock1/2/3/PokemonStorage goldens4/4. Focused source/art/installer23/23. Broad host787 outcomes786PASS/one unavailable-ARM-path skip, then activated mapjson11/11 including test_arm_link_preserves_slots_and_requires_layout_events_and_scripts. Broad run preceded the last additive QA CLI scopes; final focused23 covers them, including source-module identity, read-only flags1/9/0 and restored scope configuration. Initial copied test pathname/count mistakes corrected without source/engine change; first harness command old directory suffix failed before game. Actual logs remain. No expected-failure dilution.

Actual GCC14.2.1 20241119/MODERN1/criesOFF builds: NORMAL17,430,244 linked bytes, RAM226480/28392, SHA256317deaa9a49aab59059c65ff1334b7b1e0de8ac2ebaeb9baeb35ef03c304935b; RELEASE17,549,364, RAM226482/28336, SHA2563a9e01bb81cc445b7964ddaeaac33254a59172afe85452cc347029b92262246a. Both+36,900 versus matching unchanged-engine baselines17,393,344/17,512,464, RELEASE16,005,068B free under32MiB. Matching ROM/ELF segment/extent checks in resource reports; configuration labels alone are not build proof. mGBA0.10.5. No human audio or Delta acceptance.

Original private flash remains44cd2e2d651128b18439e9f9763705beee6ae32e6c901fc3f24d982328512f9d. Unique paired ROM/ELF/map files and exact source identity/recipe archived privately at /workspace/scratch/sunyshore-built-20261023. No binaries/private saves/expected snapshots/donor art uploaded. Completed-case duplicate generated ROM copies removed only after matching archived hashes. Source237 still owner-handoff blocked; no work moved to evade it.

Reproduce source/art tests as in ART_CHECKPOINT. Marked current-main scene installer:

```sh
python3 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/sunyshore-coast/prepare_runtime.py' --repo /marked/exact-base/checkout --install
# In its engine after onboarding activation:
make -j4 all MODERN=1
make -j4 all MODERN=1 RELEASE=1
# Curated TEST_SRCS: test_runner.c,test_runner_args.c,test_runner_battle.c,test_test_runner.c,
# averon_map_registry_contract.c,averon_corridor_location.c,averon_location_compatibility.c,
# averon_region_save.c,averon_northern_location.c,save.c,averon_sunyshore_runtime.c (all test/).
make -j4 check MODERN=1 TESTS=Averon TEST_SRCS="$coast_test_sources" ROMTEST=/path/to/mgba-rom-test
make -j4 check MODERN=1 'TESTS=*backwards compatible' TEST_SRCS="$coast_test_sources" ROMTEST=/path/to/mgba-rom-test
```

Ordinary-input runner requires matching ROM/ELF, marked source and --recipe runtime-recipe.json, persistent Xvfb77; full default plan starts gate6,5 via copied-flash fixture. `--dry-league` independently starts upper16,35/lower11,59. `--expect` uses the actual private snapshot after real Save in a fresh process. Explicit `--ledge-x 36`/37 starts copied-flash Route222x,15 and returns FAIL; never relabel these negatives PASS. Legacy copy uses unchanged MAP_SALTMERE expectation. No memory/engine/collision patch to obtain gameplay passes.

Next independent engineering: PR242 original Victory Road three-floor DEV/stair/follower/save package, prepared11/11 focused tests. Five new named origins would be needed for this coast+core wave if individually named (Sunyshore,222,223,League,Victory Road), but no codes are allocated. Existing227–252 space26 codes and full future grouping/encoding policy remain owner-only; physical source/DEV work continues without pretending217 is production identity. Existing actual19 production maps remain unchanged.
