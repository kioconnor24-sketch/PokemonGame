# Existing map registry contract

Scope: test/verification files only, based on main `7f4ecc44`. Claim:
[#15 comment 6219954060](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6219954060).
No production map, generator, engine, saved ID, region interface or QA file changes.

The pinned `.inc` is C test metadata for existing IDs, not a new map or layout.
Do not regenerate it automatically: moving old IDs would redirect saved warps.
Any later authorized registry extension needs an explicit reviewed test update;
capacity figures here do not lift the map/content freeze.

## Why this boundary matters

`WarpData` stores group, map and warp index in signed bytes. Map IDs and group
counts are generated from all registered JSON maps. The actual Emerald group
table filters out Kanto maps and preserves their group positions as NULL.
Thus a defined constant or positive debug count does not prove a usable runtime
map. A mixed enabled/disabled group would compact pointers while leaving numeric
IDs and counts unchanged, so the source check rejects it.

Three native tests compare the linked table with pinned IDs/exported group
symbols, confirm disabled group slots stay NULL, and round-trip linked IDs
through the real signed warp fields. Compile-time assertions cover numeric
identity for disabled maps too. Individual header labels are local assembler
symbols, so the optional ELF verifier reads the actual linked ARM symbol table
and pointer bytes to check every original header address independently. It
requires an unstripped ELF and never changes engine exports. Test arrays are
constant ROM data; no large stack or static EWRAM fixture is added.

## Source results

```sh
python3 scripts/check-averon-map-registry.py --engine engine --mutations --report /tmp/map-registry.json
```

Executed locally: **76 groups, 951 pinned map IDs, 534 linked maps PASS**:
35 linked groups and 41 intentionally disabled groups.
Ten in-memory mutations detected: group/map reorder, duplicate ID, missing map,
symbol mismatch, mixed-region group, group/map overflow and object/warp-count
overflow. A separate valid-boundary control accepts the last representable
event counts. Mutations never write map JSON or fixtures.

Signed storage leaves 52 group positions. The tightest registered group has
only 5 further map positions; the tightest linked group has 20. These describe
ID representation only, not ROM, flash, gameplay, asset or design capacity.

## Native/build status and limits

```sh
make -j5 -O check TESTS='Averon map registry' ROMTEST=/workspace/.onboarding/mgba-rom-test
make -j5 -O all
```

The retained cloud toolchain is selected with
`. /workspace/.onboarding/activate.sh`; the ROMTEST override is environment-specific.
Local GCC ARM 14.2.1/headless mGBA execution: **3/3 registry tests PASS**;
the broader Averon suite also passed **50/50**, with zero failures/skips.
On that actual test ELF, the verifier checked **534 original header symbols**
and detected **3/3 in-memory pointer mutations** (a linked group nulled, a
disabled group made live, and a valid but wrong header placed in a slot).

```sh
python3 scripts/check-averon-map-registry.py --engine engine --mutations \
  --elf engine/pokeemerald-test.elf --report /tmp/map-registry-linked.json
```

Normal `make -j5 -O all` also **PASS**. The actual normal ELF independently
matched all **534 header symbols**, and all **3 pointer mutations** were caught.
Source/code tested at `9b40e538b7c0c936b9ebc10ea83ff1a4fd57f357`; subsequent
evidence-only edits leave those C/Python/manifest inputs unchanged.

```sh
python3 scripts/check-averon-map-registry.py --engine engine --mutations \
  --elf engine/pokeemerald.elf --report /tmp/map-registry-normal.json
```

| Normal build measurement | Bytes |
| --- | ---: |
| EWRAM used / free | 226,420 / 35,724 |
| IWRAM used / free | 28,392 / 4,376 |
| Linked ROM used / free | 26,729,436 / 6,824,996 |
| Padded private ROM | 33,554,432 |

ROM SHA256: `f118f53442d5610568c54486f78486d96ae43dfcf6e25860b9679c6e2f74dc40`.
Object-symbol measurements place both test arrays in read-only data (`r`):
608 + 2,136 = **2,744 bytes** in the test build; neither is a BSS/stack buffer.
The normal game build excludes the test source entirely.

Source-contract CI [38933734690](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38933734690)
passed. Normal GBA/native CI is separately tracked on PR #63; do not infer a
CI pass from local execution. Earlier compile/link failures were corrected only
in these new test files and are not counted as successful builds.
Existing standard native CI will compile/run these tests; the separate source
workflow checks the source registry and stores input hashes without an ARM/ROM
dependency. Later results must identify the actual tested source SHA.

This verifies current registration, not safe handling of arbitrary corrupt
map IDs: `Overworld_GetMapHeaderByGroupAndId` directly indexes the table, so the
tests never pass invalid indices to it. Claude owns future region/save/travel
validation. No new Sinnoh destination, invalid-warp engine repair, rendered
travel, graphical QA, save compatibility or BACKEND_READY claim is made.
