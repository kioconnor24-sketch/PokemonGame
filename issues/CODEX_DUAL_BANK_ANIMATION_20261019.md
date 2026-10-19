# Paired General/Petalburg import staging — stop/resume handoff

Codex branch `codex/sinnoh-dual-bank-animation-staging-20261019`, based on merged
#177 main `bb52ffd9`. This extends scratch import infrastructure only. No engine,
map, saved ID, existing General asset, audio or Claude QA file is modified.

## Implemented

- New `scripts/sinnoh-dual-bank-family.py` reuses #177's verified tracked-blob,
  CRLF, palette and revision primitives. Supports the measured donor
  General/Petalburg pair:512 primary plus up to512 secondary metatiles, both
  graphics banks,32 source palettes and all26 General animation frames.
- Actual consumed source files are bound to pinned Git HEAD/blob bytes. Complete
  fieldmap/behavior/animation source contracts must match the selected engine.
- Checks map AND border dependencies, per-bank graphic/metatile bounds,4bpp
  pixels, record/attribute counts, dimensions/field buffer and animation frame
  transfer sizes. Other tileset/callback families fail closed.
- Outputs source-identical map/border, isolated `primary/sinnoh_imported` and
  `secondary/sinnoh_imported` assets, generated `family.c`, `animations.inc`,
  metadata/hash receipt, static daytime preview and attribution notice.
- General's engine-identical callback/data closure is extracted through an exact
  whitelist and renamed `SinnohImported`; existing General symbols/art are not
  replaced. Generated animation include belongs INSIDE tileset_anims.c, where
  existing private scheduler state/helpers are visible. This is not automatic
  production registration. Petalburg has no animated callback dependency;
  generated secondary callback is NULL. Future other secondary callbacks require
  explicit measured adapters.
- Maps retain original lower10-bit metatile IDs and upper6 collision/elevation
  bits. Events, connections, story scripts, trainers, encounters, flags and saved
  identities are not imported.

## Actual verification

**12/12 targeted tests PASS**, zero failures/skips, using temporary committed Git
fixtures and indexed PNG assets. Includes dual-bank pixels/palette ownership,
raw map upper bits, a second synthetic map identity using the same family,
isolated generated symbols, dirty animation, wrong frame transfer size,
secondary attribute/graphic/border bounds, contract mismatch, unsupported pair
and malformed callback extraction.

One test compiles and executes the GENERATED animation include with host `cc`,
checks initialization and all256 timer ticks, all80 resulting transfer calls,
exact VRAM tile offsets, byte sizes and frame pointers/order. Fake Append records
transfers; it does NOT emulate DMA/mGBA or copy actual donor frame pixels.
Initial harness had a missing u8 typedef and incorrectly assumed sand-water's
seven distinct frames meant a seven-entry cycle. Corrected fixture now checks
its real eight-entry cycle (frame0 repeats). Production callback was unchanged.

Actual pinned donor Route202 staging PASS at upstream
`38228bb574a3557345852b758d5f1a65eb01bb22`:
30x34 map,2x2 border,25 metatiles,36 graphic tiles,palettes0/1/2/3/5;
map SHA256 `9f58a62052998ed869259356c395302ef5bfa35624b612c0e68ae1922e00437b`.
Static RGB SHA256 remains
`452c09c70b01f5c249a5003138ac4c975224765792ec49236f00aaca67284343`,
identical to #177. The real map does not exercise secondary/animated references;
those are exercised by the new executable fixtures. Do not claim another real
city/route or gameplay PASS from them.

Existing read-only workflow extended with12 tests, real paired-family staging,
map/border cmp and cross-adapter static pixel/dependency equality. Upload remains
analysis JSON only. No donor assets, generated source containing donor code,
ROMs, ELFs or saves are committed/uploaded by this PR. CI status must be read live.

## Resume / genuine remaining gates

User requested finish immediate work, save and STOP; no new task/session starts.
All recoverable implementation/tests/evidence are pushed to a normal PR.
Independent peer review is required for the workflow/adapter before merge.

Next: read PR's newest CI results, fix any real failure; obtain independent
source review. Then Claude can integrate the generated family on a separately
protected actual map branch and test NORMAL+RELEASE, grass/ledge/field effects,
night palettes, follower layers, seams, real animation and Save→fresh Continue.
No full linked ROM delta, native GBA, ARM object for THIS adapter, mGBA, door
compatibility, other secondary callbacks or distribution acceptance is claimed.
Source permission reported in #15/6274520543; retain author credit and document
third-party/public asset distribution scope before publishing art.

Local scratch: `/workspace/scratch/route202-dual-family`.
Local test log: `/workspace/averon-session-evidence/dual-bank-tests.log`.
Reproduce:
```
python3 -m unittest discover -s "Pokemon Game/scripts/tests" -p test_sinnoh_dual_bank_family.py -v
python3 "Pokemon Game/scripts/sinnoh-dual-bank-family.py" \
 --donor-root /path/to/pinned/donor --engine-root "Pokemon Game/engine" \
 --revision 38228bb574a3557345852b758d5f1a65eb01bb22 --map Route202 \
 --output /new/off-engine/scratch
```
