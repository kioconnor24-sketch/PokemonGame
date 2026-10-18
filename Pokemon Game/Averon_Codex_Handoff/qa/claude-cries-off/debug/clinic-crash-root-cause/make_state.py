"""Scratch debugging only: drive a RELEASE ROM to the Alderfield clinic counter
(facing the nurse), then save an mGBA savestate with Shift+F1."""
import pathlib, shutil, subprocess, sys, time
sys.dont_write_bytecode = True
ROOT = pathlib.Path('/root/claude-dev/wt-cries/Pokemon Game')
sys.path.insert(0, str(ROOT/'scripts/coordination'))
import codex_cry_gameplay as w
from codex_cry_gameplay import driver, emu, game, mapdata, play

src, scratch = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
engine = src.parent
rom = scratch/'game.gba'
shutil.copyfile(src, rom)
info = emu.load_build_info(src.with_suffix('.elf'), engine, scratch/'symbol-cache')
info['symbols'] = w.lto_aliases(info['symbols'])
out = scratch/'state-out'
e = emu.Emulator(rom, out)
g = game.Game(e, info)
d = driver.Driver(e, g, mapdata.World(engine), out/'events.jsonl')
d.moves = game.MoveTable(rom, info)
g.map_names = d.w.by_num
try:
    play.boot(d, False)
    d.travel_to('MAP_ALDERFIELD')
    d.walk_path('MAP_ALDERFIELD', {(17, 13)})
    d.settle()
    d.e.key('UP', True); time.sleep(6.0); d.e.key('UP', False); time.sleep(1.0)
    s = d.state()
    print('at', d.here(), 'locked', s.locked, flush=True)
    e.capture('at-counter')
    subprocess.run(['xdotool', 'key', '--window', e.window, 'shift+F1'], env=e.env, check=True)
    time.sleep(3)
    print(sorted(p.name for p in scratch.iterdir()), flush=True)
finally:
    e.close()
