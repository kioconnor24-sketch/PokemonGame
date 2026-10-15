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

Starter gift follow-up: all eight named native tests PASS, exit 0. Nine gift
cases cover Snivy/Fennekin/Piplup with 0, 5 or 6 occupied slots; successful
awards are Lv5, assign Mira the third species, preserve existing party members,
and reject repeated awards. Full parties preserve the unclaimed reward and
Mira assignment. Native award logic is shared by the actual confirmation flow
and the isolated script tests. Dialogue choice UI and persistence still pending.
A visible Gym statue now marks the cap/Set rules; native collision checks pass
and the layout was rendered for visual review. No manual emulator navigation.

Harvest fair and reward mapping checkpoint: all **11** named native tests PASS,
exit 0, through `make check -j12 TESTS="Averon"`. New tests cover real fair
script order/one-time reward, full-pocket failure and later claim, and actual
TM01/Work Up item mapping. Fair content is compiled and isolated state/reward
logic tested; conversation UI, whiteout and native-save walkthrough remain
pending. The latest full game compilation exits 0 (`evidence/m2/fair-final-build.log`).
Latest ROM SHA256 `f333ca782f09875095c5de28ca3052ac615066212ce27f26d2e8d16be328f0bc`.

Static authoring and dialogue checks pass: 63 files stable across repeated
regeneration; 151 normal-font dialogue lines fit a conservative 208px margin.

## Healing, respawn, cap and Gym reward checkpoint

All **19 named Averon tests PASS**, exit 0 (`automated-split-check.log`). New
checks execute healing through the native script special (HP/status/PP restored,
species/items preserved); actual whiteout target selection for home/clinic;
large EXP rewards clamped at Lv15 without banking excess; native Dark physical
versus Ghost special move damage; and badge-gated, one-time Gym TM delivery
with full-pocket retry. Actual whiteout scene/warps, not just target selection,
remain a separate gameplay check.

Elio's generated team stays Bunnelby12/Lechonk13/Lillipup15. His ace holds an
Oran Berry and knows naturally learned Work Up. Check Viability AI is enabled;
the production trainer has no Omniscient flag. Team-generation assertions pass;
natural battle difficulty has not been tuned or declared passed.

Direct native Rare Candy regression first FAILED: the menu guard existed but
the underlying item effect still accepted a capped Pokemon. A player-only
guard in PokemonUseItemEffects fixes this path. The same test now PASSES:
14→15 succeeds, another candy is rejected, and after Badge1, 15→16 succeeds.
Before/after logs: `automated-candy-before.log`, `automated-candy-after.log`.
Normal build exit0: `gym-reward-build.log`; ROM SHA256
`dced4e3cf19cc5c440ef54b4342cb43fc8eaed6ea939259134f67fc7d96b9491`.

Existing `make check -j12 TESTS="test/save.c"` also passed all four save-layout
tests (SaveBlock1/2/3 and PokemonStorage). This is structural compatibility
evidence, not a replacement for a native save/reset walkthrough.

Map-check follow-up traces a single connected component through each map's
real door/border entries, blocks NPC occupancy and Surf-only water, handles
counter interactions, and checks every current NPC/sign approach. All 13 maps
pass. This is a static walking model; elevation/ledge events and actual camera,
warps, input, scripts and saves still require full gameplay acceptance.

Coastal preview checkpoint `19e5072e2589968981530f29a40fa4e4624d84cd`:
all20 native tests and four save-layout tests PASS through build-averon.ps1.
New production trainer test verifies reused slot568, unchanged MAX864, and
Wingull14/Rookidee15. All14 native maps and166 dialogue lines pass static
checks;68 authored files are stable across regeneration. Bounded route gameplay
and repaired north terminus remain pending; no Breakwater implementation claim.
Current ROM SHA256 `0646a37269e04c09ad873e69d98deb8d791924c492eebd17501306fc6c718861`.

Evolution and native flash checkpoint (2026-10-14 EDT):
`make check -j12 TESTS=Averon`: 23/23 PASS; save-layout check:4/4 PASS.
`make -j12 -O all`: exit0, normal ROM hash unchanged0646a372…718861.
Logs: evidence/builds/20261015T032656Z/{native-tests,save-layout-tests,build}.log.

All three starters are blocked from crossing cap15 with Rare Candy; after
Badge1 the actual native evolution resolver selects Braixen/Prinplup at16
and Servine at17. Everstone blocks these evolutions; removing it permits them.
The evolution animation, confirmation/cancel and post-evolution moves remain
unverified in ordinary gameplay.

Native flash regression initializes actual detected flash, erases only the
isolated test runner save, saves and reloads twice. It verifies party species,
level, held EXP Share, errand and harvest progress, sluices, badge, coastal pickup
and Gym TM flags. The actual Gym claim script grants Work Up; its bag entry
survives the second load and a repeat script call cannot duplicate it. No user
playthrough save is opened. This is not a power-loss or menu/reset test.

An intermediate expanded fixture failed because it wrongly called SavePlayerBag,
a link-room backup restore helper. Inspection confirmed ordinary bag pointers
already reference SaveBlock1. Removing that fixture error restores23/23 PASS;
no production bag code was changed. Failed log:20261015T032625Z/native-tests.log.
The build wrapper rejected that failure and preserved the prior published ROM.
It now also rejects missing/zero/partial result summaries and writes actual
passed/total counts into BUILD-MANIFEST.json before publishing a successful ROM.
