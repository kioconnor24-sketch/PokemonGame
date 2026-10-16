# Pokémon Averon — dependency roadmap (engineering-first)

**Status:** stable navigation for *dependencies and gates*, not a live issue tracker or permission to begin all stages. Live work and source SHAs are in [open PRs](https://github.com/kioconnor24-sketch/PokemonGame/pulls), claims in [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15), [active assignments #24](https://github.com/kioconnor24-sketch/PokemonGame/issues/24), and [QA #23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23). See [TASKS.md](TASKS.md) for the current queue.

## Stage gates (review current GitHub before claiming a stage)

| Stage | Owner / entry | Required outcome | Current gate at writing (2026-10-15) |
| --- | --- | --- | --- |
| Integrated opening, first Gym and field licenses | Previously merged to `main` | Preserve working baseline, correct persistent flags and menus | Source integrated, but specific natural emulator interactions may still be unverified |
| QUEST | Codex [PR #14](https://github.com/kioconnor24-sketch/PokemonGame/pull/14) + independent QA | Reliable event prerequisites, full Bag/party retry, save/load, graphical event acceptance | Draft; CI native 49/49 verified, Q1–Q5 interactive acceptance outstanding |
| SCRIPTED-BATTLE | Claude [PR #25](https://github.com/kioconnor24-sketch/PokemonGame/pull/25) | Reusable forced loss, chain damage, ambush semantics, safe recover/flag cleanup | Draft primitives, integration/shared flag/window pending |
| TWO-REGION mechanics | Codex, experimental `codex/two-region-groundwork` | Region identity, 8+8 badges, Fly/heal/whiteout and persistence with current engine | Symbolic/new-file-only badge/region groundwork; no production map work authorized |
| LEGEND and verified mechanics gaps | Next independent claim, usually Claude when free | Generic encounter state/eligibility/save robustness and targeted battle/evolution fixes | Future file-disjoint code; no canon species/legend sites |
| Shared-feature integration | A coordinated owner when prerequisite PRs merge | Source ABI, flag safety, save migration, actual GBA builds and native tests | Do not assume two green independent PRs integrate without regression |
| Playable new districts, Averon Gyms 2–8, League | **Owner approval required** | Approved geography, NPCs, battles, routes, progression, QA | **FROZEN**: no new map files, routes, story scenes or encounter placements |
| Full Sinnoh, major story, legendary quests, postgame | **Owner approval required** | Approved production designs and full playable tested journey | **FROZEN**: backend contracts may be developed without map/story data |
| Patch/Delta release | Integrator and owner | Reproducible build, non-ROM distribution, complete gameplay/compatibility and actual Delta owner test | Future; cannot claim release-ready from compile/native checks |

## Technical work allowed during the map/story freeze

Finish claimed PRs; develop approved generic engine interfaces using **synthetic in-memory identifiers and existing unmodified maps**; repair verified native gameplay/engine defects; test saves and regression coverage; classify build warnings; improve source/build reliability without modifying other agents' files. No map JSON/layouts, production routes, terrain, story/legendary placements, final trainer tables, art, or numerical level curve.

## Dependencies and shared-source access

- QUEST changes to event registers/flags must be integrated before Claude takes an explicit scripted-battle shared-file handoff.
- Region/save/heal/badges and battle no-whiteout flag/registries are serialized via Issue #15, not edited concurrently.
- QA graphical tests need actual frame/input/ROM provenance; a CI native test is not a rendered acceptance.
- Never force the current work to wait just for a future owner map or story decision; work on other **unclaimed and truly disjoint** approved technical tasks if available.
- No map generation, even temporary fixtures, without explicit owner authorization. Use symbolic numeric/map identifiers instead.

The detailed **conditional** future candidates remain in [Issue #26](https://github.com/kioconnor24-sketch/PokemonGame/issues/26); their production-content rows are not approved work until owner releases the freeze.

## Release evidence vocabulary

`DEFINED` → `SOURCE` → `BUILD` → `NATIVE-TESTED` → `EMULATOR-TESTED` (specified interactions) → `DELTA-VERIFIED` (owner iOS) — these are *different proofs*, not automatic sequential guarantees. Report exact SHA and test counts; never infer a later state from an earlier one.
