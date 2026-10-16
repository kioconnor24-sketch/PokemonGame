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
only array on the test stack is a 200-byte PC-item snapshot. There is no static
item-buffer allocation to shift the shared EWRAM layout.

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

## Verified CI evidence

Tested source commit: `33f370de3285874cf789f45a0360967e2a8c3ccf`.
[Run 38879938381](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38879938381)
and [text/JSON artifact 12036839861](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38879938381/artifacts/12036839861):

- Real `make -j4 -O all`: PASS, GCC ARM 13.2.1, 33,554,432-byte padded ROM.
- `make -j4 -O check TESTS='Averon'`: **51/51 PASS**, zero failed or skipped,
  including all four new PC tests and all three key-rotation parameters.
- EWRAM 226,416 B (35,728 B free); IWRAM 28,376 B (4,392 B free);
  linked ROM 26,728,048 B (6,826,384 B free).
- Private ROM SHA256:
  `cda091f60f3638efc2e08cc9a1b2792cc0e879fa224b419284071135ec0ad184`.
- Source checks and PR hygiene also passed. Later evidence-only documentation
  commits do not alter the native test source that this run executed.

These are VERIFIED EXISTING item/PC behaviors, tested through native execution;
the PR adds regressions, not a gameplay fix. No full upstream-suite, graphical
PC/menu, flash round trip or Delta acceptance is claimed. The regional
save/travel and general held-battle-item suites remain Claude's separate work.
No maps, saves or ROMs are distributed.
