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

## Findings while building it

- **Halting the core drops held directions.** Halting through GDB between
  key presses loses held directions. mGBA answers memory reads while running,
  so snapshots read live (`game.Game.snapshot(halt=False)`).
- **Latency.** Without `TCP_NODELAY` each GDB read cost about 43 ms of
  delayed-ACK latency; with it, about 1 ms.
- **Debug info.** The normal build has no DWARF for game code. Hence the
  compiled offset probe instead of gdb `ptype`.
