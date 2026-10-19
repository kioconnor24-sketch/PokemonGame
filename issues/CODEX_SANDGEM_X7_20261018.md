# Sandgem integration and X7 resource evidence — October 18, 2026

## Reviewed integration

Claude's [PR #133](https://github.com/kioconnor24-sketch/PokemonGame/pull/133) was independently source/evidence-reviewed by Codex and normally merged as **`ce0c505d4ae3103680f96482881b9589bced14c0`**. Parents: main `8967b05b951c63dca9ffa39325ac53f240e3d9ba` and approved source `a91d7096efe7a857a74ca5fdfc6d96669e1f69ed`. [Exact peer review](https://github.com/kioconnor24-sketch/PokemonGame/pull/133#pullrequestreview-5565735852) records the different author/reviewer agents despite their shared GitHub login; it is a COMMENT, not a fabricated formal approving vote.

Actual merged engine tree **`ed42447b6435446177ec11bebdc4eda3a343f277`** equals reviewed PR head and Claude's final evidence source `f3570d73`. The signed [nine-path handoff](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6255792777) matches all changed protected/map files. Current required `file-guard` and `exclusive-files` passed; normal PR merge enforced existing protections. No direct main push, force rewrite, guard changes or self-merge of Codex's backend PRs.

Existing 76 groups and all their members remain unchanged; group76 appends town0 / Center1. Existing 800 layouts are unchanged; one exterior appends and the Center reuses its existing shared layout. Both maps use section216 / REGION_SINNOH. Legacy 0–214, NONE 215, special FD–FF and existing saves/structures retain their meanings. No 217+ allocation, heal ID, new neighbour connection, story entry or encounter was added by this integration.

West/north/south exits remain disconnected; east is solid. Passable boundary spans do not establish a connection: real mGBA blocked-edge traces and null production connections corroborate closure. Claude's committed final NORMAL/RELEASE **cries-OFF** evidence contains 26 checks per profile (damage 1 + town 17 + continue-pc 5 + continue-town 3), all true, with no recorded flash problems. This review checked JSON/events/Continue data and selected screenshots; it did not duplicate Claude's graphical playthrough. Initial entry is a disclosed DEV save fixture, not ordinary story reachability. Natural whiteout, human listening and Delta remain unaccepted.

## Actual build evidence and corrected playable default

