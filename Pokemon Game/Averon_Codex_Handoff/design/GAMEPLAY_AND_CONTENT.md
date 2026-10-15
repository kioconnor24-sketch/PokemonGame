# Averon — World Systems, Balance & Content Rules

## The actual game to create
Pokémon Averon, based on `rh-hideout/pokeemerald-expansion`, compiled into a REAL GBA `.gba` ROM compatible with Delta on iOS after testing. Original world: Averon. Full second region: Sinnoh. Include latest *supported and verified* Gen IX species/moves/abilities/form data, then audit against a frozen National Dex manifest. Do not silently invent unimplemented forms. GBA visual style; high-quality new tiles and authentic, credited Pokémon resources where permitted. Use normal Pokémon gameplay and a more intricate but restrained original story.

## Gameplay rules
- One fixed challenging difficulty. Permanent forced SET style (no free opposing send-out swap prompt), one standard mode only.
- Gym + story-based hard level caps, max 100. No overleveling by candy, daycare, boosted EXP, traded Pokémon, or event gifts; test all possible bypasses. Preserve experience progress safely under cap.
- **Original Gen 5 held-item EXP Share**; NOT universal party EXP. Modern EXP yield tuning to avoid grinding for average party of six.
- Smart opposing teams with role synergy, switching awareness, items, EV/IV/nature tuning, move coverage, but no omniscient reading of player's button inputs.
- Physical/special split, Fairy type, modern Gen 9 typings, moves, abilities, evolutions, Mega Evolutions, regional forms. Do not include Z-Moves, Dynamax, Gigantamax or Terastallization. Leave Primal Reversion/Ultra Burst disabled by default because only Mega Evolution was selected; revisit explicitly if needed for completion.
- Following Pokémon where field animations support it; safe hiding on bikes, Surf, cutscenes and tiles that cannot fit follower; no crashes if sprite absent.
- Field traversal without occupying move slots: earned field toolkit licenses for Cut, Surf, Waterfall, Strength, Rock Smash, Dive, etc. Some moves may still be learned in battles, but none is mandatory for traversal. Avoid overgating every optional cave.
- Optional Nuzlocke toggle at new-game start independent of difficulty (first *eligible* encounter per named zone, fainted Pokémon unusable, separate rules for gifts, static Pokémon, species clause and scripted losses). Persistent encounter log; accessibility setting for permanent-death confirmation. A scripted unwinnable Renn battle is excluded from Nuzlocke permadeath and records no losses.
- No multiplayer dependency for main story; GBA link trading/battling on other supported environments can be a separate compatibility experiment. **Do not promise story co-op or GBA links in Delta**.
- Challenge remains fair: opponents do not have inaccessible mechanics; opponent Pokémon that are genuinely above player's cap must be flagged as special story-only events.

## Starter algorithm
Starter trio design selection: **Snivy, Fennekin, Piplup** (Grass / Fire / Water from three generations). House first helped: greenhouse → Snivy, workshop → Fennekin, harbor → Piplup; first meaningful visit stored. Rival receives typing advantage, second rival the remaining Pokémon. If the resulting individual starter breaks pacing or type balance during prototype, adjust only with documented rationale; do NOT casually generate random replacements. Show confirmation to player before irrevocable handoff; choices are indirect until then.

## Level curve and EXP acceptance
The cap BEFORE each Averon badge: Gym1 15; Gym2 23; Gym3 31; Gym4 39; Gym5 47; Gym6 55; Gym7 62; Gym8 69. Post-Gym8 final assault cap 72, regional League cap 76. Sinnoh Gym caps 79/81/83/85/87/89/91/93, Cynthia/second League 95, then optional postgame 97–99, Red 100.

These are **initial target ceilings, not implemented mechanics**. The average naturally trained party should be near each cap without grinding if player fights ~65–80% of visible trainers, uses reasonable catches, and evenly distributes battle appearances. Player fighting all optional trainers should not trivialize bosses or cause forced experience waste. Player skipping some trainers should not be forced into hours of wild grinding. Simulate EXP yields for parties of 3, 4, 6 and diverse growth curves before freezing final trainer levels. If cap is hit, do not permit EXP overflow, negative experience or permanent experience loss causing mid-game underleveling.

Averon League victory does not end the level progression: Sinnoh and postgame must carry player naturally toward 100. Late battles become more strategic instead of simply reaching levels above 100. Red uses carefully curated level-100 team; player can reasonably be near 100 by then without grinding to unlock the confrontation.

## Pokédex and ecology
- Main adventure: curated approx. 420–480 species (working target 450), balanced by habitat and evolution access. Exact number subject to spreadsheet audit, not a promise all fit immediately.
- Postgame + Sinnoh + breeding/fossils/other quests eventually make **every species through Generation IX obtainable**, including trade evolution alternatives for Delta single-player, all required form items, and special case evolutions. The target is a complete National Dex manifest audited against the selected expansion revision.
- Encounter systems: geography first, then time of day/season if support is stable, rare habitat and water/fishing/diving tables. Do not dump unrelated species into all routes to meet coverage metrics.
- Birds/water Pokémon frequent on coast, water-based species in Rillfall and reefs, mixed woodlands west, Rock/Ground/Ghost/desert species east, Alpine/Ice/Dragon northern, Fire/Rock volcanic islands. Cities get limited urban encounter strips, not random dungeons inside every alley.
- Legendary ownership by villains: only a few commanders, such as Registeel, Raikou, Silvally; player can obtain them legitimately later by retrieval/release/recovery quests. Do not give regular operatives Arceus, Palkia, Kyogre, Rayquaza, etc.
- Legendary quests should meaningfully use placed geography, returning to early routes, persistent key items (e.g. department-store key to Jirachi observatory), seals, weather, or quests. No all-legendaries-in-one-room solution. See `legendary_quests.csv`.
- Evolution/forms unsupported by current engine revision must be tested or implemented honestly; never mark species complete because sprite exists.

