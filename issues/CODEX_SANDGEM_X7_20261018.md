# Sandgem integration and X7 resource evidence — October 18, 2026

## Reviewed integration

Claude's [PR #133](https://github.com/kioconnor24-sketch/PokemonGame/pull/133) was independently source/evidence-reviewed by Codex and normally merged as **`ce0c505d4ae3103680f96482881b9589bced14c0`**. Parents: main `8967b05b951c63dca9ffa39325ac53f240e3d9ba` and approved source `a91d7096efe7a857a74ca5fdfc6d96669e1f69ed`. [Exact peer review](https://github.com/kioconnor24-sketch/PokemonGame/pull/133#pullrequestreview-5565735852) records the different author/reviewer agents despite their shared GitHub login; it is a COMMENT, not a fabricated formal approving vote.

Actual merged engine tree **`ed42447b6435446177ec11bebdc4eda3a343f277`** equals reviewed PR head and Claude's final evidence source `f3570d73`. The signed [nine-path handoff](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6255792777) matches all changed protected/map files. Current required `file-guard` and `exclusive-files` passed; normal PR merge enforced existing protections. No direct main push, force rewrite, guard changes or self-merge of Codex's backend PRs.

Existing 76 groups and all their members remain unchanged; group76 appends town0 / Center1. Existing 800 layouts are unchanged; one exterior appends and the Center reuses its existing shared layout. Both maps use section216 / REGION_SINNOH. Legacy 0–214, NONE 215, special FD–FF and existing saves/structures retain their meanings. No 217+ allocation, heal ID, new neighbour connection, story entry or encounter was added by this integration.

West/north/south exits remain disconnected; east is solid. Passable boundary spans do not establish a connection: real mGBA blocked-edge traces and null production connections corroborate closure. Claude's committed final NORMAL/RELEASE **cries-OFF** evidence contains 26 checks per profile (damage 1 + town 17 + continue-pc 5 + continue-town 3), all true, with no recorded flash problems. This review checked JSON/events/Continue data and selected screenshots; it did not duplicate Claude's graphical playthrough. Initial entry is a disclosed DEV save fixture, not ordinary story reachability. Natural whiteout, human listening and Delta remain unaccepted.

## Actual build evidence and corrected playable default

