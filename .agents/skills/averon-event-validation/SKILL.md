---
name: averon-event-validation
description: Validate native Averon NPC events, script prerequisites, saved flags, one-time rewards and retry behavior.
---

Inspect existing native scripts and tests before adding helpers. Audit flags/vars
with `scripts/audit-averon-event-ids.py --engine engine`. Preserve allocated IDs,
save layout and native Pokémon interactions. Use the smallest script/flag solution.
Do not introduce a journal or formal quest-management UI.

Exercise the actual compiled script boundary, not only a Python model: decline
and return, absent prerequisites, out-of-order/repeated interactions, inventory
failure and retry, one-time reward, flash save/load at relevant stages, whiteout
and coexistence with opening/Gym/FIELD state. Run applicable host flow/installer
checks and deterministic regeneration. Distinguish native reset/warp tests from
rendered NPC/nurse flow. Hand exact outstanding visual steps to ChatGPT QA on the
owning PR; do not claim acceptance or silently relax the dependency gate.
