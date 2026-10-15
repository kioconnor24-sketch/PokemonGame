# Focused automated checks — 2026-10-14

Actual source behavior tested, rather than configuration-only claims:

- `python3 scripts/test-averon-caps.py`: PASS. Host C compiler runs extracted
  production cap functions with mocked save flags: 11 progression ceilings,
  unchanged EXP below cap, zero EXP at/above cap. Rare Candy configuration
  checked; native item use not tested.
- `python scripts/check-averon-maps.py`: PASS. Native warp/link/collision checks
  plus Gym flood fill with NPC obstruction. Sluices reachable before unlocking;
  Elio inaccessible before and accessible after; exits remain reachable.
- `make check -j12 TESTS="Averon"`: PASS, exit 0. Bundled
  `mgba-rom-test-hydra` + `mgba-rom-test` executes one parameterized battle test
  with six scenarios. Six-member party: nonparticipants without the held item
  gain no EXP; actual Exp. Share holder below cap gains EXP; lead/holder at cap
  gain none; active Pokemon receives less EXP when the item shares the pool.
  These are actual automated emulator battle results, not manual gameplay.
- `make -j20 -O all`: PASS, exit 0. Local test ROM SHA256
  `251c6947b807674fd0b8b73cb750a69a12827a2ecb91c5ad43cbe2892ec50e95`.

Still pending: first-Gym event/badge/TM/reload/whiteout gameplay; Mega, forced
Set/no-switch prompt; remaining starter branches and full bag/party; native
save compatibility after latest fixes; natural progression balance; Delta.
No manual emulator playthrough performed this session.

Relevant source checkpoint: `303ab9c6134f8fcbbf45190a2c6d8add1c53eaf9`
plus subsequent test-only extension covering the capped holder and allocation.
Logs remain local under `evidence/m2/`; this concise record is shared on GitHub.

## Subsequent rules, doubles and errand checkpoint

`make check -j12 TESTS="Averon"` now passes all seven named tests:
held EXP/cap, legal Mega Charizard X (including Tough Claws), excluded gimmicks
for both battlers, old-save Shift overridden by Set through an opponent faint
and replacement, production Nico doubles team generation, all six first-errand
orders, and repeat acceptance preserving active/completed errand states.
The testing-only Set override was removed; tests exercise the production rule.
Native tests use the actual compiled acceptance script subroutines, not a
separate model. Dialogue choices, complete starter award, Gym event rewards,
save/reload, natural balance and Delta remain separate acceptance checks.

Nico now offers the optional doubles preview specified in the Gym design:
Bunnelby Lv10 and Lillipup Lv11. Native trainerbattle_double supplies the
fewer-than-two-usable-Pokemon refusal path. Actual NPC interaction still pending.
Latest incremental game build exited 0; `evidence/m2/starter-build.log`.
