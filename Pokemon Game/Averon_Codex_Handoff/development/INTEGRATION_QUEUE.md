# Live integration queue — October 21, 2026

Codex is the only active developer. Claude is paused. This dated index must be refreshed against GitHub before acting. The [operating contract](CURRENT_PHASE_AND_HANDOFF.md) governs approvals, reviews, preserved source, and testing. The [October 21 manager handoff](CHATGPT_MANAGER_NEXT_SESSION_HANDOFF_20261021.md) retains older history.

## Current verified state

| Component | GitHub source | Status and next action |
| --- | --- | --- |
| Production main | `d182c7b53f2566cba175e2ad01549af617e04032` | Route 202 [#181](https://github.com/kioconnor24-sketch/PokemonGame/pull/181) **merged** following owner approval and passing required checks. Post-merge native-build, source-contract, python-source-checks and production-config succeeded. Do not repeat Route202 merge work. |
| Verity production | `codex/verity-production-20261021` at `6cb1f82af0f3bba0c19842cb1b551d884568205b` | Codex transplanted Verity and Lakefront onto current main, 36 changed files; latest commit fixes a struct-padding-dependent test. No open production PR or complete new-source acceptance yet. Finish normal/release, native, graphical, save and compatibility testing, then open a scoped PR and follow applicable protected-path review. Approved section 220 is unchanged. |
| Jubilife production staging | `codex/jubilife-production-20261021` at `e1c17f9e6dfb9ccb194e47731931a6d96c8864a1` | Codex staged 41 production paths on top of Verity, including Jubilife, Route203, Oreburgh Gate and neutral interiors. Not yet a separate production PR or tested final production tree. Keep dependent registration changes serialized after Verity integration, then retest and review. Sections 221–223 are approved. |
| Jubilife source/evidence | Draft [#184](https://github.com/kioconnor24-sketch/PokemonGame/pull/184) at `08ff30cac2fb827a4f6a12787e0eac7811fbcae5` | Final-source **scratch** NORMAL/RELEASE graphical 66/66 and fresh Continue3/3 each, host28/28, native37/37, save4/4. Preserve the exact-source evidence. Scratch success does not mean production merged. |
| Route204–205 staging | `claude/route204-donor` at `7f24a0c310cb3f94a8ccdac22bd051156cb2ee78` | Claude's six-area staging preserved. Codex has claimed a separate takeover branch, but no pushed new branch was observed. Complete North and full corridor testing without changing Claude's branch. Section allocations from 224 onward remain undecided. |

## Current substantial assignment

The existing [Codex Verity → Jubilife → Route204–205 work package](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6310701355) already provides a connected multi-phase workload. Preserve its order and the associated Verity, Jubilife and Route204–205 claims in Issue #15. Do not assign small duplicate tasks or restart accepted conversions.

Proceed with Verity current-source acceptance and production review; keep Jubilife staged while Verity owns shared registrars. Once Verity is integrated, update Jubilife's registry slots and run actual changed-tree builds, emulator traversal and save compatibility tests. Continue independent off-engine Route204–205 testing while awaiting necessary owner decisions.

The manager should promptly review ready PRs and remove legitimate process or tooling obstacles. Do not treat older queue references to a missing Route202 authorization as current. Preserve meaningful guardrails, old saves and source provenance; do not treat a scratch ROM as production acceptance or an issue comment as a running developer session.
