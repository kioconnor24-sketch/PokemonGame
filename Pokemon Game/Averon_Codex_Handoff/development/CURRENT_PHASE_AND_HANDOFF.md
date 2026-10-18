# Pokémon Averon — CURRENT STATUS AND NEXT-PHASE HANDOFF
_Last verified: 2026-10-17. Read this page before dated M1 task plans._

## Owner decision — authoritative
**Pre-Sinnoh Milestone 1 (M1) is OWNER-ACCEPTED and its map-independent backend engineering is complete.** The owner explicitly accepted Claude's consolidated verdict on 2026-10-17, approved closing M1, and authorized proceeding to the next development phase **with human audio listening postponed**. The documented Gym 1 victory/badge/Save→Continue evidence is accepted despite missing postbattle dialogue screenshots. The other disclosed bounded QA and resource limitations are accepted as planning constraints, not secretly marked tested.

This authorization supersedes historic _M1 is open_, _Codex paused_, _Claude sole M1 executor_, _no new map production under any circumstances_, and _awaiting owner M1 signoff_ notices in dated docs and archived issues. It **does not** approve any invented map geometry, specific Sinnoh/Averon content, plot/canon, dialogue, Gyms/rosters, level curves, permanent saved/map IDs, unlicensed assets, a final ROM release, or bypasses of repository safeguards. Work on new content **may be proposed and executed as individual approved designs**, and necessary technical preparation can proceed. If scope or an actual design is undecided, ask the owner instead of selecting it silently.

