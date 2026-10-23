# Codex long-run Sinnoh implementation checkpoint — 2026-10-22

Repository kioconnor24-sketch/PokemonGame. Production main last verified **c6ac2f967b02473741791eb24b5cc9b11bda3904**. Claude remains paused. The owner assigned ChatGPT manager reviews/authorizations/merges for this session: **no PR was self-merged, no main push, protection change, permanent227+ origin or save migration occurred**. This preserves the earlier completed resume/upload checkpoints rather than overwriting their history.

All work uses donor revision **38228bb574a3557345852b758d5f1a65eb01bb22** for geography/metadata only. Every new pixel/color is existing Averon art. No donor PNG/palette/music, scripts, NPCs, trainers, encounters or story imported. Temporary DEV registries never constitute production identity approval.

## Pushed implementation and dependency graph

These are code/source anchors; later evidence/checkpoint-only heads are recorded in the final Issue15 handoff. Review the actual latest PR head/checks before integration. Counts are per branch, largely reusing the same upstream cases; **do not sum them as unique tests**.

| PR | Code/source anchor | Parent | Concrete result / actual source tests |
| --- | --- | --- | --- |
| #217 |ca1e097892f3bfe30046c24de8dc750d1af0205c|#212|Current-main Oreburgh DEV reconciliation,232/232; actual paired builds/native32/save4/traversal79/Continue3/upper6/legacy3 each profile;40 evidence files.|
| #218 |9c75a9cbdda1eb3cbaf98748f331e7f73742cc3b|#215|Forest artwork6892 map/border cells,General/Rustboro364 secondary,222/222,8/8 generated outputs identical.|
| #219 |f77b81d049b29f72d8a470ec03c2559c9b8cc52f|main|Cycling Road,two gateways,211West actual art,4582 cells,210/210,21/21 repeated files.|
| #220 |200a3370d5af4a0360a7ea21f1a04676865c9abd|#219|Eterna City3304 cells,shared82-record family,217/217; both neighbouring road RGBs unchanged.|
| #221 |61ecf80bdc96b29ff2dd1799892b26d7d2107c4c|#220|Current-main Eterna5-map DEV actual paired builds/native29/save4/source236/236;55 traversal+Continue3+legacy3+upper150+lower42 EACH profile;63 evidence files.|
| #222 |367371867a4aceec7242c077ec95629823168532|#218|QA exact same-map warp/return coordinates; all15 actual2F self-events plus external/negative fixtures,229/229.|
| #223 |22919e59f4d4ae43bb6d6d1c32c51a7305a1565a|#216|Six new Celestic/northern Coronet source maps9445 cells,48 elevation15,237/237;31/31 stage files reproducible. No art/runtime claim.|
| #224 |afd1c49382954e3f02f0ee5ebb34665153f6efb0|#216|Five central outdoors artwork17368 cells,58 bridge15,one129-record family,237/237;20/20 identical outputs.|
| #225 |bc9c4380f4773851846a06c270ca6d35d892475f|#222|Forest6-map DEV; real same-map driver and falsey-State fixes; transparent Museum660 replaced by opaque existing649; source247/247. Repaired paired builds/native29/save4/visual0magenta; final exact runtime evidence55 files pushed ata2fb49c995b98fa82ac96111b87e1866fb1a6e9e.|
| #226 |ea801a08bb6de9ad7d9a528a37843a102302db00|#223|Twelve eastern/southern source maps34720 cells,17 coupled warps,97 elevation15; four neutral gates432 cells; real final-seam closure repair. Source251/251,61/61 stages+13/13 gate outputs repeat.|
| #227 |2aa16c82b5ce290efe7ff584ccfa3fe33d9da6e3|#224|Central7-map actual paired builds/native29/save4/source255; EACH profile55 traversal+Continue3+legacy3+upper87+lower16 PASS. Lower15/16 original QA failure retained and repaired without engine edits.|
| #228 |3f538cc453136c1021299c9af8c99836bdf8bb1b|#223|Three Celestic northern outdoors permitted-art,5237 cells/48bridge15 preserved,39 secondary records,245/245 source and14/14 reproducible outputs. Source/art only; caves/runtime remain unfinished.|

Existing #215 c0a9265c042fbb51a8d347fe49829fbb7a41a4b2 and #216 b559164ded89d98e425ea9dd20e9e47b0dc5f0a4 remain preserved parents. The original #212 frozen Oreburgh recipe2c26ed624dc4f8c6ea14d1f65824af1eb56ae9fe was reused, not relabelled as a current-main run. #206 northern production and #205/#208/#213 assets already on main were not reconstructed.

