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

## Continued checkpoint — existing-art city and coherent corridor bank

Owner explicitly directed using existing Averon art/original adaptations until
redistribution of specific donor graphics is verified (Issue15/6283227749).
No new donor art uploaded. `build_city_art_draft.py` now authors a full70x64
Averon-art alternative: existing neutral facade templates replace the two broken
landmark envelopes; existing Center/Mart facades preserve active door anchors;
existing fountain restores the nine source records absent from Averon Rustboro;
existing tree screens close northern/western unbuilt roads. Streets, park and
residential pattern remain source-grounded outside explicit recorded edits.
Two landmarks reuse the same neutral existing facade: this is a disclosed
silhouette/style adaptation, not a claim of exact Platinum artwork. No company,
Gym, service, story or character is assigned. Everything remains PROVISIONAL.

`build_corridor_banks.py` resolves source behavior/layer mismatches WITHOUT
changing global General: corridor Rustboro clones its350 existing records and
appends19 existing-Averon tile-word records with explicit source semantic/layer
attributes. Final369records, under512capacity; no new graphic/palette source.
This preserves source sideways stair behavior and other unchanged terrain
semantics while keeping actual original primary bank byte-identical. New local
metatile numbers are NOT persistent met-location identifiers or old map IDs.
The authored region edits and semantic packing are separate from176's original
source identity conversion; no false donor→Averon identity assertion is made.

City+203 share this secondary. Final City rows57–63 (490cells) are primary-only,
so Route202's FillNorthConnection sees no incompatible secondary IDs. Incoming
Route202 source uses only General too. This is bank-compatibility proof, not a
final offset/traversal/collision/mGBA acceptance. Actual181 source/head and
upper/south seam opening still need integrated tests before enabling a connection.

20/20 host tests PASS:14 earlier/source-negative checks +6 real generated bank
invariants. Added a negative that reopens an unbuilt edge AND updates its hash;
the verifier now rejects it semantically instead of relying only on checksums.
Existing350 record meanings preserved; all cloned glyph words are existing art;
active city doors55,36 /54,26 /43,36 preserved; all new IDs in range; semantic
packing preserves upper6bits. No supplied native failure baseline changed.

Generated bank compiled through actual Emerald cpp→preproc→ARMcc1→assembler,
GCC14.2.1/apcs-gnu:6668B read-only,0data,0BSS. Object SHA256
6ba5b6a0f658f6513befef5cb3980a744390dcb926f1248c6c52335f6458e619.
No ROM linkage or runtime acceptance implied. Exported bank definition references
existing Rustboro graphics/palettes/callback; source binaries stay untouched.

Current best CITY/203 candidates are `corridor-banks/{JubilifeCity,Route203}/map.bin`
and their Averon renders. Four other maps remain `averon-adapted/`. Earlier
`staged/` and `city-art-draft/` preserve provenance/intermediate states; do not
confuse them with final registered engine maps. Still need natural cave/door/
stair/grass behavior, visible closures, animations, follower/menus and complete
Save→fresh Continue after protected production registration. Upper cave ladder
is currently inert without a warp and still needs an intentional closed visual.

Reproduce added stages:
```
python3 "Pokemon Game/Averon_Codex_Handoff/design/sinnoh/jubilife-corridor/adapt_existing_assets.py" --donor DONOR --engine "Pokemon Game/engine" --staged STAGED --output NEW_FOUR_MAPS
python3 "Pokemon Game/Averon_Codex_Handoff/design/sinnoh/jubilife-corridor/build_city_art_draft.py" --engine "Pokemon Game/engine" --staged STAGED --output NEW_CITY_ART
python3 "Pokemon Game/Averon_Codex_Handoff/design/sinnoh/jubilife-corridor/build_corridor_banks.py" --engine "Pokemon Game/engine" --donor DONOR --staged STAGED --city-art NEW_CITY_ART --output NEW_BANKS
python3 -m unittest discover -s "Pokemon Game/scripts/tests" -p 'test_sinnoh_corridor*.py' -v
```

NEXT: prepare six engine-shaped neutral headers/layout/script fragments and bank
registration inputs, preserving section221/222/223 and parent-city interiors;
serialize global registrars with existing181/ClaudeVerity instead of editing their
claimed files. Then concrete protected PR, actual paired ROMs/native and real
mGBA route-through/save acceptance. Existing draft184 is still not merge-ready.


## Saved and stopped — owner request, 2026-10-21

The next preparation step above is now staged in `engine-overlay/`, generated by
`prepare_engine_overlay.py`: six engine-shaped neutral map headers/scripts, six
layout binaries/borders, the corridor bank and unapplied registration fragments.
These are OFF-ENGINE candidates, not registered production maps. CLI generation
succeeded; no additional overlay-specific test coverage is claimed. Sections
221/222/223 use owner-approved symbols; interiors share Jubilife. MUS_DUMMY is
a placeholder, and no services, encounters, trainers or story are implemented.
No donor graphics were added: the bank references existing Averon art.

