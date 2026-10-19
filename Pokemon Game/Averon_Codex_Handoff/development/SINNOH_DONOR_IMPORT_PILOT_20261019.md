# Sinnoh donor map reuse — first conversion pilot

**Owner direction (2026-10-19):** the project owner reports securing permission to reuse the Sinnoh map work and authorizes changing from predominantly manual reconstruction to a source-grounded donor-import approach. See [Issue #15 owner-report checkpoint](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6274520543). This is a permission report, **not a published open-source license**, and the exact permission message and third-party asset terms are not stored here yet.

**Primary donor:** [LiderMorti00/Sinnoh-pokeemerald-expansion](https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion), inspected current revision `38228bb574a3557345852b758d5f1a65eb01bb22` (2026-10-18). Earlier in-repo [159-map technical inventory](SINNOH_SOURCE_AND_PIPELINE_RESEARCH_20261017.md) covers revision `a430af4281408b03fdf808e0f5af8d6d2965d676`. Its prior three binary exemplars and metatile differences are important: geometry is reusable in principle, but raw map bytes are *not* interchangeable with Averon tilesets.

## Change in production strategy

1. Prefer authorized donor geography and recognizable Platinum topology. Supplement with [pokeemerald-platinum](https://github.com/sinnoh-remakes/pokeemerald-platinum) as an **unlicensed reference only**, not an automatic source of copied assets.
2. **First map: Route 202**, because #167 already provides an independently authored 34×34 candidate and the physical Sandgem↔Jubilife junction targets. Do not overwrite the accepted Sandgem/Route 201 or unmerged Twinleaf (#166) just to resemble a donor; preserve intended geometry and saved identity decisions.
3. Import **geometry + explicitly verified tile dependencies**. The first staging script deliberately excludes trainer/NPC events, scripts, story flags, item rewards, warp lists, connections, audio, map IDs and saved met-location codes.
4. For an asset family, decide whether original donor tilesets can be reused based on ownership and documented permission. If not, map each source metatile to a verified equivalent in the destination primary/secondary bank. **Matching numeric metatile IDs do not guarantee matching art, palette, animation or behavior.**
5. Do a small visual/behavior and memory pilot **before** scaling to multi-map connected batches. Never use a full donor map_groups.json: the donor prepends 18 groups and would renumber Averon's accepted IDs.
6. A successful pilot should produce a repeatable dependency-closure manifest and converter, allowing faster import of later source-grounded connected regions instead of rewriting map-specific generators.

## First pinned Route 202 dependency inspection (GitHub source read)

On donor revision `38228bb574a3557345852b758d5f1a65eb01bb22`:
- **Donor Route202:** `MAP_ROUTE202` / `LAYOUT_ROUTE202`, **30 × 34** cells; primary `gTileset_General`, secondary `gTileset_Petalburg`. Its declared binary is `data/layouts/Route202/map.bin` (Git blob `25c724524810a7a188d30947cb885a4e5e44e8b9`); actual raw bytes/behavior remain to be checked via an ordinary local Git clone, not guessed from the connector's binary transport.
- **Connections:** down to Sandgem at donor offset −2; up to Jubilife at donor offset −38. These are donor-relative offsets, NOT authorized Averon seam values. Re-evaluate against current Sandgem geometry and the yet-unbuilt Jubilife.
- **Story/event baggage excluded from converter:** six object events, no warp events, ten coordinate events and four background events.
- **Independent local candidate:** #167 Route202 is **34 × 34**, not the same footprint. Before selecting one, compare faithful visual geography, practical seam positions, donor-family graphic quality, and the total dependency closure, not merely width.

The importer intentionally does not claim the caller-supplied 40-hex donor revision is authenticated from the checkout's Git HEAD. Before production approval, the developer must compare the local `git rev-parse HEAD` with the declared revision and confirm the actual binary's Git blob identity as well as the SHA-256 recorded by the tool.

## Implemented in this isolated PR

- `scripts/sinnoh-donor-map-pilot.py`: reads a **local, pinned donor checkout** and cross-references `data/maps/<MapName>/map.json`, `data/layouts/layouts.json`, and the declared 16-bit `map.bin`. `inspect` reports dimensions, actual referenced metatile IDs/frequencies, donor tileset symbols, event/connection counts and SHA-256 of the precise binary; optionally generates a deliberately *unverified* map manifest.
- `convert` refuses absent/unverified source→target tile mappings, bank crossover, changed blob hash, path escape, oversize padded GBA maps, unintended overwrites and output into an engine directory. It preserves all six collision/elevation upper bits and writes a **scratch-only** converted block plus provenance receipt.
- `scripts/tests/test_sinnoh_donor_map_pilot.py`: synthetic source/behavior/asset/negative tests. No donor assets are copied or pushed by this PR.
- **Not yet done**: byte-verifying and analyzing the actual donor Route202 map.bin through a local clone; completing the metatile correspondence, clearing individual asset provenance, converting a real layout, working map integration, actual NORMAL/RELEASE builds or genuine mGBA QA. Do not mark production/area-register progress for this tool.

## Example local test and pilot workflow

A developer with a local checkout of the donor at the pinned SHA can run:

```bash
cd "Pokemon Game"
python3 -m unittest discover -s scripts/tests -p 'test_sinnoh_donor_map_pilot.py' -v

python3 scripts/sinnoh-donor-map-pilot.py inspect \
  --donor-root /path/to/Sinnoh-pokeemerald-expansion \
  --map Route202 \
  --donor-revision 38228bb574a3557345852b758d5f1a65eb01bb22 \
  --template-out /tmp/route202-remap.json
```

Inspect source dependencies and fill each **real, verified** tile correspondence in the scratch manifest. Specify a proposed destination map ID and destination primary/secondary tileset family. Do not assign an unapproved saved location code. Then stage a converted binary **outside** `engine/`:

```bash
python3 scripts/sinnoh-donor-map-pilot.py convert \
  --donor-root /path/to/Sinnoh-pokeemerald-expansion \
  --map Route202 \
  --mapping-json /tmp/route202-remap.json \
  --output /tmp/route202-import/map.bin
```

**The importer intentionally stops short of playable conversion.** A later map-integration PR must reconcile the actual destination bank art/collision, reserved/approved section 219, existing Map IDs, reciprocal seams, real warp events if ever approved, protected exact-file handoffs, old saves, resource budget and emulator evidence. Not every donor building interior, script or map is complete; no 87/87 production claim is implied.

## Permissions and publication requirements

The owner reports permission. Before moving donor files into **public Averon Git**, retain the permission message or durable reference and clear any file-specific restrictions. Separate (a) layout geometry/mapping work made by this donor maintainer from (b) imported graphics, music, sprites, scripts or third-party art. Track author, URL, source commit, transformed files, required credit text, and any exceptions per asset family. The third-party creator cannot authorize rights they do not possess. The developer should not silently inherit donor's ROM, original storyline, map IDs, save format, or upstream engine.

**Next handoff:** use the new script on a clean clone, establish real Route202 metatile equivalence or a licensed tileset-family import strategy, compare to #167, then build **one** real map under existing guards. If full per-tile manual remapping proves more expensive than creating clean compatible graphics, document measured costs and switch strategy; don't scale a poor converter.
