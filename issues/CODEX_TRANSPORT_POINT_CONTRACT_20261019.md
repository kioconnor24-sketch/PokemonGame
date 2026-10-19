# X06 transport-point implementation and upload checkpoint

Codex, 2026-10-19. Source commit `e002f2464d8567708fae54628dbea3dec1cb31aa`; tested integrated source `780382655efebb38e0e7f07082b54e615fea810e` adds merged resource tests #162 without changing the adapter. Current assignment is the owner's expanded engineering/cleanup packet; engineering takes priority. This production API requires independent peer review before integration.

## Implemented contract

New `engine/include/averon_transport.h` and `engine/src/averon_transport.c` provide a caller/ROM-only point descriptor and validation adapter around the **existing** `AveronRegion_BeginTravel` transaction. No competing transaction, saved point IDs, registration table, save bytes, permanent section/heal IDs, scripts or physical terminals are added.

- Validate a point's actual linked map/header/layout/warp and declared saved region. Under the existing convention, saved Averon means engine Hoenn; saved Sinnoh means engine Sinnoh. Unknown section IDs cannot gain permission from the Hoenn display fallback. This checks engine region metadata, not whether arbitrary upstream Hoenn content is approved Averon geography.
- Departure must be an exact coordinate activation point, match the loaded player's map/position and active saved region, and differ from the arrival region.
- First arrival uses the configured valid coordinate/indexed warp. Explicit saved-return mode requires an existing return in the correct physical engine region and actually selects that stored position instead of the configured first-arrival point.
- A configured target healer must be valid and belong to the target engine region. An unset healer preserves the existing transaction's arrival fallback. Wrong-region returns/healers and invalid activation requests are refused before changing the travel transaction or pending warp.
- The caller still performs the normal fade/warp. No collision/walkability, terminal placement, transport vehicle, story/unlock policy, new progression or graphical arrival is approved here. No production caller or script activates this API yet. Existing low-level region-travel behavior stays intact.

## Actual native verification

`engine/test/averon_transport.c` has **8/8 focused native identities PASS**,20 parameter combinations, plus257 saved-region inputs inside the point-validation identity. Positive and negative tests cover first arrival and return in both directions, invalid/current-region/position/null/indexed inputs, wrong-region cached return/healer, a recorded return distinct from the configured first arrival, and actual flash-save/reload followed by return in both directions. Refused requests preserve region record, position, heal/escape warps and pending destination. Native coordinates are fixtures on existing maps, not selected transport terminals. Indexed arrival verifies the armed warp, not graphical field coordinate resolution.

Exact source/test hashes:

| File | SHA256 |
| --- | --- |
| `include/averon_transport.h` | `a21f740eb7eb6f85d05777b510bc102a6146cc717af4e8bb85d2a6a05fdfbe90` |
| `src/averon_transport.c` | `0ffffd62f1a743bd6522085f6e8b12267799986e61a6850d81ee65511b8ad468` |
| `test/averon_transport.c` | `9785991a354c748535444e758bb3591a659d1d15d783d48c9e306544d4589625` |

Commands from `Pokemon Game/engine`, GCC14.2.1 (20241119), ld2.44, newlib4.5.0.20241231:

```sh
make -j4 -O check 'TESTS=Averon transport' ROMTEST=/workspace/.onboarding/mgba-rom-test
make -j4 -O RELEASE=0 all
make -j4 -O RELEASE=1 all
make -j4 -O check 'TESTS=Averon' ROMTEST=/workspace/.onboarding/mgba-rom-test
```

The final complete Averon run on the integrated source is in progress at this upload checkpoint: expect288 preexisting +5 merged #162 +8 adapter identities =301. Its actual final result must be posted before merge. Existing legacy-save, saved-ID, encrypted party/PC and flash interruption identities are retained; do not relabel current-format flash fixtures as an old-ROM graphical Continue test or repeat the accepted unfiltered M1 baseline. No saved structure or migration changes.

## Actual production builds

