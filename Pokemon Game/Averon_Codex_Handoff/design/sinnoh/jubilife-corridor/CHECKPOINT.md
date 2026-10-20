# Recoverable corridor checkpoint — NOT production or gameplay acceptance

Owner assignment is Jubilife→Route203→Oreburgh Gate plus neutral Center/Mart/School.
User asked to upload recoverable work before low usage; this is an INCOMPLETE
construction checkpoint, not a completed corridor. Claude's Verity untouched.
Base main21086c44e56fa9262440859a1e49b960cfc37125. PR/head SHA in GitHub handoff.

## DONE / actual source construction

- All SIX physical candidates generated from actual Git-pinned donor geometry.
  7529 cells,11 neutral warp entries and2 reciprocal staged connections.
- Jubilife70x64, Route20364x30, OreburghGate29x27 match all three supplied Git
  blobs exactly (12595aaa72d215853f86582e1d7433f34b47bc4b,
  495ce46a43e485738f55c3786f30303be35f2930,
  1bc0f35104e168d9ed2f2cb024b077af4cc4ccf1).
- Neutral source Center14x9, Mart11x8, School12x11 also generated; full source
  blob/hash/dimensions/dependencies in corridor-spec.json +staged/receipt.json.
- Existing176 converter actually executed for each map, with source==destination
  donor-only identity mappings and exact byte cmp. These boolean attestations
  apply ONLY to identical donor banks, never to Averon's destination graphics.
  No competing converter or guessed graphical equivalence.
- source.bin preserves exact donor geometry. map.bin preserves every lower10-bit
  metatile and all elevation bits; only explicit documented collision closures
  differ. Close unbuilt204/218 edges, unsupported city entrances, Gate's unbuilt
  Oreburgh exit and Center2F stair; retain neutral city/interior return pairs.
- Candidate headers have no objects/coord/background/scripts/encounters/services;
  no donor story/music/flags/trainers/healer. Pure source-grounded terrain remains.
  Each interior uses parent-city identity concept; no saved structure change.
- Local source-art static PNGs rendered for all6 and Jubilife visually inspected:
  recognizable full city street network/buildings/landscaping, no generic rectangle
  replacement. These are donor-only host renders, NOT actual GBA/mGBA screenshots.
  Source artwork permission/distribution is unresolved; **no donor art is committed**.
  Public collision.png files are authored color schematics, NOT gameplay graphics.

## Owner approval received during work

The user directly answered "Approve221 /222 /223" to the exact proposed allocation:
Jubilife +neutral interiors221, Route203222, OreburghGate1F223, all legacy/special
values preserved. Recorded attribution in Issue15/comment6282653675.
This is NOT a forged protected-file handoff. Registration still requires a real
PR/path authorization and normal tests. Candidate section stays null until actual
production registration; no MAPSEC_NONE/unrelated existing section workaround.

## EVIDENCE

6/6 actual host tests PASS, zero skips/failures. Tests catch wrong reciprocal
seam offset, invalid warp index/unbuilt destination, inherited story and false
Averon graphic attestation. Actual verifier output:
6maps /7529cells /11warps /2connections; HOST_VALIDATED_NOT_INTEGRATED_OR_PLAYTESTED.

Source donors use normal doorway collision1 for some retained city doors; the
first overly strict checker rejected them. Fixed checker preserves each source
warp's collision class (rather than falsifying all doors as walkable floor).
This does NOT prove actual door stepping or follower behavior; runtime acceptance
is pending. Negative unbuilt-warp test can reject earlier at missing reciprocal
return; either genuine graph failure is expected, not a production defect.

Source code, graphs, candidate binaries, remap receipts and authored collision
schematics are uploaded. PRIVATE donor-art PNGs remain only at
/workspace/scratch/jubilife-corridor-previews; reproducible with command below.
No ROM, ELF, saves, assets from donor tilesets or secret material uploaded.

## BLOCKED / INCOMPLETE — exact next work

1. Graphics conversion is NOT finished. These are source-identity candidates,
   using measured donor bank definitions General+Rustboro, General+Cave and
   Building+interior banks. Existing paired stager only supports General/Petalburg;
   we reused its verified readers/render primitives without pretending it supports
   these other callbacks. Donor General art still differs from Averon.