The owner corrected the intended default during X7: **cries OFF for ordinary playable builds; ON retained only as a reversible restoration option.** [PR #146](https://github.com/kioconnor24-sketch/PokemonGame/pull/146) implements that correction without changing cry assets or adding an in-game toggle. Claude independently reviewed final head `3083758282e07ff1a795e19430ec07bc2b1523c4`; normal integration completed as **`de127dff378abe720bba8b627dd123c4db478fb8`**. OFF is now the ordinary build default on main. No in-game cries toggle was introduced.

Two pre-correction ON builds were completed on actual main `ce0c505d`; they are historical restoration-budget measurements. New default-OFF NORMAL/RELEASE and explicit ON RELEASE builds use candidate `5c33cd4e2cf55160c22ef1303dfd9d26ab404d68`, engine tree `97624367c72e7679dbdb36fad5a78153a63e0fa2`, containing the same merged Sandgem content plus the single default configuration correction. These remain exact-source measurements of the correction branch, not fresh measurements of later main commits containing other backend changes.

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

Audio comparison reuses `codex_cry_profiles.compare`, `capacity.inventory` and existing song-object hashes for the candidate's actual default-OFF versus explicit ON RELEASE restoration pair. It verifies linked cries are present ON and absent OFF, song-object hashes/symbol inventory match and all retained non-cry sample bytes match. This is BUILD/static byte proof, not new gameplay/listening/Delta acceptance. The cry-source tree is unchanged: `cd221ddb39468e64ca89bbf6177da1b5862c8ffe` in both main and the correction candidate. The owner has already selected OFF as default; independent integration has completed, so no further default-adoption decision remains. Human listening/Delta are separate release checks.

All five measured linked save-headroom reports: SaveBlock1 **304 B**, SaveBlock2 **84 B**, SaveBlock3 **1,556 B**, PokémonStorage **1,568 B** free. Existing BoxPokemon/Party formats and save structures were not edited. NORMAL warning count and RELEASE's existing newlib syscall warning count are in the build table; no new warning was silently skipped.

## Registry, native and scene constraints

- Independently rerun source registry: **77 groups /953 pinned slots /536 linked maps**, **12 harmful mutations detected**, **1 valid extension accepted**. Existing disabled slots retain their values. Section audit: **7 saved pins preserved**. Sinnoh preflight: **2 maps /80 geometry dependencies /0 errors /0 warnings**.
- Actual default-OFF NORMAL ELF: **536 header symbols PASS**, **3 harmful pointer mutations detected**, all source registry mutations/pins still pass. The earlier actual-main ON NORMAL ELF also passed536 symbols; neither result substitutes source-only registration for compiled pointer proof.
- Pre-merge default-ON CI on reviewed source: **264/264 Averon native PASS**, run39173403073/job117811008032/artifact12153407045, artifact zip SHA256 `fc2918d55abe671ba1990593cb8b16bda59270c08cde4a1fe817d2dacbee0a44`.
- Actual merged-main historical default-ON CI: **264/264 PASS**, run39178828769/job117827054908/artifact12156050856, zip SHA256 `c7bfc47051b0ec24e614120213c4477f2943eab89771add4943d59d80d87fc5f`. Corrected default-OFF engine at5c33cd4e: **264/264 PASS**, run39180211213/job117831162448/artifact12156605822, zip SHA256 `a3230043cc316a56c446669894007582f9b229cbcbd0de03cb377c1495961109`. CI GCC13/newlib4.4 differs from the local GCC14 toolchain; do not equate ROM hashes. Final #146 head `3083758282e07ff1a795e19430ec07bc2b1523c4` also passed **264/264**, run39181331358/job117834518462/artifact12155569933, zip SHA256 `9a615eb022928eaa19f3ea4aedd58288c8add42f04cb5f200ffd746ab37327aa`. Final production-config CI ran the 4 default-profile tests and detected all24 mutations, run39181331375/job117834518436/artifact12156078430, zip SHA256 `033fb93011ee6535ece51f15c4840c33f760a795165e46085776691ea0e288ee`. All applicable final-head checks passed before Claude merged.
- The accepted full M1 run is not repeated or relabelled here. Its strict expected-failure identities/workflows were not changed. Codex's previous284/284 backend-only combined experiment is a different tree; those six backend PRs subsequently merged under Claude's attributed independent review, but their combined tree is not the source measured in the tables above.
- Town 32×28: 1,974 buffered u16 cells /3,948 B used inside the preallocated 10,240-cell map buffer. Center 14×9: 667 cells / 1,334 B. No buffer enlargement. Exterior raw blocks 1,792 B + 8 B border; shared interior layout adds no new block asset. Existing General/Dewford graphics/music are reused.
- Town declares 4 NPCs, Center 3; with one player and one follower the declared object-event scene is 6 / 5 versus 16 engine object slots. This is a source count, not a runtime peak measurement. The 64-sprite budget also includes transient UI/field/healing effects; palette/VRAM/stack high-water for every interaction remains unmeasured by this resource run. Claude's visible follower/heal/Continue evidence is bounded evidence, not an exhaustive maximum-occupancy proof.

## Final upload checkpoint — October 19, 2026

Live main observed during upload: **`b0219d88fad0216da99619b397ef507e94ac9fcc`**, engine tree `1a101993c12b21b871b4946645f898c57f187973`. This is a later integration snapshot, not a new build or native result for the earlier measured engine trees. No full ROM, ELF, save or private fixture is uploaded.

- **#146 delivered and merged** at `de127dff378abe720bba8b627dd123c4db478fb8`. All cry sources remain intact. Default OFF RELEASE saves9,416,568 linked bytes versus the measured explicit ON restoration. Owner-default correction, RED/GREEN evidence, three actual build results, source/ROM hashes and final CI evidence are retained in [the issue report](CRIES_DEFAULT_OFF_OWNER_CORRECTION_20261018.md). Claude's independent review additionally reports byte identity with his previously tested explicit-OFF images using his own toolchain; local hashes above use a different toolchain. Human listening and Delta remain unverified.
- **Backend queue integrated:** #136/#138/#137/#140/#134/#141 and checkpoint #142 were merged by Claude after attributed independent review. Their combined284/284 focused native result is distinct from #146's264/264 exact-head CI and the accepted full M1 baseline. No author self-merge of these backend changes occurred.
- **#135 design review is historical:** Codex's reviewed head `d6540f26946da0455db8d3d8af1181373c69e63a` passed7 positive/5 negative cases and reproduced JSON SHA256 `deed033eaea4e2dea5d3d0f1434cead5d98365dbd2adb49ca3f0030677f06f29`. That review did not cover later geometry corrections. Claude subsequently corrected the seam to Route201 right−4 / Sandgem left+4 with reported real mGBA35/35 and3/3 fresh Continue, merged the design as `89454ce5c616e8c2563ea3bfdbc012e20450ecde`, then obtained [owner construction approval](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6258911084). Production construction/section217 is now Claude's **draft #150**, not accepted by this report.
- **#139 correction requests superseded:** Codex requested correct north-buffer rows/east8-column terminology and removal of an unsupported Route202 opening assertion. Claude corrected the docs at head `1fb0082f5a287d776a0e49de5c70a299b8da296a` and merged as `37648757a842f1c5aa4bb9bc86b8b43955e34771`. Do not carry the old changes-requested state forward. Route202 is now explicitly deferred by the owner pending a reliable reference.
- **#143 runtime hold resolved by committed evidence:** head `484c12e962ccb781c0844a37cd646f6ae1021800` records run2 **6/6 expected fixture outcomes**, superseding run1's4/6. Claude merged the QA-only tool as `db45baf26b5a26680aba09acbd251adfe393463a` under the adopted low-risk policy. This report verifies live source/status attribution, not a new independent graphical run or source approval of later changes. Its NORMAL-only/DEV-entry/no-HM-model/human/Delta limitations remain. #149 subsequently adds region-UI fixture coverage on main; #152 is another unreviewed QA extension at this checkpoint.
- **#144/#145 are adopted:** governance merged at `0c9ec0c361a45ff24a6d4c72711e0e95b2f3bb1a`; read-only advisory merged at `8e67abf76a2d9829e76b840778e37c5e26412907`. The contract now correctly states cries OFF. Its owner-approved tiered process permits bounded docs/test-tool author merges with exact-head evidence; production/saves/IDs/protected paths/workflows retain independent-review requirements. Older reset snapshots and earlier comments are historical. No agent was restarted.
- **Sandgem natural respawn:** owner [approved the exact packet](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6259265791): healer44, exterior(15,10), Center interior(7,4), nurse1, set on entry. Claude owns implementation in **draft #151**. Approval is not runtime acceptance: exact protected-path handoff, Codex independent source/evidence review and meaningful whiteout/Continue checks remain required. A DEV-triggered whiteout must remain labeled; ordinary battle-loss reachability is not established.
- **Next executable technical task after upload:** refresh #150 and #151 exact heads, claims, literal-path handoffs and completed NORMAL/RELEASE/native/graphical evidence; independently review only when ready. Do not edit Claude's route, healer, graphics or QA claims. Review #152 as isolated QA tooling if requested/needed. Keep final human-audio/Delta checks and expanded origin-encoding adoption separate; no production migration was selected by the experimental tests.

This report's only changed path is `issues/CODEX_SANDGEM_X7_20261018.md`. All observed approvals and future claims must be refreshed from live GitHub before acting. Historical build/test source identities above remain unchanged.

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
