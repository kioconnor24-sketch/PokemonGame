# Opening prototype implementation

User steering: proceed directly with changes and continuous checkpoints. The
baseline compiled and booted; complete untouched-base battle/save smoke test
was deferred at the user's request. Do not mark it Tested.

Authoring source: scripts/build-averon-opening.py and scripts/averon-opening.inc.
Generated engine maps use standard map.json, scripts.inc and layout binaries,
registered in gMapGroup_AveronOpening. No random placement or empty map bulk.

Saltmere: western/southern waterfront, short pier, homes and household errands,
Fenwick's gathering point, Renn by north exit. Coastal Meadow: two catchable
grass pockets, a stream crossing, optional lookout and one trainer. Windrow:
orchard rows, growers, cooperative healing. Alderfield is not open yet.

Prototype uses upstream Oldale house graphics and generic interior layouts.
Distinct greenhouse/workshop art, seagrass roofs, proper stone pier tiles,
lighthouse view and more interior decoration remain unfinished art work.
The existing region-map background is still Hoenn: three map-name sections
were appended but a full Averon region map is not implemented.

First accepted household task fixes VAR_AVERON_FIRST_HOUSE once (1 greenhouse,
2 workshop, 3 harbor). Completing that errand allows starter confirmation.
Refusal preserves the assignment. Full party is checked before award.
Starter flag is set only after MON_GIVEN_TO_PARTY. Renn gets the advantage
species; Mira's third species is recorded. Optional Pip screw and Windrow
Berry activity use separate saved flags. Standard in-game save is retained.

State reservations: vars 404E,4083,408B,4091,409B,409D,40A1; flags 020–022.
Both original initial heal-location slots now return to Saltmere/Home, avoiding
unintended Hoenn whiteouts. Fresh prototype saves required because map-section
and species-related save assumptions must be tested. Baseline save kept separate.

Follower configuration enabled, not yet claimed functional. Fixed Set mode,
hard caps, held-item EXP Share behavior and excluded-gimmick validation remain
M2 work. Starter bag supply retry has been added to the next build; runtime
bag-full and party-full tests remain required.

Build/test records: evidence/m1/. First build detected numeric local_id fields
being interpreted as preprocessor names; those fields were removed. Positional
NPC IDs remain valid native map data. Next: rebuild, boot, visual/collision/warp
review, starter interactions, battles and native save/reset. Do not call the
prototype playable until those actions actually run.

Saved engine checkpoint: `02c3cf5839` on `codex/averon-opening`.
Trainer IDs 855–858 assigned within original capacity 864; count raised to 859.
Static native map checks pass for reciprocal connections, warp destinations,
door approaches and NPC collision cells (evidence/m1/map-check.log).
