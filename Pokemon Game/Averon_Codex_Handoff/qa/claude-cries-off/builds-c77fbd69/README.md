# Artifacts built from c77fbd69 (#117 merged with main 43a95f85), this host

Builds were incremental after the merge (only union_room changed): make -j16 RELEASE=1 CRIES=off|on (logs in this folder).
Native: make -j12 CRIES=off|on check TESTS="Averon cry safety" (headless) and mgba-rom-test-hydra on a copy of the unpatched pokeemerald-cries-*-test.elf (non-headless).

```
06e3e40a9a7ff49c372166448333b4337b466c29f19d12e2b176ca90c31226bd  pokeemerald-cries-off-release.gba
32531a987b8d67741e9cac79391f36555b61b7c6e10486a46f659d8af8230b56  pokeemerald-cries-off-release.elf
4dbf3be4029176c4d428c2f230d7121501b88213b277beb85186560ca7815651  pokeemerald-cries-on-release.gba
016a8dad1118c2a0a900351c08794346e0deafe4461c9777f2cbaa2e6888f5c6  pokeemerald-cries-on-release.elf
# claude/test-merge-117-124 (40b0abb4, same engine tree) RELEASE OFF ROM:
06e3e40a9a7ff49c372166448333b4337b466c29f19d12e2b176ca90c31226bd  pokeemerald-cries-off-release.gba
```

## After the review fixes (Makefile `CRIES` strip and the new ducking test; head after `57a9fcbc`)

- **ROMs unchanged:** rebuilding both RELEASE profiles gives byte-identical ROMs, OFF `06e3e40a…` and ON `4dbf3be4…`, with the 4 newlib stub notes plus 1 assembler warning (`.rodata.compound_string… size is not a multiple of its entry size`). The assembler warning is pre-existing: main's RELEASE build has it too. See `build-117r-*.log`.
- **`Averon cry safety` is now 10/10** on each profile, headless (`native-*-final.log`) and non-headless (`native-*-final-nonheadless.log`).
- **The new test fails without the fix (RED, `native-off-duck-RED.log`):** with the OFF gating removed from `PlayCry_Normal`, `ByMode` and `Script`, it fails with `EXPECT_EQ(21, 64)`. `sound.c` was restored afterwards and is identical to HEAD.

**Correction (2026-10-18):** earlier notes, including the #124 evidence comment, said "only the 4 newlib notes". Those notes came from a case-sensitive `grep warning:`, which missed the assembler's `Warning:` line. That warning is present on every RELEASE build here and on main.
