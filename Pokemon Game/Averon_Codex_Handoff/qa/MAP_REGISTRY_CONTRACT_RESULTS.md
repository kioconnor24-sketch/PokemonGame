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

Executed locally: **76 groups, 951 pinned map IDs, 534 linked maps PASS**.
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

The first build rejected cross-enum sentinel comparisons under `-Werror`;
the test now casts to unsigned before comparing values. The initial direct C
references to local header symbols failed to link; exported group checks plus
read-only ELF inspection provide that coverage without engine changes. These
failed attempts are not counted as passing builds.

A new normal GBA build and its separate ELF verification are still PENDING.
Existing standard native CI will compile/run these tests; the separate source
workflow checks the source registry and stores input hashes without an ARM/ROM
dependency. Later results must identify the actual tested source SHA.

This verifies current registration, not safe handling of arbitrary corrupt
map IDs: `Overworld_GetMapHeaderByGroupAndId` directly indexes the table, so the
tests never pass invalid indices to it. Claude owns future region/save/travel
validation. No new Sinnoh destination, invalid-warp engine repair, rendered
travel, graphical QA, save compatibility or BACKEND_READY claim is made.
