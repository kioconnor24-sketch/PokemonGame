# Technical and creative decisions

2026-10-14 engineering session: retain untouched upstream source at
73b3fbeb574327cd9420c89e56bef5aa3c08fead for M0. Follow its WSL instructions;
do not attempt MSYS2/Cygwin, which this revision explicitly says are broken.
Pause game-code work at the failed WSL setup boundary. This changes no
creative requirements. A separate upstream engine checkout preserves history;
root Git ignores generated ROMs and the nested checkout.

Date | Decision | Evidence / reason | Implications
---|---|---|---
2026-10-14 | GBA Emerald Expansion rather than White 2 | Mature source-level tooling | Output `.gba` not `.nds`
2026-10-14 | Averon + Sinnoh, Red final boss | User-approved story and map structure | Two full regions and extensive QA required
2026-10-14 | Max level 100 | User choice | Do not alter experience bitfields for 120/200
2026-10-14 | The ten-operative battle sequence has a scripted allied heal afterward | User choice | Test whiteout/resume and status carryover
2026-10-14 | Boss rupture after a four-Pokémon first phase if true in-battle interruption is unstable | Avoid unsupported assumptions | Cutscene must still feel seamless
2026-10-14 | Starter assignment via first meaningful house visit | User choice | Must offer clear eventual acceptance and safe reentry
2026-10-14 | Rename childhood rival from provisional Rowan to Renn | Avoid conflict with Sinnoh's established Professor Rowan | All new text/flags should use RENN
