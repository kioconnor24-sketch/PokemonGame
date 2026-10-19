# Pokémon Averon — narrow execution packet for limited Claude/Codex usage

**Prepared 2026-10-19. Executable snapshot, not a new governance policy.** Source of truth remains the [operating contract](CURRENT_PHASE_AND_HANDOFF.md), [Sinnoh master roadmap](SINNOH_MASTER_PRODUCTION_ROADMAP.md), [original 22 work packages](SINNOH_DEVELOPER_WORK_PACKAGES.md), and [live Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). **Refresh live main/open PRs/claims** before acting; never treat the SHAs below as perpetual task locks. If one of these PRs is already merged, skip directly to its dependent task, not another progress report.

## Objective and operating constraints

**Single near-term product outcome:** get the first **donor-derived Route 202 playable in Averon**, with existing Sandgem–Route 201–Twinleaf intact, tested in normal/release builds and authentic graphical/save QA. Prefer donor-first geography for later Sinnoh waves; do not copy donor NPC scripts, trainer encounters, flags, events, music, shared `General` tileset or arbitrary saved IDs.

**Don't waste developer tokens on:** a full re-read of hundreds of Issue #15 comments; rerunning the #176/#177 donor studies or their 15+19 unchanged passing tests; repeating obsolete PR #150/#151/#163/#169/#171 decisions; bulk speculative maps before first successful import; unrelated branch/release/admin audits; broad parallel workers editing shared map files; writing another 20-page manager handoff.

**Minimum startup, each session:** (1) current main SHA + open PR status/heads + latest owner decision/claims in #15; (2) this execution packet + relevant PR diff/test evidence; (3) specific code/files of your one current assignment. Read the full contract only when a specific rule or risk tier is unclear. Preserve real guard behavior and exact protected handoffs. GitHub comments do **not** restart a paused or usage-limited agent.

### Live snapshot at packet creation

