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
