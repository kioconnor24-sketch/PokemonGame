# Bind capacity measurements to actual linked artifacts

Codex, 2026-10-19; base `bd705ed5b0987b7a7dcc071d553d5bd89cdcb2d4`. Owner Phase4 resource-tooling task. Narrow extension to the existing reporter; no engine, save, ID, map/asset, CI or governance changes.

## Demonstrated hazard and optional guard

The reporter takes a linker log and optional ROM/map independently. A RELEASE log plus NORMAL ROM arguments can therefore produce RELEASE usage beside a NORMAL hash. During this session that argument mistake was caught and corrected **before publication**; #163's published RELEASE result uses actual `pokeemerald-release.gba/.elf/.map`. Caller labels remain unverified, so filenames alone are insufficient evidence.

Add **`--elf`**, requiring `--rom`. Read actual little-endian ARM ELF32 executable program headers. For every nonempty PT_LOAD segment, use its physical ROM load address (including initialized IWRAM/EWRAM images), check bounds, and compare loaded bytes with the ROM. Require a cartridge-base load, no overlapping nonempty load segments, and exact equality between loaded ROM extent and the log's linked ROM usage. Empty BSS file segments are ignored. JSON records artifact hashes, matched counts, extent and scope. Detect a ROM changing between checksum and verification reads.

Default CLI/report behavior and caller-label disclaimer are preserved. This does **not** authenticate source revision/build flags, map-object attribution, RAM/save runtime, gaps/padding, rights, hardware support for oversized ROMs, emulator compatibility or gameplay. Whole-ROM SHA256 identifies padding; only load bytes are compared to ELF. No acceptance cache or automatic CI gate. Existing output files are not deleted on failure; consumers must honor nonzero status and not accept an older report.

## Actual tests

**26/26 host tests PASS** (18 retained +8 new identities): multiple segments/gaps/padding/RAM BSS; same-size wrong bytes; wrong log extent; malformed/truncated/wrong-class/endian/machine/executable/header table; invalid file/memory/capacity bounds; overlaps/missing base; optional report compatibility/missing-ROM refusal; real CLI failure without writing a new JSON result. Fixtures are temporary bytes/files, not production maps or ROM assets. `git diff --check` PASS.

Actual newly built pairs from transport-hardening source `5f21a9238bf1723959ed69312ae48926711b5073` both PASS verification; GCC14.2.1/ld2.44/newlib4.5.0.20241231. Each has3 nonempty ROM load segments. No ROM or ELF uploaded.

| Profile | Matched bytes = linked ROM extent | ELF SHA256 | ROM SHA256 |
| --- | ---: | --- | --- |
| NORMAL OFF |17326872|`c41307d99c35bd3575c5a533429f7df53c6ff08d0847ae38b54b12b718605419`|`b59523623853c03652d6321c497ecc2b63f3e995b15faf531fe503ed9febf19a`|
| RELEASE OFF |17446008|`5a86ba2b20b49a46fa5746318a4a6d7e71fe18b824469272906e480d1b2a2a36`|`f1ef364e4f641d04d48a2c652e7c01db191edf6028d44a5d09b72dd7e8a6ab30`|

Actual negative CLI checks exit2 without creating new reports:

- RELEASE log + NORMAL ELF/ROM: `ELF linked ROM extent 17326872 differs from linker log 17446008`.
- NORMAL ELF + RELEASE ROM: `ELF and ROM load bytes differ at segment 0`.

After real builds, from engine (substitute retained matching log paths):

```sh
python3 ../scripts/check-averon-resource-budget.py \
  --log /path/to/normal.log --rom pokeemerald.gba --elf pokeemerald.elf \
  --json /tmp/normal-bound.json
python3 ../scripts/check-averon-resource-budget.py \
  --log /path/to/release.log --rom pokeemerald-release.gba --elf pokeemerald-release.elf \
  --json /tmp/release-bound.json
```

The host tool allocates no game memory. R1 Fast Lane A after final-head applicable checks; transport runtime hardening has its separate peer requirement. Existing native CI already exercises this host suite and real build on these paths but does not yet pass `--elf`; no unreviewed workflow change is bundled. The option is not automatically enforced CI provenance policy. Future measured batches can use it immediately.
