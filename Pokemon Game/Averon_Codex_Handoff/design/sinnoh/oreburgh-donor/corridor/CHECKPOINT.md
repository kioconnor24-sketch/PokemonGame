# Oreburgh City / Route 207 — source geometry checkpoint

**GEOMETRY ONLY. Graphics adaptation, ROM builds and mGBA traversal NOT TESTED.** No production engine, registry, saved-location code, scripts, story, encounters or donor pixels/palettes/music changed. Reuses accepted mine pair from #198; does not recreate it.

Pinned donor: `38228bb574a3557345852b758d5f1a65eb01bb22`. Base: `469c8db52cd713def08e8bddc3773103fc759bbc`. Run from repository root:

```sh
python3 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/oreburgh-donor/stage_corridor.py' --donor /path/to/pinned-donor --out /tmp/new-oreburgh-output
python3 -m unittest discover -s 'Pokemon Game/scripts/tests' -p test_sinnoh_oreburgh_corridor.py -v
python3 -m unittest discover -s 'Pokemon Game/scripts/tests' -p 'test_sinnoh_*.py'
```

The donor checkout must include City/Route207/Gate headers, layouts, and metadata read by the existing converter. The first build exposed missing sparse-checkout border/header files; adding the required source paths fixed the local checkout. No validation was removed. The builder verifies consumed bytes against pinned Git objects and calls the existing converter for donor-only identity proof; this does NOT verify Averon graphics.

## Actual result

- City: 70×59, blob `e475d8891ee8e50160679d05b9095c72b05e1f38`, 75 primary +183 secondary used metatiles. Staged SHA256 `bbad53605044afb179affd2aa7c44c5bde025c3a707e34f446af1db6093f422c`.
- Route207: 64×32, blob `08fb2516a753dbb621316d13703e564be9a94619`, 52 primary +15 secondary. Staged SHA256 `b21dff39fc3f721a48f654d934c5eeecd952458032f95010ca9c1e4482a474e6`.
- All6,178 cells retain exact elevation AND metatile bits. Exactly1 City and10 Route207 collision words change to close unbuilt endpoints; full coordinates/before/after/reasons are in the map manifests. All source NPC/coord/background gameplay events are excluded.
- Source City north↔Route207 south offsets +35/-35 verified; only overlapping boundary spans remain eligible. Route206 and Mt Coronet stay closed. City Gym/building/Museum exits are excluded; no unrelated Lilycove destination substituted.
- Source City warp IDs0,11,12,13,14 remain explicit sparse IDs. Both B1 City returns11/14 and all6 B1/four-wide basement entrances remain unchanged. These sparse manifests are DATA, not engine event arrays: a later installer must preserve slots or explicitly prove a coupled renumbering; never compact silently.
- Gate source warp1 is `(25,20)`→City warp0; City `(6,12)`→Gate1. #194 intentionally has ONLY Gate warp0, so restore the tested east endpoint and correct graphics/collision ONLY in a coherent combined candidate. This source package does not open production Gate.
- Local focused tests **10/10 PASS**, complete Sinnoh host discovery **167/167 PASS** (focused tests included, not additional unique outcomes). Two independent fresh conversions: **11/11 output files byte-identical**. Collision PNGs are original schematics, not donor-art renders or graphical acceptance.

## Next executable work

Adapt City/207 using existing Averon General/Rustboro/Cave/corridor art with source-specific behavior/layer/bridge validation; do not assume equal numeric metatile IDs imply equal records or pixels. Reuse accepted mine art. Build a disposable connected candidate with corridor #194 inputs, Gate east restoration, City/207 and mines; use only explicit temporary DEV identity mappings until owner chooses permanent227+ policy. Then NORMAL/RELEASE, relevant native/save goldens, two-way seams/warps, bridge/elevation/follower/menu and Save→fresh-process Continue with exact source/ROM identities. Existing source evidence is not that acceptance.

#202 independent security review is published separately; manager merge plus a new complete #194 handoff remain real production dependencies. Do not wait for them to continue source graphics work, and do not merge the divergent northern aggregate. No donor art rights or Delta acceptance have been established.


## Route207 existing-art follow-up (after #204 merged)

Main now includes policy202 and production194; previous authorization blocker is resolved. The separate follow-up branch adds `adapt_route207.py` and a rendered candidate using **existing Averon General graphics/palettes only** and existing Rustboro wood-bridge tile words. No donor pixels or palettes are copied. Raw map geometry is unchanged from b21dff39. Source behavior/layer words are copied exactly for every used map AND border metatile; runtime enums/fieldmap contracts compare equal. The pinned border adds478/479 absent from interior cells and is explicitly covered. Three initial naive/adaptation renders stayed private; final source trees remain intact rather than being replaced by grass.

Source 515–868 cliff/soil/wood/grass records are explicitly mapped into a 357-record isolated secondary metadata bank (155 remaining slots). Six primary sideways-stair records use existing flat gray step art while retaining exact diagonal movement attributes0x1049/0x104A and source elevations; this visual tradeoff still requires genuine mGBA review. Shared General files are untouched. All used graphics/palettes are in existing General, so the new secondary family needs no animation callback. No ROM/runtime result is claimed. Artifact provenance and per-used source attribute values are in Route207/art-receipt.json.

Actual follow-up tests: art11/11, complete Sinnoh178/178 against current main f4548cca (includes focused tests, not additional unique outcomes). Real static preview inspected: no water cliffs or architectural grass; original 2×2 trees retained; donor paths/vertical timber staircase remain legible in Averon style. City architecture is still unfinished, and paired coherent corridor builds/gameplay remain pending. Northern production is now the higher-priority unblocked lane; source-art progress is saved separately before switching.
