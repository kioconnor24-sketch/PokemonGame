# Expanded native traversal acceptance — 2026-10-15

Latest source `5c92e6ff`; local `build-output/Pokemon-Averon-Field-Menu-5c92e6ff.gba`.
Size 33,554,432; SHA256 `86800da9ec7531feabe5ef59fc0ceec0b4d2a188ac01d088567b3e3568e3dada`.
Native **43/43**, save-layout **4/4**, normal `make -j12 -O all` PASS.
The ROM hash matches the prior menu build because additional harness/test code
is excluded from normal game compilation; no production source changed in this
second test extension. Logs are recorded by the local BUILD-MANIFEST.json.

Added real-map Surf/Waterfall terrain and direction checks, native Dive/emerge
preparation from actual tiles, Pokemon follower water/land visibility policy,
actual Fly-cursor rejection of an unvisited destination and selection of the
Saltmere landing, Fly cancellation preserving second-party-slot selection,
and all seven licensed actions rejecting unusable contexts without trapping
controls. Test driving explicitly stops before initializing an unrelated
full overworld scene. These are NATIVE-TESTED semantics, not rendered traversal.

Focused Windows mGBA acceptance is being attempted on an isolated ROM/save in
`evidence/field-runtime/`; original saves are unchanged. No field gameplay
acceptance or Delta verification is claimed by this note.

---
# Latest native Field Kit acceptance — 2026-10-15