All applicable latest file-guard/exclusive-files/python/source-pilot/route jobs passed at the listed code heads. Weekly readonly audit is intentionally SKIPPED, not PASS or a missing required test. Actual inspected CI logs: #225 source247/0skips job120112994756; #226251/0 job120105346627; #227247/0 job120107871753. Final evidence/doc-only heads need their own latest checks and are included in the final live handoff.

## Actual built ROMs and source identities

All ROM/ELF/map binaries and private flashes remain private. GCC14.2.1,MODERN=1,default criesOFF; existing generated assets reused. These are real NORMAL/RELEASE builds, not a clean-build claim. Paired baseline c6ac: NORMAL17393344B SHA5bf7e16f41bf2e6e1e55538f45412699ab20493e62566e2b26db9c9c6577c259; RELEASE17512464B SHA64c4ab1d5052804612092080ce08066a72e502571d76c64f03f78adb1e088130.

| Separate DEV candidate | Exact engine subtree | NORMAL used/hash | RELEASE used/hash | Increment each/limits |
| --- | --- | --- | --- | --- |
| Current Oreburgh |20585b0fb4a0931ab7fd07d76e7736b9cb0e698e|17443636 / d2b74033a5098d0dd10d2c9da95f9655c0b6b6634897628859f423b0c830b4bf|17562756 / 77db1bbe9a48fcd635dea5e44aadcec41bf8f14ccf544815aea3cc9b566c1dda|+50292B;RELEASE15991676B free.|
| Eterna/Cycling/211 |077938717b95b6b8aefad5f319579bc020b77ce1|17425948 / 8e14c7150d1a3e8aa29c35155b8280ae3bb2cd4ca4649db2a0e6dc9f51090057|17545076 / f00e37527b27c55c5cd20f5377d5b426a869d874deb715e7b7dc9ea337f2ad4c|+32604/+32612B;RELEASE16009356B free.|
| Repaired Forest/Chateau |dc3845c18b78304261656d390603f78f3cb14915|17436904 / 0d3f92944d02c9c0d0ff5fcba249f46f9217de3eec0336b56fb0f84c697c760e|17556024 / d2a8723a67ca94d923b8d3f199e263595d7d4417c7393c927abb974a67dc2aca|+43560B;RELEASE15998408B free.|

Central candidate engine **fdd73c038d8339827648ba5478e62488276dc460**, repository tree05db193718514f4f67eb95487d29b98cad47492b: NORMAL17446444B SHA1fa065a9a5e05f1548c2847753aee35082865b316c8c2d973e22992ce4a232a5 (+53100B); RELEASE17565572B SHA833b349d7ed6d42b096e1048bfb1cf060bd705bd5a1b68a45f9a3169d2657271 (+53108B),15988860B free. RAM unchanged. Actual53 runtime evidence/reproduction files published with #227.

All padded ROMs33554432B; used bytes from matching ELF/map, not padding. NORMAL EWRAM226480/IWRAM28392B and RELEASE226482/28336B unchanged across candidates. No new stack measurement claimed. These are **separate candidates against one baseline**, not a cumulative production delta or proof a combined temporary registry can be installed.

Exact repository trees: Oreburgh0355f585069c7ad40a7e45717309c11a98fcf6ed; Eterna beeb31fddc575b70a0cfab727304cc0d41f6843f; repaired Forest ce5b4506152ac6470583018948d436f770298a89. Per-file source hashes, linker inventories, raw builds/native/golden logs, original failures and actual controller result/events/screens are in each runtime evidence folder.

Current paired checks preserve the genuine original legacy flash SHA **44cd2e2d651128b18439e9f9763705beee6ae32e6c901fc3f24d982328512f9d**. DEV entry copies are not old-save baselines. No full unfiltered M1 strict native rerun is claimed; the focused native counts32/29 and save goldens4 are not the M1 baseline's6107 outcomes. GUI used X11/software/dummy audio; human listening/Delta remain unverified.

## Real defects/failures repaired and retained

