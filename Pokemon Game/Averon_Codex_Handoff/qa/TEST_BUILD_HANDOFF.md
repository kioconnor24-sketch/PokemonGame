# Compiled build handoff

Local upload file: `build-output/Pokemon-Averon-Test-Build.gba` from the
working project directory. This is the latest successful developer QA build,
not a final release. Generated ROMs remain local and ignored by Git.

Compiled with the existing WSL ARM GCC 14.2.1 toolchain using
`make -j20 -O all`; exit 0. SHA256:
`251c6947b807674fd0b8b73cb750a69a12827a2ecb91c5ad43cbe2892ec50e95`.
Source: `303ab9c6134f8fcbbf45190a2c6d8add1c53eaf9` on
`codex/first-gym-verification`. Latest fixes redraw the live Gym gate and
use Gen 5 EXP allocation. Host cap and native map reachability checks pass;
these do not replace native runtime acceptance.
Size: 33,554,432 bytes. Build source metadata is in the adjacent local manifest.

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
