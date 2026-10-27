# Local mGBA playthrough driver (Claude)

Plays the unchanged game in a real graphical mGBA, under a private Xvfb
display, with ordinary button presses. It produces **EMULATOR-TESTED
supporting evidence** for Playtest (#23). It is not a Gate A/B verdict.

## What it does and does not do

- **Inputs:** xdotool key presses to the mGBA window only (A=`x`, B=`z`,
  Start=`Return`, arrows).
- **Observation:** read-only memory reads through mGBA's GDB stub (`-g`).
  The driver never writes memory, registers or save files. There is no cheat
  file and no savestate.
- **DEV-ONLY fixtures (disclosed):** a few phases open the expansion's own
  debug menu (R+START) with ordinary key presses: Field Lab entry and Access
  PC for Q4 (no ordinary route exists in Averon maps), and Fill Pocket for
  the full-Bag quest negatives. Those change game state through the game's
  debug code. Each use is logged in `events.jsonl` as `debug-menu` with
  `dev_only: true`; `evidence.py` marks every case that contains one as
  `scope: DEV_FIXTURE` and names the fixture in each statement. Run them only
  on save copies, never on the natural save chain.
- **Build match:** `--rom` must be a byte-identical copy of the engine's
  `pokeemerald.gba` outside the engine tree, so symbols, offsets and the ROM
  agree; provenance records both hashes.
- **Persistence:** only the game's own flash file. Phases continue from the
  previous phase's in-game SAVE through the title screen's CONTINUE.
- **Addresses, struct offsets and constants** come from the exact build being
  played:
  - symbols from `arm-none-eabi-nm` on its ELF;
  - offsets and `#define`/enum values from a probe compiled with the engine's
    own flags (`emu.probe_offsets`);
  - move power, type and the type chart from the ROM file.
- **Routing:** uses the source layouts (`map.bin` collision, tileset
  behaviours, `map.json` warps and connections). Tiles that turn out to be
  impassable at runtime are learned and avoided.

## Use

```bash
cd "Pokemon Game/scripts/claude_play"
cp ../../engine/pokeemerald.gba /tmp/play/rom.gba      # scratch copy; never commit ROMs or saves
python3 run.py --engine ../../engine --rom /tmp/play/rom.gba --out /tmp/play/run1 --new-game opening save to_alderfield save
python3 run.py --engine ../../engine --rom /tmp/play/rom.gba --out /tmp/play/run2 <next phases>
```

Each run writes numbered screenshots and `events.jsonl`: every map change,
battle start and end (species, levels, HP), save status and capture. Report
the source SHA, ROM sha256, ELF sha256 (logged at start) and the phases run.

## Evidence each run writes

- `provenance-start.json` / `provenance-end.json`:
  - source SHA and committed engine tree, plus whether the engine tree was dirty;
  - ROM and ELF sha256, and the save sha256 before and after;
  - the driver's SHA and dirty state;
  - the mGBA version and the phases run.
- `inputs.jsonl`: every key transition (key, down/up, wall time, and the
  game's own `gMain.vblankCounter1` frame), so the screenshots and states
  can be lined up with the inputs that produced them. This is a record of
  the run, not a frame-exact replay. Inputs are real-time, so RNG-dependent
  events such as wild encounters differ between runs. The phases are the
  reproducible part: rerun them from the same save on the same ROM.
- `state-<label>.json`: read-only facts at each milestone (map, position,
  frame, badge, quest and sluice flags, party, Poké Ball and Berry pockets,
  save status), its screenshot, the expectations and any problems. A
  mismatch stops the run with an error (`run.ExpectationFailed`). A loss or
  missing reward is recorded, not hidden.
- `events.jsonl`: map changes, battles (species, levels, HP), heals, trainers
  and saves.

`evidence.py` turns runs into the input for the manager's
`coordination/qa_evidence_report.py`. It refuses missing files, a dirty engine
tree, runs from different source/ROM builds, and states with recorded
problems. `READY_FOR_INDEPENDENT_REVIEW` from that tool is not a gameplay
PASS; Playtest decides.

## Audio (`--audio`)

There is no sound server or ffmpeg here. SDL2's `disk` audio driver writes
mGBA's real mixed output to `audio.raw`. The run wraps it as `audio.wav`
(S16LE stereo, 44.1 kHz assumed) and writes `audio-report.json`, a per-second
RMS/peak timeline. A first capture showed silence on the copyright screen,
then intro and title music (RMS about 1,000–2,700, peaks up to 11,532). That
shows sound is produced; whether it sounds right still needs a human listen.

## Tests

```bash
python3 test_claude_play.py   # offline: real map sources + SYNTHETIC fixtures
```

They also cover the read-only decoders (Bag quantity key, stack high-water,
GDB stop replies during reads), title-screen and empty-party fail-closed
checks, DEV_FIXTURE tagging and ROM/ELF build matching. These cover routing on real maps (including the Gym gate that only opens in
the live map grid), map-to-map routes and unreachable maps, fail-closed
observations, the frame-stamped input trace, and evidence packaging through
`qa_evidence_report.inspect_package`. Removing either fail-closed check makes
them fail.

## Findings while building it

- **Halting the core drops held directions.** Halting through GDB between
  key presses loses held directions. mGBA answers memory reads while running,
  so snapshots read live (`game.Game.snapshot(halt=False)`).
- **Latency.** Without `TCP_NODELAY` each GDB read cost about 43 ms of
  delayed-ACK latency; with it, about 1 ms.
- **Debug info.** The normal build has no DWARF for game code. Hence the
  compiled offset probe instead of gdb `ptype`.
- **Turning before talking.** A 50 ms facing tap before A sometimes left the
  player facing elsewhere (a trainer talk did nothing). `talk()` now holds the
  direction toward the NPC (blocked, so the player only turns) and retries
  until a script actually starts.
- **The static map isn't the live map.** Scripts change the map at runtime
  (`setmetatile`, for example the Gym gate). Routing on the current map reads
  `gBackupMapLayout`.

## Connected-area map QA (`map_qa.py`)

This is a reusable check for each **approved** batch of new maps, such as Sandgem plus its Center, or a future route plus its seams. It has two layers, both derived from the batch's built source (warps, connections, `map.bin` collision, tileset behaviours):

- **`static`**: collision and pathfinding only, the part the #125 source preflight explicitly leaves out. It reports:
  - ledges that land on a solid tile (the engine never checks);
  - seam tiles that face a solid tile across a connection;
  - entry/exit pairs cut off from each other inside a map;
  - one-way pockets (reachable but no way back to any exit).

  Warp targets, return indices and offset reciprocity stay with #125.
- **`run`**: real mGBA with controller input, observed read-only. For every map in the batch it:
  - checks that each closed-edge run blocks;
  - walks connection seams out and back (first, middle and last passable tile);
  - takes every warp in and back (a Center's two mats returning through one door is accepted);
  - after each arrival, checks the follower is visible and an exit is still reachable;
  - probes any static pocket (the run must find no way out);
  - opens and closes the Start menu, and can `--save`.

  `--expect saved-*.json` in a fresh process checks CONTINUE.

```bash
python3 map_qa.py static --engine ../../engine --map MAP_SANDGEM_TOWN --map MAP_SANDGEM_TOWN_POKEMON_CENTER_1F
python3 map_qa.py fixture-save --engine ../../engine REAL.sav /tmp/qa/game.sav MAP_SANDGEM_TOWN 15 10   # DEV-only entry, disclose it
python3 map_qa.py run --engine ../../engine --rom ../../engine/pokeemerald-cries-off.gba --build normal \
    --scratch /tmp/qa --out /tmp/qa/run1 --map MAP_SANDGEM_TOWN --map MAP_SANDGEM_TOWN_POKEMON_CENTER_1F --save qa
python3 map_qa.py run ... --out /tmp/qa/run2 --expect /tmp/qa/run1/saved-qa.json                          # fresh CONTINUE
```

**Self-test with test-only placements.** `map_qa_fixtures/*.json` holds positive and negative placements: a loop connection, a one-way connection, a wrong warp return, a ledge pocket and a walled-off seam. `fixture` and `selftest` refuse any engine tree without a `.map_qa_throwaway` marker, so they only ever edit a disposable `git worktree`, never production map data. `selftest` handles each fixture as follows:
1. restores the tree and applies the fixture;
2. runs `static`, then rebuilds (`CRIES=off`);
3. enters with the DEV continue-warp save and runs in a fresh process;
4. requires positives to PASS, including a second-process CONTINUE, and negatives to FAIL on the named check.

```bash
git worktree add --detach /tmp/qa-tree <sha-with-the-batch>
touch "/tmp/qa-tree/Pokemon Game/engine/.map_qa_throwaway"
python3 map_qa.py selftest --engine "/tmp/qa-tree/Pokemon Game/engine" --save REAL.sav --out /tmp/qa/selftest
```

`test_map_qa.py` covers the static layer and fixture safety offline (`python3 test_map_qa.py`).

### Region-map UI check (`--region-ui`)

Sinnoh has no approved Town Map or Fly grid yet. Since #138 the game refuses the three ways into a region map there: PokéNav **MAP**, the **Town Map** item, and **FLY** from the party menu's FIELD KIT. `run --region-ui refused --region-ui-map MAP_X` drives all three on `MAP_X` with real input. For each one it checks that:
- no map opens: for PokéNav, the main menu's tasks survive; for the Town Map and Fly, no region-map or Fly callback runs;
- the player ends up back in the field;
- the screen is not left black (`gPlttBufferFaded` is not all zero);
- a real step still moves the player.

`--region-ui opens` asserts the opposite, for regions that do have a map.

The check needs the PokéNav flag, the Fly licence and a Town Map. The TEST-ONLY fixture op `grant` adds an on-transition script that sets those flags and gives the items once. It refuses a map that already has an on-transition script, and, like every fixture, it only runs in a throwaway tree. The `section` op relabels a map's section. The negative fixture uses it to give Sandgem a Hoenn section, so the maps open and `--region-ui refused` must fail.

The party-menu and menu-cursor offsets come from private structs that the offset probe can't see. `party_menu_layout()` reads them from source, and stops with an error if those structs' leading fields ever change.

### DEV scenes for staged overlays (`static_scene.py`, `compose_scene.py`)

Staged batches (`design/sinnoh/<batch>/staged/`) are tested on a Codex family's DEV scene, never on production. `static_scene.py REPO FAMILY BATCH_DIR MAP_ID ...` works only in a throwaway checkout, one carrying the `.map_qa_throwaway` marker:
1. It resets the engine tree.
2. It installs FAMILY's scene: the family's `prepare_runtime.assemble()`, or `-` for production alone, or a `family/module.py` path.
3. It applies the batch:
   - each `<Map>-dev-overlay/map.json` replaces that map's header, whether the map is the family's or a production one;
   - an optional same-size `map.bin` replaces its blockdata;
   - every other staged map is appended.
4. It runs `map_qa.py static` on the listed maps.

The installed tree can then be built and run with `map_qa.py run`, entering through a `fixture-save`.

`FAMILY` may be `a+b+c`: `compose_scene.py` merges several family scenes into one, for links between families. It works like this:
- each family keeps its own map, layout and art files;
- the families' appends to `event_scripts.s` and the tileset headers are concatenated;
- `map_groups.json` and `layouts.json` are merged in order;
- the registry slot list is renumbered.

It fails closed if two families write one file differently, if a family rewrites rather than appends an index file, or if a tileset is declared twice. Tests: `scripts/tests/test_compose_scene.py`.
