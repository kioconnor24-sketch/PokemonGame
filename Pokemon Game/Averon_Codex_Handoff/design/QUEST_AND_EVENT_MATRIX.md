# Map and event progression matrix

> **2026-10-17 PROVISIONAL EVENT OVERRIDE:** Q04/Q13/Q16/Q23/Q25 and `RENN_RIGGING_EVIDENCE` entries below belong to the older October 14 plot blueprint, NOT immutable implemented events. The preferred new rival Gym loss is **genuine**, with player suspicion of manipulation, villain confirmation and independent proof still under discussion; avoid implementing rigging flags/revelation until decided. The leader's motive must predate Threshold, while controlling collars and a possible Plate/Arceus-led antagonist continuation into Sinnoh are being explored. See [full narrative working dossier](STORY_DEVELOPMENT_WORKING_DOSSIER_20261017.md). Existing technical and already implemented flags remain unchanged by this notice; don't claim old scripts are rewritten.


The main quest is *intermittent*. Not all routes have an organization encounter. Every step below needs its own safe save flag, reset-proof script entry and rollback rules if whiteout occurs.

| Key | Approx. point | Player activity | NPC/story consequence | Guard / test |
|---|---|---|---|---|
| Q00 | Saltmere | Visit household errand first; choose to accept assigned starter | Renn and Mira receive appropriate remaining Pokémon | First-house var set exactly once; visiting other houses cannot overwrite; bag/party full cases |
| Q01 | Windrow/Alderfield | Catch Pokémon, orchard festival, Gym 1 | Fun trainer intro; no villain foreshadowing | Gym badge/level cap persists on load |
| Q02 | Breakwater | Lighthouse Gym, fishing derby | Kit's petty stolen cart; separate offscreen blueprint theft | Cart event unrelated to machine; no forced mystery text |
| Q03 | Coralside/Mossveil | Beach and forest, Ghost Gym, side quests | Tavi habitat survey; Mira visits ruins unrelated to villain | Playable return shortcut, independent quest flags |
| Q04 | Rillfall/Slateford | Rescue miners from Aster's grunts; Gym 4 | Dorian helps player, secretly benefits; Renn fails Gym challenges | Renn can fail only within NPC script, player can win normal legal badge match |
| Q05 | Sunscar | Bazaar, ancient cistern, Ground Gym 5 | Nadia awards badge then starts hostile two-Pokémon no-heal fight | Whiteout keeps badge and proceeds; no infinite retry |
| Q06 | Sunscar/Vesper | Independently find mismatched government records | Calder, Tavi and player compare clues; research room blueprints recovered | Player gets discovery credit, detective has imperfect hypotheses |
| Q07 | Pre-Gym 6 | Ordinary mountaineering and lodge quests | Renn reveals Vantage allegiance at restricted checkpoint; forced loss | Nuzlocke immunity, no money loss, safe warp to Pokémon Center |
| Q08 | Palehaven | Gym 6 + lake/animal tracking | Community volunteers introduced as allies | No second sinister reveal |
| Q09 | Crownspine approach | Summit trails and Gym 7 | Scattered appointments and political movements | Gym flow continues despite coup flags |
| Q10 | Around Gym 7 | Short playable coup and announcement | Vantage takes government; officials reveal membership | Shops Centers warps intact across state changes |
| Q11 | Vesper | Brief reaction window #1 | New guards/posters, restored train, mixed NPC reactions | Exactly one mandatory compact window; optional dialogue expands |
| Q12 | Main/optional research annex | Obtain record matching stolen Threshold blueprints | Dr. Quill recognizes them; player finds decisive evidence | Clue isn't automatically delivered by Calder |
| Q13 | Before Gym 8 | Uncover Dorian's private illegal counterteam records | Renn learns of rigged Gym matches before climax; not instantly redeemed | Evidence flag saved; RENN_REACTION separate event |
| Q14 | Gullhaven | Brief reaction window #2 and ferry | Human-built engines offer benefits, some costs | Short; no lengthy political interlude |
| Q15 | Ashfall | Gym 8, volcanic islands, spa and geothermal sidequests | Organization rushes modified Threshold activation | Region still fun, island identity distinct |
| Q16 | Truth reveal | Examine secure research and original experiment | Pokémon test subject killed by concentrated dimensional feedback, Zygarde emerged; boss witnessed | All three motive layers explicitly distinct; explanation concise |
| Q17 | Coalition staging | Choose/cross safe entry route; allies split tasks | Calder coordinates, other characters take initiatives | No unlimited NPC escort problems |
| Q18 | Threshold corridor | Ten one-Pokémon consecutive operative battles | Reuses recognizable grunts/captains | HP persists; checkpoint; progress idempotent |
| Q19 | Corridor landing | Ally heals full party | Later Gym rematches enabled | The heal cannot be farmed or replayed to reset boss state |
| Q20 | Core facility | Upgraded Dorian then Nadia rematches; boss first phase | Betrayals paid off through gameplay | Teams legal, post-heal difficulty fair, save policy tested |
| Q21 | Device incident | Damage/overflow after boss fourth Pokémon or scripted 4-Pokémon phase | Rift sucks player + Vale in | No half-battle state leaks; party saved safely |
| Q22 | Alternate dimension | 15–30 minute 2D dungeon, puzzles | No second world drama; survival because ambient energy ≠ lethal pulse | Warps and escape routes avoid trapping player |
| Q23 | Final Vale battle | Full team battle | Weaponized activation stopped; Giratina enables return | Post-loss safe checkpoint; game remains winnable |
| Q24 | Averon League | Victory Isle Elite Four and Ansel | Ordinary Champion conclusion, light fallout | Correct 8 badges, cap <=76 |
| Q25 | Sinnoh | Full second region with Gyms and Cynthia | Renn's calmer personal follow-up | All Sinnoh towns reachable and scripted |
| Q26 | Postgame | Legendary arcs, circuit, gauntlets, secrets | Characters pursue independent interests | No fully optional content becomes hidden required gate for Red |
| Q27 | Summit | Red revealed on arrival | Final canonical trainer boss | No subsequent story trainer stronger than Red |

