# Pokémon Averon — ChatGPT manager next-session handoff (2026-10-21)

> **HISTORICAL SNAPSHOT — superseded as the default manager start document on October 22, 2026.** Read the [current October 22 manager handoff](CHATGPT_MANAGER_NEXT_SESSION_HANDOFF_20261022.md) first. The old statements below that #202/#194 remain open, #184 remains an active draft, and northern saved origins224–226 lack an owner choice are outdated. Preserve this document as historical evidence; refresh live main, PR checks and Issue #15 before acting.



**CURRENT DEFAULT MANAGER START DOCUMENT. READ IN FULL.** The previous [October 20 handoff](CHATGPT_MANAGER_NEXT_SESSION_HANDOFF_20261020.md) and older dated manager documents are historical checkpoints, not live task assignments. The [operating contract](CURRENT_PHASE_AND_HANDOFF.md) remains the source of authority for permission, review, owner approvals, and preservation; this file gives **dated, evidence-scoped state and execution order**, not a policy override. Always refresh GitHub first. Do **not** infer that an issue comment, scheduled task, or this handoff starts a Codex session.

**Repository:** https://github.com/kioconnor24-sketch/PokemonGame  
**Live coordination:** https://github.com/kioconnor24-sketch/PokemonGame/issues/15  
**Current integration queue:** [INTEGRATION_QUEUE.md](INTEGRATION_QUEUE.md)  
**Snapshot of main:** `350f20dcd7b4535926bc4fcd7c5e40d5a7143daa` (manager [#189](https://github.com/kioconnor24-sketch/PokemonGame/pull/189) documentation queue merged after #187/#188 test routing).  
**Only active developer by owner direction:** **Codex**. **Claude paused**. See [owner-staffing execution checkpoint](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6308769794). This may change; confirm newest owner instructions at every restart.

## 1. Product goal and hard bounds

Build a substantial enjoyable traditional Pokémon adventure in **Averon**, followed by a full second **Sinnoh** region inside an Emerald-decomp GBA ROM, preserving existing saves, Pokémon, Bag, PC, mechanics and player progress across the region transition. The existing first-region opening, M1 core backend, following Pokémon, and traditional held-item EXP Share matter. The eventual late-game Sinnoh exploration, postgame and Red final battle are goals, **not already shipped content**.

Developers are broadly delegated ordinary Sinnoh **physical geography**, but not final plot, villain/Threshold/rival storyline, dialogue arcs, encounters, Gym content, level curves, permanent saved-location policy, asset redistribution or final release. The Sinnoh donor revision is pinned to `38228bb574a3557345852b758d5f1a65eb01bb22`; use original/Averon graphics unless distinct rights are demonstrated for donor and third-party art. Do not import donor NPCs/story/audio under geometry permission. No rewriting existing main branch history, old save fields or old identity codes.

## 2. Verified production versus branch-only work

| Target | Exact GitHub ref at snapshot | Evidence level / remaining action |
| --- | --- | --- |
| `main` | `350f20dcd7b4535926bc4fcd7c5e40d5a7143daa` | Pre-Sinnoh M1 accepted. Registered Sinnoh: Sandgem Town (+ Center), Route201, Twinleaf Town exterior; no full contiguous Jubilife experience on main. #176–#178 map tooling and #187/#188 map QA tools already merged; #189 live queue merged. |
| [#181 Route202](https://github.com/kioconnor24-sketch/PokemonGame/pull/181) | `b4c1d39f0476b004f772506abd1b378e055ad03e` | **Non-draft, NOT MERGED.** Source-corrected Sandgem↔Route202 offsets ±3, accepted earlier production engine tree `8a60e891`: developer reports 0 static findings, 313/313 native, genuine NORMAL/RELEASE mGBA 20/20 and Save→fresh Continue 3/3 **per build**, deliberate negative fails as expected. Current head includes non-engine asset-provenance cleanup. `exclusive-files` **FAIL** because trusted owner PR-specific eight-path handoff absent. Other reported relevant checks green; weekly audit skipped, not passed. |
| [Claude held Verity integration](https://github.com/kioconnor24-sketch/PokemonGame/tree/claude/verity-integration-hold) | `4ed99916f0aeb6bee81e9aedf51f40fb6d66730e` | Lake Verity + Verity Lakefront, section220 already owner-approved; accepted reported combined Route202+Verity engine source `36c4103a`, 316/316 native, 0 static, NORMAL/RELEASE mGBA40/40 and Continue3/3 each, negative tests. **Not a production PR**, overlapping global `event_scripts.s` with #181. No duplicate design/retesting of unchanged sources. |
| [Codex draft #184](https://github.com/kioconnor24-sketch/PokemonGame/pull/184) | `a7837a43d7518103f62c46f41d9c5f5a31c76412` | **Six-map Jubilife→Route203→Oreburgh Gate plus neutral Center/Mart/School, OFF-ENGINE stage only**, latest branch head; neither merged nor production accepted. Detailed immediately below. |
| [Claude staged Route204–205](https://github.com/kioconnor24-sketch/PokemonGame/tree/claude/route204-donor) | `7f24a0c310cb3f94a8ccdac22bd051156cb2ee78` | Off-engine Route204/Ravaged Path/Floaroma Town/Meadow/Route205 South+North. Earlier five-map NORMAL scratch mGBA56/56 + Continue3/3, static0; North staged later and has **not** earned same paired emulator acceptance. **No permanent sections ≥224 owner-approved.** Preserve branch. |

GitHub commit/check metadata and authored test manifests are sources; the manager has **not independently executed** the builds or mGBA tests. Do not extrapolate a scratch test to a changed source or merge candidate.

## 3. What Codex actually did most recently — important update

**Primary active task remains [draft #184](https://github.com/kioconnor24-sketch/PokemonGame/pull/184)** on `codex/jubilife-oreburgh-corridor-20261020`, **not new map construction**. Read:
- `Pokemon Game/Averon_Codex_Handoff/design/sinnoh/jubilife-corridor/CHECKPOINT.md` — latest appended "Active resumption".
- `.../engine-overlay/build-checkpoint.json`, `.../engine-overlay/registration-fragments.json`, `.../evidence/20261021/`, and `.../apply_scratch_overlay.py`.
- [Codex exact scoped claims](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6309522536); [PR184 acceptance comment](https://github.com/kioconnor24-sketch/PokemonGame/pull/184#issuecomment-6309373564) and [newer Center-fix comment](https://github.com/kioconnor24-sketch/PokemonGame/pull/184#issuecomment-6309488910).

**Already executed and recorded on PRE-Center-fix scratch source `44945713517e5e87b6c5ae8bb7ab075e701f3ffb`:**
- Reproducible isolated scratch integration of six map candidates against Route202 `b4c1d39f` and exact existing Verity220 section definition. No direct edits to Claude branches and no protected production registrar commit.
- Removed unsupported Oreburgh Gate ladder `(19,5)`; replaced closed east mouth with existing cave wall; restored existing music; verified reciprocal Route202↔Jubilife ±38 seam. Seven-map static QA reported 0 findings.
- Genuine NORMAL and RELEASE *scratch* ROM builds and mGBA **63/63** checks plus **3/3 fresh-process Continue per profile**; additional Gate checks 7/7 and Continue3/3. Focused native37/37, save-layout4/4, host25/25, with deliberate negative/mutation coverage.
- Same-toolchain NORMAL linked ROM growth reported **+22,540 bytes**, RELEASE **+22,532 bytes**; no reported linked RAM increase. Screenshot/evidence+hash manifests committed, test-only DEV transport explicitly disclosed. Existing production gameplay accessibility is **not** proven by a DEV transport.
- Stable receipts link NORMAL scratch ROM SHA256 `4151a11f…`, RELEASE `3f10a152…`; the 38-file source manifest identifies the pre-fix scratch code. These are not final release hashes.

**Latest changed source NOT yet fully accepted at snapshot:**
- [Branch head `a7837a43`](https://github.com/kioconnor24-sketch/PokemonGame/commit/a7837a43d7518103f62c46f41d9c5f5a31c76412) replaces **seven Pokémon Center escalator cells** to close an unsupported upstairs exit while preserving the two actual doors.
- New scratch source identified by Codex as `1f21747e` (short SHA of scratch-only tree, not a GitHub merged commit). **Host28/28 PASS and static0** on this repair; Codex reports NORMAL rebuild done, **RELEASE/full paired mGBA/native + old-save rechecks in progress**. Earlier 63/63/37/37 evidence is not acceptance of this changed source. [Latest #15 checkpoint](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6309522536).
- Production #184 remains DRAFT and off-engine; the `engine-overlay/` content and `registration-fragments.json` are **unapplied candidates**. Map sections221 Jubilife+interiors,222 Route203,223 Oreburgh Gate **already owner-approved**; permanent paths' exact PR handoffs still apply.

**Next substantive Codex work package (not tiny chores):** finish all changed-source Center/Gate/entire six-map corridor visual checks, paired NORMAL/RELEASE/native/mGBA/save/old-save acceptance; inspect test logs and immutable source manifest; then prepare a **clean, serialized production integration** onto correct freshest `main` and #181/Verity ancestry when allowed. Preserve protected globals/old slot indices, validate local corridor tileset linking, section pins, sprite/animations, door closures, natural route connectivity and resource headroom. Avoid dozens of minor new PRs or recreating accepted old M1 suites. Codex should keep its current reproducible scratch QA moving even if owner approval is late. A *new source tree* needs *new source-relevant acceptance*.

## 4. Actual blocker matrix — no fictional restrictions

**Owner action required, cannot be performed by manager/Codex:**
1. [#181](https://github.com/kioconnor24-sketch/PokemonGame/pull/181) is blocked on the GitHub `exclusive-files` checker until **the owner personally provides a genuine trusted `HANDOFF_APPROVED PR=#181 PATHS=...` with all eight exact protected paths** via [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). Owner-approved section219 is NOT that handoff; old manager/developer issue comments are NOT authority. The exact prior requested eight-path line appears in [Issue #15's Route202 blocker report](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6298723295); the [current integration queue](INTEGRATION_QUEUE.md) summarizes the blocker without conferring authorization. Do not forge a line, alter checkers/workflows, mark a check green in prose, bypass the PR, or merge while `exclusive-files` fails.
2. After #181 really merges, held Verity's eventual PR and then Codex's production registration need their **own** real PR/path authorizations for changed protected files. Determine literal lists from actual diffs rather than inheriting #181's line.
3. Claude's future Route204–205 production requires an **owner decision** on new met-location sections. [Three-code shared grouping is only a proposal](https://github.com/kioconnor24-sketch/PokemonGame/blob/claude/route204-donor/Pokemon%20Game/Averon_Codex_Handoff/design/sinnoh/route205-donor/SECTION_RECOMMENDATION.md). No assumed value ≥224. No third-party asset redistribution without proven rights.

**Developer/manager CAN do now:** finish independent scratch tests; review sources and exact diffs; fix legitimate compilation, map, graphics/door and QA defects on Codex-owned branches; update one current handoff/queue when material; merge any truly authorized, exact-head, fully-checked Fast Lane A/B PR; provide necessary nonauthor review for higher-risk changes. **No need for Claude to return to do routine review, and no owner approval needed to BUILD a disposable test ROM.** Wait on authorization only for actual guarded production integration. If #181 remains blocked, do not waste Codex usage on idle status discussion or arbitrary new geography.

**Potential technical guardrails:** legacy met-origin values0–214, NONE215, specials253–255; section216–223 identities already owner-approved as recorded (some still unmerged); save compatibility; map group/slot append-only, actual compiled normal/release paths, unchanged source graphics licensing and test profiles. Avoid mistaking source-only CI green for production gameplay PASS.

## 5. Integration order and next manager actions

1. **Refresh before acting:** main full SHA, open PR numbers/head SHAs/files/checks, Issue#15 most recent comments (including new Codex updates), #184 source/ROM evidence, #181 newest `exclusive-files`, branches Verity and Route204–205. GitHub snapshot in this document is dated, not a lock.
2. If Codex has published final Center-fix paired evidence, compare its new scratch source identity, actual steps and visual evidence against the last source change. If genuinely current, recognize **scratch accepted**, not production accepted. Ask only for *specific missing validations*, not a repeated huge suite.
3. If genuine owner authorization for #181 arrives and its exact final-head guards/source acceptance are valid, review bounded diff and merge normally with pinned head SHA, verify main. Then Codex (sole developer) can serialize Verity without modifying Claude branch or duplicating existing content; get separate scoped owner handoff and tests, then continue #184. Do not accidentally open overlapping protected PRs prematurely.
4. If #181 still waits, actively remove only legitimate coordination/engineering restrictions. Let Codex finish its own #184 test/integration preparation and keep a recoverable boundary. Avoid false deadlines, branch mass-deletion, broad review restrictions, unwarranted owner approval questions or mass reports.
5. After genuinely integrating the first connected Sinnoh corridor, choose the next **large coherent** geographic work package, probably Claude's Route204–205 source on new Codex-owned integration branch, conditioned on owner saved-section policy. Preserve existing proof instead of redoing graphics.
6. Post a **single concise** manager issue/pr update only when state changes materially. Document exactly what changed and any remaining owner-only decision. Source of truth: verified repo, actual checks and genuine owner comments, then contract, then this dated handoff.

## 6. Scheduling, responsibility, and handoff discipline

The owner requested a repeating **every-two-hour ChatGPT manager task** to inspect GitHub, adjust large Codex work packages and remove legitimate administrative blockers. It has been configured in ChatGPT. Codex's own checkpoint also mentions a separate instruction-check task. Neither scheduled reminder **starts a paid Codex session**, authorizes protected changes, or proves that any developer is currently running. Avoid duplicate/no-op GitHub posts, and never change staffing away from Codex-only absent an owner instruction.

**Fast Lane A/B stays active** for genuinely eligible docs/tooling and bounded authorized map additions, with actual exact-head checks; no extra manager ACK. Consequential R2/R3 review, real restricted-file authorizations, old-save compatibility, and real ROM/mGBA evidence remain required. Manager may do bounded independent review if source/runtime expertise permits; never attribute it to paused Claude.

**Future-manager quick start:** Read this document → refresh GitHub → look for final #184 changed-source replay → check trusted #181 authorization → solve lawful blockers and update a **substantial**, executable Codex development assignment if needed. Do not repeat solved Gate ladder, Center art, map QA driver, or 63/63 pre-fix scratch tests as though unfinished. Success = more **properly merged playable Sinnoh geography** rather than more administrative output.
