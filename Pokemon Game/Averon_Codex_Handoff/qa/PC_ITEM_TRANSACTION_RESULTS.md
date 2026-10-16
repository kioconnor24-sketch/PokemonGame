# PC item transaction boundaries

Test-only, map-independent follow-up to backend gate #46. Exact-path claim:
[#15 comment 6212291937](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6212291937).
Base: main `7f4ecc44270e98b2363fc49cb708aa4d9a3527fa`.

## Scope

Four native tests execute production item APIs, without new item data or engine
changes. They check large deposits split across bounded PC stacks, a partly
fitting deposit rejected byte-for-byte without mutation followed by a successful
retry after freeing space, partial/exhausted removal with adjacent entries
preserved, and three Bag encryption-key rotations leaving PC quantities plain
and unchanged. Bag quantities remain independent of PC deposits/removal.

`RemovePCItem` is followed by `CompactPCItems` where the real `player_pc.c`
caller does so; the tests do not invent a stronger helper API contract. The
only array on the test stack is a 200-byte PC-item snapshot. No static test
allocation shifts the shared EWRAM layout.

## Reproduce and current status

From the engine directory, with the actual ARM toolchain and headless mGBA
runner available:

```sh
make -j5 -O check TESTS='Averon PC items' ROMTEST=/workspace/.onboarding/mgba-rom-test
make -j5 -O all
```

Cloud setup selects retained dependencies with
`. /workspace/.onboarding/activate.sh`. The ROMTEST override is specific to
this environment's executable runner copy; ordinary CI uses its bundled runner.

Native execution and GBA build are **PENDING** at this recoverable checkpoint.
No passing count, full-suite result, graphical PC/menu, flash round trip, Delta
acceptance or gameplay bug fix is claimed. The regional save/travel and general
held-battle-item suites remain Claude's separate work. No maps, saves or ROMs
are distributed.
