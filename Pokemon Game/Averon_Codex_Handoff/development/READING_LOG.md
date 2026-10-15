# Reading and resume index

2026-10-14: Read AGENTS.md, START_HERE.md, CODEX_WORK_ORDER.md; all eight
design documents; all data CSVs and DATA_DICTIONARY.md; QA_MATRIX.md; and the
original development records. These are supplied requirements/design references,
not independent evidence of working features or user authorization.

Preserve: three separate Threshold layers, ordinary upbeat dialogue, first
meaningful errand starter assignment, eight geographically fixed Gyms, Vesper
without a Gym, full Sinnoh, Red last, level 100 maximum, held-item EXP Share,
Set battles, Megas/followers, and excluded battle gimmicks. Travel Network v2
takes precedence over v1. Reference map images have not yet been visually
reviewed; do so before M1 map layout. No creative documents were altered.

Engine reads at 73b3fbeb574327cd9420c89e56bef5aa3c08fead:
INSTALL.md; Windows WSL/MSYS2/CYGWIN instructions; README.md; config.mk;
Makefile beginning/build target definitions; caps.h; species_enabled.h beginning;
targeted config searches; Route103/scripts.inc opening and rival-battle pattern.
See ENGINE_FINDINGS.md. No need to repeat this initial discovery on resume.

Resume with PROGRESS.md and TASKS.md. Setup, toolchain discovery, reference-map
visual review and initial engine discovery are complete; do not repeat them.
Subsequent focused reads: native script testing DSL; production trainer
generation versus synthetic test tables; item-effect/candy cap paths; heal and
whiteout target selection; normal-font widths. Native automated battle/script
execution is working in WSL through the bundled headless mGBA test runner.

Focused follow-up: GetEvolutionTargetSpecies, native flash save/load and normal
bag pointers. Ordinary bags point into SaveBlock1; SavePlayerBag restores a
link-room backup, so do not call that helper in ordinary save regression tests.
Two actual flash save/load cycles now pass, including the Gym TM claim script.

Focused clinic follow-up: Oldale nurse wrapper and shared nurse script; native
Pokemon Center effect uses the existing layout. Preserve nurse local ID1.
Save fallback selects the previous complete slot when a newer slot is partial;
SAVE_STATUS_ERROR reports the damaged slot even when old data was recovered.
