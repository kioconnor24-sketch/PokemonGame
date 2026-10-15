---
name: averon-event-validation
description: Validate Averon quests, events, flags and scripted battles for allocation safety, repeatability, save/load and whiteout behavior. Use when adding or changing event scripts, persistent flags or vars, rewards, or story battles.
---

# Averon event and flag validation

## Flag allocation (check before adding any flag)
1. Read `Pokemon Game/engine/include/constants/flags.h`. Averon flags currently occupy `0x20-0x37` (`FLAG_AVERON_*`; `0x30-0x36` are field licenses; `0x37` was claimed by QUEST PR #14). Check open PRs for newer claims.
2. Never renumber or reuse an allocated ID. Old saves depend on it.
3. Persistent flags must not sit in the daily-reset range. `DAILY_FLAGS_START` resolves to `0x920`; avoid `0x920` and above.
4. `FLAG_BADGE01_GET..FLAG_BADGE08_GET` are `SYSTEM_FLAGS+0x7..0xE` and the next flag is a Hoenn visited flag. Code that loops `FLAG_BADGE01_GET + NUM_BADGES` assumes contiguity; do not change `NUM_BADGES` without auditing every such loop.
5. Flag allocation, event registries and save code are serialized by explicit claim in issue #15.

## What every event needs
- One-time rewards guarded by a flag; behavior with a full Bag and a full party (retry, no loss).
- Prerequisites and repeated NPC interaction handled; no softlock if the player leaves and returns.
- Save/reload mid-sequence; whiteout during the sequence; no state leaking into ordinary battles.
- Story defeats are intentional: no money loss, no permanent Pokémon loss, no repeatable exploit.
- Quest UI stays traditional: NPC dialogue, flags, items. No quest journal or objective markers.

## Existing tests to extend
`Pokemon Game/engine/test/averon_save.c`, `averon_scripts.c`, `averon_respawn.c`, `averon_healing.c`, `averon_gym_reward.c`, `averon_field_licenses.c`; host-side `Pokemon Game/scripts/test-averon-quest-flow.py` and `test-averon-sidequests.py`. Follow `averon-build-verification` for how to run them.
