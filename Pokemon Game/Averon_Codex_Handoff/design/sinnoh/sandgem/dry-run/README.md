# Sandgem candidate: local DRY RUN (scratch build; nothing applied to the repo)

**What this is.** This is EMULATOR-TESTED evidence that the *pipeline* works for this exact candidate. It does **not** build the area or approve it.

Claude built the candidate in a **local scratch tree**:
- `main` `de1d350c` plus this branch's docs;
- plus the files in [`scratch-maps.NOT-APPLIED.patch`](scratch-maps.NOT-APPLIED.patch);
- plus the layout `map.bin`, written by `sinnoh-placeholder-art.py plan … --blockdata` from [`../sandgem-town-candidate.json`](../sandgem-town-candidate.json).

It then played that ROM in mGBA 0.10.5 with real controller input. **No map file, pin or protected source is changed in the repository by this PR.**

## Dry-run-only choices (disclosed; none of them become permanent)

- **Section:** `region_map_section` is `MAPSEC_NONE`, with the map-name popup off. The real section is the owner's and Codex's decision. Preflight correctly flags `MAPSEC_NONE` as a review warning.
- **DEV entry:** Averon's Alderfield clinic exit was **redirected to Sandgem's door in the scratch tree only**. It is not in the patch. Real Averon → Sinnoh travel is a later owner decision.
- **Placeholders:** music `MUS_DEWFORD`, and one placeholder townsfolk NPC and sign with neutral text.

## Results (`result.json`, `continue-result.json`; normal `make`, ROM sha256 `d33a5f80…`)

| Check | Result |
| --- | --- |
| Codex's map preflight on the two new maps | 0 errors, 80 geometry dependencies; 2 warnings, both `MAPSEC_NONE` |
| Map-registry contract | **FAILED on main's checker** (`unsupported-region REGION_SINNOH`). **Passes** with the checker from PR #129 plus 3 appended pin lines: 77 groups, 953 IDs. |
| GBA build | Links once the two `scripts.inc` includes are added to `data/event_scripts.s`. Sandgem's direct ROM contribution is **2,242 B**, of which the layout is 1,920 B and the rest is events, scripts and text. |
| Door warp into Sandgem; arrival at (6, 12) | PASS ([screenshot](0009-arrived-sandgem.png)) |
| West edge closed while Route 201 doesn't exist | PASS: the player stays at (0, 13) |
| North edge closed while Route 202 doesn't exist | PASS: the player stays at (15, 0) |
| Sea blocks walking without Surf (south corridor) | PASS ([screenshot](0012-sea-shore.png)) |
| House wall is solid | PASS |
| Pokémon Center door in, to the exit mats | PASS ([screenshot](0014-inside-pokemon-center.png)) |
| Nurse heals the whole party | PASS ([screenshot](0015-healed.png)) |
| Exit mat back out to Sandgem's door (6, 12) | PASS |
| Follower visible after the door round trip and two steps | PASS ([screenshot](0017-sandgem-outside.png)). It is invisible for the first frames after the warp, until the player moves, which is normal follower behaviour. |
| Start menu opens and returns to the field | PASS ([screenshot](0018-start-menu.png)) |
| SAVE in Sandgem | PASS: success dialog, and a valid flash slot newer than before |
| Fresh-process CONTINUE | PASS: same map, position, party, money, 14 named flags, Ball and Berry pockets |

## Findings that change how the real first-slice PR must be made

1. **Protected files.**
   - Every map's `scripts.inc` is listed explicitly in `data/event_scripts.s`, which is on the protected list. A Sinnoh map PR needs 2 include lines there.
   - New maps live in the frozen `data/maps` and `data/layouts` paths.
   - So the real PR needs a recorded `HANDOFF_APPROVED PR=#… PATHS=…` from the owner or manager in #15.
2. **Registry contract.** `check-averon-map-registry.py` predates #126 and rejects `REGION_SINNOH`. **PR #129** fixes this narrowly. The map PR must still append its group and slots to `engine/test/data/averon_map_registry_slots.inc`; the native contract test requires that too.
3. **Exit mats.** Arrow-warp mats warp when DOWN is pressed while standing on them. The QA script was corrected for this; the game was right.

The dry-run script is [`sandgem_dryrun.py`](sandgem_dryrun.py). It is scratch tooling, kept for reproducibility.
