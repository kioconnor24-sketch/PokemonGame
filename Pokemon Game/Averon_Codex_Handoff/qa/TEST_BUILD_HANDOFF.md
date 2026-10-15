# Current compiled field-license build

Local file: build-output/Pokemon-Averon-Field-Licenses-d1395442.gba
Also available as build-output/Pokemon-Averon-Test-Build.gba.
Source d1395442f3e11efcd539c14590d6fda67aa4ad85 on codex/field-licenses (PR10).
Size33554432bytes; SHA256 ea651ca5feb9e03ad06902e594841591818498b92292dbf13434d49e405db5c0.
Normal incremental build exit0; logs evidence/builds/20261015T071739Z/.

Field licenses gate Cut/Rock Smash/Strength/Surf/Waterfall/Dive/Fly without
teaching moves. Party FIELD KIT exposes the existing native callbacks.
Native29/29 and save-layout4/4 PASS for the license core at
 evidence/builds/20261015T070904Z/. Later developer-map-only changes were
statically checked and normal-compiled; the native suite was not rerun.

Developer R+START -> Scripts -> Script4 enters the isolated field lab.
Use a backed-up test save. Left scientist asks before granting all licenses;
next scientist revokes them; right NPC returns to Saltmere. Obstacles: Cut
 tree, Rock Smash rock, Strength boulder and Surf pool. No party is overwritten.
Release preprocessing excludes entry/grant implementation and emits stubs.

Task2 IN PROGRESS: paired Dive/Waterfall fixtures, Fly destination coverage,
actual menu/cancel/follower/obstacle/animation traversal and Delta pending.
The implemented license core/menu are BUILT — RUNTIME TEST PENDING, not PLAYTESTED.
Existing opening/Gym1 natural walkthrough is also incomplete.
Stable integration baseline preserved at evidence/backend/averon-integrated-baseline.gba;
clean GitHub build +26 native tests pass in run38696580924 on baseline3318b59c.
Generated ROMs and saves remain local and ignored; never publish full binaries.
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
