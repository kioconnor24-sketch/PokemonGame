# Connected Oreburgh DEV candidate — actual paired acceptance evidence

**Source-only recipe and isolated DEV ROM acceptance, not production map integration.** Manager has since merged northern206 and source205/208/213. Preserve those maps; do not merge this frozen scratch engine into production or reuse its temporary slots. Production saved origins227+ remain undecided.

## Exact identity and resources

Frozen source base `f0a8bcaa10b410245d240b6014779ba69eb31c74`; art source `0005ba56711ba5c73e4d1b31402b62b1a7863800`; donor `38228bb574a3557345852b758d5f1a65eb01bb22`. All34 installed overlay files verified; actual engine source tree **`4579c9085d3fc417c784317d4f1e9788eabec22e`**; recipeSHA256 **`9a15868d30ee3402fb290618f36b32f07fa2463ba7aa14216cbfef4b83cb8f95`**. Source identity and native source list: [receipt](evidence/source-identity.json). No other runtime source changes. Later branch merges import legitimate main into the tooling branch; they do not relabel the earlier ROM base.

GCC14.2.1, MODERN=1, default criesOFF, generated-asset cache reused. Actual compile/link and matching ELF/ROM load-byte/extent verification passed:

| Profile | Linked ROM | SHA256 | EWRAM / IWRAM |
| --- | ---: | --- | --- |
| NORMAL |17,410,100B|`9e81fb199833f26290bf568028c02a02eda70257a2339b70fd30cee6febf02cb`|226480 /28392B|
| RELEASE |17,529,236B|`7f1b592e34775c83e168e5a75018c035620e2fe96ae9ea55b1fc69c249564686`|226482 /28336B|

Growth from the same Jubilife base50,292B/50,300B, RAM delta0. RELEASE headroom16,025,196B. [NORMAL resources](evidence/normal-resource.json), [RELEASE resources](evidence/release-resource.json), [actual NORMAL build](evidence/normal-build.log), [actual RELEASE build](evidence/release-build.log). Existing newlib stub warnings are retained, not a zero-warning claim. No ROM, ELF or private save uploaded.

## Implemented and actually tested

Uses existing City70×59, Route20764×32, B1F24×26 and B2F32×28; no reconstruction. Connected Route203→Gate→City↔Route207 and City↔B1↔B2. All six B1 event identities/four basement triggers, B2 return2, coupled City11/14→candidate1/4 indices and reciprocal±35 offsets survive. Gate restores only four east doorway cells/event1, preserving west exit and closed unbuilt ladder. A reproduced unmatched Route20713,31→solid City48,0 seam closes collision only0x310C→0x350C; existing art/elevation and six reciprocal walking spans remain. [Final static audit:0 findings](evidence/static.json).

- **Actual graphical mGBA0.10.5, EACH profile:** walking/warps/follower/menu/save **79/79**, fresh-process Continue **3/3**, separate upper Coronet closure **6/6**, genuine unmodified pre-corridor save load **3/3**. Final receipts/events are under evidence/{normal,release,normal-continue,release-continue,normal-upper,release-upper,normal-legacy,release-legacy}. Original old flashSHA44cd2e2d651128b18439e9f9763705beee6ae32e6c901fc3f24d982328512f9d; only runtime entry copies receive disclosed DEV continue-warps. Those patched saves are never used as production old-save baselines. Preexisting Saltmere static seam warning1 is disclosed in legacy results; no new Saltmere change.
- **Actual native29/29** including five compiled-header/warp/offset/surrogate fixtures, exhaustive legacy origin compatibility and flash recovery tests; **save goldens4/4** (SaveBlock1/2/3 and PokemonStorage). [Native log](evidence/native29.log), [save log](evidence/save4.log). Ten TEST_SRCS, including four required runner files, are listed in source-identity.json. TESTS=Averon then TESTS=test/save.c, ROMTEST=/workspace/.onboarding/mgba-rom-test. This is focused verification, not a repeat/full-M1 acceptance.
- Host focused **19/19**, latest full source suite on merged main **221/221**, zero skips. Negative/source coverage includes all6 individual mine events, wrong sparse return/offset/anchor, malformed metadata/capacity, input immutability, correct music symbols, corrupt caches and no-history/empty-checkout replay. Actual GitHub final-head outcomes belong in the PR, not assumed here.

