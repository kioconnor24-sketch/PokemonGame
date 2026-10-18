# Sandgem Town + Pokémon Center 1F: mGBA acceptance (PR #133)

This is Claude's EMULATOR-TESTED evidence from mGBA 0.10.5, played with real controller input and read-only GDB observation. It is not human or third-party QA and not Delta. No ROMs or saves are committed. The maps are those in commit `38100116`.

## Disclosures

1. **Section shim.** `MAPSEC_SANDGEM_TOWN` (216) is Codex's and is not on `main` yet. These builds used a **local, uncommitted** `#define MAPSEC_SANDGEM_TOWN 216` in the section constants template. Both map headers therefore carry 216, and nothing else changes. The acceptance will be re-run on the integrated tree once Codex's reviewed change lands.
2. **DEV-only entry.** [`dev_continue_warp_save.py`](dev_continue_warp_save.py) copies a real save and sets the engine's own continue-game warp, `CONTINUE_GAME_WARP` plus `SaveBlock1.continueGameWarp` = Sandgem (15, 10), with valid checksums. No source or map is changed and no Averon map is redirected. Only the first Sandgem entry uses it. Every later step is ordinary play, saves and CONTINUEs.
3. **The hurt party is real.** Before the fixture is made, the same ROM plays a genuine wild battle in Averon and saves.

## Builds (`CRIES=off`, cries-ON stays available)

| Build | Sandgem ROM sha256 | Linked ROM used | Main baseline (`203a89cc`) | Growth |
| --- | --- | --- | --- | --- |
| NORMAL `make CRIES=off` | `2fcef531…` | 17,323,592 B | 17,320,628 B (`48c438a9…`) | **+2,964 B** |
| RELEASE `make RELEASE=1 CRIES=off` | `7c8fda92…` | 17,442,180 B | 17,439,216 B (`b62c42a3…`) | **+2,964 B** |

Both build with exit 0.

**Source checks**
- Map-registry contract: `PASS: 77 groups; 953 pinned IDs; 536 linked maps; 12 mutations detected; 1 valid extension accepted`. No existing ID moves.
- Map preflight: 80 geometry dependencies. The only errors are `Unknown map-section 'MAPSEC_SANDGEM_TOWN'` (×2), which are expected until Codex's entry lands.

## Results: identical on NORMAL and RELEASE

[`sandgem_qa.py`](sandgem_qa.py) runs in four modes; each step is a separate process.

| Step | NORMAL | RELEASE |
| --- | --- | --- |
| `damage`: a real wild battle in Averon hurts the party, then SAVE | PASS (Piplup 25/31) | PASS (Piplup 23/29) |
| DEV continue-warp lands in Sandgem at (15, 10) | PASS | PASS |
| Follower visible on arrival | PASS | PASS |
| West edge (Route 201) closed | PASS | PASS |
| North edge (Route 202) closed | PASS | PASS |
| South edge (Route 219) closed | PASS | PASS |
| Forest wall, house wall | PASS | PASS |
| Mart door without an interior: no warp, stays in the field | PASS | PASS |
| Walking the roads, including the south road and bottom road to the beach | PASS | PASS |
| Talking to a townsperson, reading the town sign | PASS | PASS |
| Pokémon Center door in | PASS | PASS |
| Nurse heals the hurt party | PASS: 25 → 31/31 | PASS: 23 → 29/29 |
| Start menu opens and closes | PASS | PASS |
| SAVE inside the Pokémon Center: success callbacks, valid newer flash | PASS | PASS |
| Fresh CONTINUE matches the inside save | PASS | PASS |
| Exit mat back to the Center door (15, 10); follower visible after the round trip | PASS | PASS |
| SAVE outside in Sandgem: 2 saves, counter advanced by ≥ 2 | PASS | PASS |
| Fresh CONTINUE matches the outside save; follower visible | PASS | PASS |

Each run's `result.json` and `events.jsonl` is under `normal/` or `release/` (`damage`, `town`, `cpc`, `ctown`), with screenshots.

**One QA-script note.** The first nurse A-press sometimes doesn't register right after the door warp. The script now retries until a script actually starts; on the passing run the conversation started on attempt 2. This is input timing in the harness, not a game defect: the nurse script itself is the shared, unchanged `Common_EventScript_PkmnCenterNurse`.

## Not covered / still open

- **Integrated-tree rerun after Codex's `MAPSEC_SANDGEM_TOWN`:** NOT RUN yet.
- **Map-name popup:** off (`show_map_name: false`) until the section has a name entry.
- **No heal location / respawn for Sandgem:** a whiteout returns to the last Averon healer. That is the Codex and owner interface.
- **Town Map, Fly, routes and Averon → Sinnoh travel:** not built and not approved here.
- **Human listening, Delta:** UNTESTED.
