# Claude M1 gameplay evidence (Gate B, Q1–Q5)

Real graphical mGBA 0.10.5 runs, played with ordinary key presses by the
`scripts/claude_play` driver (PR #97). Memory is only **read** (GDB stub); the
driver never writes emulator memory or save files. Runs start from the game's
own flash save through title → CONTINUE in a fresh emulator process. The
exceptions are disclosed fixtures (below): debug-menu actions on save copies,
and one save copy damaged on purpose before run30.

**This is Claude's own QA (self-operated, plus a separate read-only reviewer
pass by a Claude subagent). It is not a third-party or independent Playtest
verdict.** Nothing here contains a ROM, ELF, `.sav`, raw audio or emulator log.

## Build identity

| Runs | Source commit | ROM sha256 | ELF sha256 |
| --- | --- | --- | --- |
| run17 | `abb13f29fd…` (pre-#14 merge) | `66b58c3a90…` | in `provenance-start.json` |
| run18 onward | `bcfeb28dbc0f92b929747d41ffc66e4f1712c6e6` (main after #14) | `e6870c30ece40c6d180e9077b79c47ebae8b0d241ff02bdec645d3422a7f34e1` | `aa2efbd95a6285c04d197b7a956878647fc97968fefe9eed02f347bda3f4262d` |

The two ROMs are **not** byte-identical. After `bcfeb28d`, main's non-test
engine changes are only `data/event_scripts.s` and
`data/scripts/averon_legend.inc` (#25, SCRIPTED/LEGEND macro registration) and
`src/pokemon.c` (#96, delivery OT key); #95 added tests only. Open #101 changes
egg hatching. They do not change the Q1–Q5 quest, gym or clinic scripts, but #25 does
change `event_scripts.s` (which includes every script), so this is not proven
equivalence: the gameplay runs prove the `bcfeb28d` build. Each run's
`provenance-start.json`/`provenance-end.json` record source, engine-tree state
(never dirty), ROM/ELF/save hashes, driver commit and whether the driver tree
was dirty. **Driver dirty or driver changed during the run:** run17
(81500a2a→231570c4), run18, run19, run21, run22, run23, run26 (start clean, end
differs), run20 and run34 (clean at start, dirty at end). The driver only reads
memory and presses keys, so this affects reproducibility of the inputs, not the
game build; the packages list each run's start driver state.

## Save chain (flash sha256, first 12 hex)

```
run17 (old ROM)  29ea0df40d71 -> 0a7429783b43   Gym 1 won (Badge01)
run18 (new ROM)  0a7429783b43 -> 80100f9a6a0a   old-ROM save loads on current ROM; Q1 reward (state only: no dialogue frames were captured in this run)
run19            80100f9a6a0a -> 80100f9a6a0a   fresh-process Continue, trainer card, Bag
run20            80100f9a6a0a -> 2bc19b97b053   Q2 by walking, reward, save
 ├ run21 (COPY, DEV fixture) 2bc19b97b053 unchanged (stopped on a driver PC-menu bug)
 ├ run22 (COPY, DEV fixture) 2bc19b97b053 -> 1c05fc46dc1d   Q4
 └ run23         2bc19b97b053 -> 4b4eb93da3f5   Q3 genuine loss, whiteout, clinic, save
                 (the party first fainted in a wild battle on the walk to the
                 Bluffs, t≈40–171 s; that whiteout and heal were not captured.
                 The loss loop then lost again and that second whiteout and the
                 nurse were captured. The whiteout frame 0028 is caught
                 mid-print; run34 has the full text.)
   run24/25      4b4eb93da3f5 -> 4ca9b7f40dc6   Q3 fresh Continue, Q5 field checks
```

Full-pocket negatives run on **copies**, so the natural chain is not contaminated:

```
run26 (COPY of 0a7429783b43, after Badge01)  -> 1831b3f69997   Q1 full Balls pocket: refuse, toss, +2 once
run27                                        1831b3f69997 (unchanged)   fresh Continue (Bag frames do not show Great Balls: scrolled; see run37)
run28 (COPY of 80100f9a6a0a, after Q1)       -> 96e3f895a25e   Q2 full Berries pocket: refuse, toss, +3 once
run29                                        96e3f895a25e (unchanged)   fresh Continue, Bag
run30/31 (COPY of 4ca9b7f40dc6, newest slot deliberately damaged)       corrupt-slot fallback
run32    (COPY at 1c05fc46dc1d, Q4 dev copy)                            Q4 fresh Continue
run33    (COPY of 29ea0df40d71, before Badge01)                          Bluffs gate: player stays west of the trigger; message NOT captured (see run39)
run34    (COPY of 2bc19b97b053, the pre-Q3 save)                         Q3 repeated with in-battle defeat frames (not saved)
```

Reruns after the evidence review (driver `7824fe12`, clean; ROM = engine build):

```
run35 (COPY of 0a7429783b43, after Badge01) -> eeaef2093efa   Q1 ordinary play again: Hiker and researcher
                                                              dialogue, Bag before (no Great Ball) and after (x2)
run36                        eeaef2093efa (unchanged)         fresh Continue, Bag on Great Ball x2
run37 (Q1 full-pocket copy)  1831b3f69997 (unchanged)         fresh Continue, Bag on Great Ball x2
run38 (NATURAL chain)        4ca9b7f40dc6 (unchanged)         fresh Continue: Bag Great Ball x2, Oran Berry x3, party
run39 (COPY of 29ea0df40d71, before Badge01) unchanged        gate message on screen, blocked, Bag opens/closes
run40 (Q4 dev copy)          1c05fc46dc1d (unchanged)         fresh Continue, party screen with one Wobbuffet
run41 (COPY of 2bc19b97b053, pre-Q3) -> 9b59fcbe5c90          Q3 loss with defeat frames, whiteout, nurse, party, save
run42                        9b59fcbe5c90 (unchanged)         fresh Continue in the clinic, party screen
run43/44 (same copy)                                          re-save in the clinic with the save box and
                                                              "saved" text on record, then Continue
```

`package-e6870c30.json` (evidence.py) and `audit-e6870c30.json`
(`scripts/coordination/qa_evidence_report.py`, 8/8 READY_FOR_INDEPENDENT_REVIEW)
cover the current-ROM cases; `package-66b58c3a.json`/`audit-66b58c3a.json`
cover Gym 1 on the older ROM. READY_FOR_INDEPENDENT_REVIEW is completeness,
not a PASS. Cases using a fixture are `scope: DEV_FIXTURE`.

Two earlier attempts at run26 stopped on driver bugs before any save (a wild
battle on the walk to the Hiker was not fought; the toss helper read the pocket
from the wrong place, after the refusal had already been shown). Each was
rerun from the same untouched copy after its fix (`93a47f98`, `e2b527d7`).

## Developer-only fixtures (disclosed)

- **Q4:** the Field Lab has no ordinary entrance and Averon maps have no PC.
  The run uses the debug menu's Scripts → Script 4 (lab entry) and PC/Bag →
  Access PC, on a save copy. The party is the natural save's party: Piplup is
  the starter; the other five were caught with Poké Balls in earlier
  driver runs (catch phases before run17, not packaged here).
- **Q1/Q2 full pocket:** debug PC/Bag → Fill → Fill Pocket Poké Balls / Berries
  makes the reward pocket full (999 of each). The quest NPC, refusal, Bag TOSS
  and retry are ordinary play.
- **Save corruption (run30):** `run30-corrupt/fixture-corrupt_newest_slot.py`
  flipped one SaveBlock1 byte in the newest slot of a save copy before the run
  (`fixture.txt`).
- Each debug use is logged as `debug-menu` with `dev_only: true` in
  `events.jsonl` and has its screenshots; evidence.py marks those cases
  `DEV_FIXTURE`.

## Which screenshots prove what

State-milestone frames (`NNNN-<label>.png`) are taken when the state is read;
many are plain field views and several are byte-identical (nothing on screen
changed). The frames that show the facts are the dialogue frames
(`*-talk-*`, `*-gate-text-*`, `*-clinic-NN`, `*-defeat`), Bag frames
(`*-bag-pocket-N`, `*-bag-great-balls`, `*-bag-oran-berries`, `*-tossed-*`),
party screens (`*-party*`), the trainer card and the save box. The packages
list those explicitly.

## Known artifacts (not game defects)

- Caught Pokémon are nicknamed "A": the driver's naming-screen handling typed it.
- Some screenshots are night-tinted (real-time clock during the runs).
- run21 stopped on a driver PC-menu assumption (state file records the
  problem); run22 is the working Q4 run. run24 stopped on a wrong follower
  expectation (the follower spawns hidden on the player's tile after a warp,
  `UpdateFollowingPokemon`); run25 is the corrected rerun.

## Files per run

`provenance-*.json`, `inputs.jsonl` (every key transition with the game frame
counter), `events.jsonl`, `state-<label>.json` (read-only facts, expectations,
problems) and numbered PNG screenshots. `audio-report.json` is a per-second
RMS/peak timeline of mGBA's real mixed output (SDL disk driver); run23's
`audio-by-state.json` aligns it approximately with battles, field and clinic.