- `main`: `9b821db36589593afaf9ac4166e0f785c12e0453`.
- [#166 Twinleaf, section218](https://github.com/kioconnor24-sketch/PokemonGame/pull/166): **merged** at packet creation; never spend tokens doing it again.
- [#177 isolated Route202 donor static tileset stager](https://github.com/kioconnor24-sketch/PokemonGame/pull/177): **reviewed independently and merged** as `bb52ffd9c99b34539e8908e57821b865383cd3cf`. Codex's actual source-pinned staged map/border/static pixel tests and 19/19 new + 15/15 old unit tests have passed.
- [#176 donor map inspector/identity converter](https://github.com/kioconnor24-sketch/PokemonGame/pull/176): **independently reviewed and merged** as `9bb1f1efdb3b6eb1e95d3dfa28d385a1b77a04fa`.
- [#175 Route201/Sandgem visual bush repair](https://github.com/kioconnor24-sketch/PokemonGame/pull/175): **OPEN/DRAFT**, unchanged uploaded Claude head `2e8ce15a55ce66a69567084f1e61fc4a957680d0`; exact two-map protected-file approval [already recorded](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6274003354), relevant GitHub checks PASS; **genuine final graphical QA not uploaded/accepted**.
- Donor `LiderMorti00/Sinnoh-pokeemerald-expansion` pinned `38228bb574a3557345852b758d5f1a65eb01bb22`; owner reports use permission [here](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6274520543), but maintain asset-by-asset provenance/credit and do not claim broad Nintendo/third-party IP clearance.
- Route202 donor `30×34` layout; **25 primary-only General metatiles**, 36 referenced graphic tiles, palettes 0,1,2,3,5; isolated `SinnohGeneralStatic` family works in a scratch stage and test ARM object, **not yet linked to a full playable ROM**.
- Saved Sinnoh met-location section **219 approved for Route202**; section 220 shared for Verity Lakefront/Lake Verity, but permanent full-region origin encoding is not decided. Never allocate additional origin IDs without their own authority.

## CLAUDE — one gameplay lane (full remaining usage on a deliverable, no Ultracode for closeout)

### C-A: Finish visual PR #175 — no redesign

**Inputs:** [#175](https://github.com/kioconnor24-sketch/PokemonGame/pull/175), existing branch `claude/tree-repair-r201-sandgem`, merged Twinleaf #166, original images and `scripts/sinnoh-tree-repair.py`. The change is two existing `engine/data/layouts/{Route201,SandgemTown}/map.bin` files plus one unit-test pin and four before/after screenshots; Claude reported exactly 93+57 orphan quarters removed with existing bush22.

**Execute:** refresh current main and compare all changed map bytes for conflicts after #166; do not blindly overwrite Twinleaf connections. Validate original collision/elevation bits and visual before/after. Reuse passing dedicated unit/native and CI evidence where the source has not changed. Complete only **missing real** NORMAL/RELEASE mGBA traversals Route201↔Sandgem↔Center and Save→**fresh-process Continue**, with follower/collision/edge visibility, and record source/ROM hashes + honest PASS/FAIL/SKIP. The protected handoff exists and should not be requested again. Update just PR #175 evidence, transition draft→ready if eligible, and perform SHA-pinned guarded merge; if mGBA setup fails, upload the precise missing command/log and continue to the next independent action without reporting PASS.

**Stop:** #175 merged with source-pinned visual evidence, or a narrow reproduced blocker with precise next command. Do not spend an entire session regenerating duplicate screenshots.

### C-B: Build the first **playable** donor Route202, *after C-A or if C-A externally blocked*

**Inputs:** merged #176/#177; [#167 original source-grounded Route202/Verity candidate](https://github.com/kioconnor24-sketch/PokemonGame/pull/167); existing `scripts/sinnoh-donor-map-pilot.py`, `scripts/sinnoh-isolated-tileset.py`, `scripts/averon-mapsec-pins.json`, `scripts/audit-averon-map-readiness.py` and registered Sinnoh map layouts. Use #177's exact Git-pinned dependency, graphic/palette and generated isolated-family method; **do not research from scratch**. Its generated standalone `gTileset_SinnohGeneralStatic` must be correctly registered with normal engine source before the imported map uses it.

**Production change scope:** one genuinely new Route202 map/layout/border, isolated static Sinnoh family needed by that map, minimal append-only registration, preserved existing map slots/section meanings. Do not replace the original Averon primary General or overwrite any accepted map geometry. Do not import donor's trainers, items, quest scripts, events, flags, audio or unexplained warps. Route202's donor Sandgem down offset −2 and Jubilife up −38 are source **observations, not accepted Averon seam geometry**; derive the real Sandgem reciprocal connection and leave future Jubilife connection safely undeclared until its target exists. Keep source metadata/provenance and explicitly credit original map work.

**Prerequisites:** exact protected-path handoff for the NEW PR and correct owner-approved location section219; checked ROM-space/static asset/palette compatibility; no collision with Codex's claimed paths. Batch use only after first map works.

**Acceptance:** self-consistent registration/pins, native and negative geometry/ID checks, actual NORMAL + RELEASE builds, meaningful resource change comparison, genuine mGBA rendered Route202/Sandgem boundary and interior route walking/follower/edges, menu and Save→fresh-process Continue. Report whether ordinary legitimate gameplay can enter (or DEV-only if that is the only mechanism). Treat donor static pixel comparison as **host-only** source fidelity, not actual game proof.

**Stop:** focused Route202 production PR ready/merged under applicable R2 guards, or exact trace of the first blocking integration flaw with the tested SHA and smallest safe next action.

**Claude fallback (only if both blocked):** use verified donor source to prepare disjoint geography/layout candidates for Verity Lakefront/Verity or Jubilife **without** new saved IDs/plot and without editing shared production map registries.

## CODEX — one engineering lane (no more CI cleanups or repeated donor research)

### X-A: Safe accelerated-import coverage classification

**Problem:** isolated `SinnohGeneralStatic` solves the 25-primary-metatile static Route202 case, not all 87 Sinnoh areas. Build the **smallest useful, read-only, source-pinned compatibility census** across other donor layouts that tells Claude which map clusters can reuse it and which need secondary/animated tileset adapters. Do not allocate map IDs or import donor assets into public Averon.

**Inputs:** merged `scripts/sinnoh-isolated-tileset.py`, its 19 tests, `scripts/sinnoh-donor-bank-audit.py`, 87-area coverage, actual fixed donor revision. Read only donor header, layout, block, border, tile dependencies and verified source/engine behavior contracts. Preferred priority targets: **Route203, Route204, Verity Lakefront, Lake Verity, Jubilife exterior**, then connected clusters; inspect actual donor map names rather than inventing them.

**Deliverable:** a source-checked command/reproducible report identifying for each candidate map: real map name, dimensions and buffer limit; unique referenced primary vs secondary metatiles; whether the existing static family is sufficient; animation / palette / callback / layer blockers; external asset-family need; donor file SHA and geometrical connections; suitable next importer batch. Distinguish (a) current static family definitely supported by measured input dependencies from (b) needs dedicated adapter from (c) actual ROM/visual QA not yet proven. Output no copied ROM, private saves or donor graphics. Positive/negative host tests on representative simple/complex layouts. **Do not refactor production engine for unsupported future regions**; first report actionable coverage gaps.

**Acceptance:** a focused test/tooling PR with actual counts, source pin and no unreviewed CI changes; let author integrate if R1 truly applies. If modifying workflow or production source, obtain genuine independent R3/source review. This census should let future map building happen in connected batches without one-off manual route research.

**Codex fallback:** when Claude has a real Route202 integration/compiler incompatibility, inspect the exact production change and debug a **disjoint file** (e.g. tileset adapter/runtime contract) with failing-before/passing-after evidence. No speculative saves, release work, new origin schema, branch deletion, lengthy weekly reports.

## CHATGPT — coordination lane, no developer paid-model usage needed

1. Refresh exact PR heads, file collisions, check results and owner decisions only when an actual PR stage changes; don't duplicate every developer's global GitHub scan.
2. Independently review disjoint code/workflows where technically qualified and honestly record that **source/CI inspection is not mGBA gameplay or independent GitHub-account identity**. Never self-approve ChatGPT's own R3 work.
3. Handle status classification, approved protected handoffs when owner delegated the decision, normal eligible SHA-pinned merges and record actual main integration. Don't unilaterally delete PR branches, license assets or mark missing QA PASS.
4. Precompute source/asset inventory and acceptance matrices. Maintain this **single narrow packet** instead of creating another task registry/agent hierarchy.
5. If an agent reaches quota mid-run, use pushed commits/actual CI logs, not presumed local background-job success; preserve PR as ready/draft honestly.

## Shared low-usage operating rules (execution, not new policy)

- **One main goal and one fallback per agent**. For a closeout use normal Claude, **not Ultracode**; use parallel workers only if independently isolated major content maps genuinely benefit more than their orchestration costs. Never launch concurrent writers of `map_groups.json`, `layouts.json`, `region_map_sections.json`, or the same `map.bin`.
- **Targeted tests before broad:** changed Python converter→focused Python tests + existing source-pinned GitHub job; map geometry changes→static source preflight/native then paired builds and *real* targeted mGBA/Save→fresh Continue; save/runtime changes→relevant native matrices plus actual old-save tests. Never treat skipped or missing required checks as PASS. A full historical 6107-result M1 rerun is unnecessary for docs/source-only changes.
- **Reuse result identities, not optimistic summaries.** If tested source unchanged, record actual source/tree/ROM hashes and which evidence applies; if integrated source differs, rerun the *narrow affected behavior* rather than casually asserting inheritance. Exact branch/commit and ROM profile matter.
- **Single compact handoff at stopping time (copy format):**

```text
DONE: <PRs genuinely merged and current main SHA>
PUSHED: <branch, full head SHA, exact changed production paths>
EVIDENCE: <command/test profile, exact PASS/FAIL/SKIP, source and ROM hashes, genuine mGBA? yes/no>
BLOCKED: <one reproducible issue and error or "none">
NEXT: <one specific source file/action/command; owner decision only if truly required>
```

- **End on a pushed checkpoint, not a report-only task.** GitHub comments don't restart other agents. If code is ready but CI is pending, keep it in the honest draft/ready state, move to one disjoint task or close session.
- **Do not weaken approvals, save protection, intellectual-property safeguards, genuine emulator gates or branch rules** in the name of minimizing usage.
