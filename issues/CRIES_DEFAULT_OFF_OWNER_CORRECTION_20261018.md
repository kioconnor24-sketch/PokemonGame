# Owner correction: cries OFF by default — October 18, 2026

The owner explicitly reconfirmed that the ordinary Pokémon Averon build must have **Pokémon cries OFF**, with **all cry sources retained in GitHub for later restoration**. No in-game toggle or further audio-engine feature is requested. Existing music and other sound effects remain enabled.

## Reproduced mismatch and repair

Main `ce0c505d4ae3103680f96482881b9589bced14c0` still defaults `P_CRIES_ENABLED` to TRUE. A regression executing actual Make overrides and the production configuration reproduced wrong defaults for both NORMAL and RELEASE; explicit ON/OFF controls already behaved correctly.

The correction changes only the fallback configuration to FALSE, inside the existing `#ifndef P_CRIES_ENABLED`. Ordinary `make` / `make RELEASE=1` now select OFF on this branch; explicit `CRIES=on` restores the retained cries and explicit `CRIES=off` remains supported. No cry source, definition, species association, music, instrument, sound effect, saved format or map is deleted or changed.

Actual host RED: 3 identities, two failing default subcases (NORMAL/RELEASE); explicit ON/OFF controls PASS. GREEN: **3/3 identities**, all six mode/profile subcases PASS. The existing production-config CI checker now enforces the OFF default and detects a mutation back to TRUE. Workflow/guard code and frozen failure baselines are unchanged.

## Adoption and associated instructions

This is a tested PR candidate until independent review and normal integration. Do not claim main has changed merely because the owner approved the direction. Codex must not self-merge its own configuration PR.

The existing reversible-owner policy is updated directly. Pending organizational-reset #144 still owns the canonical routing/queue files; its reviewer has been notified in #15 and #144 to replace “default ON / adoption undecided” with this owner decision. Codex does not edit that pending branch or its claimed routing files concurrently. Historical source hashes, ON/OFF measurements and old RED evidence remain preserved and attributed; they are not rewritten as new results.

Human audio listening and Delta remain deferred/unverified release checks. The original cry cold-start defect was fixed by merged #117; the clinic crash was fixed by #124. This default correction reuses those implementations and their disclosed gameplay evidence rather than reopening Claude's audio work.

## Build and native evidence

Fresh default-OFF NORMAL/RELEASE and explicit ON restoration build results will be recorded here after execution. Retained-asset tree identity, song/non-cry sample equality, native counts, exact source/ROM hashes and any limitations must be recorded as observed; a started build is not PASS.

## Resume the independent work

Sandgem #133 is normally merged at `ce0c505d`; its engine tree equals reviewed/evidence tree `ed42447b6435446177ec11bebdc4eda3a343f277`. Prior X7 main ON measurements remain historical restoration-profile evidence. Continue the resource record with the corrected default-OFF budget and clearly labelled ON restoration projection. No ordinary story entry, natural Sandgem whiteout, new heal ID or additional map is authorized by changing the cry default.