- Eterna recipe initially guessed Building asset aliases; real build caught it. It now reads actual InsideBuilding graphics/palette/callback declarations. Existing World parser spacing mismatch caught by actual virtual-overlay parser regression; parser was not weakened.
- Eterna initial2D graphical46/49 and first height-aware40/43 failed. Planner now models native0/15 layer transitions, excludes a current arrow warp's trigger direction from ordinary walking and requires exact follower neighbour/return. Upper first3/4 setup and4/5 falsey-State assertion failures retained. First stricter full51/52 failed before walking settled; fixed helper settles/rechecks. Final exact ROMs pass55+Continue3+legacy3+upper150+lower42 EACH profile. City↔Road has0 direct foot spans; actual gateway route used. City↔211 walking seam is constructed/tested.
- Chateau QA initially only detected map-ID changes. Actual15 same-map driver fixtures and genuine first66/67 Stuck at2F(3,7) exposed repeated teleports/wrong-room alternates. Driver stops at exact arrival and only treats equal destination indices as equivalent self-map mats. The separate wrong-driver replay was explicitly interrupted28/29, not accepted. Guarded launcher verifies actual loaded source driver and all42 engine hashes.
- Source game.State falsey dict snapshots omitted the intended follower return step. Actual-State positive/failed-step negatives now cover the repaired None comparison.
- Forest pre-art-repair profiles passed134+Continue3+legacy3, but settled diagnostics found1024 magenta pixels in BOTH profiles at Entrance(9,16). Functional PASS was not called complete graphical acceptance. Only metatile660's16-byte art record (8 byte positions differ) now reuses already accepted opaque floor649;12 cells' full attrs/IDs/C/E and all original map/warp data unchanged. Repaired profiles show0 pixels immediately/after3s; prior source/ROM/receipts and before/after images remain separate.
- Eastern first7/8 source tests found Route213 left(0,57) open to Pastoria(67,59), which another boundary pass subsequently closed. Shared stager now seals final mutually reachable seams to a fixed point, respecting real retained warp anchors. New corner/negative fixture proves this; only new eastern geometry changed339→340 closures. Every older237 case/fixture remains unchanged.
- First central artwork previews caught same-index roofs on bridges, grass used as paving and duplicate Center roof rows. Explicit existing wood/street/bush records and intact4×4 Centers fix the previews without physical/attribute changes. Historical gate receipt key/declared CRLF palette hashing test assumptions corrected without ignoring actual hash differences.

No genuine production save regression or engine/save format change was invented. Old Saltmere source warning remains disclosed; no fabricated natural arrival, story/bike progression, whiteout/services or full release acceptance.

## Workspace and recoverability

- `/workspace/averon-oreburgh-geography`: **codex/central-dev-runtime-20261022**, #227; central source/art/44-file recipe. This checkpoint-only commit adds no runtime code.
- `/workspace/averon-oreburgh-corridor`: now **codex/celestic-permitted-outdoor-art-20261022**, new outdoor art from #223; former #225 branch/source/evidence remain preserved at a2fb49c995b98fa82ac96111b87e1866fb1a6e9e. No competing QA process uses this checkout.
- `/workspace/averon-corridor-scratch`: clean exact-c6ac **codex/central-runtime-scratch-20261022**, verified central44-file source/marker preserved in stash **b28c3443d0903edf6411ff473c7f398b4f14d403** after all successful tests. All older stashes remain intact. Ignored binaries still describe central fdd73c, never clean-main source.
- `/workspace/sinnoh-donor-pinned`: immutable donor38228bb...; sparse missing files may still exist as Git blobs. No new clone/worktree was created.
- Preserved engine stashes: frozen Oreburgh8b3c2909a64c1cf916977452c7f9614efe690abf; current Oreburgh3f2a4a018de3885c0b684daaa50dfa4034b24bdd; Eterna67ca13973d300d79440683d1d74463487151fb1b. No accepted history deleted.
- Private accepted pairs: `/workspace/scratch/oreburgh-current-accepted-20261022`, `/workspace/scratch/eterna-current-accepted-20261022`; Forest pre-floor-repair `/workspace/scratch/forest-before-opaque-floor-20261022`. Repaired accepted Forest pair/source bundle is `/workspace/scratch/forest-current-accepted-20261022`; full overlay stash1693d080fc35c8b952f26a136bf54ac422ed3e7f.
- Raw results/failures/scripts at `/workspace/averon-session-evidence/`; all recoverable new source is pushed through the listed PRs. Generated Python caches/ROMs/ELFs/private flashes are excluded from GitHub. Approximately6GiB free but only18k inodes; reuse the existing scratch and avoid redundant builds/clones.

## Next executable task and genuine remaining gates

