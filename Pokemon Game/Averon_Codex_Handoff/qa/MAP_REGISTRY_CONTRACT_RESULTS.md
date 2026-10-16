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

Three native tests independently compare the actual linked table with pinned
IDs/header symbols, confirm all disabled group slots stay NULL, and round-trip
linked IDs through the real signed warp fields. Compile-time assertions cover
numeric identity for disabled maps too. Test arrays are constant ROM data; no
large stack or static EWRAM fixture is added.

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
Native execution and a new real GBA build are PENDING at this initial checkpoint.
Existing standard native CI will compile/run these tests; the separate source
workflow checks the source registry and stores input hashes without an ARM/ROM
dependency. Later results must identify the actual tested source SHA.

This verifies current registration, not safe handling of arbitrary corrupt
map IDs: `Overworld_GetMapHeaderByGroupAndId` directly indexes the table, so the
tests never pass invalid indices to it. Claude owns future region/save/travel
validation. No new Sinnoh destination, invalid-warp engine repair, rendered
travel, graphical QA, save compatibility or BACKEND_READY claim is made.