2. Route202 uses existing Averon General+Dewford; streamed seam strips are not
   compatible automatically with this city's donor banks. Need explicit cleared
   graphics remapping/bank arrangement; city↔203 share source bank but require
   actual collision/visual seam validation. No global General edits permitted.
3. External Route202 join remains a recorded requirement, NOT enabled. Donor
   offset38 is reference only. Actual181 source/head must be compared before final
   Route202↔Jubilife offsets and border openings. Closed north/west city boundaries
   and other exit closures currently alter collision only; visible barrier/gate
   art still needs an appropriate permitted adaptation.
4. Warp graph is source-verified/sanitized in staging. No engine registration or
   map-group IDs chosen; no protected source paths edited. Proper append-only
   registrar serialization with Claude Verity is still required after181.
5. No NORMAL/RELEASE build, native GBA, mGBA, Save→fresh Continue, linked ROM delta
   or final gameplay acceptance for this source. Do not manufacture those PASSes.
6. Need complete actual post-adaptation bank/metatile/attribute/layer verification,
   physical reachability, closure/path negatives and scene inspection. Current
   verifier is intentionally a SOURCE graph/hash/collision-preservation check.

## Reproduce / resume

Pinned donor38228bb574a3557345852b758d5f1a65eb01bb22, Pillow and existing scripts
from main176–178/183 required. Sparse checkout must include all6 maps/layouts,
layouts.json, include/fieldmap.h, include/constants/metatile_behaviors.h and the
seven relevant tileset families (General,Building,Rustboro,Cave,Center,Shop,School).

```
python3 "Pokemon Game/Averon_Codex_Handoff/design/sinnoh/jubilife-corridor/build_corridor.py" --donor-root DONOR --output NEW_OFF_ENGINE_DIR --private-previews NEW_PRIVATE_DIR_OUTSIDE_REPO
python3 "Pokemon Game/Averon_Codex_Handoff/design/sinnoh/jubilife-corridor/verify_corridor.py" "Pokemon Game/Averon_Codex_Handoff/design/sinnoh/jubilife-corridor/staged"
python3 -m unittest discover -s "Pokemon Game/scripts/tests" -p test_sinnoh_corridor.py -v
```

NEXT EXECUTABLE TASK: inspect cleared Averon Rustboro/Cave/interior art against
used dependency sets, adapt city+203 coherent banks and Route202 seam, regenerate
candidates/previews with real verified mappings. Continue this assignment, not
old Verity preflight/manager cleanup. All three new section identities are now
approved, but that does not waive source protections or graphical acceptance.

## Continued checkpoint — four actual Averon-asset conversions

`adapt_existing_assets.py` now proves every used metatile record, full attribute,
indexed graphic8x8 and selected palette against existing Averon assets for Gate1F,
Center1F, Mart and School, including border dependencies. All4 pass. Unused
Building palette4 differs, but none of these maps uses it; blanket PNG/palette
hash rejection would incorrectly block an exact USED dependency match.

Actual176 converter ran for all4 using graphics/behavior attestations backed by
these comparisons; geometry remains identical before documented closures.
`averon-adapted/` contains real converted map binaries, manifests, hash receipts
and static previews rendered solely with already present Averon assets. No donor
art is added. Gate preview inspected: cave terrain/entry geometry retained;
visible upper ladder has no source warp, so its future-floor treatment needs
explicit neutral closure/adaptation before gameplay acceptance.

7/7 additional tests PASS: used record/attribute/pixel/palette changes and missing
records rejected; unrelated unused palette/tile changes accepted. Together with
6 prior corridor checks:13/13. This is static graphics verification, NOT actual
runtime animation/door/follower/warp/GBA acceptance. General+Cave and
Building+interior existing callbacks still need in-game observation after real
registration. Raw Rustboro city/203 adaptation remains unfinished:94/57 used
primary IDs respectively; city157secondary IDs with9 absent destination slots.
No global General replacement or automatic approximate matching performed.
