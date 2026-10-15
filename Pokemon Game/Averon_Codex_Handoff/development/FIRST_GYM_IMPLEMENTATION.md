# Alderfield prototype (under construction)

Authoring entrypoint: scripts/build-averon-first-gym.py. It also regenerates the
opening using the prior authoring source. Keep layout IDs in place on updates;
saved map layout indexes must not change when editing a layout.

Orchard Lane connects Windrow to Alderfield. Includes two grassy forks, a
picnic clearing, canal crossing, three optional trainer teams and an Exp. Share
giver. Alderfield has farm fields, a canal market, supply shop, clinic and Gym.
Clinic has a dedicated whiteout respawn location. Existing upstream tiles are
prototype art. Distinct mill/dairy/market props remain future map polish.

Gym: west and east sluice interactions set independent saved flags, both open
the central farm gate. Elio uses Bunnelby/Lechonk/Lillipup at 12/13/15; one
optional Gym trainer. Badge 1 is granted after victory. TM01 is mapped to Work
Up for this prototype, and a bag-full reward can be reclaimed later. Team levels
and route EXP pacing remain unverified until a natural playthrough is tested.

Set behavior enforced in battle initialization and Options. Hard EXP cap uses
the engine flag list with approved Averon ceilings, plus candy cap. Badge 1
raises the ceiling from 15 to 23. No Sinnoh cap chain implemented yet.
Mega is the only usable battle gimmick; Primal/Ultra Burst forms disabled.
Held-item EXP Share remains GEN_5 with party-wide sharing flag 0.
EXP allocation now also uses B_SPLIT_EXP GEN_5: participants share one half
when a holder exists, holders share the other half. Modern full-participant
EXP allocation no longer applies. Runtime six-member checks remain pending.
These are source changes, not runtime passes. Mega/cap/EXP edge cases pending.

Build corrections: use upstream `Leader Norman` portrait identifier for Elio's
placeholder; TM01 Work Up needs both move mapping and its own item description,
with legacy Focus Punch item references aliased to that slot. Final incremental
build detected a zero-byte Linux heal_locations.json; restored from the saved
Windows source (43 entries). Do not treat a stale previous ROM as that build.

New reservations: flags 024 (future assault complete), 025/026 (sluices), 027
(Exp. Share), 028 (Gym TM). Trainer IDs 859–863 use remaining original slots;
trainer count 864, original maximum 864. No new saveblock trainer space.

Opening follow-ups included: PC tiles in home/cooperative, National Dex enable
on starter receipt, walkable route grass, immediate follower refresh. Preserve
all old local ROM builds and save evidence. Source maps/dynamic saved viewport
data can differ after edits; clean new-game tests are required for final QA.

## Gate/EXP follow-up

Both live sluice interactions redraw the map after changing gate tiles, as in
upstream's Petalburg puzzle. Elio also checks both sluice flags before offering
his first battle. On-load tile restoration remains separate and persistent.
The native checker flood-fills the actual collision grid with NPC obstruction:
both workers reachable while closed, leader unreachable before and reachable
after opening, and both exit tiles accessible afterward. These static checks
do not establish animation, save reload or battle behavior in an emulator.

`scripts/test-averon-caps.py` compiles the actual first two caps.c functions
with mocked save flags using the host C compiler. All 11 progression ceilings
and EXP below/at/above each ceiling pass. Rare Candy configuration is checked;
actual item use is still a runtime test.

`engine/test/battle/averon_exp.c` adds six automated native battle scenarios:
six-member party, held item present/absent, lead and holder below/at first cap.
The active member receives less EXP when a holder shares the pool. These use
the existing `make check TESTS="Averon"` framework and headless mGBA runner.
Executed successfully: one parameterized test, six scenarios, PASS; command
exit 0. Evidence: `evidence/m2/automated-exp-check.log`. The runner operates
headlessly and does not verify overworld traversal, Gym events or native saves.

## Harvest fair and starter follow-up

The market vendor and canal keeper now provide the atlas's ordinary harvest
fair errand. Accept, collect the apple crate, return to the stall, receive one
Super Potion. VAR_AVERON_HARVEST_FAIR reuses unused 0x40A8 with states 0–3.
Bag-full reward failure leaves state 2, allowing a later claim. Native script
tests execute delivery/reward ordering, duplicate protection and full-pocket
retry successfully. Conversation UI and save persistence remain pending.

Optional Nico double battle uses Bunnelby 10/Lillipup 11 and the native
two-usable-Pokemon refusal. Production trainer generation and TM01 Work Up
mapping pass automated checks. A visible Gym statue marks the rules.

Starter acceptance and gift operations are small native subroutines shared by
the actual dialogue flows and isolated script tests. They preserve the first
accepted errand, refuse full parties without committing Mira/claimed state,
and prevent duplicate starter awards. All three gifts at 0/5/6 occupied slots
pass, along with all six household orders and active/completed reacceptance.

Authoring regeneration is deterministic across 63 checked source/map files.
Dialogue uses actual normal-font widths, with an 8px reading margin in the
216px message window; all 151 authored lines fit. Rendering/width checks do
not replace gameplay or final art review. Native tests now total 11 PASS.
