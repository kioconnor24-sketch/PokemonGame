# Design table dictionary

These are DESIGN data, not engine data files. Codex should transform validated rows to the actual pinned engine structures with native events, flags and sprites. Never rename fields in upstream C based on guesses.

- `locations.csv`: `name` unique location; `category` design grouping; `biome`, `visual_identity`, `main_hook` are design notes; **`story_milestone` is the major associated event/completion flag, NOT a rule preventing entry to the location**. Actual arrival permissions are in `route_network.csv`.
- `route_network.csv`: unique `id`; `from` / `to` named hubs (undirected conceptual links); `environment` route tileset story; `unlock` minimum story/badge/field equipment condition; `purpose` exploration reason. Some links represent rail/ferry and must be implemented as interactable transports, not a continuous footpath. Duplicate endpoints may represent multiple different routes with different unlocks.
- `gyms.csv`: progression `number` 1–8; `level_cap_before_badge` tentative player maximum before defeating the named leader; exact battle teams need implementation and gameplay playtest.
- `level_curve.csv`: post-8-badge progress ceiling targets; not a combat EXP simulator or complete trainer roster.
- `habitat_examples.csv`: illustrative species for ecological clusters only, **not the finished regional encounter tables**.
- `legendary_quests.csv`: linked quest arcs and planned environmental triggers for official legendary/mythical Pokémon; must be expanded into individual persistent encounters, Pokédex/form coverage and actual capture rules.
- `gym_team_blueprints.csv`: candidate teams, counters and learning objectives; not yet audited against exact learnsets or levels in selected engine.
- `final_gauntlet_blueprints.csv`: exact order of ten proposed single-mon enemy operative fights, some named commanders have relatively lower-power Legendaries. Test this sequence for resource depletion and fair counterplay.

Averon world graph deliberately omits **Silverwatch Summit** from its local land travel edges because it is in the *planned Sinnoh* region. Codex must give it a proper Sinnoh map and connecting paths; this is an outstanding integration task, not a missing bridge in Averon.
