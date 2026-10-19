# Route202 isolated static tileset adapter — Codex

## Decision and implemented boundary

Base main `9bb1f1ef` contains independently reviewed #176. Preserve Averon's shared
General graphics. Prefer one isolated source-compatible Sinnoh family over per-map
remapping: all25 current references keep exact source metatiles, indexed pixels,
flips, daytime palettes and attributes. Ten records lack any Averon structural
match, and the other15 were never visual equivalence evidence. Reusing one family
avoids maintaining manual graphical mappings across every later route.

`scripts/sinnoh-isolated-tileset.py` implements this first **static primary-only**
adapter. It verifies actual donor HEAD and every consumed tracked dependency,
compares full fieldmap/behavior/animation contracts with the selected engine,
checks map AND border closure, image bounds/4bpp indices, bank membership,
attribute count, palette colors and padded map buffer. It rejects referenced
animated tiles (432+), secondary metatiles/graphics/palettes and unsupported layer
types. It does not execute donor code or copy arbitrary directories. Declared Git
CRLF palette checkout conversion is accepted only when normalization exactly
matches the committed blob. Git symlinks and modified dependencies are refused.

New scratch output only: source-identical map.bin/border.bin, separate
SinnohGeneralStatic assets, static daytime preview, source/asset/hash receipt,
attribution notice, and a standalone generated `sinnoh_general_static.c` using
`gTileset_SinnohGeneralStatic`, compressed graphics and NULL callback. It never
writes production engine files, registers a map, imports events/connections/scripts,
allocates saved identities or modifies existing General. The generated C is an
integration input, not an automatically registered or gameplay-tested family.

## Actual local evidence

Pinned donor: LiderMorti00/Sinnoh-pokeemerald-expansion
`38228bb574a3557345852b758d5f1a65eb01bb22`, actual Git checkout. Source URL and owner
reported permission: #15/comment6274520543. Exact public-distribution/third-party
terms remain to be documented before publishing donor assets; this PR contains
code/tests/prose only, no donor assets or ROMs.

- **19/19 new focused temporary-Git/graphics tests PASS**, zero skips/failures.
  Tests cover real snapshot staging, dirty map/art, wrong HEAD, contract mismatch,
  symlink, overwrite/unsafe output, map/border secondary dependencies, border
  truncation, animation, palette, attribute count, absent graphic, 4bpp overflow,
  layer refusal, declared CRLF, palette quantization/flip/transparency.
- Reuse unchanged #176 real CI15/15 tests and pinned nine-blob donor-only1020-cell
  identity result. These are different tests; not a new claim of native GBA tests.
- Actual Route20230x34 map +2x2 border staged. Source map SHA256
  `9f58a62052998ed869259356c395302ef5bfa35624b612c0e68ae1922e00437b`;
  border `79b69203a110e809fc15c473032143cb8861764ce3c1959dba6bbba7b60f1079`.
  **25** metatiles, **36** distinct graphic tiles, palettes **0,1,2,3,5**.
  Reopened staged assets reproduce exact source static RGB pixels; RGB SHA256
  `452c09c70b01f5c249a5003138ac4c975224765792ec49236f00aaca67284343`.
  This is host-render equality, not actual mGBA scene/collision acceptance.
- Full fieldmap.h, metatile_behaviors.h, tileset_anims.c donor/engine bytes equal.
  No current referenced graphic reaches animation writes432+; NULL callback is
  safe for this measured static dependency set, **not** a claim future water,
  flowers, cities or arbitrary General references work without another adapter.
- Actual engine gbagfx conversion:16384-byte4bpp; existing compresSmol output
  **7852bytes**, SHA256
  `da99598923de0eae1ebaeb8c92826feea8825d63440288f03245716b13d1b77f`.
  Full primary metatiles+attributes9216bytes and16x16-color palettes512bytes:
  **17580 bytes of payload**, before alignment/header/linking, plus2040-byte map
  and8-byte border. Not an actual linked ROM delta or a full-region forecast.
- Generated family source actually passed the engine's cpp→preproc→ARMcc1→as
  pipeline, using real converted/compressed graphics and all16 converted palettes.
  GCC14.2.1 (20241119), ARMv4T/apcs-gnu; **17604 bytes read-only,0 data,0 BSS**
  (17580-byte payload+24-byte Tileset header). Object SHA256
  `4baa82c92f7a866ab9f55d065654e4396f90a438693b3a6bab2af9c5eff79a0c`.
  Generated constants include paths were reused from the existing local native
  build; no map/header/registry was changed and no ROM link is claimed.
- **Actual GitHub Actions run39326076386/job118312144210 PASS** at implementation
  `342d40b24d0239492d0bf1c9885232d81ce4a30e`: completed logs confirm15 retained
  tests+19 new tests, real pinned sparse checkout, source/staged map+border cmp,
  exact dependency/pixel assertions. Other applicable guards/source checks PASS.
- No runtime changes: NORMAL/RELEASE/native/gameplay tests are not rerun or
  claimed here. Production registration later needs actual paired ROM builds,
  resource measurement, native and genuine mGBA seam/Save→fresh Continue evidence.

## Reproduce

```
python3 -m unittest discover -s "Pokemon Game/scripts/tests" -p test_sinnoh_isolated_tileset.py -v
python3 "Pokemon Game/scripts/sinnoh-isolated-tileset.py" \
  --donor-root /path/to/pinned/checkout --engine-root "Pokemon Game/engine" \
  --revision 38228bb574a3557345852b758d5f1a65eb01bb22 --map Route202 \
  --output /new/off-engine/scratch/route202-family
```

Pillow required (CI pins11.3.0; local12.3.0). Existing workflow is extended with
19 tests, actual sparse Git source verification and real staging. Only analysis
JSON is uploaded; no preview, C-generated assets, map binaries or donor art.
Workflow changes require genuine independent review before normal merge.

## Claude handoff / next executable action

Claude owns protected Route202 map integration and graphical QA; #166/#175 remain
untouched. Use the produced separate family and approved section219, retaining
current map-group pins. Do not reuse donor -2/-38 connection offsets blindly:
resolve actual Sandgem endpoint and future Jubilife separately. No donor event,
script, encounter, flag or trainer import is authorized by this adapter.

For a playable pilot, obtain exact-path map/assets handoffs and documented rights
scope, introduce the separate family symbol through normal engine registration,
then review behavior-specific substitutions (grass/ledge/field effects), palette
night swaps, border/seam blending and follower layers in actual NORMAL/RELEASE
mGBA + Save→fresh Continue. General doors elsewhere key on tileset pointer, so
future buildings need a separate door adapter, not blind primary reuse. Current
Route202 has no door behavior in its referenced set.

For additional maps, rerun this adapter: supported static primary-only maps reuse
this family without remapping; a rejected secondary/animated dependency is an
explicit request for a measured family/callback adapter, not permission to mark
it verified. No blanket city compatibility, natural travel reachability, new saved
identity or distribution acceptance is asserted.
