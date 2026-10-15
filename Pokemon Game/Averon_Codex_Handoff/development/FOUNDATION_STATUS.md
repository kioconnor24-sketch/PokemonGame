# Pokémon Averon — engineering foundation handoff

Snapshot: 15 October 2026. This is a verified-status handoff, **not** a statement that all 30 objectives are complete.

## Source and development rules

- The active engine is Emerald Expansion, pinned upstream to 73b3fbeb574327cd9420c89e56bef5aa3c08fead, in the repository's Pokemon Game/engine folder.
- Codex owns codex/first-gym-verification (PR #1), which has built and tested an early-game slice. Its first-Gym full walkthrough and Delta acceptance are still pending.
- ChatGPT PR #2 adds species and wild/evolution-source audits. PR #3 adds two early quests (authored, not yet game-tested). PR #4 provides graphics/source and asset-file audits. PR #5 provides the engine-readiness and native-cap verification. PR #6 gives real trainer-party and growth-curve information. PR #7 adds Linking Cord alternatives for the last two trade-only source evolution routes.
- PR #5 and PRs #6–#7 target Codex's Gym-1 branch; PRs #2–#4 target main. Do **not** merge all PRs blindly. Integrate dependencies in the correct order after verified native builds and conflict resolution.
- The numeric first-region caps 15/23/31/39/47/55/62/69, and League 76, are **not approved balance targets**. The user wants comparisons to HeartGold/SoulSilver and other official games before new caps are chosen. Do not bake those guessed later-region numbers into new scripts.

## Objective-by-objective implementation status

| # | Objective | Present evidence | Still needed |
|---:|---|---|---|
| 1 | Audit Emerald Expansion | Initial source inventory/ENGINE_FINDINGS and PR #5 | Verify every critical runtime feature |
| 2 | Lock essential configs | PR #5 checks 23 source settings | Confirm all forbidden battle mechanisms inaccessible |
| 3 | Generations I–IX | Nine flags enabled; 1,365 species/form initializers scanned | Full support/obtainability manifest and runtime checks |
| 4 | Battle mechanics | Existing expansion and Codex native fixtures | Real player and AI interactions throughout game |
| 5 | Mega Evolution | Config and early native fixtures | Every expected legal Mega, graphics, interaction |
| 6 | Exclude other gimmicks | Dynamax and Tera gating inspected; Primal/Ultra disabled | Review item/menu/debug access; other form data still compiled |
| 7 | Held-item EXP Share | Native engine config and Codex tests | Full playthrough, all party sizes and edge cases |
| 8 | Level caps | Codex C implementation and host-compiled verification | Balanced full-region curve and natural EXP economy |
| 9 | Forced Set | Codex early native fixtures | Full trainer/boss/doubles acceptance |
| 10 | Smarter trainers | Early Elio logic authored | Tune and review entire game's opponents |
| 11 | Following Pokémon | Enabled; early native evidence; PR #4 asset paths | Form/animation/collision/field transitions across all species |
| 12 | Save reliability | Codex flash test evidence | Menu/whiteout/save/reload throughout 2 regions |
| 13 | National Dex manifest | PR #2 inventories; PR #4 art references | Exhaustive normalized dex + forms + obtainable paths |
| 14 | Graphics completeness | PR #4 checks asset files and followers | Match source symbols, actual image display and licensing |
| 15 | Solo evolutions | PR #7 adds Karrablast and Shelmet alternatives | Make Linking Cord and other items obtainable; native use tests |
| 16 | Wild encounter system | Expansion core and early coastal preview | Ecological tables for remaining Averon/Sinnoh |
| 17 | Move-slot-free traversal | Existing field move unlocks use badges | Implement safe licenses for Cut, Surf, Strength, etc. |
| 18 | Quest framework | PR #3 guarded two quests | Runtime script validation, reusable scenes and flag lifecycle |
| 19 | Legendary infrastructure | Existing battle/event primitives | One-time capture/failed attempt/retry and 9-gen quests |
| 20 | Scripted battles | Some early battle/whiteout guards | Renn forced defeat, no-penalty recovery, boss and operative relay |
| 21 | Save flags and vars | PR #5 reserved names and collision audit | Registry integration with all future quest flags |
| 22 | Averon–Sinnoh transition | Design plans only | Entire region, 8 gyms, party/save travel system |
| 23 | Map/script templates | Codex already authors native maps by Python | Reusable stable design kit and reviewed tilesets |
| 24 | Resource budgets | Clean 32 MiB build: ROM 79.64%, EWRAM 86.37%, IWRAM 86.60% | Recheck when additional maps/forms/content arrive; graphics palette limits separately |
| 25 | Automated validation | GitHub Actions PRs #4–#7; PR #5 clean ARM compilation passing; Codex native tests | Permanent integrated native emulator and Delta acceptance gates |
| 26 | Species attainability | PR #2 static audit | Gifts, quests, item use, Sinnoh and capture walkthroughs |
| 27 | Level balance | PR #6 includes 10 existing Averon trainer definitions / 17 Pokémon | 2-region density, actual EXP income and team-size simulations |
| 28 | Licenses and assets | Design-led asset ledger exists | Legal attribution and replaced/commissioned assets as needed |
| 29 | Branch integration | Pull requests #1–#7 separated | Merge only after parent changes validated |
| 30 | Codex handoff | This handoff and original design package | Codex integration review after new code lands |

## Tests and acceptance tiers

1. SOURCE: parsed C config, species, trainer, flags, assets and evolutions. Never call this a playable game test.
2. HOST-NATIVE: compiled actual C functions from src/caps.c and exercised them with mocked game flags; verifies source behavior, not real gameplay.
3. GAME-BUILT: actual pokeemerald.gba compiled from clean checkout and recorded checksum/size.
4. EMULATOR-TESTED: ROM actually run in mGBA, test summary and/or real gameplay paths collected.
5. DELTA-ACCEPTED: user-run iPhone test confirms native saving, maps, followers and normal battle flow.

The whole game must pass all five tiers, where relevant. No item, species or trainer is obtainable just because its source definition exists.

## Current build reproducibility issue

GitHub clean checkout initially lacked tools/compresSmol (the directory was ignored by .gitignore), although the makefile requires it. PR #5 restores that folder from the exact pinned upstream source. **Clean native ARM compilation now passed**, demonstrated by GitHub Actions run 38689686458 on October 15, 2026. It produced a 32 MiB .gba, SHA-256 75893cd9ae3a19297e9a5958cffdf4646a07a3d258c9b787aa3b254015c8cba2. Linker budget in that tested build: ROM 26,722,880 B / 32 MiB = 79.64%; EWRAM 226,416 B / 256 KiB = 86.37%; IWRAM 28,376 B / 32 KiB = 86.60%. **No emulator or Delta acceptance is inferred from compilation.** CI uploads the text build log but never the ROM.

## Immediate integration steps

1. Inspect the latest PR #1 head and Codex's TASKS.md before applying any changes to the live Gym 1 branch.
2. Review the difference from PR #5 and replay the essential checks plus clean native build.
3. Review PR #7's Generation V Linking Cord changes and confirm they compile and evolve normally in game. Avoid putting the Linking Cord in the early Gym 1 shop without balancing its acquisition.
4. Keep PR #6's reported Ace levels separate from a final level-cap proposal. Only a handful of Averon trainer encounters exist; full late-game trainer/EXP evidence cannot yet be gathered.
5. Continue Codex's real playable route/town content while adding shared infrastructure from this work in small mergeable increments.

**Do not stop development merely because the complete world is not finished, but do not claim unfinished features are completed either.**