## Retained failed trials and resolved test assumptions

First NORMAL link used nonexistent MUS_ROUTE111; corrected to real MUS_ROUTE110 with symbol preflight ([failed link](evidence/failed-music-link.log)). First source static check found the seam above ([original finding](evidence/failed-seam-static.json)). The first native invocation omitted the runner sources and could not link CB2_TestRunner; the corrected ten-source invocation actually passed29+4, without an engine/test-baseline change ([failed harness log](evidence/failed-missing-runner.log)).

Four graphical failures remain separate in evidence/failed-*:

1. A northern-branch seed stored map76,17, outside the17-slot frozen candidate; Continue hung before field. Operator terminated it, so the recorded GDB-close error is **not** falsely described as an unexplained engine crash. Retry used the genuine valid pre-corridor seed.
2. NORMAL79/80 failed the extra upper Coronet probe because preserved Muddy Slope cannot be climbed on foot. Terrain/behavior was not changed. The unchanged79 lower checks are now clean in both profiles; the same blocked-Coronet assertion is actually tested through a separate explicit upper DEV entry, not silently removed.
3. Continue2/3 failed a follower probe that attempted the non-climbable slope and never placed the follower. Launcher now tries a successful on-foot neighbour before observing the real follower; final Continue3/3 passes. No memory edit/spawn or acceptance assertion override.
4. First upper5/6 failed an extra exact-position assertion after follower placement moved the player. Runner now walks back to the same exact asserted probe; final upper6/6 passes. The blocked exit assertion itself passed in both trials.

## Safety, limits and reproduction

`prepare_candidate.py --repo REPO` only plans. `--install` demands the exact frozen base, clean tracked engine, codex/oreburgh-runtime-scratch-* branch and .map_qa_throwaway marker. Public source headers retain MAPSEC_PENDING_OWNER; only that disposable tree uses existing217 as a conspicuous surrogate. **Never promote its flash, slots13–16 or origin names into current main**, whose legitimate northern slots13–18 now exist.

Seven essential #208 blobs are cached in9,152-byte city-art-inputs.zip (SHA73ed064f3570c31a1eb6cf09bddf474e20fe547d9de972bf004fe071e9b42409);24 canonical frozen-base blobs in85,184-byte base-inputs.zip (SHA79c53813a74f979875e1f9c5e4a163659001e5fc0f14cbabad94eccd8fbf121a). Caches are hash-checked, not a waiver to install on a newer base. They contain no donor PNG/palette or ROM/save. Source word/attribute metadata reuses accepted artifacts; global General pixels stay untouched.

Activate /workspace/.onboarding/activate.sh; verify source hashes, inspect recipe.json, install only into the marked old-base test tree, build `make -j4 MODERN=1` and `make -j4 MODERN=1 RELEASE=1`, then actual native/source/resource checks. `run_qa.py` verifies every installed source hash, uses the existing shared assertions/controller and discloses DEV entry. It adds ordinary-foot follower navigation and a separate `--upper-probe`; no engine memory writes. Fresh Continue uses the previous game-written saved-oreburgh-corridor.json, not a fabricated state. Genuine legacy load uses the untouched old flash separately.

This proves a bounded connected scratch slice. Resampled City facades/simplified yard remain graphical revision items; no story/services/encounters, normal first-arrival, Muddy Slope progression/bike unlock, natural whiteout, human listening or Delta acceptance is claimed. Next production task requires the owner's met-origin policy and a newly reconciled current-main append-only registration, with its own real builds/tests/authorization. Meanwhile continue permitted-art/source geography in Eterna/Forest and central Sinnoh; do not rebuild merged northern maps or stall on the identity decision.
