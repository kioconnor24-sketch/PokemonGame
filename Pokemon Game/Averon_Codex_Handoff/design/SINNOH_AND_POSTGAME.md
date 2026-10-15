# Sinnoh, postgame, Champions' Circuit and Red

## The purpose of Sinnoh
Sinnoh must be a **full second adventure**, not a three-town reference to Platinum. Preserve the recognizable shape and identities of Twinleaf, Sandgem, Jubilife, Oreburgh, Floaroma, Eterna, Hearthome, Solaceon, Veilstone, Pastoria, Canalave, Snowpoint, Sunyshore, Mt. Coronet, the three lakes, Spear Pillar, Victory Road and the Battle Zone. Eight Gym challenges, Cynthia as Champion, and meaningful multi-route exploration are mandatory. Integrate rest stops, optional fishing/caving and active town life. Use a real world map distinct from Averon's map.

## Transition
After Averon's Champion, earn passage on a ferry or air/sea transfer through Vesper/Breakwater to Twinleaf/Sandgem (consistent onboarding). Give the player an accessible Pokémon Center immediately on landing. Their existing team continues with level cap 76 at entry; Sinnoh Gym cap 79 onward (table in `data/level_curve.csv`). The game never resets the player's items, Pokédex or Pokémon. Existing species can remain accessible; Sinnoh expands habitats rather than wiping catches.

## Suggested Sinnoh Gym path
Follow recognizable Sinnoh geography without claiming it's already coded: Oreburgh (Rock), Eterna (Grass), Veilstone (Fighting), Pastoria (Water), Hearthome (Ghost), Canalave (Steel), Snowpoint (Ice), Sunyshore (Electric). To preserve plausible travel, schedule Hearthome visitation before its badge battle; make the route/story locks obvious in-universe. Gym leaders need modernized fair teams, not illegal power leaps. Preserve regional lore but write original side adventures and avoid lengthy copy/paste of Platinum dialogue.

## Familiar Sinnoh people
**Professor Rowan** is the Sinnoh professor, completely distinct from our Averon rival **Renn**. Cynthia appears in an archaeological/adventuring capacity as well as the Sinnoh Champion; retain her thoughtful and gently imposing demeanor, trademark Garchomp and credible team without excessive cutscenes. Other familiar leaders may feature. If the recognizable Cynthia battle theme's music rights cannot be cleared for redistribution, use a commissioned, original battle arrangement that does not copy the melody; do not borrow commercial music files indiscriminately.

## Personal-story continuation
Renn appears in several *ordinary* Sinnoh encounters: glimpsed visiting a workshop, offering help in a village, attending a local tournament or taking a solo training route. The game does not force another trauma monologue. An optional late Sinnoh rematch demonstrates that he still enjoys training; rebuild trust gradually. Mira has discoveries of her own and is not an exposition assistant. Calder returns only for a few small case follow-ups, not a second world-spanning conspiracy.

## Difficulty and 100 cap
Averon Champion target 76; Sinnoh 8 gym caps 79/81/83/85/87/89/91/93; Cynthia 95; postgame milestone 97; Champions' Circuit apex 99; Red 100. These are ceilings and must be adjusted after encounter EXP simulation. Endgame must be hard through polished teams, tactical sequencing and varied battle facilities—not uncapped enemies or mandatory hours of grinding.

## Full postgame menu
1. **Champions' Circuit** — A permanent, optional, repeatable bracket with four entry divisions (open singles, doubles, type-specialist, Champions exhibition). Rotate teams and player-chosen bracket size; bring back Rivals, noncorrupt Gym Leaders, Averon E4, Sinnoh leaders, Cynthia and visiting veterans. It is never the last narrative encounter.
2. **Frontier Gauntlet** — Multiple facilities: endurance of consecutive battles and limited heals; weather/field-condition rotation; doubles with flexible partners; species-restricted tower; expert puzzle battles. Each facility has clear item/healing restrictions. Keep every mode replayable after Red.
3. **Legendary expeditions** — All species on `data/legendary_quests.csv`, with time gates, old-route returns, Sinnoh mythology and ecology. Completed quest flags keep the Pokémon from respawning as endlessly catchable copies; players can revisit their places.
4. **Regional secrets** — A long optional Tideglass dive chain; deep Sunscar badlands; Crownspine's sealed crystal cavern; Ashfall deeper caldera; ancient observatory; high-level optional Sinnoh mountain paths.
5. **Personal follow-ups** — Renn's rematch, Mira's field guide, Pip's craft competition, a new museum wing for Tavi, Calder's retired-case cameo, and a select recovered corrupt official encounter. No endless conversation side quests.

## Red is the final narrative challenge
Reach a quiet summit after both Champions, region-wide field exploration milestones and one special mountain challenge; the player does NOT need to finish every repeatable Champions' Circuit bracket or catch all Pokémon. Sprinkle **at most two** unobtrusive references to a silent, extraordinary trainer across the *entire* adventure; never say 'Red', describe his cap in advance, or play his theme earlier. On summit: minimal or no dialogue, reveal Red at the beginning of battle, level-100 carefully curated iconic team with modern legal moves, formidable but beatable AI. Do not place another canonical 'true final trainer' after him. Post-Red facilities remain available for repeated play.

## Sinnoh map source due diligence
Possible reference/source: `https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion` and other Platinum-on-Emerald projects. These are **not proven turnkey drop-ins**. Inspect exact code, map coverage, asset provenance, commit/version alignment, licenses, unique IDs, NPC warp/flag collisions, music rights and required attribution. Build one Sinnoh exterior plus interior in the Averon engine before undertaking a mass merge. If import fails, reconstruct native maps by hand from geographical references while preserving the same playability requirements.
