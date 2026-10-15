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
