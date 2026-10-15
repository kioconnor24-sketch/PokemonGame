# Coastal route preview — R03

One bounded native map, CoastalBluffs (64×40), extends Alderfield toward the
approved Breakwater route. Upper road/lookout and sheltered beach fork are
authored explicitly; the coast faces south at this local cove. No random map
generation and no empty Breakwater town/warp. North cliff steps stay closed
until later town production. This is a preview, not completed R03 or Gym 2.

Alderfield's eastern boundary admits only three road tiles. Each crosses a
Badge1 trigger before reaching the border; all other boundary tiles are solid.
Native static checks verify the trigger coverage and connected paths, with
Surf-only water excluded. Actual gate movement/transition still needs gameplay.

Content: Jules with Wingull14/Rookidee15, lookout and beach conversations,
repair worker, Super Potion pickup using native finditem, grass encounters
at levels10–13. Trainer slot568 was explicitly unreferenced outside its unused
definition/party and is reused; MAX_TRAINERS_COUNT remains864. Pickup flag029
was unused. Existing map/layout IDs and save sizes stay stable.

Full authoring command is now `python scripts/build-averon-coast.py`; it first
regenerates the opening and Gym. Do not run the older partial authoring commands
alone as final output: they recreate Alderfield before the coastal extension.
`check-averon-authoring.py` uses the full authoring command and checks stability.

Normal-font dialogue, walking model, native map rendering and source/compile
checks do not replace runtime acceptance. The prior M2 ROM is preserved at
`evidence/m2/averon-m2-stable.gba`, SHA256
`dced4e3cf19cc5c440ef54b4342cb43fc8eaed6ea939259134f67fc7d96b9491`.

Compiled successfully with all20 named native Averon tests and four save-layout
tests passing. Authoring stable across68 source/map files, all14 maps pass the
walking/border/interaction checker, and all166 dialogue lines fit. Final route
dialogue compiled afterward; local ROM SHA256
`0646a37269e04c09ad873e69d98deb8d791924c492eebd17501306fc6c718861`.
**BUILT — RUNTIME TEST PENDING**. The badge-gate trigger coverage is checked
statically; actual stepping, item pickup, encounters and transition need gameplay.

## Reusable local build command

`scripts/build-averon.ps1 -Sync <relative engine files> -NativeTests -SaveLayoutTests`
copies only changed specified files into the persistent WSL checkout, runs
native tests/save-size checks, incrementally compiles and writes the local ROM
plus build manifest. Include every changed generated source/layout file in
Sync. Paths are separate arguments, not interpolated shell code. Failed tests
or build leave the previous output ROM intact. Logs are timestamped locally.
The manifest identifies a Git reference and hashes supplied inputs, including
whether they differ from the publishing checkout; do not mistake a reference
SHA for a clean source snapshot when that mismatch flag is true.
