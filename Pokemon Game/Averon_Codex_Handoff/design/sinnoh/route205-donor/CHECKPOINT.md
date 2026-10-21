# Northern corridor: source-only implementation and runtime checkpoint

**Not production integration.** The six staged maps retain `MAPSEC_PENDING_OWNER`; only the disposable ROM uses existing section217 as a display surrogate. Its saves must not ship. No permanent224+ identity, save schema, new asset rights or gameplay is authorized by this evidence. Claude remains paused and its branches were preserved.

## Exact sources and resources

- Production base: main `d182c7b53f2566cba175e2ad01549af617e04032` (Route202 merged).
- Reproduction base: published queued Jubilife `f77bc9511f0afdbab665165d49c2f7433c92e41d`.
- Tested disposable source: `f803d3d085f5084b234c3c4fcd15950c10c50e03`; engine tree `4edc7114dce2e85afff71d83ffed149a21320903`. This local-only commit is not required for reproduction: the public base and guarded helper reproduce all30,441 tracked engine files byte-for-byte, with zero mismatches. Input aggregate,30 changed paths, resources and sampled stack data are in [source-manifest.json](evidence/20261021/source-manifest.json).
- QA code: `6879dc20f7098d98132268a48424b6e607df3bb9`; initial main NORMAL began before the final static/count post-run guards were added; its actual receipt independently has67 passing checks and0 findings. The route and inherited acceptance methods were unchanged. RELEASE used the guarded version.
- Preserved Claude stage `7f24a0c310cb3f94a8ccdac22bd051156cb2ee78`; donor revision `38228bb574a3557345852b758d5f1a65eb01bb22`. North converter output/header/scripts reproduce that stage. No donor art was added.

| Build, default cries OFF | Linked ROM bytes | Growth beyond queued Jubilife | Padded ROM SHA256 |
| --- | ---: | ---: | --- |
| NORMAL | 17393272 | +33464 | `68d40c282709e89aa41c23ea2ef7584f495f0a72220ea606a576d4be6e2e159e` |
| RELEASE | 17512400 | +33464 | `afaaf49e1aa5105d798c56cfcb96a6b26af4f0195686a6c5980ace305e0f2a1c` |

Both actual builds passed, GCC14.2.1/apcs-gnu; graphical mGBA0.10.5. ELF load bytes/linked extent verified against each ROM. Padded artifacts are32MiB; RELEASE linked headroom16,042,032B. Linked RAM growth0: NORMAL EWRAM226480/IWRAM28392; RELEASE226482/28336. Actual normal-ELF free save space: SB1=304B,SB2=84B,SB3=1556B,PC=1568B. Sampled minimum stack free was1376B NORMAL/1032B RELEASE across9 state captures each, not a worst-case stack bound. Existing newlib stub linker warnings are disclosed in link-log excerpts, not a zero-warning claim.

## Actual results

- Focused host19/19: donor pin/dimensions, all64 collision/elevation combinations, unknown bank refusal, neutral pending headers, reciprocal seam, throwaway/reentry guards, hash-pinned routes, both bridge levels and invalid level transitions.
- Current-source native registry3/3; save compatibility goldens4/4 (SB1/SB2/SB3/PC). Not the full unfiltered M1 suite.
- Complete six-map static0; registry77groups/970pinned IDs/553linked maps. Twelve invalid registry mutations and3 ELF pointer mutations detected;1 valid append accepted. Repeated registration rejects before writes.
- Existing North wrong-offset fixture rejected. Two more current-source static negatives reject the swapped Ravaged Path return and shifted South/Floaroma seam. Whole six-map baseline0 is used for these source-static mutations; the original one-map South runtime fixture batch intentionally lacks the North detour and has a source reachability warning in isolation. These are not claimed as negative emulator runs. Headers restored afterward.
- NORMAL67/67 and RELEASE67/67: all inherited seam/warp/closed-edge/follower/menu/SAVE checks, plus fresh-process Continue3/3 each. Flash-slot verdicts clean. Initial entry is a DEV continue-warp fixture, not natural story access. Subsequent SAVE and Continue use actual game-written flash.
- Supplementary ordinary-controller bridge and converted-walkway probe: NORMAL69/69; RELEASE69/69. Low bridge, upper bridge in both directions, walking underneath, water refusal without Surf, converted North walkway and visible followers. No Surf, Delta or human listening acceptance claimed.