## Evidence behind the transition
- **[Claude final consolidated acceptance](M1_ACCEPTANCE_REPORT_20261017.md)** — PR [#112](https://github.com/kioconnor24-sketch/PokemonGame/pull/112) merged at `275e8591`; Q1–Q5 documented with genuine emulator input/frames and explicit DEV_FIXTURE cases; graphical Gym 1 caveat and postponed audio noted. A separate human/third-party playtest was *not* performed.
- **[Codex native/backend closeout](CODEX_M1_NATIVE_CLOSEOUT_20261017.md)** — PR [#109](https://github.com/kioconnor24-sketch/PokemonGame/pull/109) merged at `9ae0b32a`; complete **6,107** unfiltered results, **5,332 PASS**, exactly the unchanged **327 normalized expected failing identities / 329 failing results**, no new unexpected differences; actual NORMAL and RELEASE builds and a focused 30/30 save-integrity batch passed. Do **not** report all 6,107 as passing.
- **[Sinnoh technical readiness](SINNOH_TECHNICAL_READINESS_20261017.md)** — PR [#111](https://github.com/kioconnor24-sketch/PokemonGame/pull/111) merged at `fe184495`; a *planning assessment*, not maps or capacity proof. RELEASE ROM had **6,699,508 B** remaining; SaveBlock2 **84 B** remaining. Candidate ROM allocations and compression savings are not approved guarantees. The map-section/met-location namespace, Fly and map build inclusion need explicit design and integration.
- Main's game engine tree for the final M1 evidence was `5d81cc8431cc4c915889b303c22aca2059b78aa3`; later non-engine docs/QA merges were checked for engine equality. For new production changes, regenerate pertinent build/test and current-head evidence.


> **Current temporary owner reassignment, 2026-10-17:** Codex's reversible cries safety work stopped at its pushed draft PR #117 checkpoint. The owner now directs Claude to complete that specific audio/graphical-QA lane; consult [CLAUDE_CODEX_CRIES_TAKEOVER_20261017.md](CLAUDE_CODEX_CRIES_TAKEOVER_20261017.md) and the live claim in Issue #15. This is a temporary exact-file handoff, not permanent permission to overlap later Codex work or bypass production review. Default main still includes cries; no-cries remains experimental until accepted and merged.

## Now-active navigation
| Purpose | Canonical location | Status |
| --- | --- | --- |
| Current ownership, proposed work and nonoverlapping claims | [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) | Active coordination hub, **new phase** |
| Next-phase design/engineering backlog | [Issue #26](https://github.com/kioconnor24-sketch/PokemonGame/issues/26) and [this handoff](CURRENT_PHASE_AND_HANDOFF.md) | Provisional until owner approves each concrete design |
| Real emulator/visual QA and deferred **human audio listening** | [Issue #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23) | Open; audio not yet certified |
| Developer questions and evidence-backed blocker triage | [Issue #55](https://github.com/kioconnor24-sketch/PokemonGame/issues/55) | Open |
| M1 acceptance and archived source/CI/QA evidence | [Issue #46](https://github.com/kioconnor24-sketch/PokemonGame/issues/46), [report](M1_ACCEPTANCE_REPORT_20261017.md) | Accepted historical milestone; **not** current work queue |
| Previous routing/dated handoffs | [INDEX](INDEX.md), old issues and PRs | Historical; retain for provenance |

## Immediate next-phase work: independent, reviewable lanes
1. **Owner/manager + designers:** Establish a concrete design/content and resource contract: intended region map order, reachable routes/landmarks, section/met-location policy, progression/badge/Fly/healing semantics, legal asset sources and an explicit ROM reserve. Existing game canon: **Averon is the original region; Sinnoh is the full second region**. Do not silently finalize unsolved story or geography choices.
2. **Codex — technical foundation, exact file claims:** Build/verify *noncontent* budget tooling and compatibility checks first; prepare append-only map/section registry strategy and save-safe Fly/healer integration only after the relevant owner decisions. Identify applicable native regressions, resource growth per PR, and safe existing-art/audio reuse. Do not reimplement M1 or make speculative refactors. [Technical analysis](SINNOH_TECHNICAL_READINESS_20261017.md) is guidance, not blanket permission for map IDs.
3. **Claude — approved content and real gameplay QA, exact file claims:** Once design scope is owner-approved, build small playable vertical slices with actual mGBA Save→Continue, warps, menus, follower, Gym/progression and visuals. Before content approval, review design/build contracts and work on independent, nonoverlapping bounded tools/evidence only. No unsupervised new plot/canon, maps or music.
4. **Manager — integration/coordination:** Keep #15 claims authoritative, review protected-file/code changes, track budget/CI/visual evidence, authorize normal eligible merges; never treat a planning document or green native check as completed gameplay.
5. **Deferred human QA:** Audio listen (title, areas, battle, fanfare, jingles, effects/cries, audible artifacts) remains open on #23. It is **not** a blocker to beginning the next phase, but **must not be marked PASS** or silently omitted from later release QA.

## Nonnegotiable safety / precision
- No direct unreviewed `main` edits, forced shared-branch rewrites, bypassed `file-guard`/`exclusive-files`/CI/PR review. Owner approval changes *scope*, not technical protections; if an old map-freeze guard needs revision, propose a **small separately reviewed policy/guard change** rather than disabling it.
- Two developers can code concurrently in separate branches/worktrees on **disjoint exact paths** after checking recent claims in #15. Notice of an unclaimed ordinary path is not an approval queue; overlapping protected paths require coordination and normal checks.
- Do not upload playable copyrighted ROMs, private saves, secrets, friend likenesses, unlicensed art/music, or claim Delta verification without an actual owner test.
- Exact terms: `SOURCE` ≠ `BUILD` ≠ `NATIVE-TESTED` ≠ `EMULATOR-TESTED` ≠ `DELTA-VERIFIED`. Record source/ROM hashes, observed test identities, original fixture/debug use, screenshots and failure caveats.
- Current resources are **constraints**: RELEASE ROM ~6.39 MiB left, SaveBlock2 84 B, and live sprite/palette/stack peak capacity not exhaustively known. All future additions must measure actual linked deltas; do not promise an entire second region fits.
- Retain old M1 runbooks, issue history, source artifacts and test evidence in place. Their dates and old instructions are **historical**, not work to be redone. No automated agent sessions are started by GitHub comments.

**Before acting:** refresh live main, open PRs/checks and #15 claims, read this page and the relevant feature source, then perform the nearest approved concrete task; do not request another blanket M1 signoff.
