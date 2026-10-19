# Route 201 candidate: local DRY RUN (throwaway build; nothing applied to the repo)

This is **EMULATOR-TESTED evidence that the candidate works when built**. It does not build the route and does not approve it. The owner decisions in [`../ROUTE201_CANDIDATE.md`](../ROUTE201_CANDIDATE.md) stay open.

## Setup

- **Throwaway worktree:** main `de127dff`, carrying the `.map_qa_throwaway` marker.
- **Applied with:** [`route201_dryrun_prepare.py`](route201_dryrun_prepare.py), which refuses any tree without the marker. It:
  - writes `map.bin` from [`../route201-candidate.json`](../route201-candidate.json) using the existing `sinnoh-placeholder-art.py plan --blockdata`;
  - appends the layout, the group slot and the `scripts.inc` include;
  - adds the **reciprocal connection read from the plan**: Route 201 `right` = `offset`, Sandgem `left` = `−offset`.
- **Dry-run-only choices, disclosed:**
  - `region_map_section` is `MAPSEC_NONE` with the popup off, so **no section 217**;
  - music `MUS_ROUTE101`;
  - no events, encounters or trainers;
  - Sandgem's tree border is reused.
- **Entry:** DEV continue-warp save into Sandgem (15, 10).
- **Play:** real controller input in mGBA 0.10.5, state read through GDB, driven by `map_qa.py` from #143.

## Results (NORMAL, cries OFF = main's default; ROM `c1657e9c…`)

| Check | Result |
| --- | --- |
| `map_qa static`: collision, seams, ledge landings, pockets | **0 findings** |
| Codex's map preflight (`audit-averon-map-readiness.py --group gMapGroup_Sinnoh`) | 3 maps, 82 geometry dependencies, **0 errors**. 1 expected warning: `MAPSEC_NONE` |
| Linked ROM growth over main `de127dff` | **+2,948 B** (17,323,848 → 17,326,796) |
| `map_qa run` on the batch Route 201 + Sandgem + Center | **35/35 PASS** ([`result.json`](result.json)) |
| Seams crossed both ways at the first, middle and last open tile | Route (63, 6/8/9) ↔ Sandgem (0, 10/12/13) **and back**, every one exact |
| Route 201 closed edges: Twinleaf (16, 21), Lake Verity upper (0, 10) and lower (0, 14) | all **block** |
| Sandgem's other closed edges, both Center warps in and back, follower, an exit still reachable after every arrival, Start menu, SAVE | PASS |
| Fresh-process CONTINUE | **3/3 PASS** ([`continue-result.json`](continue-result.json)) |

## Finding that changed the design

The first dry run used the reviewed plan's offset **−5**. Walking was correct, but the seam was visibly broken ([`seam-before-odd-offset.png`](seam-before-odd-offset.png)).
- **Cause.** The placeholder round trees are 2 × 2 metatiles: top halves on even rows, bottom halves on odd rows. With an **odd** offset, Route row y meets Sandgem row y + 5, of the opposite parity, so every tree row on the seam showed a top half next to a bottom half.
- **Fix.** Keep the reference path rows 7–8, which DPPt uses anyway, and meet Sandgem's road at **offset −4**. The trees now line up ([`../route201-sandgem-seam.png`](../route201-sandgem-seam.png), [`seam-entering-sandgem.png`](seam-entering-sandgem.png)).
- **Prevention.** `verify_route201_plan.py` gained **check 7**, tree phase across the seam. It fails the old plan and an odd-offset mutation.

**Separate placeholder-art note (not changed here).** The shared placeholder forest generator can leave unpaired tree halves where a stand's width or height is odd. Under a strict 2 × 2 count:
- **Merged Sandgem:** 56 tiles.
- **This candidate:** 92. That is down from 100, because this revision opened row 9 at x 58–60 and completed the 2 × 2 at x 60–63, rows 4–5, and it adds none.

This belongs in a later art pass that treats both maps the same way, not in an unapproved geometry change.

`route201_dryrun_prepare.py` is scratch tooling, kept for reproducibility. Production construction after approval follows the #133 pattern, with a signed literal-path handoff.
