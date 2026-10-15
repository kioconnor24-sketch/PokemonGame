# Source research for Codex — links verified on 2026-10-14

**Current/public documentation, NOT proof that the sources have been cloned, built or merged into Averon.** Pin actual source revisions before using any advice.

| Tool / source | Link | Verified relevance | Caution |
|---|---|---|---|
| Pokémon Emerald Expansion | https://github.com/rh-hideout/pokeemerald-expansion | GBA source-level ROM hack framework with battle/data systems | Not a playable custom Averon game on its own; build and test |
| Features | https://github.com/rh-hideout/pokeemerald-expansion/blob/master/FEATURES.md | Modern moves, type data, Mega Evolution, AI, level caps and follower configuration | Feature list is a catalog, not a tested combined game |
| Hard cap configuration | https://github.com/rh-hideout/pokeemerald-expansion/blob/master/include/config/caps.h | Supports `B_EXP_CAP_TYPE`, `EXP_CAP_HARD`, flag/variable caps and `B_RARE_CANDY_CAP` | Confirm edge cases on actual pinned commit |
| AI flags documentation | https://github.com/rh-hideout/pokeemerald-expansion/blob/master/docs/tutorials/ai_flags.md | Trainer AI customization | Tactical fairness and performance need in-emulator QA |
| Pokémon/follower tutorial | https://github.com/rh-hideout/pokeemerald-expansion/blob/master/docs/tutorials/how_to_new_pokemon.md | Species/sprite and follower species configuration reference | Not proof all Gen IX visual frames work out-of-box |
| Installation | https://github.com/rh-hideout/pokeemerald-expansion/blob/master/docs/install/windows/WSL.md | WSL/toolchain guidance | Follow OS-appropriate instructions from the pinned revision |
| Porymap | https://github.com/huderlem/porymap | Native map editor for Gen 3 decomp projects | Requires compatible engine data/maps |
| Porymap region maps | https://github.com/huderlem/porymap/blob/master/docsrc/manual/region-map-editor.rst | Supports multiple region maps | Building two full regions remains a large integration project |
| Sinnoh expansion fork | https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion | Candidate reference for an Emerald-based Sinnoh | Audit actual completeness, copyright and license before import |
| Delta import formats | https://faq.deltaemulator.com/getting-started/importing-games | Delta accepts `.gba` files | A correct extension does not mean a ROM boots |

## Explicit corrections to avoid
- Don't make a Nintendo DS `.nds` file: the selected engine/output is **`.gba`**.
- Do not say a full Gen IX dex is 'implemented' until each species, evolution/form, held items, move effects, front/back icon/follower and accessibility are verified.
- Never change maximum level over 100: the user explicitly chose **100**.
- No third-party or official music/sprites shipped without understanding their license; GitHub access is not license permission.
- Sinnoh is a second complete region, not a placeholder fast-travel menu.
- Do not build all maps or full script with fake code symbols. Validate a tiny slice in a real emulator first.
