# ChatGPT manager handoff — October 24, 2026

**Repository:** https://github.com/kioconnor24-sketch/PokemonGame  
**Purpose:** exact current project-management and Codex recovery handoff, replacing the *task priorities/status snapshot* in the October 23 late document, not replacing game design or governance.  
**Live-main snapshot:** \`871c46b6fc8b4fdaae9e2bef04543c649987542a\` (merged documentation PR #244, October 24 00:59 UTC).  
**Latest substantive Codex checkpoint:** [Issue #15 comment 6379919709](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6379919709) (the exact source for verified new work and workspace inode fault).  
**Earlier handoff (historical, still useful for context):** [October 23 late](CHATGPT_MANAGER_NEXT_SESSION_HANDOFF_20261023_LATE.md).

> **Source-of-truth warning:** This is a dated snapshot. Refresh main, open PR heads, their *base branches*, CI, changed paths, and Issue #15 claims before changes or merges. A source-stage, neutral-art candidate, disposable emulator scene, and permanently reachable production map are four different acceptance states.

## 1. Fast startup: stop reading historical noise

1. Read root [README](../README.md), root [AGENTS.md](../AGENTS.md) (Claude additionally [CLAUDE.md](../CLAUDE.md)) and the [operating contract](../Pokemon%20Game/Averon_Codex_Handoff/development/CURRENT_PHASE_AND_HANDOFF.md). The contract and live owner decisions control permissions/merge authority; this handoff does not alter them.
2. Read [Issue #15 live router](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), [open PRs](https://github.com/kioconnor24-sketch/PokemonGame/pulls?q=is%3Apr+is%3Aopen), latest *owning* PR checkpoint and any literal-file claims. Do not reread hundreds of old comments, aged October 15–23 task lists, or 252 branches to reconstruct one task.
3. Existing [Sinnoh master roadmap](../Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_MASTER_PRODUCTION_ROADMAP.md), [87-site coverage](../Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_FULL_AREA_COVERAGE.md) and **single** 159-map donor ledger in PR #237 are scope/reuse references. Do not start a second inventory or converter.
4. **Claude remains paused.** Codex acts only in an active Codex session. Posting here/on GitHub does **not** launch autonomous development.

## 2. Actual Codex progress since the October 23 late handoff

Codex responded substantially to the manager's previous instructions, but these changes are **on PR branches, not merged into production main**:

| PR / exact head | Actually delivered and evidenced | Status / boundary |
| --- | --- | --- |
| [#241 Sunyshore coast](https://github.com/kioconnor24-sketch/PokemonGame/pull/241), \`3e00eab223722dda747f2ac3f748682a33c47026\` | Five maps/neutral permitted art, paired **142/142 positive GUI**, native29/29, strict old-save goldens4/4. | **Draft.** Original two Route222 ledges physically land in solid boulders. Explicit source negative 6/7; original failures retained. Route223 water-only; no natural Surf/Waterfall acceptance. |
| [#245 targeted Route222 repair](https://github.com/kioconnor24-sketch/PokemonGame/pull/245), \`0fa671e3717b57b6f1409a3cee866950eca6a5d9\` | Corrects exactly Route222 (36,16) and (37,16), metatile 0x487→0x491 (cliff, not jumping into boulders). Preserves collision/elevation, the actual boulder targets and legal neighboring jumps. Paired **142/142 real GUI** including formerly failing probes, native30/30, original strict save goldens4/4, host9/9, static0. **No incremental linked ROM/RAM growth** from the two-cell repair. | **Draft**, based on #241; visually review deviation and normally reconcile/integrate proper corrected source through stack. New tests do not retroactively change #241's original failed receipt. |
| [#242 connected Victory Road](https://github.com/kioconnor24-sketch/PokemonGame/pull/242), \`3624fddbf0fdf944f821d89c1aef006fb62a8fb5\` | New original Victory Road 1F/2F/B1F and both real League cave doors; actual eight-map disposable scene, paired **224/224 GUI**, native31/31, old-save goldens4/4, focused27/27, static0. Both Normal and Release genuinely compiled. | **Draft** stacked on #241. Not production; Route223 remains a water transit issue, no story/final art. |
| [#243 Mt. Coronet upper 2F/3F](https://github.com/kioconnor24-sketch/PokemonGame/pull/243), \`bbe29978d262e2b69054489d0833882286965a13\` | 3,128 original source cells, real same-floor and 2F↔3F reciprocal stairs. Actual **100/100 paired GUI**, native30/30, strict save goldens4/4, focused host12/12, static0. Both Normal and Release compiled with +6,504 linked bytes over comparable base, no RAM change. | **Draft** stacked on #242. Verified **two-floor** scene ONLY; outside/4F not tested by this receipt. |
| [#246 Coronet ascent source/art](https://github.com/kioconnor24-sketch/PokemonGame/pull/246), \`e034551df6c2cde9d2db7170824bd9d229b7cfe4\` | Four new original physical shells: Outside South (46×40), Outside North (50×46), 4F Rooms 1+2 (64×30), 4F Room 3 (24×14): **6,396 NEW cells**. With reused 2F/3F, connected six-map candidate has 9,524 total cells, **18 reciprocal events**. Actual source/host6/6 and **31/31 generated files byte-identically reproduced**. Existing 2F byte-identical; precisely one 3F source cell/warp opened. | **Draft** stacked on #243; **SOURCE/ART ONLY**. No six-map Normal/Release build, native, mGBA or Save/Continue proof. Rocky exterior shells are provisional, not faithful mountain/snow/Rock Climb implementation. |
| [#238 42 interior candidates](https://github.com/kioconnor24-sketch/PokemonGame/pull/238), \`9d21973f94a5ffe6e4d77fad4a4ba69d682f76f4\` | Neutral permitted-art interiors; four Twinleaf floors had paired 74/74 GUI, native29/29, goldens4/4. | Non-draft child of #237, cannot merge before protected parent resolution. **Most of 42 are not runtime accepted**. |
| [#237 entire donor source reuse](https://github.com/kioconnor24-sketch/PokemonGame/pull/237), \`e3663c8b86999f23442d366eb2379e22291d7332\` | 91 additional maps/67,285 cells; all **159 pinned donor definitions accounted for** as existing production19 + source-staged140, with **47 additional missing-physical-site/child targets**. Source generation and tests passed. | Non-draft; **exclusive-files FAIL** on precisely three owner-reserved development documents; cannot merge on current guard without genuine owner authorization. |
| [#235 northern snow](https://github.com/kioconnor24-sketch/PokemonGame/pull/235), \`63c3a8887cb37e32b69f796a58f7dde606f64557\` | Paired movement/weather/save evidence for DEV corridor. | **Draft**: visible upper-bridge white gap not resolved by two-plane art experiment. Cannot call visually accepted. |

**Stack dependency graph:** #237→#238; #237→#241→#242→#243→#246; #241→#245. #235 stands apart. A child CI PASS does not make a parent/owner gate pass. Do not merge the stack out of order or ignore #241's original failure; target #245's correction for coherent reconciliation. Review the actual combined final diff, not only PR titles.

**CI as checked:** Latest #243, #245 and #246 applicable GitHub checks show PASS, with optional weekly audit SKIPPED. #237's **exclusive-files** fails by design; source/inspect/file checks pass. Never label a failure as fixed by a manager marker or claim new approval. All PRs other than #237/#238 are drafts at this snapshot.

### Authentic ROM evidence, scoped only to tested disposable scenes

- **Victory Road eight-map #242:** Normal linked **17,445,624 B**, SHA-256 \`d1ff5018460b730f9c6a65801f4f822b2827702a231d9fc519cad4e90167ab0a\`; Release **17,564,744 B**, SHA-256 \`8f95a6ca81297cd2c204da7b504128fb6cad1c0600e0f697c4b57e625737a06d\`. Matched +52,280 B, RAM unchanged; Release headroom 15,989,688 B. This scene tests League/cave navigation, **not** Route223 ocean naturally.
- **Coronet 2F/3F #243:** Normal **17,399,848 B**, Release **17,518,968 B**; matched +6,504 B, RAM unchanged. Exact ROM/checkpoint hashes on owning PR.
- **Route222 corrected coast #245:** Normal **17,430,244 B**, Release **17,549,364 B**, no incremental bytes from the two-cell repair; native/save/GUI passed as specified above.
- These are Normal/Release builds in **guarded disposable DEV trees** using temporary append slots and a disclosed existing section217 popup surrogate. None is evidence that 140 source maps are installed in the real game. The production engine still has **19 registered Sinnoh map slots** at the latest inspected source; verify again when integrating.
- M1 and old-save compatibility evidence is preserved; user-facing Delta iOS, faithful graphics/music, natural post-Averon transfer, story, encounters and level progression remain unverified/deferred.

## 3. Urgent newly discovered blocker — filesystem **inode exhaustion**, not ROM size

[Codex's exact incident and recovery](CODEX_WORKSPACE_FILE_LIMIT_20261023.md) was committed on #246. Its execution overlay had **2,097,152 / 2,097,152 filesystem inodes consumed** despite approximately **410 MiB byte headroom**. A Git checkout failed with ENOSPC; this is a filesystem **file-count** problem, not ROM/RAM exhaustion, lost saves or a source bug.

Codex safely restored the interrupted checkout using existing committed hashes, removed only regenerable untracked Python bytecode and hash-identical completed-job caches/duplicate archived ROM copies after canonical verification; preserved all unique work, private saves, source/evidence, branch history and already pushed #243/#245. The reported remaining inode headroom was only **a few hundred** (about 178 at the latest issue comment), far too little for another full paired game build.

**Next session Priority 0:** inspect \`df -i\`, \`df -h\`, source/scratch/worktree status and active processes **in the actual Codex environment**; procure a clean workspace with adequate inode count (fresh cloud/dev container or appropriately sized volume), or perform **targeted, logged, checksum-safe cleanup of clearly regenerable completed build caches only**. Preserve/verify unique ROM+ELF evidence, original saves, stashes, committed artifacts and per-scene hashes before cleanup. Do not delete or mass-prune entire repositories, force-reset, manually alter guards, or claim that free disk bytes alone solve inode exhaustion. If the environment cannot be fixed, continue source-only review/work without another failing build, document exact blocker and next step.

## 4. One realistic high-value Codex next run (once workspace healthy)

1. **Resume PR #246** from actual source head: replay its six source tests and 31 regenerated artifacts; check its latest CI and exact parent #243 source hashes. Keep original 2F and accepted donor Coronet maps unchanged.
2. Create the **existing-pattern guarded six-map Coronet ascent DEV scene** on a clean current-main baseline with strictly temporary appended slots; use same reusable packers/native/mGBA harness; *no competing converter*. Include 2F, 3F, both exteriors, both 4F maps. Verify 18 reciprocal events, both same-floor stair pairs, every actual cross-floor arrival+return, ordinary-player movement, followers, menus, Save→fresh-process Continue and unchanged actual legacy flash. Capture real Normal/Release ROM/source SHA, linked ROM/RAM deltas, native/save-golden/negative/visual evidence; inspect outside screenshots rather than accepting rock placeholders as finished visuals.
3. Keep **1F-South / Route207 / 1F-Tunnel / 5F** unfinished portals honestly closed until adjacent source-grounded content exists. No invented connection, Rock Climb implementation, permanent saved IDs, scripted story, trainer teams, encounters or copyright-uncleared DS tiles/music.
4. **Merge-stack hygiene:** independently review parent #237 owner-only gate and #241 source negatives; prepare precise legal merge/rebase order for #245 Route222 correction, then #242 Victory, #243 upper, #246 ascent and separate #238 interiors. Do not merge still-draft/blocked work without its current review/approval requirements and exact-head green checks. Since parent #237 needs genuine owner action, continue physical geography and art disjointly.
5. After six-map proof (or a genuine blocker), construct an additional **source-grounded major missing connected physical package** from the 47 targets (e.g. missing Coronet 5F/1F seams, Iron Island or Snowpoint Temple), using permitted GBA compatible art. Prioritize actually playable map/nav work over another planning spreadsheet.

**For the manager, do immediately when able:** keep Issue #15 router linked to this handoff; review ready independent R0/R1 PRs; get owner direction on the **three protected #237 inventory files** if the owner wants that branch merged, plus future **named saved-location code 227+** policy. The manager's routine handoff marker is NOT an actual owner signature for these reserved paths. Do not request per-map ordinary geography approvals or invent saved encoding changes.

## 5. Concrete protection/approval boundary

#237's three blocked files are exactly:
- \`Pokemon Game/Averon_Codex_Handoff/development/SINNOH_DONOR_REUSE_CHECKPOINT.md\`
- \`Pokemon Game/Averon_Codex_Handoff/development/SINNOH_DONOR_REUSE_INPUTS.json\`
- \`Pokemon Game/Averon_Codex_Handoff/development/SINNOH_DONOR_REUSE_LEDGER.csv\`

A *genuine owner-authorized* explicit path/PR handoff is required by the active guard. Do not move paths merely to evade it, weaken \`check_protected_files.py\`, fabricate the owner's GitHub authorship, or interpret author-collaboration status as independent identity. Even after a correct owner signature, perform required substantial diff review and exact-head CI before an ordinary pinned merge. **Values 227+ remain reserved.** Existing old save layout and all current section IDs/semantics (including owner-approved 221–226 and sentinel) remain stable.

## 6. Recovery references and housekeeping

- [Latest Codex exact checkpoint](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6379919709), with pushed PR heads, all actual test counts and private archive/stash addresses.
- [#246 Coronet ascent checkpoint](https://github.com/kioconnor24-sketch/PokemonGame/blob/e034551df6c2cde9d2db7170824bd9d229b7cfe4/Pokemon%20Game/Averon_Codex_Handoff/design/sinnoh/coronet-ascent/CHECKPOINT.md) and [inode report](CODEX_WORKSPACE_FILE_LIMIT_20261023.md) (note: inode report exists on #246 branch; on main it may still be absent until merging).
- [#245 corrected Route222 checks](https://github.com/kioconnor24-sketch/PokemonGame/blob/0fa671e3717b57b6f1409a3cee866950eca6a5d9/Pokemon%20Game/Averon_Codex_Handoff/design/sinnoh/route222-safety/CHECKPOINT.md).
- [#243 two-floor genuine runtime checkpoint](https://github.com/kioconnor24-sketch/PokemonGame/blob/bbe29978d262e2b69054489d0833882286965a13/Pokemon%20Game/Averon_Codex_Handoff/design/sinnoh/coronet-upper/CHECKPOINT.md).
- [#242 League/Victory runtime checkpoint](https://github.com/kioconnor24-sketch/PokemonGame/blob/3624fddbf0fdf944f821d89c1aef006fb62a8fb5/Pokemon%20Game/Averon_Codex_Handoff/design/sinnoh/victory-road-shell/RUNTIME_CHECKPOINT.md).
- [Existing source ledger/complete missing-site index #237](https://github.com/kioconnor24-sketch/PokemonGame/pull/237).

Branch audit from previous manager run classified **252** remote branches (205 tied to merged PR heads, 12 tied to closed-unmerged PRs, 35 without a matched closed PR); these were **not deleted**, because historical build receipts/private recovery may depend on them. New PR branches after that audit will make those totals stale. Continue live-first navigation and avoid destructive cleanup. GitHub repo is set **not** to auto-delete merged head branches; changing Settings is an owner/admin choice. Root README and Issue #15 entrypoint were improved/merged in #240, previous manager handoff #244 merged to main.

### Next manager-session completion criteria

A subsequent manager should be able to answer: **(a)** what exact Codex PR/head is active, **(b)** whether inode count is sufficient for builds, **(c)** whether the tested six-map ascent is real or still source-only, **(d)** whether #237 has a genuine owner handoff, and **(e)** what may actually enter *production* vs remain DEV. Do not claim progress via plan/PR creation alone; demand actual source commits, tests, screenshots and checked merge status.
