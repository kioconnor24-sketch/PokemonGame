# Pokémon Averon — level-curve research and balance gate

**Status: research benchmark, not an approved or implemented level-cap schedule.** Prepared October 15, 2026 following the user's direction to compare real Pokémon games, especially HeartGold and SoulSilver (HGSS). Do **not** treat older planned caps (Averon League 76; Sinnoh League 95) as final.

## Verified canonical-game examples

The numbers below are **highest-level opponent Pokémon** in the listed encounters, **not enforced player caps**. Official Pokémon games generally do not use Averon's hard badge-based level cap.

| Game | Milestone | Opponent ace level |
|---|---|---:|
| HGSS | Johto Gym 1, Falkner | 13 |
| HGSS | Johto Gym 8, Clair | 41 |
| HGSS | First Champion, Lance | 50 |
| HGSS | Kanto Gym 8, Blue | 60 |
| HGSS | Postgame Red | 88 |
| Platinum | First Champion, Cynthia | 62 |
| Black 2 / White 2 Normal Mode | First Champion, Iris | 59 |

Primary fact-checking references (trainer rosters and level data):
- https://pokemondb.net/heartgold-soulsilver/gymleaders-elitefour
- https://www.serebii.net/heartgoldsoulsilver/elitefour.shtml
- https://bulbapedia.bulbagarden.net/wiki/Red_(game)
- https://pokemondb.net/platinum/gymleaders-elitefour
- https://retrogameindex.com/games/pokemon-black-2-white-2/elite-four/

## Design implications and cautions

1. **Two-region structure:** The greatest value of HGSS is its division into first-region League, second-region badges, and a distant final Red showdown. Averon's former hard cap of 76 before the first League allocates much of the 1–100 scale too soon, before a *full* Sinnoh storyline.
2. **Not a carbon copy:** HGSS has a famously criticized experience economy. The second region often offers low-level wild Pokémon despite strong Gym Leaders. Do not reproduce that progression gap. See https://neonmajora.wordpress.com/2024/02/16/an-analysis-of-level-economy-in-pokemon-heartgold-and-soulsilver/ and community discussions, e.g. https://www.reddit.com/r/pokemon/comments/m5j0qz/ .
3. **Other benchmarks:** Platinum's single-region first Champion (ace level 62) and Black 2/White 2's first Champion (ace level 59 in Normal Mode) show that first championships vary; HGSS's ace level 50 is a reference, not a mandated exact cap.
4. **Different EXP rules:** Averon deliberately uses a **held-item Generation 5 EXP Share**, not automatic party-wide experience. The chosen engine's EXP formula and group curves must be confirmed and modeled using actual trainer and encounter data. Experience growth differs across species, and a level-based cap is not a measure of how much EXP exists. See https://bulbapedia.bulbagarden.net/wiki/Experience and https://bulbapedia.bulbagarden.net/wiki/Exp._Share .
5. **Player cap vs. opponent ace:** Don't conflate the game's hard badge cap with the level of a trainer's ace. First establish an intended difficulty relationship and test parties that start below the cap.
6. **Modern strategic difficulty:** Better move sets, team synergy, AI, items, Mega Evolution where narratively suitable, and battle format can increase difficulty without forcing early high levels.
7. **The Red endpoint:** Keep level **100 as the absolute maximum**, and the user wants the player's team to approach it near the end of the postgame. That does not automatically imply 100 must be the first obtainable level after completing a specific scripted flag. Exactly when the cap rises is still undecided and should be tested.

## Explicitly withdrawn assumptions

- Fixed old Averon Gym cap schedule: **15 / 23 / 31 / 39 / 47 / 55 / 62 / 69** — implemented in Codex's source but **not yet balanced/approved**.
- Old Averon League hard cap **76** — **unapproved; likely too high** for a two-region design and may need significant lowering.
- The attempted Sinnoh hard cap schedule **79 / 81 / 83 / 85 / 87 / 89 / 91 / 93; League 95; then 97 / 99 / 100** — **withdrawn**. These extra flags and cap entries have been removed from this contribution's engine branch. Codex's original configuration is left unchanged until a revised design has evidence behind it.

## Before selecting actual new numbers

A gameplay/economy balance pass must provide:
- A stage-by-stage map/route/trainer inventory: available opponent party count, levels, species/base EXP values and non-repeatable sources.
- Every intended major fight from opening through Averon League and full Sinnoh; corresponding enemy **ace levels**, not just generic numeric caps.
- The player's ordinary play variants: party size 3, 4 and 6; optional trainer completion around 65–80%, all trainers, and a lower-engagement run.
- Species experience groups (fast / medium / slow / erratic / fluctuating), level distribution of caught Pokémon, EXP Share item availability and assignment, trainer rewards, lucky eggs, and actual mechanics from the pinned engine.
- Estimated level ranges for those playthroughs *without grinding* and with the existing level caps, including the amount of lost/wasted EXP at the cap.
- A full two-region + late postgame progression that reaches ~100 organically, without the HGSS low-level-wild versus high-level-boss mismatch.
- Gym 1 and later battles evaluated in real emulator tests; adjust major trainer lineups, encounter levels and distribution to avoid excessive forced grinding.

**Acceptance rule:** Until this evidence exists, leave post-Averon cap implementation uncommitted. Existing hardcoded values on Codex's branch are **provisional implementation**, not approved game balance. New cap designs need a clear before/after table against the actual game data and user approval before rewriting established native tables.
