> **CURRENT ROUTING — 2026-10-18:** Follow the [single operating contract](development/CURRENT_PHASE_AND_HANDOFF.md) and [integration queue](development/INTEGRATION_QUEUE.md). Process, ownership, freeze and work-order directions below are historical and superseded, including the old PR #66 takeover and absolute map freeze. Keep approved product/design constraints and evidence requirements. No paused session is restarted by this file.

---

> **HISTORICAL CREATIVE HANDOFF — NOT CURRENT IMPLEMENTATION INSTRUCTIONS (2026-10-15).**
> This file describes an earlier proposed design package and bootstrap workflow. Its claims of a complete/finalized design and of having no compiled game code are no longer current. **Do not implement its speculative maps, routes, NPCs, story, trainer teams, dialogue, or levels.** The owner has frozen all map development (including temporary map files) and unresolved creative decisions. For current direction see [repository README](../../README.md), [development INDEX](development/INDEX.md), [current TASKS](development/TASKS.md), [active work #24](https://github.com/kioconnor24-sketch/PokemonGame/issues/24) and [owner freeze #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). The material below is preserved intact as historical reference.

# Pokémon Averon — Complete creative handoff for Codex

**Status: COMPLETE DESIGN PACKAGE v1; GAME CODE AND GAME BUILD NOT CREATED.**

## What is in this folder
- `AGENTS.md`: persistent developer instructions for Codex.
- `CODEX_WORK_ORDER.md`: milestones, code-review procedure, build and acceptance requirements.
- `design/STORY_BIBLE.md`: complete narrative throughline, cast, villains, Gyms and event flags.
- `design/GAMEPLAY_AND_CONTENT.md`: gameplay, level caps, region progression, Pokédex, postgame and compatibility.
- `design/REGION_ATLAS.md`: scene-by-scene map and district design, transitions, route pacing, landmarks and optional towns.
- `design/DIALOGUE_GUIDE.md`: natural Pokémon-style writing rules, playable scenes, examples, editing tests.
- `design/SINNOH_AND_POSTGAME.md`: second region and postgame design with Red and Cynthia.
- `design/QUEST_AND_EVENT_MATRIX.md`: concise event checkpoints and content progression, including non-plot sidequests.
- `design/SPRITES_AND_AUDIO.md`: character sheets, asset intake and attribution policy.
- `data/`: machine-readable CSVs with places, connections, Gyms, milestones, habitat examples and legendary quest groups.
- `qa/QA_MATRIX.md`: essential build, gameplay, battle, save, balance, assets, emulator and Delta acceptance tests.
- `reference_maps/`: TWO CONCEPTUAL SCHEMATICS, not map tilesets, not a built game. **Travel Network v2 takes precedence over Master Map v1** whenever they differ.
- `scripts/validate_design.py`: static lint and travel connectivity checks for the design data.
- `development/`: progress, engineering decisions, source/version notes and block trackers.

## Single creative premise
Averon is a lively, geographically diverse Pokémon region where most people are concerned with normal lives. An ordinary-seeming criminal group, Team Vantage (working name), is secretly integrated into the government, police and League. Its one *public* ambition—**end humanity's dependence on Pokémon**—has supporters for plausible reasons and delivers a few visible reforms after its successful coup. But its leader used that organization to obtain a classified government device, Threshold. Threshold was built to temporarily depower dangerous Pokémon. An old filtration failure caused a dimensional rift and a concentrated discharge that killed an exposed Pokémon test subject. Zygarde emerged in the aftermath. The future villain leader was present and realized the lethal effect might be scaled into a Pokémon-specific weapon. A coalition ultimately invades the installation, fights a ten-opponent gauntlet, receives an allied heal, battles corrupt Gym Leaders, and interrupts the device. The resulting rupture pulls the player and leader into a short alternate-dimensional area for the final main-villain battle. Then the League, Sinnoh, optional international tournament and final Red encounter remain.

## Project constraints
- Engine: `https://github.com/rh-hideout/pokeemerald-expansion`
- Intended emulator: Delta on iOS, via a real `.gba`; use mGBA for development tests first.
- Other tools: Porymap for overworlds and region maps; check source compatibility before importing Sinnoh work.
- Full species coverage **through at least Generation IX**, all forms/evolutions where possible, audited against an authoritative species manifest at the selected engine revision, not assumed complete because engine claims support.
- National Dex, movement and save formats are engineering/verification problems, not solved merely by being written in this packet.
- All plot dialogue is *draft material* until edited in game; no long sermonizing, no modern corporate jargon, no excessive ominous hints.
- The romanticized image of a 'fully complete AAA game in a single Codex run' is not an acceptable milestone. Deliver honest playable slices, then complete areas iteratively.

## How to use this package
1. Put this handoff folder inside a fresh Git checkout of `pokeemerald-expansion`, at a stable path (e.g. `planning/averon/`), or make this folder your Codex workspace and point Codex to the checked-out engine next door.
2. In Codex, say: **“Read AGENTS.md, START_HERE.md and CODEX_WORK_ORDER.md. Implement M0 exactly; don't claim any ROM works until it boots in an emulator. Document every change in PROGRESS.md.”**
3. If Codex's working directory is the engine root, copy `AGENTS.md` into that root too so its instructions are honored for later code changes.
4. After M0 tests pass, instruct it to proceed milestone by milestone. Review playable screenshots and short dialogue scenes before expanding production.
5. For actual distribution, produce a legally distributable patch and clear instructions for applying it to a legitimately obtained base game. The owner's local authorized build may produce a playable `.gba` to import into Delta.

## Not yet provided or verified
No copyrighted original ROM image, no compiled Averon `.gba`, no custom tilesets/animated character sheets or photographs of friends, no complete executable Sinnoh merge, no final National Dex coverage audit, no verified Delta playtest. These are implementation tasks, not hidden files in this package.
