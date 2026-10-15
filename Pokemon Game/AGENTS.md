# Pokémon Averon — project operating requirements

First read repository-root `AGENTS.md`, `Averon_Codex_Handoff/development/WORKFLOW.md`, and `development/TASKS.md`; fetch live GitHub. The old M0–M2 work order, WSL/Windows setup paths, and past task ownership statements are historical. Do not rerun completed setup.

Game source: Pokémon Emerald Expansion in `engine/`, targeting real, saveable `.gba` and separate owner-tested Delta iOS playthrough. The user designs Averon's final map, towns/routes, exact Gym progression and numerical level caps. Keep Gym 1 and current gameplay intact. For backend mechanics awaiting a region map, use tiny developer fixtures. Averon plus full second Sinnoh region, Red last canonical opponent, cheerful traditional adventure with selective late conspiracy story.

Locked mechanics: level 100 maximum, held-item Gen V EXP Share, forced Set, modern physical/special split, Fairy, Megas, following Pokémon, eventual solo Pokémon availability. No Z-Moves, Dynamax, Terastallization, Primal Reversion, Ultra Burst, or unapproved first-League level 76. Optional Nuzlocke paused. Do not import unlicensed fan-hack assets.

Codex's live field-license source belongs to PR #10 while open. Before editing global event scripts, save flags, species, field moves or follower code, compare open PR changed files and coordinate. Work on scoped branches; push tests/commits, then a PR HANDOFF comment. Distinguish SOURCE/BUILD/NATIVE-TESTED/EMULATOR-TESTED/DELTA-VERIFIED. Do not downgrade a failed build to 'skipped'. No complete ROMs or save files in public Git.