Source: `54432345` on `codex/field-licenses` (PR #10). Local artifact:
`build-output/Pokemon-Averon-Field-Menu-54432345.gba`, 33,554,432 bytes,
SHA256 `86800da9ec7531feabe5ef59fc0ceec0b4d2a188ac01d088567b3e3568e3dada`.

- `scripts/build-averon.ps1 -Sync ... -NativeTests -SaveLayoutTests -Jobs 12`:
  38/38 named native tests, 4/4 save-layout tests; normal build exit 0.
- New integration harness drives real native party/Fly callbacks, input tasks,
  windows, sprites and fades in headless mGBA. Tested all seven locked actions,
  Back/B, party selection/exit, Fly-map cancellation/reopening, nine-action
  capacity, fainted/egg eligibility and three obstacle target preparations.
- Guarded the native missing-object sentinel before reading obstacle graphics.
- NPC follower restriction test initially failed because the optional human
  NPC follower feature is disabled. Preserved that production configuration;
  tested its current policy and outdoor/indoor Fly rules. Did not enable a new
  save structure. Pokemon followers are a separate enabled system.
- Evidence: SOURCE / BUILD / NATIVE-TESTED. No manual emulator or Delta check.
  Full rendered movement/obstacle effects/Surf/Waterfall/Dive and Pokemon
  follower transitions remain pending; FIELD is not merged or complete.
- Test seams are under `#if TESTING`; release menu behavior is unchanged.
  Stable baseline ROMs are preserved. No ROM or save is published to GitHub.

The first menu run passed 34/34 before adding four more tests. The intermediate
38-test run failed one incorrect NPC-feature assumption; it was not counted as
passing or published. The corrected final run passed 38/38. Exact logs are in
`build-output/BUILD-MANIFEST.json`'s local `logs` directory.

---
# Current field-license checkpoint — Fly fixture

Branch: `codex/field-licenses`, PR #10. Exact pushed commit and evidence are
recorded in the latest PR HANDOFF comment. Field licenses remain IN PROGRESS.

The lab scientist at (5,16) confirms before enabling the native test Fly
destination. It sets only the visited flag; a Fly license and healthy non-Egg
partner are still required. Select LITTLEROOT TOWN on the placeholder Hoenn Fly
map to land at the existing Saltmere home point (18,18). Both player genders
are covered by the native destination/warp test. Debug Script4 returns to the
lab. Release builds stub this preparation control. This is a developer fixture,
not final Averon geography or a license earning location.

Fixed: Fly formerly selected vanilla ground-floor home destinations, escaping
into unused Hoenn. It now uses the existing Averon home/initial respawn entries.
No save IDs or structures changed.

SOURCE / BUILD / NATIVE-TESTED: `make -j4 -O all` passed; `make -j4 -O check
TESTS='Averon'` passed 31/31 named tests, including both gender parameters in
the new Fly regression; `make -j4 -O check TESTS='test/save.c'` passed 4/4.
Repeated authoring (79 files), map checks (16 maps), dialogue (207 lines),
design integrity and persistent event-ID audit passed. The new regression
failed against the old resolver before passing with the fix.

EMULATOR gameplay / DELTA: NOT VERIFIED. Native tests execute through the
bundled headless mGBA runner; they do not prove rendered menus or animations.
Next: exercise Field Kit locked actions, B/CANCEL, Fly-map cancellation and
return to ordinary movement, then obstacle effects, follower interactions and
Surf/Waterfall/Dive gameplay. Keep all full ROMs and saves out of Git.

# Archived compiled build — a25755fb

Local file: build-output/Pokemon-Averon-Field-Licenses-a25755fb.gba
Also: build-output/Pokemon-Averon-Test-Build.gba.
Source a25755fb8870c73d6ff6605998a5312e6af731ce on codex/field-licenses (PR10).
Size33554432bytes; SHA256 1a7414dc408ced396eedeba0267a19c8caaeff0fb2ceed90d6359636c0a10a41.
Normal build exit0; native30/30 and save-layout4/4 PASS.
Logs: evidence/builds/20261015T073022Z/.

Native checks cover seven independent move-free license permissions, unusable
parties, flash persistence and actual bidirectional Dive map warp functions
preserving coordinates, party and licenses. Static16 maps/201 lines/79-file
authoring PASS. These checks do not demonstrate field-effect animations.

Developer R+START -> Scripts -> Script4 enters the isolated lab. Use a backed-up
test save. Left scientist confirms before granting licenses; next revokes them;
right NPC returns to Saltmere. Native Cut tree, Rock Smash rock, Strength boulder,
Surf pool, Waterfall column and a deep-water patch with a matching underwater
room are available. No party is overwritten. Release entry/grant code is inert.

Task2 IN PROGRESS: Fly destination fixture and actual menu/cancel/follower/
obstacle/animation traversal remain. Delta and the natural Gym1 walkthrough
are unverified. Compiled features: BUILT — RUNTIME TEST PENDING.
The integrated baseline and previous clinic ROM remain preserved locally.
Generated ROMs/saves must never be published on public GitHub.
The user can upload this file directly into the ChatGPT testing conversation
where sharing is appropriate. Do not publish the full binary on public GitHub
or Releases. No direct transfer to another conversation has occurred.

Runtime capability of ChatGPT's environment is unverified. An executable named
`mgba-rom-test` does not establish ability to boot or inspect this game. Report
the actual emulator/version, launch result and screenshot/log evidence first.

Focused outstanding acceptance:

1. Workshop/Fennekin and harbor/Piplup first accepted errand; declined starter
   confirmation, full bag/party, native save during an errand and reset/reload.
2. Route traversal, clinic healing/PC and whiteout recovery in Alderfield.
3. Both irrigation switches, persistent open gate, Elio victory, one badge,
   Work Up TM and retry when bag full; cap 15 before win and 23 afterward.
4. Six-member EXP: active member and actual held Exp. Share recipient gain EXP;
   other nonparticipants do not. Test item removal and cap behavior separately.
5. Set mode without free switch prompt; legal Mega transformation; starter and
   nonstarter followers. Delta iOS acceptance is a separate human test.

Developer-only R+START menu, Scripts 1/2/3 respectively creates a cap-test
party, legal Mega Charizard, or six-member EXP party. Back up the native save
first; fixtures overwrite test parties. Never count fixture battles as natural
progression balance. The fixture code is built but has not been runtime tested.

Bug reports should include source SHA, ROM SHA, map/event, expected and actual
behavior, reproduction steps, and relevant screenshots/logs. Do not label
untested features as passed. Use **BUILT — RUNTIME TEST PENDING**.
