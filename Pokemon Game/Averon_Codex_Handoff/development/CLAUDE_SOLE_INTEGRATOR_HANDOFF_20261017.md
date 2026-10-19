> **ARCHIVED PROCESS / SNAPSHOT — superseded 2026-10-18.** Use the [single operating contract](CURRENT_PHASE_AND_HANDOFF.md), [integration queue](INTEGRATION_QUEUE.md) and [#15 live claims](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). All prior “current”, “authoritative”, pause, freeze, manager-only and resume commands below are historical. Retained evidence and approved product constraints are preserved; this file grants no new work or content approval.

---

# Claude sole-integrator handoff — 2026-10-17

> **Snapshot, not the live route.** Written at main `ebcd54a9` (03:40 UTC).
> Live [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15),
> current PR heads and CI always win. The newest `CLAUDE_RESUME_CHECKPOINT`
> comment on #15 records later changes.

Owner handoff [#15 6228037998](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6228037998)
made Claude the sole engine writer and integrator after Codex ran out of
usage. Playtest alone judges Q1–Q5 gameplay ([#23](https://github.com/kioconnor24-sketch/PokemonGame/issues/23)).
New maps, story, rosters and saved IDs stay frozen.

## 1. Done in this session

| Item | Result | Where |
|---|---|---|
| Mystery Gift init-script overread | `Client_Init` copied 1024 bytes from a 16-byte script; it now copies the script's exported `sizeof`. Host ASan red (main) / green (fix). Normal and release builds; the release `-Wstringop-overread` warning is gone | #79, merged `4ac95cab` |
| Faraway Island / Colosseum declarations | Header and definition types now match; the canonical multiboot header is used; code identical except one dropped redundant byte truncation. Both release `-Wlto-type-mismatch` warnings are gone | #80, merged `aece7c6b` |
| Scripted-battle core | #25's `config/battle.h` returned to its base (`ba24e52d`) so #81's protected header had no open-PR overlap. Guard PASS, then #81 was merged | #81, merged `6d5c0967` |
| #25 | Main merged in (`090ecbdb`). The owner-directed `bfffafac` then held its include back, so #14's guard is green. #25 is now docs-only and a draft | #25 |
| #48 Pokémon readiness | Codex's capture fix `5002fa7b` reviewed. Full unfiltered suite on main + #48: 6,088 tests, strict baseline OK. Normal and release builds PASS | #48, merged `cc252447` |
| QUEST Q3 support | CI runs Playtest's unchanged #71 QA step plus Claude's observer: real Elio loss → whiteout → nurse heal → clinic SAVE → no-debugger Continue back in the clinic | #77 (ready); evidence [#23 6228908947](https://github.com/kioconnor24-sketch/PokemonGame/issues/23#issuecomment-6228908947) |
| #14 technical review | No blocking findings; rehearsal main + #14 + #25 is clean; the integration contract passes | [#14 6228303008](https://github.com/kioconnor24-sketch/PokemonGame/pull/14#issuecomment-6228303008) |
| LEGEND registration | `.include "data/scripts/averon_legend.inc"` next to the scripted-battle include; `test-averon-legend.py` now requires exactly one include and still no callers | branch `claude/legend-registration` `901a3533` |
| Linker finding | LEGEND and SCRIPTED natives are dead-stripped (`--gc-sections`, no callers). Recorded as POST-CONTENT | [#55 6228318523](https://github.com/kioconnor24-sketch/PokemonGame/issues/55#issuecomment-6228318523), #85 |
| Read-only reviews | #78, #76 and #70 reviewed; #82's broken YAML reported | comments on those PRs |

## 2. Verification evidence

Raw logs are on branch `claude/evidence-20261017`, under
`Pokemon Game/Averon_Codex_Handoff/qa/evidence/claude-20261017/`. All builds
used local arm-none-eabi-gcc 14.2.1.

| Tree | Normal ROM sha256 | Release ROM sha256 | Full unfiltered suite | Strict baseline |
|---|---|---|---|---|
| main `6d5c0967` | `5c022d4c…bc36` | `3b93e988…f87f` | 6,013 total / 5,238 pass / 327 fail | 1 problem: the known animation flake (accepted after #48) |
| main + #48 (engine and scripts trees equal to main `ebcd54a9`) | `7d5cf738…7e41` | `1cb6b26e…2976` | 6,088 / 5,313 / 327 | OK |
| End state: main + #48 + #14 + #25 + LEGEND | `24766c09…801d` | `e36ca6ab…55ad` | 6,093 / 5,318 / 327 | OK |

Every tree:
- normal build has no C warnings;
- release has only the four newlib syscall stubs and the RWX segment note;
- save headroom: SaveBlock1 304 B, SaveBlock2 84 B, SaveBlock3 1,556 B, PokemonStorage 1,568 B free;
- memory: EWRAM 35,660 B and IWRAM 4,376 B free, about 6.8 MB of ROM free.

## 3. Remaining integration — exact steps

1. **#14 QUEST:** waits for Playtest's `GATE_A_POSITIVE_PATH_ACCEPTED` on #23,
   or an explicit owner override. Its guard is already green. Normal merge by
   the manager or owner.
2. **#25 registration, after #14 merges.** Branch
   `claude/scripted-battle-after-quest` (`f6873eca`) is `bfffafac` plus two
   commits: restore the scripted-battle include, and register LEGEND.
   ```
   git fetch origin
   git checkout claude/scripted-battle
   git merge --ff-only origin/claude/scripted-battle-after-quest
   git merge origin/main             # #14's lines are at the end of event_scripts.s
   python3 "Pokemon Game/scripts/coordination/check_integration_contract.py"
   for t in quest-flow sidequests scripted-battle legend; do python3 "Pokemon Game/scripts/test-averon-$t.py"; done
   (cd "Pokemon Game/engine" && make -j4 all && make -j4 release)
   git push origin claude/scripted-battle
   ```
   - Both includes must stay above `data/averon_optional_sidequests.inc`.
   - #25 already has `HANDOFF_APPROVED` for `event_scripts.s`; its guard passes once #14 is closed.
   - Then mark ready, review and merge normally.
   - **Do not push this into #25 before #14 merges:** it recreates the protected overlap.
3. **After #25:** on the new main, run `make -j4 -O check` and
   `check-averon-native-baseline.py`, plus `make release` and
   `report-averon-save-headroom.py`. Expect about 6,093 tests and a strict OK
   (the end-state row above).
4. **#77:** optional merge of the Q3 support tooling.

## 4. Q3 clinic evidence (Playtest decides)

[CI run 38996685926](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/38996685926)
uses `.github/workflows/averon-quest-support-q3.yml` on #77. Its annotations:
- whiteout text frames `q3-play-x-001`/`-002`;
- nurse heal frames `-003` to `-012`;
- `Q3X_SAVE_SUCCESS`;
- flash after shutdown: slot 0, counter 2, (75,11) x7 y4;
- `Q3X_CONTINUE_RESULT CLINIC_FIELD`, with 0.999 identical pixels against the pre-save clinic frame;
- observer rc 0.

The run has no ROM or save uploads. Not covered: party HP (no probe), and
Badge01 → Hiker, full Bag / party and Q5 audio. Those need a real playthrough
or an owner-approved fixture.

## 5. Facts for the next cloud session

- **GitHub API:** GraphQL is blocked; use `gh api` REST.
  - Follow `--paginate` links manually: they use `repositories/{id}` paths, which the proxy refuses. Use `?per_page=100&page=N`.
  - Draft/ready only through `/pulls/{n}/ccr/ready_for_review`, and only for PRs this session opened.
- **Actions logs and artifacts** redirect to `productionresultssa*.blob.core.windows.net`, which the environment's network policy blocks. Read check-run annotations instead, or ask the owner to allow the host.
- **Merges:** Claude Code's permission check refuses Claude's own PR merges through the API (self-approval). The manager or owner merges after Claude posts READY with evidence.
- **Guard:** `exclusive-files` fails any PR whose protected paths overlap another open PR, drafts included. Grandfathered #14 is exempt only from approvals and the map freeze. Check locally with `tools/guard_snapshot.py` on the evidence branch.
- **Emulator:** mGBA is `/usr/games/mgba`.
  - `pkill -f mgba` inside a command that mentions "mgba" kills that same shell.
  - In the lit clinic, the generic 0.30 dialogue threshold misreads the floor (0.33); use 0.60.
- **Tests:** a full unfiltered `make check` takes about 45 minutes on 4 cores. The runner exits 2 whenever expected failures exist; `check-averon-native-baseline.py` is the verdict.

## 6. Owner decisions still open

- Fixture or playthrough policy for the GATE B cases above.
- Sinnoh caps and obedience numbers, the regional badge rule, Mega Ring placement, regional evolutions and follower art (see #46).
- Map unfreeze. Nothing in this handoff authorizes maps, scenes or new saved IDs.
