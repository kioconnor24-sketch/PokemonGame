# Local mGBA playthrough driver (Claude)

Plays the unchanged game in a real graphical mGBA, under a private Xvfb
display, with ordinary button presses. It produces **EMULATOR-TESTED
supporting evidence** for Playtest (#23). It is not a Gate A/B verdict.

## What it does and does not do

- **Inputs:** xdotool key presses to the mGBA window only (A=`x`, B=`z`,
  Start=`Return`, arrows).
- **Observation:** read-only memory reads through mGBA's GDB stub (`-g`).
  The driver never writes memory, registers, flags, items, Pokémon, badges or
  saves. There is no debug menu, no cheat file, no savestate and no injected
  state.
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

## Tests

```bash
python3 test_claude_play.py   # offline: real map sources + SYNTHETIC fixtures
```

These cover routing on real maps (including the Gym gate that only opens in
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
