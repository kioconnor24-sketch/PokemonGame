import sys, time, pathlib
sys.path.insert(0, "/root/claude-dev/wt-play/Pokemon Game/scripts/claude_play")
import emu
rom, out = sys.argv[1], pathlib.Path(sys.argv[2])
e = emu.Emulator(rom, out)
e.start_trace(out / "inputs.jsonl", None)
try:
    time.sleep(6)
    for i in range(4):
        e.tap("A", after=1.5); e.capture(f"intro-{i}")
    e.tap("START", after=2.0); e.capture("title-start")
    e.tap("A", after=2.0); e.capture("main-menu-continue")
    e.tap("A", after=6.0); e.capture("field")
    for i in range(8):
        e.tap("B", after=1.0)
    e.capture("field-settled")
    e.tap("START", after=1.2); e.capture("start-menu")
    e.tap("B", after=1.2); e.capture("start-closed")
    e.tap("DOWN", hold=0.5, after=0.8); e.capture("step-down")
    e.tap("LEFT", hold=0.5, after=0.8); e.capture("step-left")
    e.tap("UP", hold=0.5, after=0.8); e.capture("step-up")
finally:
    e.close()
