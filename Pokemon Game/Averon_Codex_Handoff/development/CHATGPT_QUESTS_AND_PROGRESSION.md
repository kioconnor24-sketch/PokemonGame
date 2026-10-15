# ChatGPT independent development batch: optional quests and region progression QA

Branch: chatgpt/early-quests-and-world-progression.

This batch adds native script source and a guarded installer, not a compiled game update.
Do not mark either quest runtime-tested or assume either exists in published ROMs.

## Coordination with Codex's first Gym

Codex PR #1 owns opening, Alderfield, CoastalBluffs and the current map generators.
This branch does not edit any of those generated map files or battle source
on GitHub. It provides an opt-in overlay generator meant to run after PR #1.

Integration order AFTER PR #1 is accepted:

1. Run python scripts/build-averon-coast.py in the Pokemon Game project directory.
2. Run python scripts/build-averon-sidequests.py AFTERWARD.
3. Run python scripts/test-averon-sidequests.py and existing map/dialogue
   checkers and regenerated-file consistency checks.
4. Synchronize regenerated engine changes to the verified build checkout.
5. Compile using the existing persistent toolchain.
6. Run appropriate native automated tests and later targeted emulator tests.
7. Commit generated source only after the pipeline is reproducible.

Running the base generator after the sidequest installer overwrites added NPCs.
Do not add the overlay to the build wrapper until the full authoring pipeline
and reproducibility tests include both steps.

## Optional quest A: Coastal Field Notes

- Researcher in Alderfield's market path asks the player to consult the lookout.
- Hiker on CoastalBluffs high trail supplies the requested observation.
- Returning to the researcher grants two Great Balls.
- Badge 1 implicitly gates the coastal portion via Codex's existing route.
- Stages are represented by the previously unused saved slots 0x2A–0x2C.
- If the Bag is full, the completion flag remains unset so the player can retry;
  the reward cannot intentionally duplicate.
- Dialogue is brief and unrelated to the main conspiracy.

## Optional quest B: Berry Tree Sketch

- Amateur artist in Windrow asks about the trees in CoastalMeadow.
- Child on CoastalMeadow identifies the berry tree.
- Returning to Windrow earns three Oran Berries.
- Uses previously unused saved slots 0x2D–0x2F; same retry guard.
- Available early and entirely optional.

These short adventures preserve an ordinary, cheerful Pokemon-adventure tone.

## Installer safeguards and known limitations

The installer reads the actual native layout binary and refuses to place an
NPC on a blocked tile, outside the map, or atop a registered event. It rejects
flag slots claimed by another feature and conflicting preexisting NPC scripts.
It validates target maps/slots before writing files. Idempotence is tested.

Intended placement coordinates:

| Map | Position | Role |
|---|---|---|
| Alderfield | (12, 16) | Field notes initiator/reward |
| CoastalBluffs | (35, 7) | Field notes observation |
| Windrow | (20, 14) | Berry sketch initiator/reward |
| CoastalMeadow | (10, 22) | Berry sketch observation |

These positions were chosen from the authored path geometry but have NOT
been tested against a current compiled game. If guarded install rejects a
coordinate, investigate the newest map rather than disabling safety checks.

Six persistent flag aliases are proposed; verify that they remain unused
before generating new game assets. Save compatibility depends on that check.
The script event commands match established Averon source conventions.
Compilation and gameplay validation remain outstanding.

## Region progression design audit

Command: python scripts/audit-averon-progression.py --project . --json-out progression-report.json

Reads design CSV files under Averon_Codex_Handoff/data: locations.csv,
route_network.csv and gyms.csv.

Validates route identifiers, endpoint names, unlock tokens, Gym locations
and expected badge-by-badge access from Saltmere. Also checks routes under
field cut, water traversal, postcoup, story-finale and postleague scenarios.
The Red fight endpoint in Sinnoh is explicitly excluded from Averon route
connectivity checks.

IMPORTANT: This is a design graph, not a scan of actual native map warps.
Bidirectional links and unlock availability are modeling assumptions.
Results do not establish that anything can be reached in a playable ROM.

## Verification record

Controlled local fixtures:

- test-averon-sidequests.py: seven tests passed.
- test-audit-averon-progression.py: nine tests passed.

NOT RUN: live installer against actual post-PR1 maps, engine compilation,
native event execution, emulator walkthrough, flash save/load, Delta on iOS.

Do not claim these quests are part of a playable ROM until those checks pass.
