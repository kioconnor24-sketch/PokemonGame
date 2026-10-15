# Native optional events — QUEST / PR #14

Status: **BUILT — RUNTIME TEST PENDING**. Source/native evidence never substitutes for rendered
NPC interaction or Delta acceptance. Exact final source, test counts and local
ROM hash are recorded in the PR HANDOFF and local build manifest.

Local result: 49/49 named Averon native tests and 4/4 native save-layout tests
passed, including actual `DoWhiteOut` reset/heal/warp followed by reentry cleanup
at each saved event stage. Normal GBA compilation passed. EWRAM: 226420 bytes;
IWRAM: 28392 bytes; linked ROM: 26730216 bytes. No runtime heap-usage claim.
Host checks: 7 event-flow tests, 10 installer tests; 79 regenerated files stable,
16 maps reachable, 215 dialogue lines within 208 pixels; namespace 24 Averon flags
and 8 variables, zero blockers/warnings. Design integrity check also passed.

## Implemented behavior

- Coastal Field Notes keeps its existing researcher → coastal Hiker → researcher
  favor and natural optional conversation. Existing flags 0x2A–0x2C retain their
  meaning. Declining does not change saved progress.
- Berry Tree Sketch keeps its artist and meadow boy. The boy now gives a hint;
  examining the existing tree at Coastal Meadow (12,27), from (11,27), records
  the observation. Talking to the boy alone cannot finish it. Examining the
  tree before the artist, or repeatedly afterward, cannot skip/reset progress.
  Existing flags 0x2D–0x2F retain their meaning, including older saves that already
  recorded the boy's observation. No terrain, map connection or character added.
- Both NPCs call small native reward boundaries. Both prerequisites are required;
  full Bag leaves rewards pending; the saved reward flag changes only after
  successful native `additem`. Later interactions cannot duplicate rewards.
- One scientist at (25,19) in the existing developer lab offers a level-5
  Wobbuffet after the sketch reward. Full party preserves a retry; this fixture
  deliberately does not deliver to PC. Its single saved flag is newly allocated
  at 0x37; existing quest/FIELD IDs are unchanged. No new saved variables/schema.
  The existing release guard excludes its scripts and release entry is a stub.
  The fixture is not a production Pokémon placement or unlock decision.

## Reproducible checks

Run from the project directory with the existing Python/WSL environment:

```text
python3 scripts/test-averon-quest-flow.py
python3 scripts/test-averon-sidequests.py
python3 scripts/check-averon-authoring.py
python3 scripts/check-averon-maps.py
python3 scripts/check-averon-dialogue.py
python3 scripts/audit-averon-event-ids.py --engine engine
python3 Averon_Codex_Handoff/scripts/validate_design.py
```

`engine/test/averon_optional_events.c` calls the actual compiled event bytecode,
not the Python source interpreter. It covers prerequisite rejection, repeated
claims, actual full pockets, flash save/load at all four existing event states,
coexistence with badge/FIELD flags, tree observation, full-party retry and PC
non-delivery. Run `make check -j12 TESTS=Averon` and
`make check -j12 TESTS=test/save.c` in the persistent WSL engine; compile the
normal ROM with `make -j12 -O all`. Require positive executed test counts.

## Rendered acceptance still required

Use an isolated copy of the local ROM and backed-up test save:

1. Researcher in Alderfield (12,16): decline, return, agree; visit the Hiker in
   Coastal Bluffs (35,7); save/reload, return and receive exactly two Great Balls.
   Repeat with a full Balls pocket, make room and retry.
2. Artist in Windrow (20,14): decline/return, agree. Speak to the boy at Meadow
   (10,22): he only hints. Examine the existing tree from (11,27) facing right;
   save/reset/reload; return for exactly three Oran Berries. Repeat with full
   Berries pocket. An old save with FOUND already set remains claimable.
3. Whiteout before and after either observation, return and verify the correct
   dialogue/reward. Native whiteout tests do not establish rendered nurse flow.
4. Debug Script4 enters the existing lab. After sketch completion, decline and
   retry the gift scientist (25,19), test six-party rejection, deposit one Pokémon,
   retry, save/reset/reload and confirm the gift cannot repeat. No PC gift expected.
5. Check text, sound, restored player control and follower recovery. Delta is
   independent owner acceptance. Do not merge solely on native test results.

Next acceptance task: execute these bounded rendered interactions and record
actual screenshots/results on the same PR; fix any observed defect before merge.