## Reused geometry and real failures

The16,184 cells are preserved existing conversions, not recreated. The helper draws Route204 with the same existing corridor Rustboro bank as Jubilife and stages a reciprocal City/204 +36/-36 seam. The donor's east pocket is isolated: expose only City(48..51,0); keep City58/59 shut and close Route204(22/23,63). Seven-map static audit including City is0. These two-cell adaptations exist only in the disposable helper; published donor staging stays intact. Shared General graphics and all production maps are unchanged.

Keep the raw initial65/67: collision-only navigation attempted an elevation3→4 shortcut at the high North/South seam. No map defect was demonstrated or hidden. A pinned52-step ordinary walking route through North(23,53) elevation0 proves the exact high seam and return. The supplementary lower approach and105-step South exit route preserve actual bridge15 elevation retention; every controller step is observed. Shared QA source/checks, game memory and map geometry are unchanged.

Earlier bridge attempts50/51,2/2-aborted,59/60 and59/59-aborted are retained as FAIL: the height-blind planner, a post-follower position assumption, omitted cross-map travel and another height shortcut respectively. Final test code separates target assertions from the follower probe's own movement, restores route anchors and explicitly walks the correct paths. No failing check is filtered or relabeled. Startup failures on displays77/83 are not PASS; direct graphical/GDB launch worked. Final bridge sequence used display85, a real window warm-up, then one mGBA at a time; the precise intermittent video root cause is not claimed solved.

## Reproduction

Use a NEW disposable worktree/branch prefixed `codex/north-scratch-` at published base f77bc951, preserving any dirty work. Create `Pokemon Game/engine/.map_qa_throwaway`, then run:

```sh
python '<this-directory>/prepare_connected_scratch.py' --repo '<throwaway-repo>'
# Current workspace toolchain: . /workspace/.onboarding/activate.sh
make -C '<throwaway-repo>/Pokemon Game/engine' -j3 -O all
make -C '<throwaway-repo>/Pokemon Game/engine' -j3 -O all RELEASE=1
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s 'Pokemon Game/scripts/tests' -p test_sinnoh_route205_north.py -v
```

Native TEST_SRCS: four runner helpers `test_runner.c`, `test_test_runner.c`, `test_runner_args.c`, `test_runner_battle.c`, plus `averon_map_registry_contract.c` and `save.c`, all under `test/`; `make check TESTS='Averon map registry'` then `TESTS=test/save.c`, ROMTEST=/workspace/.onboarding/mgba-rom-test.

Generate your own valid disposable test save. Use existing `scripts/claude_play/map_qa.py fixture-save --engine ENGINE SRC_SAVE SCRATCH/game.sav MAP_ROUTE205_NORTH 3 57` (DEV only). Run `run_connected_qa.py --engine ENGINE --rom ENGINE/pokeemerald.gba --scratch SCRATCH --out NEW_OUT --profile normal`. For fresh Continue copy its game-written flash to a NEW scratch/game.sav and rerun with `--expect NEW_OUT/saved-northern-corridor.json`. Repeat RELEASE using pokeemerald-release.gba and --profile release. Run `run_bridge_qa.py` with the same engine/ROM/profile, `--save MAIN_SCRATCH/game.sav`, NEW scratch/out and `--display 85`. Serialize all graphical processes; GDB2345 is fixed. Xvfb/SDL must be ready in the same execution context; software SDL/X11 and writable XDG paths were used. No ROM/ELF/private save is published.

## Waiting on / next action

[Verity191](https://github.com/kioconnor24-sketch/PokemonGame/pull/191) still needs a genuine owner twelve-path handoff ([exact template](https://github.com/kioconnor24-sketch/PokemonGame/pull/191#issuecomment-6315224822)); its failing exclusive-files gate is not bypassed. After legitimate merge, reconcile the already tested queued Jubilife branch, preserve its runtime bytes/slots7..12, and open its own serialized production PR/authorization. PR184 stays preserved draft until explicit disposition.

Northern production needs the owner's three-code versus five-code naming decision from [SECTION_RECOMMENDATION.md](SECTION_RECOMMENDATION.md), then a new append-only serialized production PR and its own protected handoff. Neither a proposed identity nor merged source-only staging authorizes production. Initial assignment1–3 must integrate or wait exclusively on exact owner action before the next substantial Oreburgh-side off-engine batch. No automatic agent restarts, story, trainers, encounters or unlicensed art.
