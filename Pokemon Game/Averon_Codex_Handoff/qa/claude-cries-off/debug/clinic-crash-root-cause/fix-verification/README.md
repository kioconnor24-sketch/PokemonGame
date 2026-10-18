# Fix verification: graphical RELEASE clinic heal (Claude emulator run, not third-party)

**Setup**
- ROM: `make release` on branch `claude/clinic-union-room-overflow` at `98329090`, which is main `30a32203` plus the fix. ROM sha256 `6e37d30e…`, ELF `ce214d7b…`.
- Save: the same one every crashing run used, sha256 `73c3b87d…` (run02's save, Piplup only, at Saltmere).
- Driver: real key input through `verify_heal.py`. It boots with CONTINUE, walks to Alderfield and heals at the clinic **twice** using the YES path.

**Result (`result.json`, `events.jsonl`): alive, field ready, no problems.**

Memory checks, read over GDB after each step:

| Step | Heap blocks (magic `A3A3`, links valid) | `sFirstTextPrinter` | `sUnionRoomPlayerName[0]` |
| --- | --- | --- | --- |
| After CONTINUE | 7 | NULL | `FF` (EOS, from the new `EWRAM_INIT`) |
| After heal 1 (the heal that always crashed before) | 6 | NULL | `FF` |
| After heal 2 | 6 | NULL | `FF` |

The party is at full HP after both heals.

`0009-healed-1.png` shows the field after heal 1. Heal 2 ended on a pixel-identical frame (same tile and state), so only one copy is kept. The proof for heal 2 is the event and memory record above.

Without the fix, the same save and route crashed on **every** RELEASE attempt. That covers runs 02–04 on #117's ON and OFF ROMs and the debug runs on unchanged main RELEASE.