1. Refresh live main,Issue15/manager comments, exact PR heads/checks and claims. This document is evidence, not permission to restart superseded tasks. Owner/manager still owns merges this session; do not self-merge or restart Claude/agents.
2. Repaired #225 is now complete: **BOTH profiles134/134 traversal,Continue3/3,unchangedlegacy3/3**, native29/29,savegoldens4/4,source247/247 and before/after magenta1024→0. Exact final ROM hashes above,55 evidence files pushed. No need to repeat completed pre-repair or final runs without a new source change/failure.
3. #227 central runtime is now complete against exactc6ac44-file source: BOTH profiles55/55 traversal+Continue3/3+genuinelegacy3/3+upperT-bridge87/87+lowerordinarysoil16/16 PASS. Native29/29,savegoldens4/4,host255/255. Original lower15/16 expectation failure retained: follower legitimately stepped onto0; uniform-layer neighbour selection repaired/tested without engine/ROM changes. Do not repeat completed central builds absent new source/failure.
4. Private central paired build bundle is /workspace/scratch/central-current-built-20261022. Preserve its source overlay before reusing the sole scratch; generated binaries never prove clean main.
5. Celestic/North210/East211 outdoor art is now completed/pushed in #228, code3f538cc453136c1021299c9af8c99836bdf8bb1b;245/245 source,8/8 focused,14/14 repeated outputs,5237 preserved cells and39/512 secondary slots. NEXT: permitted art for the three already staged northern Coronet caves, preserve all6 compacted warps, then a coherent six-map DEV runtime. Exact used-bank audit is in that package checkpoint; do not reconstruct converted maps or redo the three completed outdoors. Eight eastern outdoors remain fallback; four eastern gates already complete.

Permanent origins227+/expanded met-location encoding remain owner-reserved; no production promotion of surrogate217 or temporary19+ map slots. Candidate registries deliberately overlap across **separate ROMs**: never concatenate or blindly install them together. If main moves, reconcile the exact engine/base inputs and record actual identity instead of relabelling frozen evidence. Protected production paths still require genuine authorization; source review/graphical gates survive. Pending manager review/identity policy does not block independent art/source/testing work.

Detailed reproducible evidence: the Oreburgh `oreburgh-connected/CURRENT_MAIN_CHECKPOINT.md`, Eterna `eterna-cycle/RUNTIME_CHECKPOINT.md`, Forest `forest-chateau/RUNTIME_CHECKPOINT.md`, and source/art CHECKPOINT files under `celestic-north`, `hearthome-solaceon`, `eastern-loop`. Final live Issue15 comment supplies exact pushed heads after documentation/evidence commits.

Final Forest evidence head a2fb49c995b98fa82ac96111b87e1866fb1a6e9e includes the raw failure/visual diagnostic identities, both repaired profile result/event pairs, source/ROM/native/save/resource receipts and preservation paths. All source work is recoverable in GitHub; central runtime was then pending and is now complete as recorded below. No autonomous coding session or paid agent restart was scheduled.

Resume update: central #227 paired runtime is now actually complete as above, superseding the earlier prepared-only state and immediate-next-task wording. No production merge, main push, ID allocation or automatic session restart occurred. Final live handoff identifies latest exact pushed heads.

Final central overlay actually preserved in stash **b28c3443d0903edf6411ff473c7f398b4f14d403**, scratch source clean exactc6ac on central branch. Marker stashed too. Central built bundle path above remains intact. Final code/source2aa16c82, complete evidence cee63b221a559ff57c89c3c9040de80c5201b971 ready/non-draft with all applicable checks PASS, actual final CI255/0 job120141570671.

Additional implemented progress: Celestic/North210/East211 outdoor art pushed at **3f538cc453136c1021299c9af8c99836bdf8bb1b** (new PR linked in final Issue15 handoff), parent #223. Actual source245/245 and focused8/8,14/14 repeated output files,5237 C/E/full-attribute cells,48 bridge15 cells,39/512 secondary records. No new ROM/gameplay claim. Exact source/graphics hashes in celestic-north/outdoor-art-receipt.json. Next executable task: permitted art for its three already staged northern Coronet cave maps, preserve all6 compacted events, then genuine coherent six-map runtime. Do not remake these completed outdoor assets.

Final source CI independently inspected: #227 doc head2f24dfed255/255,0skips job120145240844; #228 code3f538cc4245/245,0skips job120145075533. All applicable checks PASS, optional weekly skip remains distinct. Later checkpoint-only heads keep identical tested source and need their own final check verification.
