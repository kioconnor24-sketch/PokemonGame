# Pokémon Averon — authoritative next ChatGPT manager session handoff

> **LATEST VERIFIED EXECUTION CHECKPOINT — 2026-10-20, about 01:19 America/New_York.** This section **supersedes** every older "one open PR", "Codex stopped by owner", outdated engine SHA and "sole blocker" claim elsewhere in this historical handoff. Fetch current main/PRs again before acting.
>
> - **Main**: `21086c44e56fa9262440859a1e49b960cfc37125` after [#183 Verity preflight](https://github.com/kioconnor24-sketch/PokemonGame/pull/183). Earlier #176–#178 donor tooling and #166 Twinleaf are merged. PR #175 is **closed unmerged**; do not assume its tree repair is on main.
> - **Claude has finished its Verity build/QA, NOT merged**: [Issue #15 checkpoint](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6283760927). Off-engine `claude/verity-donor` at `e682894b`; production `claude/verity-integration-hold` at `d7f80ca6`, deliberately **no PR** until #181 is integrated due to shared `event_scripts.s` protected-file collision. On engine tree `d62eba53`, Claude reports NORMAL+RELEASE and native **316/316**, authentic mGBA **40/40 per documented batch** on both profiles, fresh Continue **3/3**, zero static findings, verified negatives. Those test claims are Claude's, not a separate manager mGBA run.
> - **Route202 PR #181 OPEN/non-draft**, unchanged head `962a472eb42f5c0d8c549bd67f3dab8fd7497430`, exact `exclusive-files` **FAIL**: absent PR-scoped owner-confirmed eight-path protected handoff. **A second, real acceptance issue was disclosed** in [Claude's seam correction](https://github.com/kioconnor24-sketch/PokemonGame/pull/181#issuecomment-6282414958): its positive 51/51 mGBA runs had *two static seam-mismatch findings*. Claude proposes only changing Route202 `down` **+4→+3** and Sandgem `up` **−4→−3**, with targeted static/seam/Save→fresh Continue recheck on both builds. These offsets are **a proposed fix, not a pushed or accepted result**. Do NOT merge #181 on prior 51/51 alone, or describe missing handoff as its only outstanding problem.
> - **Codex weekly usage is exhausted; do not assign tasks, restart its session, or represent it as reviewing until the user re-enables it.** Its substantial **draft [#184 Jubilife→Route203→Oreburgh Gate and neutral interiors](https://github.com/kioconnor24-sketch/PokemonGame/pull/184)** is safely pushed at `4d37a2b147b4e4dac4e73574412a7dac91ec390b`, **92 staging/tooling/evidence files and no production engine modifications**. Current GitHub host checks pass, but actual corridor gameplay, final art/warps and complete ROM/mGBA are NOT accepted. This branch is **PAUSED, not abandoned or transferred**. Owner has approved sections 221/222/223, *not* protected-path handoffs or donor graphics rights.
>
> **Critical path:** (1) Claude applies the minimum #181 seam correction (if it still reproduces), rechecks targeted map/static/normal+release mGBA + Save→fresh Continue and pushes final evidence; (2) user-owner provides a real PR #181 exact-eight-path authorization via the trusted GitHub path (no forged manager approval), rerun `exclusive-files` normally; (3) review exact head/source compatibility and merge eligible #181; (4) rebase/reproduce Claude's held Verity production maps on current main, recheck integration, open one PR, secure a new exact-path 12-file handoff, normal review/checks/merge; (5) only then consider Codex's paused #184 as read-only prep for the next corridor batch. Manager ChatGPT owns administrative follow-up, source reviews, link/docs work and eligible merges, **not** invented native/mGBA proofs. Claude is not to repeat Codex's completed engineering or start a competing #184 implementation.
>
> **Next Claude work is compact, not 30 tasks:** fix/verify Route202 #181, push a concise exact-head test report, then stage Verity's existing branch after #181 merges. Use already completed #183 host preflight and do not rerun unrelated M1/native work.
>
---
**LIVE CHECKPOINT: October 19, 2026, after Claude finished Route 202 gameplay QA and ChatGPT opened PR #181.** This file is the **single current manager entrypoint**. Refresh GitHub before acting: statuses, source SHAs and CI below are an observed checkpoint, not unconditional merge permission. Older handoffs and the [low-usage packet](LOW_USAGE_EXECUTION_PACKET_20261019.md) are historical and must not restart completed tasks.

**Repository:** https://github.com/kioconnor24-sketch/PokemonGame  
**Main at audit:** `d5aa4471a554259bd61a48afc5e835b64256cb81` (PR #180 manager predecessor merged).  
**ONE open PR:** [#181 donor-derived Route 202](https://github.com/kioconnor24-sketch/PokemonGame/pull/181), **non-draft**, branch `claude/route202-donor`, exact head `962a472eb42f5c0d8c549bd67f3dab8fd7497430`; expected GitHub guard failure due to missing **new PR-scoped owner handoff**. All other prior PRs discussed here are either merged or explicitly closed.  
**Developer sessions:** user reports both paid developer usages constrained; **Codex was explicitly STOPPED by owner** after #178. Never launch, schedule, or assign Codex further work without subsequent authorization. Claude's current work was pushed and its final QA reported. GitHub issue comments **do not** start autonomous sessions.

## 1. Manager mission and operative governance

The owner wants a playable **Averon** adventure followed by complete **Sinnoh** (full geographical map and postgame) on Emerald decomp. Pre-Sinnoh Milestone 1 was owner-accepted; human audio listen and Delta iOS acceptance remain unverified. Keep traditional held-item EXP Share, following Pokémon, old-save continuity and gameplay mechanics already accepted. **No Sinnoh plot, NPC scripts/story progression, encounters, trainers, levels, legendary rewards or full interregional narrative yet.** Regular playful exploration should remain the normal tone. Red is the intended eventual final trainer after Sinnoh/postgame, not an immediate milestone.

The [active operating contract](CURRENT_PHASE_AND_HANDOFF.md) defines risk tiers, normal PR merging, and real protected-file handoffs. Developers Claude and Codex are autonomous peer co-leads when sessions are running; the **ChatGPT manager is not a mandatory approval gate**. The manager should spend its available GitHub access on source reviews, issue/PR administration, disjoint safe work, check inspection and normal eligible SHA-pinned integration **instead of using scarce developer tokens for paperwork**. Do not pretend to have run GBA compiler/mGBA from source-only GitHub actions.

Read at startup, **in this order only as needed**: (1) this file; (2) fresh main/open PRs; (3) latest Issue #15 decisions/claims; (4) [contract](CURRENT_PHASE_AND_HANDOFF.md) for a relevant gate; (5) exact target PR diff plus evidence. Do **not** scan hundreds of Issue #15 historical comments or re-read 22 work packages on each restart. Long-term references: [Sinnoh master roadmap](SINNOH_MASTER_PRODUCTION_ROADMAP.md), [developer work packages](SINNOH_DEVELOPER_WORK_PACKAGES.md), [87 named-area coverage](SINNOH_FULL_AREA_COVERAGE.md).

**Real owner decisions:** broad Sinnoh geography is developer-delegated; saved/met-origin section identifiers **216 Sandgem, 217 Route 201, 218 Twinleaf, 219 Route 202, 220 shared Verity Lakefront + Lake Verity** have their explicitly recorded approvals. Owner reports permission to reuse [LiderMorti00's Sinnoh-pokeemerald-expansion](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion), donor revision `38228bb574a3557345852b758d5f1a65eb01bb22`. Exact permission text, individual third-party art and public distribution terms are not equivalent to a blanket license; track credits/provenance and do not copy arbitrary donor NPC/story/ROM/assets. Large-scale saved-origin codebook or migration still needs a **new owner architectural decision**, not implicit allocation.

**Risk tiers:** R0 docs can normal self-merge with link/guard checks + exact-head evidence; R1 isolated tests/tooling may self-merge with meaningful executed tests; *bounded ordinary map changes* can use Fast Lane B only with genuinely authorized exact PR/path handoff, paired ROMs/native and authentic emulator/Save→fresh Continue where relevant. R3 CI/guard/save migration/release/security changes need an independent attributed actual-source review. Shared GitHub account name is not evidence of reviewer independence. No direct main pushes, security bypass, invented `HANDOFF_APPROVED`, or false acceptance claims.

## 2. Integrated source — do not waste usage on already completed work

| Scope | Actual main status and evidence distinction |
| --- | --- |
| M1 Averon backend | Accepted; baseline contains expected failing tests. It is **incorrect** to say all 6,107 results passed. |
| Sandgem Town + Center | Integrated section **216**, healer **44**, including genuine nurse/whiteout and saved Continue evidence. |
| Route 201 | [#150](https://github.com/kioconnor24-sketch/PokemonGame/pull/150) merged, section **217**, accepted connection to Sandgem. |
| Twinleaf | [#166](https://github.com/kioconnor24-sketch/PokemonGame/pull/166) **merged** at `9b821db36589593afaf9ac4166e0f785c12e0453`, section **218**, exterior and connection to Route 201. Claude reported native **311/311**, NORMAL+RELEASE, genuine mGBA **41/41** + Save→fresh Continue **3/3 per profile**, evidence [PR comment 6277638780](https://github.com/kioconnor24-sketch/PokemonGame/pull/166#issuecomment-6277638780). Houses remain **closed shells**, interiors unmerged/provisional. |
| Donor converter | [#176](https://github.com/kioconnor24-sketch/PokemonGame/pull/176) merged at `9bb1f1efdb3b6eb1e95d3dfa28d385a1b77a04fa`. Real donor Route202 30×34, 1,020 blocks, 25 primary metatiles; 15+ identity/static tests and Git-pinned real input passed. |
| Isolated donor graphics adapters | [#177](https://github.com/kioconnor24-sketch/PokemonGame/pull/177) merged at `bb52ffd9c99b34539e8908e57821b865383cd3cf` (19 new+15 previous host tests, read-only source-pixel stage); [#178](https://github.com/kioconnor24-sketch/PokemonGame/pull/178) merged at `6fac21eaa27e6c08f8367556e2fc167c603b5533` (paired banks/animation scratch support, 12 more tests). **These are useful optional tooling, not an automatically playable Sinnoh tileset**. |
| Low-usage plans | [#179](https://github.com/kioconnor24-sketch/PokemonGame/pull/179) packet and [#180](https://github.com/kioconnor24-sketch/PokemonGame/pull/180) previous manager handoff merged. Their old status/priority snapshots are already superseded by **this** file. |
| Cross-region transport / build tooling | Reviewed and merged #163, #169, #171 and other native/resource/map contracts. Two-region in-story transport **not** yet enabled; no future save encoding selected. |

**Separate historical quality improvement:** [#175 Route201/Sandgem tree repair](https://github.com/kioconnor24-sketch/PokemonGame/pull/175) was **CLOSED WITHOUT MERGE**, even though the exact two-map owner handoff [6274003354](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6274003354) and Claude's later [real QA evidence 6278051413](https://github.com/kioconnor24-sketch/PokemonGame/pull/175#issuecomment-6278051413) exist. Branch `claude/tree-repair-r201-sandgem` `82f8c10ea3a3f4df7abd7f98eddd4e063355f7f9` preserves ~93 Route201 +57 Sandgem visual-tile repairs, equal collision/elevation; reported NORMAL+RELEASE, native311/311, mGBA41/41 and fresh Continue3/3. **Do not reopen #175 or say it is merged/untested** merely because an older manager packet prioritized it. Revisit only after owner/visual-priority decision or reproduced defect. It must not block current Route202 gameplay integration.

## 3. Immediate live task: PR #181, donor-derived Route 202, section 219

**PR:** https://github.com/kioconnor24-sketch/PokemonGame/pull/181  
**Exact pushed head at audit:** `962a472eb42f5c0d8c549bd67f3dab8fd7497430`.  
**Main at audit:** `d5aa4471a554259bd61a48afc5e835b64256cb81`; its engine tree equals Twinleaf-integrated main `9b821db3` tree `aa78fa60d15b9a1a75b92cf6ea576ac079bc2375`. Intervening commits #176–#180 are tooling/docs only, so old valid gameplay evidence is **not automatically invalid**. Still recheck exact final diff and base.

**What Claude already implemented on the branch (23 changed files):** pinned donor Route202 30×34 physical geometry (Git source revision `38228bb5`, `map.bin` blob `25c72452a...`); own generator, provenance and mapping receipts; intentionally uses **Averon's current General+Dewford art** so existing Sandgem/Route201/Twinleaf seam stays coherent. Donor pine trees therefore display as round Averon trees; this is a provisional art deviation, **not** grounds to rewrite all maps. No imported donor NPCs/trainers/plot/encounters/items/music. Append-only approved `MAPSEC_ROUTE202 = 219`, stable old section pins, new native tests and map registration; south Route202 `down +4` ⇄ Sandgem `up -4`, north safely closed until Jubilife, three neutral signs. Source audit has not found preexisting ID renumbering.

**Claude's reported actual acceptance [Issue #15 comment 6278697117](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6278697117):**
- NORMAL ROM hash begins `b67690c3`, RELEASE begins `39c026af`, reported zero compiler warnings.
- Native **313/313**.
- Genuine mGBA **51/51** and fresh-process Continue **3/3 for each profile**, traversing Route202↔Sandgem↔Route201↔Twinleaf↔Center.
- Wrong-offset static + emulator negative failed **as intentionally expected**.
These are **Claude-supplied results**, not personally rerun by ChatGPT. Where policy requires durable screenshots/input traces/source+ROM SHA, check the actual evidence package rather than asserting uploaded proof that has not been inspected. Do not repeat expensive unchanged tests just for administration.

**Current blocker is specific and nonnegotiable:** GitHub `exclusive-files` for #181 FAILED solely because there is no PR-specific **owner-confirmed protected-path handoff**. Owner's approval of saved section219 does **NOT** waive this. The exact eight protected paths from the failing guard are:

```text
Pokemon Game/engine/data/event_scripts.s
Pokemon Game/engine/data/layouts/Route202/border.bin
Pokemon Game/engine/data/layouts/Route202/map.bin
Pokemon Game/engine/data/layouts/layouts.json
Pokemon Game/engine/data/maps/Route202/map.json
Pokemon Game/engine/data/maps/Route202/scripts.inc
Pokemon Game/engine/data/maps/SandgemTown/map.json
Pokemon Game/engine/data/maps/map_groups.json
```

**Manager actions, in strict order:**
1. Refresh PR #181 current head, main, exact changed filenames, owner approval and the **newest** individual CI jobs. At last audit, `route`, `file-guard`, `python-source-checks`, `production-config`, `source-contract` SUCCESS; `exclusive-files` FAIL (missing handoff), `native-build` still IN PROGRESS, weekly audit SKIPPED (not PASS). These must be refreshed, not assumed green later.
2. Ask the owner for **one explicit authorization** covering exactly these eight paths for PR #181, then ensure the required trusted GitHub account posts a genuine literal `HANDOFF_APPROVED PR=#181 PATHS=...` in Issue #15. **Do not forge or infer owner consent, claim the manager's analysis constitutes owner approval, or bypass the guard.** If the owner expressly delegates that exact approval decision, identify attribution honestly and confirm the checker accepts it.
3. Once actual approval appears, **rerun the failed exclusive-files check by the normal existing mechanism**, and inspect passing final native/GitHub CI. Never edit the guard or change code simply to silence it. Treat only latest applicable completed results as PASS.
4. Review the actual PR #181 source diff and source identity, donor provenance, section219 preservation, reciprocal seam and temporary art differences. Confirm that Claude's saved graphical evidence is applicable to the final production code and base. If a code rebase creates behavior changes, run only genuinely affected acceptance; never infer mGBA PASS from a GitHub green build check.
5. If all normal Fast Lane B requirements hold, **normal expected-head SHA-pinned squash merge**, then verify new main and clear #15 claims. Do not wait for a pointless ChatGPT manager signoff or reopen #175.
6. If permission cannot be granted, **leave #181 open and preserve work**; no more developer work is needed on PR admin while blocked. Manager may analyze next donor batch in disjoint paths.

**Do not accidentally put any `HANDOFF_APPROVED` statement in this handoff or an assistant-authored manager comment**; the only valid authorization is a genuine owner-approved trusted Issue #15 record linked to the exact PR.

## 4. Next product milestone after #181: connected Verity batch

After Route202 is actually integrated, build **Verity Lakefront and Lake Verity in ONE connected physical-geography batch**, sharing the already owner-approved saved section **220** (not two new IDs). Actual donor source shapes reported by current management: **VerityLakefront 20×20**, **LakeVerity 48×46**, source bank General+Petalburg; independently recheck donor revisions and geometry before claiming them. Connect Route201 west ⇄ Lakefront ⇄ Lake, preserve lake/edge travel and existing routes. Use a single map/registry PR and a single new literal protected-path handoff after exact paths are known. No NPC plot or encounters. Prefer reusable #176–#178 donor-first tools and existing art where seams remain coherent; do **not** globally replace Averon's shared General or force full Sinnoh graphic migration just to finish this batch.

**Focused QA:** static source and map pins first, then paired NORMAL/RELEASE, native/negative as applicable, genuine mGBA traverse/follower/menus/edges and Save→**fresh-process** Continue on actual combined source. Never claim copied donor graphics/ROM acceptance from an off-engine host preview. If the two-map batch has a real special water/secondary/animation gap, isolate the exact failing dependency and request only the necessary targeted Codex tooling when owner authorizes Codex to resume.

**Other future locations**: Jubilife and Route203 later, not a massive parallel rewrite now. The atlas inventories 87 named locations, plus internal submaps; low early integration count does NOT equal a reliable percent of game-development effort.

## 5. Low-usage workload and communication rules

**Claude when authorized/available:** work on **actual gameplay/graphics/map QA**, not further manuals, whole-repository rescans or CI paperwork. For #181, no further Claude task until owner handoff/current CI or a genuine code defect; its full reported test matrix exists. Next assigned coding work: two-area Verity connected batch with clear source and current section220. Ultracode only for genuinely disjoint major parallel tasks, not one PR closeout.

**Codex: STOPPED by owner's explicit instruction.** Do not message/schedule/restart. If owner later permits use, the best small independent future assignment is *read-only donor Verity tileset/border/water/animation dependency preflight* using already merged #176–#178, with no shared map edits or speculative broad infrastructure. The separate origin-precision/save-encoding owner decision is still unresolved.

**ChatGPT manager:** take owner-facing source/CI reviews, exact-file permissions coordination, PR creation, eligible normal merges and tight issue/docs updates. No repeated full-repo cleanups, duplicate long handoffs, speculative QA reports or CI additions without measured need. In GitHub record just **`DONE / PUSHED / EVIDENCE / BLOCKED / NEXT`** with exact SHAs and links; commentary is not an agent starter.

**Reserved design decisions:** plot/canon, Gym teams, encounters, levels, story transport, additional saved codes or 8-bit namespace resolution, inherited/third-party graphics licenses, release/ROM distribution, and final physical device/Delta acceptance.

## 6. Direct prompt for next ChatGPT manager session

> You manage Pokémon Averon, repository `kioconnor24-sketch/PokemonGame`. First read `Pokemon Game/Averon_Codex_Handoff/development/CHATGPT_MANAGER_NEXT_SESSION_HANDOFF_20261019.md` on the **live main**, then refresh all open PRs and newest Issue #15 owner decisions. At this checkpoint main was `d5aa4471`; PR #181 at `962a472e` is the only open non-draft PR, with genuine Route202 30×34 geometry and Claude-reported NORMAL/RELEASE, native313/313, mGBA51/51 and fresh Continue3/3 per profile. **The sole confirmed blocker is a missing new PR-specific owner-authenticated eight-path `HANDOFF_APPROVED`**, while CI native was running; do not forge approvals or call developer tests independently proven without reading evidence. Twinleaf #166 and donor tools #176–#178 are merged, #175 tree repair is **CLOSED/UNMERGED** despite QA, and **Codex is explicitly stopped**. Prioritize inspecting #181's final diff/current guards, helping obtain genuine owner authorization, re-running the normal guard, then a normal eligible SHA-pinned merge after all checks; if blocked, preserve branch and prepare disjoint Verity source preflight. Do not waste Claude/Codex usage, duplicate import infrastructure, or rewrite story/save policies. Tell the owner only concrete progress and decisions actually required.
