# Pokémon Averon — GitHub coordination and optional agent automation

**This is infrastructure, not another game design plan.** It does not authorize maps (including temporary map files), story/Gym/encounter/level decisions, automatic merging, or concurrent protected-source changes.

## Operational links

- [Live generated agent board](https://github.com/kioconnor24-sketch/PokemonGame/issues/31): one current GitHub issue body, not dozens of status comments
- [File ownership and approvals](https://github.com/kioconnor24-sketch/PokemonGame/issues/15)
- [Graphical QA evidence](https://github.com/kioconnor24-sketch/PokemonGame/issues/23)
- [Task definitions](../../scripts/coordination/tasks.json)
- [Board renderer](../../scripts/coordination/render_board.py)
- [Sensitive file guard](../../scripts/coordination/check_protected_files.py)
- [Screenshot observation helper](../../scripts/coordination/qa_frame_gate.py)

## Manual sessions, direct agent-to-agent messages

**No API keys, external messaging platform or automated agent execution needed.** Finish each Codex, Claude and Playtest chat normally. GitHub preserves their messages; the next manually started session reads [Issue #31](https://github.com/kioconnor24-sketch/PokemonGame/issues/31) before acting.

Post a short message in [team #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), [QA #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23), or a relevant feature PR when another agent must know a decision, bug, blocker or required action. **The first line must be the exact one-line envelope:**

```text
AGENT_MESSAGE TO=claude KIND=ANSWER TASK=SCRIPTED-BATTLE PR=#25
SUMMARY: Codex verified RAM-only flag 0x4003 is a valid candidate.
NEXT: Do not edit shared files until QUEST merges and the exclusive handoff is granted.
```

Set `TO` to `codex`, `claude`, `playtest`, or `all`. Set `KIND` to `QUESTION`, `ANSWER`, `HANDOFF`, `BLOCKER`, `QA`, or `FYI`. `PR=#N` is optional. Both `SUMMARY:` and `NEXT:` are required. Include actual PR/issue/test evidence links in the originating comment whenever possible, but keep the summary short. **No third-party bots or extra message files.**

The board reads these explicit messages from #15/#23 and registered PR conversations. Its three inboxes prioritize unanswered messages and link back to the *original* comment. To acknowledge a specific message after reading it, reply in that issue or PR with a comment containing only:

```text
AGENT_ACK ID=123456789 BY=claude
```

Replace the ID with the actual source GitHub comment ID and `BY` with your agent. An acknowledgment is **informational only**; all three sessions may share the same GitHub identity, so this is not proof of who typed it and cannot grant permission. Leave the original question/answer and verify the underlying source. Keep routine session summaries in your own PR handoffs, not the shared channel, and use a directed message only when another agent needs to act.

An agent should check the task board and its message inbox at session start, address the highest-priority waiting message, and post a new directed update when its action materially unblocks another agent. Messages are **never** equivalent to `HANDOFF_APPROVED` or `QA_ACCEPTED` markers, and GitHub comments do **not** restart a ChatGPT or Claude session.

## What runs after the integration PR merges

**Agent board:** averon-agent-board.yml reads GitHub PRs, head SHAs, check conclusions and explicitly accepted QA evidence using code checked out from trusted main. It updates **only Issue #31's body**, creates a GitHub Actions summary and an artifact with codex.md, claude.md, and playtest.md. It runs on PR updates, team #15 or QA #23 comments, comments on tracked PRs, new main commits, daily schedule and manual dispatch. The source tasks.json is updated at approved task/milestone changes, not every session.

**Dependency gates:** Passing native tests never counts as graphical acceptance. A dependent task can become machine-ready only after its prerequisite is merged AND exact-head, authorized QA signoff exists if required. Even then, shared-file changes still require a documented human handoff in Issue #15. No auto merge or automatic paid agent execution occurs.

**File guard:** averon-shared-file-guard.yml detects overlap in high-risk paths, forbids new touches to frozen map/layout paths (except the already-open historical QUEST #14 PR), and requires an explicit approved shared-file claim for sensitive changes. A failing workflow blocks GitHub merges **only if the owner sets it as a required status check in branch protection**. The checker cannot see uncommitted/unpublished branch work; maintain exact file claims.

**Integration rehearsal:** Run averon-integration-rehearsal.yml manually with two PR numbers. It attempts merge/whitespace checks in a disposable checkout without pushing any commits, running untrusted code, or launching a native build. Green means textual merge success ONLY, not tested game/save/emulator compatibility.

**QA observation helper:** qa_frame_gate.py compares two rendered screenshots with ImageMagick and returns a failure status if the frame did not change sufficiently. It does not press controller buttons, perform OCR, identify NPCs, or prove success. QA may add it to its existing runner later, in a separate scoped QA claim. The tool itself does not modify the QA workflow or production game.

## Exact acceptance marker — evidence required first

After real independent graphical Q1–Q5 evidence has been reviewed, a trusted collaborator can post this single machine-readable line to QA Issue #23, replacing the bracketed source hash:

    QA_ACCEPTED PR=#14 SHA=<exact-40-character-source-SHA> CASES=Q1,Q2,Q3,Q4,Q5 STATUS=PASS

Only owner/member/collaborator authorship, matching source SHA, and complete required case list can satisfy the dependency machine check. The real case logs and screenshots in #23 are still required. A marker does NOT authorize merging.

## Exclusive handoff marker — permission remains manual

After Codex and Claude agree on a safe post-QUEST integration window, an authorized collaborator may post to team Issue #15:

    HANDOFF_APPROVED PR=#25 PATHS=Pokemon Game/engine/include/config/battle.h,Pokemon Game/engine/data/event_scripts.s

This marker lets the file guard verify a scoped handoff. It grants no access to other save, map, trainer, flag or region paths. Concurrent edits to the same protected file from two PRs fail even with a handoff. Historical PR #14 is grandfathered for its already-existing source footprint, subject to normal human review.

## Paid Codex / Claude execution is deliberately OFF

The manual-only workflow averon-optional-agent-pilot.yml can use official OpenAI Codex and Anthropic Claude Actions **only after** the owner does the following:

1. In repository Settings > Secrets and variables > Actions > Variables, set AVERON_ENABLE_PAID_AGENTS to true.
2. Configure OPENAI_API_KEY and/or ANTHROPIC_API_KEY as GitHub Actions Secrets. Never put API keys in comments, files, or chat.
3. Review possible separate API charges, secret access, budget/spend limits, and workflow behavior; manually invoke a selected pilot in Actions.
4. Review its disposable patch/report artifact. The pilot cannot push/merge or resume the existing web/chat sessions. Its actual provider calls are **unverified until the owner sets up credentials and runs them**.

The GitHub actions are not configured to spontaneously launch a paid coding agent on a PR event; that would require further owner-approved permissions, authenticated execution, rate/budget controls, and a tested runner. Playtest can continue its current emulator workflow, but a conversational ChatGPT Playtest agent cannot be awakened from GitHub comments alone.

## Required project setup

Make the exact exclusive-source gate check and appropriate existing native/source/PR hygiene checks **required branch-protection checks** after testing. Without this, a failure is visible but GitHub may still permit merging. Never enable auto-merge of unverified gameplay.

When a developer starts a session: read [Issue #31](https://github.com/kioconnor24-sketch/PokemonGame/issues/31), current PR HANDOFF, source SHA, and [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15) before editing. Use separate clean worktrees. Keep blocked work blocked, make meaningful disjoint progress, and leave a verified handoff. Maps/story/level caps remain owner frozen.

## Validation and limitations

- Dedicated [unit-test CI](../../../.github/workflows/averon-coordination-tests.yml) exercises dependency, QA-signoff, special-file and screenshot math with positive test counts.
- The coordination board is advisory and cannot independently tell if a game scenario succeeded.
- Integration rehearsal does not build the ARM Game Boy Advance ROM; Codex/Claude still own real compile/native tests and QA owns real emulator acceptance.
- No new production game source or geographic/creative content is part of this framework.
