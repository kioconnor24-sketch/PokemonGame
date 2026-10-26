# Claude session issues and handoff: 2026-10-25/26 (W15–W20, C12–C36)

An honest record of what went wrong this session, why, and what fixed it. Items marked **[model]** were caused by my own reasoning or diligence gaps, not by the environment, the repository or other agents. They are listed so reviewers can weigh my evidence accordingly.

## Issues caused by my own mistakes [model]

1. **#252 merged with a regression that broke main.**
   - **What happened:** #252 made map_qa's `map_points()` add an `exit` flag and read `p["exit"]` everywhere. Codex's `test_sinnoh_same_map_warp.py` builds points by hand without that key, so two tests raised `KeyError` on main after the merge.
   - **Cause:** I ran only map_qa's own suites (`test_map_qa`, `test_claude_play`) before asking for review, never the repo-wide `scripts/tests` discovery that exercises other agents' callers of map_qa.
   - **Fix:** the manager fixed it in #303 (fixture fix). My later alternative, #304, relaxed map_qa's semantics instead, so I closed it as superseded.
   - **Lesson:** before any shared-tool PR, run the full repository suite, not just the tool's tests.

2. **Static "0 findings" claims that were too strong.** map_qa didn't model that Acro Bike rails and bumpy slopes are a collision on foot (`CheckAcroBikeCollision` runs for every player step). Static audits that passed this session were therefore blind to rail barriers. A live emulator run on Route 212 South exposed it. The fix is #300, which is held because it correctly fails Codex's hotel-link world audit on the real Route 212 South defect. Re-audits found no other affected W batch. **Lesson:** a static PASS is only as good as the model of engine collision behind it; say so when reporting.

3. **I tried FRLG interiors for W17.** I chose the Celadon condominium layouts without checking that mapjson skips `layout_version: "frlg"` layouts in the Emerald build. The static audit crashed on them; I switched to Emerald's Cove Lily Motel. **Lesson:** check layout build eligibility before reusing a layout.

4. **The scene installer skipped maps only one level deep.** `qa-tools/static_scene.py` skipped maps leading directly into a skipped overlay, but not maps reaching it through other new maps. A Hearthome DEV build failed on Veilstone's department store 2F. It was fixed with a fixed-point skip, and that gate was rerun.

5. **Tests that encoded wrong assumptions.**
   - The W17 test assumed an animated door word is walkable; it isn't (doors are entered by pushing).
   - A W16 gate counted "starts inside the batch" as a failure because the save fixture starts in Jubilife.
   - Neither was a map defect, but each cost a rebuild or rerun.

6. **Inaccurate GitHub text, corrected afterwards.**
   - The first W15 claim had a placeholder comment ID.
   - A #300 comment cited the wrong PR number (#303 instead of #304).
   - I called the Route 213 `exit-unreachable` "unverified" when my own audit had simply excluded the Hotel Grand Lake. Route 213's halves join through the hotel interior.
   - All three were edited or corrected publicly.

7. **Production integration was planned late.** W14 put Hoenn stock stand-ins behind Jubilife's TV, Pokétch and condo doors without first checking Codex's #238, which already adapts the authentic Jubilife interiors. I found the overlap only while preparing packet A (#306). The integration now needs an owner or manager choice so it doesn't create orphaned permanent map slots. **Lesson:** check every other agent's packets for the same buildings before staging substitutes.

8. **Earlier in the project** (recorded in #15): I first proposed "elevation 15" for the Route 209 ruin steps (wrong; the working fix was 0). I also first misdiagnosed a W14 probe failure before finding the real cause.

## Issues not caused by the model

- **`make -j` race (#263; manager #289):** it intermittently truncates `heal_locations.json` mid-build. One RELEASE build failed this way, and the rerun passed. Guarded builds (`qa-tools/gbuild.sh`) detect it.
- **DEV assembler pin coupling:** every Codex DEV scene assembler pins SHA-256 hashes of main's inputs and fails closed when main changes. Any production integration therefore needs Codex to re-pin. This blocks #306 by design.
- **Identity gating:** every remaining west/central/south-east area outside the existing sections 215–225 needs owner-reserved IDs (227+) before it can be integrated. #237's interiors are owner-gated by `exclusive-files`.
- **Route 212 South rails (Codex's eastern-loop):** they cut Route 212 North off on foot, which blocks W17's live gate. The crossing contract is in `route212-mansion/CROSSING_CONTRACT.md` on #291.
- **Environment:** this host has no `jq`, so 3 coordination tests fail identically on main. The auto-mode safety classifier also intermittently fails to return a verdict, which stalled this handoff for several minutes.
- **Two scenes:** W19's Maniac Tunnel link spans Route 214 (eastern-loop) and Route 209 (hearthome-solaceon). No single DEV scene holds both, so it has no live crossing test.

## State at handoff

| PR | State | Next |
| --- | --- | --- |
| #306 C36 packet A (10 maps → production) | Open. NORMAL/RELEASE built; mGBA gates running locally; CI fails only on the 8 expected pin guards and `exclusive-files`. | Owner/manager: choose option (a) narrow or (b) full. Codex: re-pin. Manager: exact-path handoff. |
| #300 rail rule | Open, reviewed. | Merge after the Route 212 South crossing fix. |
| #285 / #287 / #291 / #293 / #294 / #297 (W15–W20) | Open. NORMAL+RELEASE DEV gates pass (W17 blocked; W19 not testable live). | Review. |
| #257 W5 | Review finding fixed (`41429f96`). | Re-review. |
| #268 / #269 / #270 | Extended with civic interiors and door pictures; NORMAL+RELEASE pass. | Review. |

**Resume next:** read the packet A gate results (`/root/claude-dev/cries-scratch/gate/packa-*`) and the Lost Tower NORMAL/RELEASE results (`w8-normal`, `w8-release`, chain13), then post them on #306 and #267.
