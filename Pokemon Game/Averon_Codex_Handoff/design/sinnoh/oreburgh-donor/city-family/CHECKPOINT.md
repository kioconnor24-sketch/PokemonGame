# Oreburgh City / Route207 shared art — saved source candidate

Saved 2026-10-22 America/New_York. This is **off-engine source art and a coupled warp plan**, not an installed or accepted Oreburgh corridor. No permanent section values are allocated. Every production engine file is unchanged from main `f4548cca06d56c45595cbcb3386ed32f09d5a362`.

## Source and output identities

- Geometry and donor semantics: `38228bb574a3557345852b758d5f1a65eb01bb22`; merged #204 geometry applies only its disclosed closures. City 70×59 and Route207 64×32.
- Existing Averon pixels/palettes, Rustboro facade templates and runtime enums are read and hash-verified against base `f4548cca06d56c45595cbcb3386ed32f09d5a362`. Full consumed-file hashes and source attributes are in receipt.json.
- Route207's prior art is consumed as immutable data from #205 `920cf050e4a79f4899ff86539540cb0efcadfe3e`. Fetch that ref before reproduction in a shallow checkout. Its 15 used secondary records and complete rendered RGB pixels are unchanged.
- Common family: primary 512 records, secondary **439 records, 73 free slots**. This is a metatile-slot measurement, not ROM growth. No donor image/palette or new pixel data is included. Bank blobs total 17,118 bytes; final linked ROM growth is unmeasured.
- Every **6,178** cell's collision/elevation upper six bits and complete source behavior/layer word are independently checked during generation and the published-file host test. City low ten-bit art indices may change. Route207 map bytes remain unchanged.
- City source indices 0,11,12,13,14 compact to 0,1,2,3,4 as one coherent plan. Both B1 City-return destinations change together 11→1 and 14→4. All six B1 events, four downstairs triggers, and B2 return to B1 event2 remain intact. Gate east event1 at25,20 ↔ City event0 at6,12 is validated. Production Gate is untouched. No installer is implied.

## Executed evidence

```sh
. /workspace/.onboarding/activate.sh
python3 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/oreburgh-donor/build_city_family.py' \
  --donor /workspace/sinnoh-donor-pinned --engine 'Pokemon Game/engine' \
  --out /workspace/scratch/oreburgh-city-family-final-b-20261021
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s 'Pokemon Game/scripts/tests' -p 'test_sinnoh_oreburgh_city_art.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s 'Pokemon Game/scripts/tests' -p 'test_sinnoh_*.py' -v
```

- Focused **13/13 PASS**, zero skips: complete attribute deduplication, all64 C/E combinations, different layer words, primary reuse, bank exhaustion, malformed dimensions/art/source attributes, input immutability, full published-map preservation, coupled sparse City returns, invalid anchors/destinations, and all source mine events.
- Complete existing Sinnoh source suite **180/180 PASS**, zero skips (13 above are a subset). Local Python3/Pillow via the existing onboarding environment.
- Two independent fresh builds `final-b` and `final-c`: **10/10 output files byte-identical**, including both PNGs, two maps, four bank blobs and two JSON receipts. No production source changes.
- Static PNGs actually inspected. The first exploratory render exposed mismatched foreign secondary ordinals (path edges rendered as water, unrelated facade fragments); those were replaced with existing Averon paths, neutral facades, soil and wood. This diagnosis did not change geography, collision or source behavior.
- No NORMAL/RELEASE ROM, native game execution, emulator traversal, service, listening, save/load or graphical gameplay acceptance was run for this source candidate. Do not reuse #206 northern runtime results as Oreburgh evidence.

## Remaining visual / integration limits

The candidate uses existing gray/gold facades in donor building envelopes. Metatile resampling visibly repeats some roof/door rows; the industrial yard is simplified soil/wood rather than donor gantries. These are disclosed art limitations, **not final graphical acceptance**. All unbuilt interiors remain closed by #204's source closures despite recognizable Mart/Center/Gym facade cues. No service scripts or interiors are installed. Mine-entry gray steps preserve source south-arrow semantics but need real traversal testing.

Next executable task: inspect/refine these static facades, then prepare one coherent disposable four-area City/207/B1/B2 integration using merged #198/#204 and the coupled warp plan. Restore Gate's east event only within that candidate, verify seam + all mine paths, and run actual NORMAL/RELEASE, native/negative, follower/menu, Save→fresh-process Continue. Source-art merge alone authorizes no production map or saved ID227+. Permanent origin policy remains a separate owner decision; do not invent it to make a ROM build.

GitHub upload/check status and exact commit are recorded in the PR and Issue15 final handoff; this file avoids a self-referential commit hash.

## Artifact SHA256

```json
{
  "city-family/OreburghCity/averon.png": "c1ee7a1485d12676e1ff4d9897aaa1c1356c07a59a7cb041789c7b79794ea95d",
  "city-family/OreburghCity/map.bin": "ebc1b5c41ef7a7d0a26eda8ac0edf02ec6945f0af5f922e3c7bd46a3101896e6",
  "city-family/Route207/averon.png": "556613c2f387ae83cfbc4edba8f7d7af2523ddb80c3337ba1c76f811add5c74c",
  "city-family/Route207/map.bin": "b21dff39fc3f721a48f654d934c5eeecd952458032f95010ca9c1e4482a474e6",
  "city-family/banks/primary/metatile_attributes.bin": "5d29d2955d8f86e187d3aa145f76747bfb9947d54f21c04bd9b9b890f265dcca",
  "city-family/banks/primary/metatiles.bin": "a610df7e921699e100e7bbe5831492a552e8ef317d23963cac78fbf2875a5ea0",
  "city-family/banks/secondary/metatile_attributes.bin": "858160b569ae7b127588e911422e95450d2b180b5de1acce6865b8a0d9a8c574",
  "city-family/banks/secondary/metatiles.bin": "323a0684dbdbd2be3c60fb5cd318b328d55c6006fe472340a2cd74cdf9b57702",
  "city-family/receipt.json": "a4f86d2a87a2240832ffa4f11c54d40af1141c0e4f869726fad89e6cd3cded3a",
  "city-family/warp-plan.json": "e6e352e45173442036aa8ac540a37f533621416c0137dda9910aa0cf61581918",
  "build_city_family.py": "8c3785cd4ff16a23c5965078b1e54beaf53d41ff067a4fe5b7e4ad3c7f955d23"
}
```
