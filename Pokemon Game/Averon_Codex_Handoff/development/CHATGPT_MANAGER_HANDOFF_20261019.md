# Pokémon Averon — ChatGPT manager handoff (2026-10-19)

**Repository:** https://github.com/kioconnor24-sketch/PokemonGame  
**Snapshot main:** `de127dff378abe720bba8b627dd123c4db478fb8` (2026-10-19; #146 cries OFF default).  
**Reset PR:** [#144](https://github.com/kioconnor24-sketch/PokemonGame/pull/144), branch `chatgpt/organizational-reset-20261018`. This handoff and updated contract/queue are **proposed in that open PR**, not necessarily merged.  
**Live authorities:** owner's recent decisions in [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), exact current `main`, PR files/heads/checks, and—once reviewed and merged—the [operating contract](CURRENT_PHASE_AND_HANDOFF.md) and [integration queue](INTEGRATION_QUEUE.md). Read **these** before any old manager handoff. Nothing in a dated snapshot overrides subsequent owner instructions.

## 0. Mission and change in management philosophy

The owner requested a full organizational reset and **more independent developer management**. Claude and Codex are autonomous **peer co-leads**, not subordinates waiting for a third ChatGPT manager to read every PR. They should plan milestones, coordinate disjoint file claims, fix their own CI, review risky changes by the other developer, execute eligible normal merges, preserve handoffs and address blockers. The ChatGPT manager is now **optional escalation/auditor**, used for owner-directed design discussions, difficult architecture, independent reviews or stalled integration—not a mandatory per-PR gate.

**Critical new owner decision:** The owner explicitly selected **option 2 (tiered review)** in [#15 comment 6258091946](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6258091946). A previous full-cross-review draft (#144) caused Claude to report four low-risk PRs stalled behind idle Codex. That draft is **superseded**, not owner policy. Stop telling Claude/Codex that every PR must be peer-reviewed or that authors can never merge their own work.

### Precise tiered merge rule (symmetric for Claude and Codex)

**Author self-merge is allowed only if ALL hold:**
1. Final diff exclusively touches **docs, trackers, design proposals or isolated test/QA tooling**. No game/engine production source, permanent map data/layout/tilesets, saves/formats, IDs, protected paths, or executable workflows/CI.
2. PR is not draft; no contradictory owner/reserved decision; no peer claim collision; all *applicable* current checks and meaningful tests pass, without suppressing failures.
3. Author posts a substantive **evidence comment** listing the exact full head SHA, changed paths and real test results (including skipped/unknown). The PR's passing checks actually apply to its changed code.
4. Author pins the merge to that exact head (`--match-head-commit` with GitHub CLI or SHA-expected API), then verifies `main`.

**Independent peer review still required** for production game/engine code, saves, map/layout/tileset data, permanent identities, protected paths, workflows/CI and consequential architectural/release changes. Claude reviews Codex's such PRs, Codex reviews Claude's. Reviewer records exact SHA, actual inspected source/evidence and risks; both agents share a GitHub login, so an ordinary GitHub `APPROVED` state is not by itself proof of independence. **No force-push, direct main edits, bypassed guards or false QA.** Having a manager role never grants self-merge exceptions for high-risk changes.

A candidate design document may qualify for low-risk self-merge yet **cannot authorize permanent production geometry/section ID**, which requires owner approval separately.

## 1. Current integrated product state (verify live on restart)

- Accepted pre-Sinnoh **Milestone 1** on 2026-10-17. Historic full run: 6,107 results, 5,332 PASS, unchanged 327 normalized expected-failing identities / 329 failure results. Not "6,107 passed". Full human audible listen and Delta iOS acceptance are **unverified/deferred**.
- **Sandgem Town + Pokémon Center** first permanent Sinnoh slice [#133](https://github.com/kioconnor24-sketch/PokemonGame/pull/133) merged at `ce0c505d4ae3103680f96482881b9589bced14c0`; section **216** is on `main` via #132; town and Center linked with their proper map name, registry pins and required unchanged legacy section IDs. Claude's merged-main NORMAL/RELEASE OFF emulator checks **26/26 each** included Center nurse, menu, follower, door, blocked exits and fresh-process Continue. **Only entered through DEV fixture:** not ordinary story access from Averon, no natural Sandgem whiteout anchor, no playable Route 201 yet.
- **Codex technical fixes/tests merged:** #136 guard u16 healer ID narrowing and optional nurse-table bounds; #138 suppress unsupported Sinnoh Fly/Town Map/PokéNav entry; #137/#140 travel/connection tests; #134/#141 origin capacity experiments (test-only, no encoding adopted); #142 handoff checkpoint. Claude peer-reviewed/merged each with SHA pinning and checked integrated engine tree identity. Reported combined **284/284 focused native identities** (not a new full M1 suite). Existing default resource constraints persist.
- **Read-only PR advisory workflow #145** merged `8e67abf7`; historic #31 generated board is *not* current authority.
- **Cries OFF is now the production default** by explicit owner direction, merged **#146** at main `de127dff378abe720bba8b627dd123c4db478fb8`. Retain full cry sound data and explicit `CRIES=on` restoration build. Do NOT restore the older "default ON" advice from old handoffs. Human listening and Delta testing remain unverified. Keep ROM measurements clearly labeled OFF/default versus ON/restoration.
- Other implemented Averon foundations (starter opening, Gym 1 progression, quest/encounter/native safety and following) are already M1 accepted. Do not restart M1 or re-open merged PRs.

## 2. Open PRs seen at handoff (refresh exact heads)

| PR | Authored by | Snapshot SHA | Status / next |
| --- | --- | --- | --- |
| [#143 map-QA](https://github.com/kioconnor24-sketch/PokemonGame/pull/143) | Claude | `484c12e962ccb781c0844a37cd646f6ae1021800` | OPEN, non-draft; second fixture run 6/6, first 4/6 preserved, actual NORMAL mGBA. **Tiered low-risk self-merge eligible** only after diff/checks/author evidence verified. |
| [#147 Sandgem tracker](https://github.com/kioconnor24-sketch/PokemonGame/pull/147) | Claude | `1f6cdb21e24a6885dfa6e72838512c69776e9142` | OPEN; SN-T02 Sandgem structure verified, narrative gameplay deferred. **Tiered low-risk tracker self-merge eligible**. |
| [#139 Sinnoh junctions](https://github.com/kioconnor24-sketch/PokemonGame/pull/139) | Claude | `1fb0082f5a287d776a0e49de5c70a299b8da296a` | OPEN docs only; incorporates Codex corrections and ±4 offset. **Tiered low-risk self-merge eligible**. |
| [#135 Route 201 candidate](https://github.com/kioconnor24-sketch/PokemonGame/pull/135) | Claude | `c957344d75b740ddf70eb3e6d025decfd32776f6` | OPEN **design only**; mGBA throwaway dry-run 35/35, Save→Continue 3/3; corrected seam phase/right -4 left +4. **Tiered self-merge eligible** as a proposal; never production approval. |
| [#148 X7 report](https://github.com/kioconnor24-sketch/PokemonGame/pull/148) | Codex | `5e3997a54c9a88fb194d72d83f860e32565b4a84` | OPEN docs-only; Claude asked to correct obsolete references to #143/#139. **Codex should fix and may self-merge R0** after evidence/checks. |
| [#144 organization reset](https://github.com/kioconnor24-sketch/PokemonGame/pull/144) | ChatGPT manager/reset | **HEAD CHANGES AS THIS HANDOFF IS WRITTEN** | OPEN, broad governance: initial Claude review flagged stale default ON, merged Sandgem, merged backend and outdated blanket review rule. This handoff plus manager/contract/queue corrections are being pushed to its branch. It spans root agent entrypoints/policy: treat as **governance-sensitive R3**, obtain genuine peer review of final head before merger. |

See [INTEGRATION_QUEUE.md](INTEGRATION_QUEUE.md) for an easier-to-update checkpoint. Never assume a snapshot is the latest PR list. Other historic PRs #133/#136/#138/#137/#140/#134/#141/#142/#145/#146 have **merged**, not stalled.

## 3. Owner-only decisions / genuine creative gates

**Route 201 is the first next playable construction priority**, *after* specific approval. Do not mistake merging #135 as approving a permanent map.

- Read original [owner packet](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6257061171) AND more recent [camera/tree-seam correction](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6257962578).
- Proposed approved-on-request: 64×22 original DPPt-inspired geometry, 3 small documented deviations; section ID **217** allocated append-only by Codex; reciprocal Route201 **right -4** ↔ Sandgem **left +4**, not older ±5; **Twinleaf and Lake Verity exits remain closed**; tall grass physical only until separately approved encounters. Owner can approve all five or request changes. New signed exact-file `HANDOFF_APPROVED` needed for production Route201 and Sandgem connection edits AFTER specific scope decision.
- **Sandgem natural whiteout**: owner approval needed for exact permanent healer ID and destination exterior/Center nurse coordinates. Codex's merged generic #136 prevents some safety bugs but does **not** implement a Sandgem respawn anchor. Claude must wire own map/script only after approval.
- **Route 202** lacks a reliable full overhead; either find/provide source, explicitly approve a marked schematic, or defer. #139 is just a specification.
- **Future met-location encoding**: only 36 ordinary 8-bit section codes remain after 216 (217–252), specials preserved. Grouped byte labels lose per-map origin precision; 13-bit experiment risks legacy/import/egg and consumer incompatibilities. Research/test PRs #134/#141 do NOT adopt a new save scheme. Owner must decide if/when a format project is warranted.
- **Full Sinnoh Town Map/Fly destinations** require later approved assets/data. Safe fail-closed entry is the implemented temporary behavior.
- **Audio**: OFF default has been approved and merged; no longer a pending choice. Human listening and final Delta acceptance remain separate checks.
- **Story**: never finalize provisional rival/leader/Arceus content by manager shortcut. Continue owner discussions and use [working narrative dossier](../design/STORY_DEVELOPMENT_WORKING_DOSSIER_20261017.md) before implementing plot.

## 4. Creative baseline: do not lose this context

Averon is the custom first region, lively normal Pokémon adventure through most of the story, with small natural amounts of foreshadowing; Sinnoh is a **full second region**; Cynthia appears in Sinnoh and Red is the ultimate final trainer battle after postgame. Gym 6/7 in northern mountains; Gym 8 southern volcanic island; distinct remote Pokémon League. Following Pokémon, Mega Evolution, original held-item EXP Share, forced Set style, one challenging difficulty, maximum level 100; no Z-Moves, Dynamax or Terastallization.

Secret Vantage organization deeply infiltrates authority and later carries out a coup with complex mixed civilian reaction. Public motive: end humanity's **dependence** on Pokémon; leader privately seeks **eradication** via dimensional energy. Government Threshold device initially extracts power, suffers a filtration/rift catastrophe killing/erasing a test Pokémon, and Zygarde emerges. Antagonist has independent personal motive prior to witnessing this event; first rupture provides means, not motive. The leader genuinely mentors childhood rival Renn and may see him privately as a successor, but no public heir proclamation. Rival's setbacks/recruitment/redemption remain in development; his eventual return to our side is essential. Rupture pulls protagonist and villain to alternate dimension during climactic device failure. Further Arceus/Plates and Sinnoh continuation details are **provisional**. Most NPCs, humor and exploration should be unrelated to the conspiracy. No prolonged grim occupation, exposition dumps or nonstop foreshadowing. Preserve varied supporting cast and ordinary Pokémon journey feel.

Do not create finalized story production instructions from provisional alternatives. Full design dossier is the primary story-detail source, not this manager process checkpoint.

## 5. Technical/resource/QA truths to preserve

- Game is Emerald-derived decompilation. Production Game Boy Advance ROM, source and native CI matter. Measurements depend on exact build profile and toolchain. An ON restoration figure is not an OFF-default reserve. Do not claim all of Sinnoh fits from extrapolation; measure actual linked ROM, RAM, save bytes and runtime sprite/palette/stack peaks as areas are integrated.
- SaveBlock2 historically **84 bytes free**. Stable preexisting legacy section IDs 0–214, NONE=215, Sandgem=216; ordinary 217–252 open pending explicit allocation; reserved FD–FF special location encodings. Don't silently modify old saved identities.
- Positive green CI does NOT establish graphical reachability, natural whiteout, human or iOS Delta proof. Claude's mGBA acceptance may use a DEV continue-warp save fixture; disclose that.
- Script/world data need original reference/source differentiation. Licensed in-repo placeholder art is temporary; future custom asset provenance must be managed. Never commit copyrighted ROMs, generated full ELFs/ROMs, user private save files, secrets or unlicensed friend likenesses.
- #143 map QA discovered 79 perceived "seam-bump" hits on frozen Averon areas; Claude inspected them and recorded facing **visible round-tree barriers**, not a reproduced invisible-wall defect. Don't start unrelated map changes on that basis.
- No agent may delete ~143 historical branches simply because their names look old; the archived branch inventory is dated and retains all, including potentially unique nonancestor tips.

## 6. What the NEXT MANAGER should actually do

1. **Refresh reality first**: read current `main`, open PRs, #15 latest, owner-decided tier rule, #144 review/CI, QA #23, issues #55 and roadmap #26. Compare updated branch #144 to current main, including policy and any merged PRs. No assumption that this document's six open PRs remain open.
2. **Finish #144 governance reset, not another reset project**: ensure tiered self-merge policy, cries OFF, merged Sandgem/backend/automation, no archaic PR backlog, latest corrected Route 201 ±4, open owner decisions, docs redirects and preservation of archives. Its author/manager should request independent source-of-truth review of changed governance documents from Claude or Codex, then let eligible normal merge proceed. Keep the 2026-10-18 reset audit as a dated archive; do not rewrite history.
3. **Empower developers**: notify Claude/Codex where policy resides (owner [#15 decision](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6258091946), corrected #144 branch), and avoid inventing cross-review waits for low-risk PRs. Developers should perform routine planning, prioritized implementation, relevant reviews and merges themselves while their sessions run.
4. **Only escalate real owner choices**: Route 201 packet (latest ±4), Sandgem healer ID/anchor, Route 202 reference decision, future saved-origin precision. Do not self-authorize these.
5. **Do not maintain one-to-one manager PR review service**: return for periodic architecture/QA audit, genuine high-risk disagreement, branch/CI policy changes or when the owner requests help. Let completed low-risk work flow to main using the owner-selected tier rule.
6. **No unsupported tool actions**: GitHub comments cannot trigger paused ChatGPT/Claude sessions. Use the appropriate agent sessions. A separate account/branch-protection policy may eventually enforce reviewers but is not currently configured; don't falsely assert that a comment is a formal multi-account approval.
7. **No broad destructive cleanup**: no unreviewed PR merges, no forced branches, no changing checks/branch rules from a doc request, no deletion of stored QA evidence.

## 7. Quick links, owner instructions, and restarting

- [Repository](https://github.com/kioconnor24-sketch/PokemonGame)
- [Current main](https://github.com/kioconnor24-sketch/PokemonGame/tree/main), [open PRs](https://github.com/kioconnor24-sketch/PokemonGame/pulls), [Actions](https://github.com/kioconnor24-sketch/PokemonGame/actions)
- [Reset PR #144](https://github.com/kioconnor24-sketch/PokemonGame/pull/144), [latest proposed operating contract](CURRENT_PHASE_AND_HANDOFF.md), [queue](INTEGRATION_QUEUE.md)
- [Live claims/owner approvals #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), [QA #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23), [owner roadmap #26](https://github.com/kioconnor24-sketch/PokemonGame/issues/26), [problem desk #55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55)
- [Sinnoh stage tracker](SINNOH_MAP_BUILD_TRACKER.md), [87-area register](SINNOH_AREA_REGISTER.csv), [location compatibility study](SINNOH_LOCATION_ID_COMPATIBILITY_20261018.md), [M1 acceptance report](M1_ACCEPTANCE_REPORT_20261017.md)
- [Reset audit](ORGANIZATIONAL_RESET_20261018.md), [branch inventory](BRANCH_AUDIT_20261018.csv) and preserved [archived process texts](archive/reset-20261018/README.md)

**Suggested next manager-session prompt:**

> Read `Pokemon Game/Averon_Codex_Handoff/development/CHATGPT_MANAGER_HANDOFF_20261019.md` from PR #144 (or main if merged) IN FULL. Refresh live GitHub, owner Issue #15 tiered option-2 review and current main. Confirm #144 governance review/merge status and developer self-merge autonomy; do not revive blanket cross-review or older manager-only merge gates. Prioritize real owner design approvals and exceptional technical blockers. Update records only when materially needed; do not create another redundant manager hierarchy.