## Region content and travel
- Exactly eight Averon Gyms in route order and separate Victory Isle League; Vesper is capital without Gym.
- Western lowlands, coastal cliffs, rainforest/waterfalls, mountain foothills, eastern desert/canyons, northern snow/alpine mountains Gyms 6–7, southern volcanic archipelago Gym 8.
- ~24 named primary hubs/dungeons plus ~36 route connections in design dataset; as implemented, break these into numerous playable GBA maps/sections to keep performance and scene quality. The target is 30–40 outdoor route segments, with vertical and indoor maps separately. The route graph is not a contiguous gigantic tile map.
- Main path must be signposted but not railroaded: optional wildlife areas, loops, return shortcuts, water routes, secrets and a transport network. Every major settlement has a distinct tileset identity or architecture treatment; test sprite palette budgets.
- Two major post-coup presentation sequences, not a prolonged occupation simulator; world remains friendly to play. Shops, Pokémon Centers and normal wandering stay operational except for individual story locks.
- Sinnoh: full coherent second region using an audited, permission-compatible Sinnoh Emerald map base where useful. Preserve recognizable geography (Twinleaf, Sandgem, Jubilife, Oreburgh, Floaroma, Eterna, Hearthome, Solaceon, Veilstone, Pastoria, Canalave, Snowpoint, Sunyshore, Mt. Coronet, Victory Road, Battle Zone) while not assuming source project is complete or plug-and-play. 8 full Gyms and Cynthia/League.
- Big optional final phase: Champions' Circuit (repeatable, many notable trainers), gauntlets, varied rematches, newly unlocked ocean and mountain locations, legendary & mythical side quests, personal character follow-ups, secrets, and final Red encounter. Champions' Circuit is never the final canonical battle.

## Side-content design (strongly unrelated to plot)
Western orchard berry harvest and cooking contest; Breakwater fishing derby and lighthouse maintenance; Mossveil mask parade and lost Spinarak family; Rillfall raft crossing and scenic photo challenge; Slateford mineral trading and minecart puzzle; Sunscar market scavenger hunt, fossil collection and water-clock repair; Vesper café requests, battle arcade and rooftop courier; Palehaven snowy wildlife survey; Crownspine climbing courses; Gullhaven sailing regatta; Ashfall hot-spring hotel and volcanic glass crafting; Tideglass diving/reef ecology. Each is compact, gives meaningful rewards, and avoids forced villain hints.

## Battle difficulty design
- Early gyms teach readable concepts; later Gyms test pivots, status management, role synergy, weather, hazards and intelligent switching.
- Enemy AI must not respond to hidden input selection with impossible knowledge; set item/ability information limits.
- Non-gym bosses (rivals, ace trainers, team lieutenants) built deliberately with defined identities; avoid endless 6-mon filler fights.
- Ten-hostile-operative gauntlet each uses one Pokémon; party HP persists. After gauntlet ally heals. Then two 4–6-Pokémon corrupt Gym Leader rematches with upgraded tactics. Then first-phase boss or rival, dimensional entry, final boss in dimension. Provide rest/saves where tested necessary to avoid slog.
- Unwinnable Renn fight: robust forced-loss script, party restored at Center, Nuzlocke exception, no money penalty and no rematch obligation.
- Starter/legendary power spike management: do not provide major overpowered species early just because data exists; every species eventually obtainable.
- Gym 5 ambush: badge granted and retained even if player loses; no required healing gap; strategic encounter short enough to be survivable under expected remaining resources and scripted failure safe.

## Audio and sprite asset rules
- Friend-photo-based original trainer sprites: request authorized friend images only when artwork begins, preserve recognizable features; generate consistent 64x64/overworld sheets then quantize to the game palette and validate in game. No pixel-art placeholders shipped as finished graphics.
- Credit and permission ledger for borrowed community overworlds/battle sprites/tilesets/arrangements. If Nintendo-owned music cannot be licensed, use an original theme with recognizable intensity, never claim the exact copyrighted Cynthia composition is safe to distribute by default.
- Rely on full Emerald Expansion sprites only when revision confirms they are present and legal for planned distribution. Missing animation/moves/form effects tracked explicitly.

## Content gating and save consistency
For every warp, badge, ferry, shrine, cutscene, and legendary encounter: unique flags, reentry guard, safe spawn and rollback instructions. Hidden paths should have visible design hints without quest-marker overuse. Save after major story beats. Pokémon Center healing never unwittingly reactivates an already cleared boss. All party sizes (1–6) and edge-case items must be tested.