The owner corrected the intended default during X7: **cries OFF for ordinary playable builds; ON retained only as a reversible restoration option.** [PR #146](https://github.com/kioconnor24-sketch/PokemonGame/pull/146) implements that correction without changing cry assets or adding an in-game toggle. It remains a candidate until independent review/merge.

Two pre-correction ON builds were completed on actual main `ce0c505d`; they are historical restoration-budget measurements. New default-OFF NORMAL/RELEASE and explicit ON RELEASE builds use candidate `5c33cd4e2cf55160c22ef1303dfd9d26ab404d68`, engine tree `97624367c72e7679dbdb36fad5a78153a63e0fa2`, containing the same merged Sandgem content plus the single default configuration correction. Do not relabel candidate builds as already integrated main.

Local toolchain: GCC14.2.1, binutils2.44, newlib4.5, MODERN default. Existing resource-budget/save-headroom tools measured actual outputs. ROM files remain private/ephemeral; padded 32 MiB length is not linked occupancy.

| Source/profile | Linked ROM used | ROM free | EWRAM / IWRAM used | Warnings |
|---|---:|---:|---:|---:|
| main ce0c505d historical ON: normal-on | 26,739,528 B | 6,814,904 B | 226,480 / 28,392 B | 0 |
| main ce0c505d historical ON: release-on | 26,858,724 B | 6,695,708 B | 226,486 / 28,336 B | 4 |
| correction 5c33cd4e: default-off-normal | 17,323,560 B | 16,230,872 B | 226,480 / 28,392 B | 0 |
| correction 5c33cd4e: default-off-release | 17,442,156 B | 16,112,276 B | 226,486 / 28,336 B | 4 |
| correction 5c33cd4e: restore-on-release | 26,858,724 B | 6,695,708 B | 226,486 / 28,336 B | 4 |

ROM SHA256 (actual padded output images):

- main ce0c505d historical ON, normal-on: `59751d3fb8bacd112dbccbee25abe407cf106a8a3827c2f2b466d5d02df61053`.
- main ce0c505d historical ON, release-on: `bd9491a7239dea0b02cbd3108cf7f05e3252c7e15bd7a62102a378100dbbcc6d`.
- correction 5c33cd4e, default-off-normal: `286e7b176cfef57b3260f3a89f841162f088b045ae06c35164b4f14bc86f9612`.
- correction 5c33cd4e, default-off-release: `4f6755b3ad5787685d4c8b6a9429e53930250acf8ddd08d55dbab26a914ff77a`.
- correction 5c33cd4e, restore-on-release: `bd9491a7239dea0b02cbd3108cf7f05e3252c7e15bd7a62102a378100dbbcc6d`.

The same-toolchain parent ON measurements retained in [the prior backend checkpoint](https://github.com/kioconnor24-sketch/PokemonGame/pull/142) were NORMAL 26,736,564 B and RELEASE 26,855,760 B. Actual measured historical ON growth: **+2,964 B in both profiles**. Claude's independently retained parent OFF measurements were 17,320,676 / 17,439,280 B, with reported +2,964 B/profile; those historical explicit-OFF values are not a same-toolchain parent pair for the new default-OFF candidate, so no unmeasured parent-OFF delta or fresh graphical-ROM identity is asserted. No full-region capacity promise follows from a single town's growth.

RELEASE restoration comparison: **9,416,568 linked bytes saved by default OFF**; **530 identical song objects / 156 identical non-cry samples**. ON restores 1,156 cry samples (9,386,416 raw linked sample bytes); default OFF contains 0. Song-object inventory SHA256 `b5053504055ac6cb367fd7a233180f7877cff951fa48a602749156a569f097ec`. The explicit ON RELEASE image exactly matches this session's pre-correction main ON image, proving restoration preserves that build.

Audio comparison reuses `codex_cry_profiles.compare`, `capacity.inventory` and existing song-object hashes for the candidate's actual default-OFF versus explicit ON RELEASE restoration pair. It verifies linked cries are present ON and absent OFF, song-object hashes/symbol inventory match and all retained non-cry sample bytes match. This is BUILD/static byte proof, not new gameplay/listening/Delta acceptance. The cry-source tree is unchanged: `cd221ddb39468e64ca89bbf6177da1b5862c8ffe` in both main and the correction candidate. The owner has already selected OFF as default; only tested independent integration remains, not another owner decision. Human listening/Delta are separate release checks.

All five measured linked save-headroom reports: SaveBlock1 **304 B**, SaveBlock2 **84 B**, SaveBlock3 **1,556 B**, PokémonStorage **1,568 B** free. Existing BoxPokemon/Party formats and save structures were not edited. NORMAL warning count and RELEASE's existing newlib syscall warning count are in the build table; no new warning was silently skipped.

## Registry, native and scene constraints

- Independently rerun source registry: **77 groups /953 pinned slots /536 linked maps**, **12 harmful mutations detected**, **1 valid extension accepted**. Existing disabled slots retain their values. Section audit: **7 saved pins preserved**. Sinnoh preflight: **2 maps /80 geometry dependencies /0 errors /0 warnings**.
- Actual default-OFF NORMAL ELF: **536 header symbols PASS**, **3 harmful pointer mutations detected**, all source registry mutations/pins still pass. The earlier actual-main ON NORMAL ELF also passed536 symbols; neither result substitutes source-only registration for compiled pointer proof.
- Pre-merge default-ON CI on reviewed source: **264/264 Averon native PASS**, run39173403073/job117811008032/artifact12153407045, artifact zip SHA256 `fc2918d55abe671ba1990593cb8b16bda59270c08cde4a1fe817d2dacbee0a44`.
- Actual merged-main historical default-ON CI: **264/264 PASS**, run39178828769/job117827054908/artifact12156050856, zip SHA256 `c7bfc47051b0ec24e614120213c4477f2943eab89771add4943d59d80d87fc5f`. Corrected default-OFF engine at5c33cd4e: **264/264 PASS**, run39180211213/job117831162448/artifact12156605822, zip SHA256 `a3230043cc316a56c446669894007582f9b229cbcbd0de03cb377c1495961109`. CI GCC13/newlib4.4 differs from the local GCC14 toolchain; do not equate ROM hashes. Final #146 host-CI integration/documentation commit retains the same engine tree; refresh latest-head checks before integration.
- The accepted full M1 run is not repeated or relabelled here. Its strict expected-failure identities/workflows were not changed. Codex's previous284/284 backend-only combined experiment is a different tree; none of those pending source PRs was silently integrated into this measurement.
- Town 32×28: 1,974 buffered u16 cells /3,948 B used inside the preallocated 10,240-cell map buffer. Center 14×9: 667 cells / 1,334 B. No buffer enlargement. Exterior raw blocks 1,792 B + 8 B border; shared interior layout adds no new block asset. Existing General/Dewford graphics/music are reused.
- Town declares 4 NPCs, Center 3; with one player and one follower the declared object-event scene is 6 / 5 versus 16 engine object slots. This is a source count, not a runtime peak measurement. The 64-sprite budget also includes transient UI/field/healing effects; palette/VRAM/stack high-water for every interaction remains unmeasured by this resource run. Claude's visible follower/heal/Continue evidence is bounded evidence, not an exhaustive maximum-occupancy proof.

## Peer review queue and concrete next actions

- [#135 technical proposal review](https://github.com/kioconnor24-sketch/PokemonGame/pull/135#pullrequestreview-5565749825): independently ran actual verifier against merged Sandgem: **7/7 positive, 5/5 broken plans caught**. Generator exactly reproduces candidate JSON SHA256 `deed033eaea4e2dea5d3d0f1434cead5d98365dbd2adb49ca3f0030677f06f29`. This is candidate preservation/review, not Route201 construction, approval of three reference deviations, section217+, encounter or reciprocal connection authorization. Final closed-neighbour overlays still need actual built-map tests once approved.
- [#139 changes requested](https://github.com/kioconnor24-sketch/PokemonGame/pull/139#pullrequestreview-5565749768): correct the camera-buffer contract (north imports the neighbour's southern/last 7 rows; east copies 8 columns), and make Route202's unverified 2-wide endpoint assertion conditional. Claude owns both files; Codex did not edit them or invent reference geometry. Re-review their new exact head after correction. Missing full Route202 reference remains an owner choice, not permission to invent it.
- #143 remains draft at `38b11f8cfa64edbaa60c3af057c25496a468a242`; no committed 6/6 runtime run2 verification at the final check. Source review/integration stays held. Offline 10/10 and smoke 26/26 do not replace fixture 6/6. Do not duplicate Claude's graphical work.
- #144 `77741ebb5403178d2a21f7a596f37587b6fde9a4` / #145 `96114f34115ac11aa8a9789c132dc9423f21948c` are still unmerged proposals with author-only reviews at the checked snapshot. No pending policy/workflow is treated as adopted. Its stale ON-default/undecided-adoption wording must be reconciled with the owner correction before adoption; the author/reviewer was notified in #15 and #144. Claude is asked directly in #15 to peer-review them and Codex's backend queue; comments do not restart agents. Legacy board output remains historical/unreliable until the correction legitimately merges.
- Sandgem natural whiteout remains the [separate owner-gated requirement](https://github.com/kioconnor24-sketch/PokemonGame/issues/55#issuecomment-6256277307): approve permanent heal ID and exact exterior anchor/interior nurse coordinates, then coordinate genuine protected-path authorization and Claude-owned hook wiring. No allocation or natural whiteout acceptance here. Generic #136 repairs and #138 map-entry protection remain separate pending peer review; no author self-merge.
- Claude's next approved independent step is merged-source/ROM confirmation and a small SN-T02 tracker PR, preserving story/placeholder limitations. Codex's report uses a separate new issues file and does not rewrite Claude's acceptance report or manager-owned queue.

## Reproduce

Use the exact recorded source/profile and stated toolchain; default-OFF commands require the #146 correction. Run builds sequentially because generated engine assets are shared. Build names are `pokeemerald[−cries-off][−release]`; actual filenames use ordinary ASCII hyphens.

```sh
make -j4 -O -C 'Pokemon Game/engine' RELEASE=0 all
make -j4 -O -C 'Pokemon Game/engine' RELEASE=1 all
make -j4 -O -C 'Pokemon Game/engine' RELEASE=1 CRIES=on all
python3 'Pokemon Game/scripts/check-averon-map-registry.py' --engine 'Pokemon Game/engine' --mutations --elf 'Pokemon Game/engine/pokeemerald.elf'
python3 'Pokemon Game/scripts/audit-averon-mapsec-namespace.py' --check-pins
python3 'Pokemon Game/scripts/audit-averon-map-readiness.py' --engine 'Pokemon Game/engine' --group gMapGroup_Sinnoh
```

For each build capture stdout/stderr to a fresh log and run `check-averon-resource-budget.py --log LOG --rom ROM --json REPORT` and `report-averon-save-headroom.py --elf ELF --json REPORT`. For static audio parity use existing `codex_cry_profiles.compare` with inventories/song-object directories for explicit ON restoration and default OFF. The helper CLI expects both explicit-profile filenames; this report calls its existing comparison functions on the actual default-OFF filename instead. No source-template shim or manual generated-header edit. New default-profile regression:4/4 identities over8 Make/mode cases; existing profile/gameplay-tool tests5/5 +18/18. Production parity217 checks per mode,24 negative mutations detected, with the default profile test invoked by existing CI. Workflow/guard code unchanged.