## Other recurring but NONPLOT events
- Orchard berry pie contest (Windrow)
- Breakwater annual fishing derby
- Tidepool race and lost parasol (Coralside)
- Mossveil lantern-mask theater and misplaced tickets
- Rillfall scenic photograph challenge
- Slateford mineral-museum rock identification
- Juniper campfire and a Hoothoot eating stored snacks
- Sunscar bazaar bargaining, fossils and water-clock repair
- Vesper department-store stamp collection, cafe courier, rooftop scenic challenge
- Palehaven ice-carving and wildlife volunteer survey
- Crownspine stargazing night and mountain trail badge (not League badge)
- Gullhaven sailing regatta
- Ashfall hot-spring water pressure mystery and volcanic-glass carving
- Sinnoh berry/poffin and archaeological sidequests not connected to Vantage

## Visual flags that must be distinct
`COUP_COMPLETE` controls banners/uniform variants, not world deletion; `POST_COUP_REACTION_1` and `POST_COUP_REACTION_2` are separate. `BLUEPRINT_FOUND`, `BLUEPRINT_IDENTIFIED`, `THRESHOLD_TRUTH` are sequentially distinct. `RENN_RIGGING_EVIDENCE` and `RENN_RESPONSE` are distinct. Gym 5 `BADGE_5` and `NADIA_AMBUSH_DONE` separate. Boss phase `VALE_PHASE1_DONE`, `RIFT_ENTERED`, `VALE_FINAL_DEFEATED`, `DIMENSION_EXITED` separate. Finale and legendary flags must all survive save/reload, cutscene interruption, loss, escape and reentry.