Both ordinary default-OFF profiles **PASS** on source78038265, measured again with real linker output and retained logs. No explicit restoration-ON profile was requested or enabled. No RAM or save growth; same linked-byte budgets as reviewed #154. ROM hashes differ and are reported exactly; no byte-identity claim is made. The unused adapter symbols are removed from production by linker/LTO; cost after future activation remains unmeasured.

| Profile | Linked ROM | Free /32MiB | EWRAM | IWRAM | ROM SHA256 |
| --- | ---: | ---: | ---: | ---: | --- |
| NORMAL | 17323776B | 16230656B | 226480B | 28392B | `c4d34df226e4c7f003abaacef586687fefcd27895adbe56ca4b9a08696cfc65c` |
| RELEASE | 17442912B | 16111520B | 226482B | 28336B | `2e8690c3cc773f1177aabe90099f5fd002ac4bdf2087e534b354cbbafd4f7271` |

NORMAL has zero warnings; RELEASE retains four known newlib syscall-stub warnings. Save headroom: SaveBlock1 304B, SaveBlock2 84B, SaveBlock3 1556B, PokémonStorage1568B. No ROMs, ELFs, private saves or caches are uploaded. Native/build results do not establish actual first-story travel, natural whiteout through a new transport, full-field performance, human audio or Delta acceptance.

## Uploaded work and precise continuation

- #154 integrated `e1bf5a76b20da7c21a36ba4818768fa857391db6`: independently reviewed invalid-section guard, final-head288/288 native CI, real NORMAL/RELEASE evidence. #160 and #161 are already complete; do not repeat them.
- #162 integrated `bc55711215126fc5f6f95e3ea2875f92ceb356ab`: local and CI293/293 native PASS, five resource identities/28 combinations, real menu sampling and limitations. CI run39221592867/job117957913223/artifact12172079109; ZIP SHA256 `9c6126fba1cdba682f2cb4f05e0a8957a9962990c414559320a09ef3753318f6`. CI NORMAL ROM `f49b009175a3e6fa6e600e4a22b8c6d56876513ab56cd7fa73697ea02d32add9` is identical to final #154 CI. Resource claims released.
- Existing recovery branch `codex/sinnoh-combined-proof-20261019` remains pushed at `81ddd4235c9b8f7a41fc8e59e89c89ed637bd196`. Its293 tests are the older temporary #150/#151/#154 combination, not the #162 test set. It does not replace actual main or Claude's acceptance.
- All eight adapter tests and implementation are pushed on `codex/transport-point-safety-20261019`; publish this report in the focused PR, finish301/301 and current CI, obtain actual independent source review, then normal expected-head author merge. **WAITING_ON** that review for integration, not routine manager approval. **RESUME_WHEN** actual peer review is recorded and all latest applicable checks pass.
- Live #151 has moved to `e2b43d9f74b05a6073bfbf295dd80132df522bed`; it remains draft at this scan, and newest CI is queued. #150 remains draft at af28cc6e. Do not integrate drafts or reuse earlier heads as current proof. After real integration, compare actual source and run affected compatibility checks.
- New owner comment6271044156 approves only Twinleaf218 in addition to existing216/217 decisions. Claude owns its maps. No218 allocation or geometry is implemented here; further identity/encoding decisions remain reserved. The #161 precision packet is already on #26; no speculative13-bit implementation.
- Remaining expanded cleanup work has not been falsely marked done: audit live branches by unique code/evidence (squash-aware), workflows and old combined-build inputs, template/tasks.json consumers, navigation and public v1.0 distribution/provenance. No branch, release asset or historical evidence has been deleted. Continue these disjoint tasks while waiting for source review.

An all-worktree upload check found only an older capacity experiment's dirty source and a generated Python cache outside the active clean worktree. The old source is **already uploaded**: exact OFF-experiment config at `c9ddb7f47f57ed7cae30d2ceb4f4a397b8c5000f`, exact sound source at `456a45016446c8b103f373b2d7b6fe082cd757c7`, exact earlier safety tests at `d84f6d52ae5ad02c6690fc46487f7ce5a5d9c527` (GitHub commit APIs verified). Its NULL probe is byte-identical to main's `scripts/coordination/codex_cry_null_probe.c`. Preserve that worktree; do not reintroduce this superseded experiment or upload caches as new implementation.
