# Pokémon Averon — current next-phase task queue (after accepted M1)


**NEW OWNER AUDIO DECISION / CODEX IMPLEMENTATION PRIORITY (2026-10-17):** [Reversible cries-OFF policy](CRIES_OFF_REVERSIBLE_OWNER_POLICY_20261017.md). Owner accepts no cries **if** music/SFX and gameplay function, but insists all cry source assets stay preserved and cries-ON remains rebuildable later. Codex's [measured report](CODEX_ROM_CAPACITY_RESULTS_20261017.md) is complete; next task is the OFF cold-start null-player fix, reversible ON/OFF build paths, real native/emulator QA and linked-byte checks in a reviewed PR. **Do not delete cry files or treat the current OFF build as already safe.** The prior ROM-capacity P0 assignment is historical/completed.

**COMPLETED CODEX ROM-RESEARCH DIRECTIVE (historical):** [ROM capacity, cries-OFF experimental builds, reclaimable Hoenn, measured Averon+Sinnoh forecast and optional 64 MiB feasibility](CODEX_ROM_CAPACITY_AND_TWO_REGION_FORECAST_20261017.md). Start with a real cries-ON vs cries-OFF RELEASE build and verify music remains; then measure actual ROM deltas and forecast the unfinished two-region game. Keep configuration experiments separate from production and Claude's content work; do not merge no-cries as a user decision. This focused assignment supersedes the generic Codex budget row below for priority, but not safeguards.

**Last owner decision: 2026-10-17.** [M1 is accepted; next phase is authorized](CURRENT_PHASE_AND_HANDOFF.md), with a **deferred, still-unverified human audio listen**. The original pre-Sinnoh implementation checklist in [M1_EXHAUSTIVE_REMAINING_WORK_20261017.md](M1_EXHAUSTIVE_REMAINING_WORK_20261017.md) is closed historical evidence, not new work. Check live [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) and [open PRs](https://github.com/kioconnor24-sketch/PokemonGame/pulls) for exact claims.

| Priority | Owner/lane | Safe next deliverable | Required dependency / stop point |
| --- | --- | --- | --- |
| **P0 — design and identity contract** | Owner + manager + relevant developers | Record approved next playable slice, owner-decided geography, intended map/section/met-location policy, saved flags/vars and Fly/heal/badge behavior; identify asset rights. | No agent invents the answers. Save and map compatibility, existing IDs and story decisions must be respected. |
| **P0 — actual linked-budget observability** | Codex, new disjoint tools PR | Optional link-delta/ROM/RAM/save/asset/section report checks and negative tests, reusing existing verifiers. | Verify no equivalent tool already exists. Do not modify engine or promise content-fit based on estimates. |
| **P1 — region/map integration groundwork** | Codex, exact reviewed source claims | Owner-approved append-only section/ID compatibility, map inclusion and Fly/healer/progression hooks, narrow native/build regressions. | **Owner contract required** before saved IDs, runtime region maps or shared-engine policy edits; normal protected file review. |
| **P1 — playable approved region slices** | Claude and designers, exact reviewed paths | Build and graphically test a small owner-approved area, real walking/dialogue/warps/Save→Continue and follower behavior. | Owner approves actual geography/story/encounters, assets, IDs before committing them. Avoid duplicating Codex integration work. |
| **P1 — design/release QA** | Claude + owner/human | Bounded new mGBA evidence and, later, owner-run Delta testing. Deferred ~10-minute human audio checklist lives in #23. | Audio remains NOT PASS until listened to; Delta not yet tested. |
| **P2 — full region / late content** | Owner-approved design and assigned developer(s) | Expand Averon and Sinnoh to the approved full adventure, legendary quests and postgame. | Budget every increment; don't assume one approved slice approves all canon. |

### Baseline resources and verification

- [Sinnoh technical assessment](SINNOH_TECHNICAL_READINESS_20261017.md): RELEASE ROM **6,699,508 B remaining**, SaveBlock2 **84 B free**, limited map-section codes, missing final per-map/asset budget and unknown deepest sprite/palette/runtime peaks.
- [Native M1 closeout](CODEX_M1_NATIVE_CLOSEOUT_20261017.md) and [graphical M1 acceptance](M1_ACCEPTANCE_REPORT_20261017.md) are done. No rerunning/reopening completed M1 PRs absent a reproduced new defect. A production engine change requires relevant new tests and an updated build/source proof.
- Prior procedural map freeze remains implemented in some guards/docs; owner authorization changes policy **only via normal reviewed update**, not by disabling or ignoring an existing protection.

**Workflow:** refresh source/claims, make a bounded path claim in #15, implement approved concrete work independently, run relevant checks and push a reviewable PR. Record tests and open risks in its HANDOFF, not in a duplicate backlog. Keep #23 for graphical and postponed human audio; #55 for genuine blocker reports.
