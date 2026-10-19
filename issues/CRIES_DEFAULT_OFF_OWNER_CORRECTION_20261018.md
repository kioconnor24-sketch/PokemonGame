# Owner correction: cries OFF by default — October 18, 2026

The owner explicitly reconfirmed that the ordinary Pokémon Averon build must have **Pokémon cries OFF**, with **all cry sources retained in GitHub for later restoration**. No in-game toggle or further audio-engine feature is requested. Existing music and other sound effects remain enabled.

## Reproduced mismatch and repair

Main `ce0c505d4ae3103680f96482881b9589bced14c0` still defaults `P_CRIES_ENABLED` to TRUE. A regression executing actual Make overrides and the production configuration reproduced wrong defaults for both NORMAL and RELEASE; explicit ON/OFF controls already behaved correctly.

The correction changes only the fallback configuration to FALSE, inside the existing `#ifndef P_CRIES_ENABLED`. Ordinary `make` / `make RELEASE=1` now select OFF on this branch; explicit `CRIES=on` restores the retained cries and explicit `CRIES=off` remains supported. No cry source, definition, species association, music, instrument, sound effect, saved format or map is deleted or changed.

Actual host RED: 3 identities, two failing default subcases (NORMAL/RELEASE); explicit ON/OFF controls PASS. Final GREEN: **4/4 identities**, all eight ordinary/default/ON/OFF mode/profile subcases PASS. The actual Make checks also run inside the existing CI production-config checker. The existing production-config CI checker now enforces the OFF default and detects a mutation back to TRUE. Workflow/guard code and frozen failure baselines are unchanged.

## Adoption and associated instructions

This is a tested PR candidate until independent review and normal integration. Do not claim main has changed merely because the owner approved the direction. Codex must not self-merge its own configuration PR.

The existing reversible-owner policy is updated directly. Pending organizational-reset #144 still owns the canonical routing/queue files; its reviewer has been notified in #15 and #144 to replace “default ON / adoption undecided” with this owner decision. Codex does not edit that pending branch or its claimed routing files concurrently. Historical source hashes, ON/OFF measurements and old RED evidence remain preserved and attributed; they are not rewritten as new results.

Human audio listening and Delta remain deferred/unverified release checks. The original cry cold-start defect was fixed by merged #117; the clinic crash was fixed by #124. This default correction reuses those implementations and their disclosed gameplay evidence rather than reopening Claude's audio work.

## Build and native evidence

| Build | Linked ROM used | ROM free | SHA256 |
|---|---:|---:|---|
| default-off-normal | 17,323,560 B | 16,230,872 B | `286e7b176cfef57b3260f3a89f841162f088b045ae06c35164b4f14bc86f9612` |
| default-off-release | 17,442,156 B | 16,112,276 B | `4f6755b3ad5787685d4c8b6a9429e53930250acf8ddd08d55dbab26a914ff77a` |
| restore-on-release | 26,858,724 B | 6,695,708 B | `bd9491a7239dea0b02cbd3108cf7f05e3252c7e15bd7a62102a378100dbbcc6d` |

Actual source `5c33cd4e2cf55160c22ef1303dfd9d26ab404d68`, engine tree `97624367c72e7679dbdb36fad5a78153a63e0fa2`; GCC14.2.1/binutils2.44/newlib4.5. Default-OFF NORMAL has0 warnings; both RELEASE profiles have only4 existing newlib syscall warnings. The later test/documentation-only commit preserves that engine tree.

Default OFF contains **0 linked cry samples**. Explicit ON restores **1,156 cry samples** from the same retained source. RELEASE saves **9,416,568 linked bytes** by default; **530 song objects and 156 non-cry samples match byte-for-byte**. Existing static comparison helpers are reused; this is not a new human listening or gameplay verdict. The explicit ON RELEASE ROM is byte-identical to the pre-correction merged-main ON image.

Retained cry-source tree: `cd221ddb39468e64ca89bbf6177da1b5862c8ffe` in both main and the correction. Only the Pokémon config header changes within engine source; cry definitions, associations and assets are unchanged. All save headroom reports remain304/84/1556/1568 B free (SaveBlock1/2/3/PC); no migration. Static RAM matches the corresponding ON baseline.

Host tools: new profile checks4/4, existing profile tests5/5, existing gameplay-tool tests18/18. Production-config:217 property checks in each of2 modes,24 harmful mutations detected, including a return to default TRUE. Actual default-OFF linked registry:77groups/953pins/536header symbols;12 source mutations +3 pointer mutations detected,1 valid extension accepted. Native status/counts belong to PR #146's exact-head check/handoff; no pending native run is labelled PASS here. Required native CI and genuine peer review must complete before integration.

Human listening/Delta are not newly claimed. The prior Claude OFF-runtime evidence is retained as evidence of #117's unchanged safety implementation; it is not relabelled as a fresh graphical test of this candidate.

Actual default-OFF native CI at source `5c33cd4e2cf55160c22ef1303dfd9d26ab404d68`: **264/264 PASS**, run39180211213/job117831162448. Textual evidence artifact12156605822, zip SHA256 `a3230043cc316a56c446669894007582f9b229cbcbd0de03cb377c1495961109`. CI uses GCC13/newlib4.4, NORMAL ROM SHA256 `44d8931af811e0d76f86fe29b1ebadbd98cd425efa68ef0172ba61b0364638f8`; do not equate its hash with the local GCC14 image. Later changes integrate the host profile test into CI and finish this document; the engine tree remains identical. Refresh final-head checks before merging. This is the Averon-filtered suite, not a repeat/relabel of the full accepted M1 run.


## Resume the independent work

Sandgem #133 is normally merged at `ce0c505d`; its engine tree equals reviewed/evidence tree `ed42447b6435446177ec11bebdc4eda3a343f277`. Prior X7 main ON measurements remain historical restoration-profile evidence. Continue the resource record with the corrected default-OFF budget and clearly labelled ON restoration projection. No ordinary story entry, natural Sandgem whiteout, new heal ID or additional map is authorized by changing the cry default.
