# Pokémon Averon — two-gate pre-Sinnoh integration contract

**Owner decision 2026-10-16/17.** For current routing and exact file claims, read [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). [Issue #46](https://github.com/kioconnor24-sketch/PokemonGame/issues/46) remains the final detailed acceptance contract. Older instructions that say *all QUEST graphical Q1–Q5 cases must finish before any unrelated generic code can merge* are superseded by the **two-gate rule**, not by an exemption from correctness testing.

## GATE A — technically safe integration (not gameplay acceptance)

A standalone core-only feature is eligible for ordinary independent review and normal merging **when all of the following are evidenced**:

- Real normal ARM Game Boy Advance build and meaningful native / actual save regression tests ran to completion with nonzero counts, on the exact candidate head.
- Required source/config/namespace/budget and protected-file CI checks passed. No rule was weakened, approvals were not synthesized, and no unsafe source overlap remained.
- An independent reviewer actually examined relevant source and test evidence; no confirmed severe data corruption or regression is being left unreported.
- The staged functionality is clearly marked **CORE_ONLY / UNREGISTERED / NOT GAMEPLAY_ACCEPTED**. Not-yet-installed caller scenes are not claimed tested.

A gameplay-bearing QUEST PR **may** enter independent GATE A review before *all* Q1–Q5 edge cases have rendered acceptance **only if** Playtest separately accepts at least one real positive original quest/reward/save→Continue case, relevant actual negative/retry native contracts pass and no known severe regression remains. Remaining **noncritical** graphical cases must be explicitly recorded as unverified and retained as **GATE B blockers**. Developer/self-generated source tests do not replace the minimum independent rendered result.

GATE A is **not** a self-merging permission; the normal GitHub branch protections, independent review, exact-head verification, sole integrator and protected file handoffs remain.

## Specific currently actionable #25 split

[Original SCRIPTED-BATTLE PR #25](https://github.com/kioconnor24-sketch/PokemonGame/pull/25) modifies `Pokemon Game/engine/data/event_scripts.s` by **one** added registration line:

```asm
	.include "data/scripts/averon_scripted_battle.inc"
```

[QUEST #14](https://github.com/kioconnor24-sketch/PokemonGame/pull/14) also edits that protected file. The existing exclusive-files checker **correctly fails #25** while both PRs overlap; it must not be disabled.

1. [Manager PR #76](https://github.com/kioconnor24-sketch/PokemonGame/pull/76) provides `scripts/coordination/stage_scripted_core.py`, adversarial tests and the **Averon staged SCRIPTED-BATTLE core rehearsal** GitHub Action. It fetches main and exact #25 head, merges only in a disposable worktree, removes only that line if the registry otherwise **byte-for-byte matches main**, verifies staged core source and absence of real macro callers, then actually builds GBA and runs native/save suites. The results are diagnostic only; evidence contains source SHA, logs and checksums, **never a ROM, saved game or ELF**.
2. If and only if that exact staged experiment passes, **Codex** (the sole engine-source owner) may create a **separately claimed, reviewed core-only PR** containing the validated implementation/tests, **omitting the protected registry line**. It must pass ordinary CI and be merged normally. No other AI modifies #25 or `engine/**` in parallel.
3. Keep the overlapping original #25 draft; after QUEST #14 is safely merged, Codex must perform the serialized exact-file handoff (including the documented `HANDOFF_APPROVED PR=#… PATHS=…` authorization if required) and integrate the one-line registration separately, with real source/native checks and review. Do not invent trainer scenes; macro definitions are not evidence that a player-facing scripted scene runs.

No automatic transition from a staged core to registered/callable story content is permitted.

## GATE B — final pre-Sinnoh backend acceptance

All feasibly testable required integration **and** relevant original mGBA user-path verification must be genuinely complete, including as applicable:

- Real Badge01 earning → positive Hiker interaction and exactly once item reward; full-pocket refusal, room-making and ordinary retry.
- Actual artist/tree Oran×3 save/Continue; original old-save and full-Berries boundaries where feasible.
- Original trainer defeat and properly initialized clinic → whiteout/return/nurse healing; no faked party, map registration or badge state.
- Gift with six-member party refusal, legitimate party-space retry, nonduplication and saved persistence.
- Follower recovery, restored player input/audio and cross-feature regression with safe staged/registered battle outcomes, real release and save compatibility.
- Owner Delta iOS gameplay acceptance is **separate** from GitHub/mGBA evidence; source tests and boot images never claim it.

Playtest owns the independent **PASS / PARTIAL / FAIL** verdict on rendered Q1–Q5 cases. An honest open `GATE_B_QA_PENDING` is acceptable for a merged-but-incomplete GATE A feature; **it cannot be counted as BACKEND_READY** or silently waived. When actual new geography, reserved canon or other owner choices are truly required, label the item **POST_MAP** or **OWNER_DECISION** with the precise reason, never invent replacements.

## Collaboration rule

- **Codex:** sole engineer writing active production engine files and final main-branch integration.
- **Claude:** separately scoped QUEST evidence / nonoverlapping helpers and read-only integration preflight. Claude's native QA support is **not independent Playtest approval**.
- **Playtest:** real gameplay cases and independent graphical acceptance.
- **Manager:** integration staging tooling, CI and honest routing. The manager does not merge its own unsafe engine patches or self-approve protected overlaps.

The owner freeze on all **new maps and unapproved story/content/IDs** remains intact. A GitHub comment or policy edit never starts a model session or automatically triggers a release.
