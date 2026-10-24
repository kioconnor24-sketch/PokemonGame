> **HISTORICAL HANDOFF (superseded 2026-10-21):** The current manager entrypoint is [October 21 — Codex-only handoff](CHATGPT_MANAGER_NEXT_SESSION_HANDOFF_20261021.md). The dated Route202 correction and Codex-paused assumptions below are no longer current. Preserve this earlier document as historical engineering evidence; refresh live GitHub and follow the current operating contract.

# Pokémon Averon — Next ChatGPT manager session handoff (2026-10-20)

**READ THIS DOCUMENT IN FULL BEFORE WORKING.** This is the **current concise manager entrypoint**, replacing the long [2026-10-19 handoff](CHATGPT_MANAGER_NEXT_SESSION_HANDOFF_20261019.md) as the default startup document. The older handoff retains historical engineering context, not the live work queue. **The operating contract remains authoritative** for policy: [CURRENT_PHASE_AND_HANDOFF.md](CURRENT_PHASE_AND_HANDOFF.md). GitHub observations below were refreshed approximately **2026-10-20 01:32 America/New_York**. Always refresh main, open PR heads, actual checks and Issue #15 claims before acting. No GitHub comment can run or resume a paid agent.

Repository: https://github.com/kioconnor24-sketch/PokemonGame  
Coordination: https://github.com/kioconnor24-sketch/PokemonGame/issues/15  
Current main at this checkpoint: `7e107d51f33bcfc1ede7c9ed0488574e75daf66f` — [merged #185 manager navigation update](https://github.com/kioconnor24-sketch/PokemonGame/pull/185).

## 1. Mission and boundaries

The owner wants a traditional, enjoyable **Averon** Pokémon adventure plus the **full second region Sinnoh** in an Emerald-decomp GBA game, with authentic geography, neutral physical locations, normal exploration, and later-owner story/content design. Sinnoh physical geography is broadly delegated to developers. **Sinnoh plot, trainers, encounters, item rewards, level curve, legendary events, transport storyline, saved-location encoding/migration and final release decisions are NOT delegated.** Preserve old saves, party, moves, levels, held items, Bag, PC, following Pokémon and traditional held-item EXP Share. The eventual full Sinnoh/postgame, optional Battle Zone/Underground, Red final battle and Delta iOS objective are future goals, NOT currently complete. Human audio-listen and Delta acceptance are unverified.

**Primary production strategy:** owner reports permission to reuse the geography from [LiderMorti00/Sinnoh-pokeemerald-expansion](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion), pinned donor revision `38228bb574a3557345852b758d5f1a65eb01bb22`. Reuse a **verified, isolated conversion approach** with Averon's existing art or separately cleared graphical dependencies. Permission for *specific third-party Jubilife/Rustboro graphics* is **not documented**; do not import those graphics/music or donor NPC/story assets into public Git on the assumption that map layout permission covers them. Keep accurate author and source credits. The owner wants **connected batches**, not rebuilding every route manually from screenshots.

## 2. Verified integrated work — never repeat

- **Accepted pre-Sinnoh M1**, Sandgem + Center saved section216/healer44, Route201 section217, and **Twinleaf exterior section218** [#166 merged](https://github.com/kioconnor24-sketch/PokemonGame/pull/166). Twinleaf houses remain **closed**; separate interior proposal is not implemented. Original Averon gameplay and established saved values remain protected.
- **Donor tooling merged:** [#176](https://github.com/kioconnor24-sketch/PokemonGame/pull/176) route inspection/real 1,020-cell roundtrip, [#177](https://github.com/kioconnor24-sketch/PokemonGame/pull/177) separate static family and tests, [#178](https://github.com/kioconnor24-sketch/PokemonGame/pull/178) paired-bank/animation scratch support; these are **not automatically playable maps**.
- **Latest merged preflight [#183](https://github.com/kioconnor24-sketch/PokemonGame/pull/183)** at `21086c44e56fa9262440859a1e49b960cfc37125`: real donor Verity inspection and host tests; no playable Verity maps on main. **[#185](https://github.com/kioconnor24-sketch/PokemonGame/pull/185)** updates historical manager/index navigation only.
- **[#175](https://github.com/kioconnor24-sketch/PokemonGame/pull/175)** Route201/Sandgem tree polish was **closed without merge**; preserve its branch and supporting accepted reported graphical QA, but do not pretend it is on main or resurrect it ahead of active Sinnoh geography.
- Codex's transport safety, native resource/registry checks, CI improvements, branch preservation audit and old-save regression tooling are already merged; do not commission redundant audits.

## 3. Critical path #1 — Route 202 production PR #181 (OPEN, NOT ACCEPTED)

[PR #181](https://github.com/kioconnor24-sketch/PokemonGame/pull/181) branch `claude/route202-donor`, last checked head `962a472eb42f5c0d8c549bd67f3dab8fd7497430`, **23 changed files**, NON-DRAFT. Approved `MAPSEC_ROUTE202 = 219`; donor-based **30×34** physical route built with Averon General+Dewford art, neutral signage, Sandgem connection and closed north exit awaiting Jubilife. No donor story/encounters copied.

**TWO independently real blockers, not just GitHub administration:**

**A. Static seam defect discovered after previously reported passing gameplay scenarios.** Claude acknowledged **two positive static `seam-mismatch` findings** despite separately reporting NORMAL/RELEASE, native313/313, real mGBA51/51 and fresh Continue3/3 per profile. Its [narrow documented fix](https://github.com/kioconnor24-sketch/PokemonGame/pull/181#issuecomment-6282414958) is Route202 **down +4→+3** and Sandgem **up −4→−3**, in the two header `map.json` files. **The correction is proposed only; it has not been pushed or accepted at this checkpoint.** Someone with actual build/emulator capability must apply/validate the smallest fix, prove reciprocal static seam and true walking/Save→fresh-process Continue on the *changed* source with both NORMAL and RELEASE, then push an exact source/ROM/evidence handoff. Do not repeat the complete earlier 51-case package when unaffected.

**B. Missing genuine owner-confirmed PR-specific protected-file authorization.** At verified head GitHub `exclusive-files` is **FAILURE**; `native-build`, `python-source-checks`, `source-contract`, `production-config`, `file-guard`, `route` are **SUCCESS**; weekly audit SKIPPED. The existing owner section219 choice is NOT a protected-source authorization. **Do not create or impersonate a trusted owner approval from ChatGPT, infer a handoff from an issue or mutate/check-bypass the guard.** The owner, via trusted GitHub procedure, must approve the eight literal protected paths in a genuine PR #181 authorization record:

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

When both requirements are truly satisfied, rerun `exclusive-files` by normal permitted means, confirm **newest applicable exact-head** GitHub checks, review actual diff and donor/save provenance, apply Fast Lane B only if full requirements hold, perform normal SHA-pinned merge and verify main. Do **not** label the earlier reported mGBA51/51 a clean current-source acceptance after the disclosed static failure. If owner approval or actual gameplay tests remain unavailable, **leave #181 open safely**; manager can work on disjoint docs/source review but not invent gameplay acceptance.

## 4. Critical path #2 — Verity already built, waiting to integrate

Claude's [actual Verity handoff](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6283760927) records two pushed branches:

- `claude/verity-donor` at `e682894b`: off-engine source-grounded geometry, generator, preview/QA and negative cases.
- `claude/verity-integration-hold` at `d7f80ca6`: **production integration already implemented on held branch**, NOT yet a PR by deliberate choice because `event_scripts.s` overlaps open #181.

The two physical areas are Verity Lakefront and Lake Verity, **shared saved section220** explicitly owner-approved. Claude's branch reports NORMAL+RELEASE, native **316/316**, real mGBA **40/40**, fresh Continue **3/3 per build**, zero static findings and specific negative cases on engine tree `d62eba53`. These are *Claude's supplied test results*, not independently rerun by ChatGPT; inspect exact remote evidence when claiming final acceptance.

**ONLY AFTER #181 merges:** rebase the held branch or regenerate via existing `build_verity.py` on freshly integrated main, resolve changed global-map registries and event-script collisions, run **targeted newly affected** native/static and emulator/save tests, open one normal non-draft Verity geography PR, obtain its **own distinct exact-literal protected-file authorization** (Claude reported ~12 protected paths; compute them from the final actual PR instead of guessing), verify checks and merge if eligible. Do not rebuild the already completed Verity design or ask Codex to redo #183 source preflight. Lake cave mouth/story reserved; no new lore/legendary quest.

## 5. Codex #184 — valuable work safely parked, NOT completed gameplay

[Draft PR #184](https://github.com/kioconnor24-sketch/PokemonGame/pull/184), `codex/jubilife-oreburgh-corridor-20261020`, head `4d37a2b147b4e4dac4e73574412a7dac91ec390b`. **92 changed files**, all off-engine `design/sinnoh/jubilife-corridor/` staging/art-adaptation/scripts and tests; **zero production engine paths**. Claimed: Jubilife City, Route203, Oreburgh Gate1F, neutral Center1F/Mart/School; 7,529 staged cells, 11 warps and two candidate connections, plus existing-Averon art replacements and bank candidates. Real host/tool tests and GitHub checks have passed; actual ROM link, field travel, graphical QA, save/Continue, final production banks and path handoffs **have not**. Owner approved append-only saved sections **221 Jubilife + interiors, 222 Route203, 223 Gate** in [#15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6282653675), **not** actual production protected-file handoff or unverified donor art redistribution.

**Codex is out of weekly usage and paused.** Do not launch, schedule, demand review from Codex or silently reassign its claimed branch. Work remains pushed and recoverable. When the owner explicitly resumes or reallocates it, use the saved [#184 PR checkpoint](https://github.com/kioconnor24-sketch/PokemonGame/pull/184) and `design/sinnoh/jubilife-corridor/CHECKPOINT.md`/FILE_INVENTORY; do not recreate staging. Ordinarily integrate #181 then Verity first to reduce shared file conflicts.

## 6. Efficiency and manager operating instructions

**Manager actions you can perform without developer usage:** refresh public GitHub refs/checks, review actual diffs and evidence honestly, prepare concise one-time owner technical decision packets, handle legitimate nontechnical status/PR problems, post accurate Issue #15 coordination updates when a real state change occurs, self-merge eligible documentation/host tooling after their gates, and **perform normal SHA-pinned integration of genuinely eligible work**. Do not waste Claude/Codex on PR prose, historic branch/audit rework, old CI reports or already-merged code.

**Real emulator/ROM QA:** genuine in-game map seams/followers/doors, negative behavior, old-save regression and Save→fresh-process Continue must be tested by a capable existing environment or verified executable workflow. Do not pretend GitHub source-only inspection, image previews or old smoke videos prove them. Avoid repeating full native/ROM suites for unchanged engine source; run targeted tests on the exact changed integration tree, then full gates only at genuine boundaries.

**Minimal restart reading:** (1) **this file**, (2) current main + open PRs + latest relevant #15 claims, (3) the actual current target PR files/checks, (4) the [operating contract](CURRENT_PHASE_AND_HANDOFF.md) only for applicable risk/owner gates. Don't reread hundreds of comments or the entire 87-area plan just for an administrative merge. [Long-term roadmap](SINNOH_MASTER_PRODUCTION_ROADMAP.md) and [22 developer packages](SINNOH_DEVELOPER_WORK_PACKAGES.md) are for selecting the NEXT actual batch after the current critical path.

**Source of truth order:** actual main/PR/checks + newest owner decisions > this dated handoff > old 2026-10-19 manager notes and historical issue comments. Preserve historical documents and source/evidence branches; no repository reset, cleanup deletion or new governance framework needed.

## 7. Next manager session's executable order

1. Confirm live state of main and PRs #181/#184, newest checks, changed files, Claude's Verity branches and most recent #15 comments. **Do not assume this checkpoint is still current.**
2. Determine if Claude pushed the Route202 ±3 correction or owner posted the real eight-path #181 handoff. If not, state precisely which requirement remains. Do not solve by waiving exclusive-file guard.
3. Independently review bounded actual PR/branch diffs or focused status/documentation, not recreate completed donor work. If new genuine evidence and trusted handoff permit #181 to merge, perform and verify normal expected-head merge.
4. Once #181 is integrated, coordinate held Verity production branch into one tested, separately authorized PR and integrate when eligible. Keep #184 safe, paused.
5. Report **what reached main versus what is only tested on a developer branch**, with exact open blockers; give the owner one concise decision/action if required. Use no speculative time estimates and do not promise unattended background progress.

**Short success metric:** increase **playable, connected, verified** Sinnoh maps on main while preserving accepted Averon saves and genuine guard/QA evidence; stop turning already finished infrastructure into more developer assignments.