Additional source-only seam check against PR181 head
962a472eb42f5c0d8c549bd67f3dab8fd7497430: Route202 north openings x8–15 align
with City south x46–53 using offsets +38/-38. City elevations are
3,3,0,0,0,0,3,3; Route202 elevations are 3. Engine elevation zero is the
transition wildcard. City southern seven rows are primary-only. This is NOT
runtime traversal acceptance. Route202 source SHA256:
9f58a62052998ed869259356c395302ef5bfa35624b612c0e68ae1922e00437b.

Evidence: 20/20 focused host tests passed before this stop; generated bank ARM
object measured 6668 bytes read-only, zero data/BSS. No linked ROM growth,
NORMAL/RELEASE builds, native regression or genuine mGBA corridor acceptance
claimed. The overlay remains unintegrated and PR184 remains DRAFT.

Unresolved: serialize protected/global registration with PR181 and Claude's
Verity changes; obtain applicable scoped protected-file authorization; resolve
the visible inert Gate ladder (19,5) and closed east exit (25,20); inspect city
art and animation; run paired builds/native checks and real route-through,
Save/Continue and warp acceptance after authorized production integration.
No merge or automatic restart is requested. Development stopped at owner request.

NEXT EXECUTABLE TASK on explicit resumption: refresh live main/claims/PR181,
review `engine-overlay/registration-fragments.json`, then prepare a serialized
production registration change under the applicable safeguards. Do not apply
fragments blindly or mistake staged candidates for accepted gameplay.


## Active resumption — 2026-10-21
Owner resumed Codex as sole active developer (Issue15 comment6308769794).
Main refreshed to9fa2f1d366b7c386910b9173967faeba86b51396, PR181 source
b4c1d39f0476b004f772506abd1b378e055ad03e. Scratch branch
`codex/corridor-scratch-integration-20261021` preserves Claude refs.
Gate overlay removes inert ladder19,5 and replaces unbuilt exit mouth24–26,21
with adjacent existing cave wall, removing arrow25,20. Exactly five changed cells;
source candidates retained. All six overlay headers reuse existing Averon music.
25/25 focused host tests PASS. Seven-map existing map_qa static: zero findings,
including8 reciprocal Route202/City openings and all neutral warp paths.
Initial build correctly rejected missing220 before221. Scratch only now includes
exact Verity220 definition from4ed99916f0aeb6bee81e9aedf51f40fb6d66730e.
Standalone C bank was invisible to existing QA parser; scratch uses conventional
headers.h/metatiles.h definitions instead. No QA infrastructure change needed.
NORMAL build currently in progress; no ROM/runtime/native PASS claimed yet.
`apply_scratch_overlay.py` reproduces this source assembly with exact pins and
requires explicit disposable marker/scratch branch; it is NOT production approval.
Route202 production exclusive-files gate still fails for missing owner authority.

Paired scratch builds now PASS at local source44945713 (full SHA in evidence):
NORMAL linked17354196B, EWRAM226480/IWRAM28392, ROM SHA256
4151a11ffc6f17065554e8889c2b45d2201db9e4c6d46dfa94c88446cef86cf6.
RELEASE linked17473332B, EWRAM226482/IWRAM28336, ROM SHA256
3f10a15235328a884ad987b630006325ea775ea02e658307cb1c7df5e39370c3.
GCC14.2.1, default cries OFF; no ROM uploaded. Native subset compiling; actual
graphical normal traversal ongoing. Xvfb initially could not bind display sockets
inside restricted sandbox; network-enabled execution permits local X/GDB sockets.
Do not claim initial no-window attempt as game defect or acceptance.

Owner explicitly requested recurring instruction checks during this session.
Native automation "Check Averon task instructions" is enabled every two hours
(America/New_York); it reads latest15/PR assignments, reports meaningful changes,
and supplements this task without spawning competing edits or restarting Claude.
This explicit owner request supersedes older no-scheduler directions only for
the requested instruction scan. No autonomous production merge is authorized.

Subsequent actual scene inspection identified Center's unused escalator still
visually open to an unbuilt floor. A narrow seven-cell overlay-only repair now
reuses its adjacent wall/floor and restores the old approach elevation. Both real
doors unchanged. Host28/28 PASS; static seven-map audit0. Updated NORMAL built;
RELEASE and complete paired graphical/native rechecks are IN PROGRESS. Prior
37/4 native and63/3 profile evidence remains tied to44945713, not this new
1f21747e source. No prior evidence is relabeled as final acceptance.
