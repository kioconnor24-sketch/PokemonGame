#!/usr/bin/env python3
"""Local Averon playthrough with ordinary inputs (EMULATOR-TESTED evidence).

  python3 run.py --engine ENGINE --rom ROM --out OUTDIR PHASE [PHASE ...]

The ROM is played from a scratch copy; mGBA keeps the game's own flash file
next to it, so each phase continues from the previous phase's in-game save.
No memory, flag, item, party or save is ever written by the driver.
"""
import argparse
import pathlib
import shutil
import struct
import sys
import time

import driver as drv
import emu
import game
import mapdata


def boot(d, new_game):
    """Title screen to field control, via NEW GAME or CONTINUE."""
    seen = set()
    named = False
    for i in range(600):
        s = d.state()
        if s.cb2 not in seen:
            seen.add(s.cb2)
            d.log("screen", cb2=s.cb2, i=i)
            d.shot(f"boot-{len(seen):02d}")
        if s.cb2 == "CB2_Overworld" and s.valid:
            if not s.locked:
                time.sleep(0.6)
                s = d.state()
                if s.cb2 == "CB2_Overworld" and not s.locked:
                    d.log("field", map=d.here(s)[0], pos=(s.x, s.y), party=s.party)
                    return s
            d.e.tap("A", after=0.3)
            continue
        if "Naming" in s.cb2 and not named:
            d.shot("naming")
            d.e.tap("A", after=0.4)      # one letter
            d.e.tap("START", after=0.4)  # cursor to OK
            d.e.tap("A", after=1.0)
            named = True
            continue
        if not new_game and "MainMenu" in s.cb2:
            d.e.tap("A", after=1.0)      # CONTINUE is the default entry
            continue
        d.e.tap("A" if i % 4 else "START", after=0.35)
    raise drv.Stuck(f"boot: never reached field control; screens {sorted(seen)}")


def phase_opening(d):
    """Saltmere: harbor errand -> Piplup from Professor Fenwick -> north exit."""
    g = d.g
    s = d.state()
    d.log("vars", intro=g.var(s, "VAR_AVERON_INTRO"), first=g.var(s, "VAR_AVERON_FIRST_HOUSE"),
          harbor=g.var(s, "VAR_AVERON_HARBOR"), starter=g.flag(s, "FLAG_AVERON_STARTER"))
    mid, pos = d.here()
    if mid != "MAP_SALTMERE":
        # Leave the house through its door mat.
        m = d.w.map(mid)
        door = m.warps[0][:2]
        d.go_map([(mid, "warp", door, "down")])
    if not g.flag(d.state(), "FLAG_AVERON_STARTER"):
        if g.var(d.state(), "VAR_AVERON_HARBOR") == 0:
            d.go_map([("MAP_SALTMERE", "warp", (25, 22), "up")])
            d.talk("MAP_SALTMEREHARBOR", (6, 4))
            d.shot("harbor-errand-accepted")
            m = d.w.map("MAP_SALTMEREHARBOR")
            d.go_map([("MAP_SALTMEREHARBOR", "warp", m.warps[0][:2], "down")])
        if g.var(d.state(), "VAR_AVERON_HARBOR") == 1:
            d.talk("MAP_SALTMERE", (28, 25))
            d.shot("parcel-delivered")
        d.talk("MAP_SALTMERE", (18, 16))
        d.shot("starter-received")
    s = d.state()
    d.log("opening-done", party=s.party, harbor=g.var(s, "VAR_AVERON_HARBOR"),
          starter=g.flag(s, "FLAG_AVERON_STARTER"))


def save_game(d, label):
    """Start menu -> SAVE -> YES (-> overwrite YES) with ordinary inputs."""
    g = d.g
    gd = g.gdb
    sym = g.sym
    d.settle()
    d.e.tap("START", after=0.8)
    for _ in range(12):
        n = gd.read(sym["sNumStartMenuActions"], 1)[0]
        cur = gd.read(sym["sStartMenuCursorPos"], 1)[0]
        actions = list(gd.read(sym["sCurrentStartMenuActions"], 9))[:n]
        if n and actions[cur] == 5:  # MENU_ACTION_SAVE (start_menu.c enum)
            break
        d.e.tap("DOWN", after=0.25)
    else:
        raise drv.Stuck(f"no SAVE entry in start menu {actions}")
    d.e.tap("A", after=1.0)
    d.shot(f"save-confirm-{label}")
    for _ in range(40):
        cb = g.func_name(struct.unpack("<I", gd.read(sym["sSaveDialogCallback"], 4))[0])
        s = d.state()
        if d.field_ready(s):
            break
        d.e.tap("A", after=0.6)
    status = gd.read(sym["gSaveAttemptStatus"], 1)[0]
    d.log("saved", label=label, status=status, ok=status == g.c["SAVE_STATUS_OK"])
    d.shot(f"saved-{label}")
    if status != g.c["SAVE_STATUS_OK"]:
        raise drv.Stuck(f"save failed: status {status}")


def phase_save(d):
    save_game(d, "checkpoint")


def phase_to_alderfield(d):
    """Saltmere -> Coastal Meadow -> Windrow -> Orchard Lane -> Alderfield, walking."""
    route = [("MAP_SALTMERE", "edge", "up"), ("MAP_COASTALMEADOW", "edge", "up"),
             ("MAP_WINDROW", "edge", "up"), ("MAP_ORCHARDLANE", "edge", "up")]
    for leg in route:
        for attempt in range(30):
            mid, pos = d.here()
            if mid != leg[0]:
                break
            d.go_map([leg], on_event=lambda s: d.battle())
            s = d.state()
            if s.in_battle:
                d.battle()
    d.log("arrived", map=d.here()[0], party=d.state().party)
    d.shot("alderfield")


PHASES = {"opening": phase_opening, "save": phase_save, "to_alderfield": phase_to_alderfield}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", required=True)
    ap.add_argument("--rom", required=True, help="scratch ROM copy; its .sav sits next to it")
    ap.add_argument("--out", required=True)
    ap.add_argument("--new-game", action="store_true")
    ap.add_argument("--fps", type=int, default=0)
    ap.add_argument("phases", nargs="*")
    a = ap.parse_args()
    engine = pathlib.Path(a.engine)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    info = emu.load_build_info(engine / "pokeemerald.elf", engine, out.parent / "play-cache")
    world = mapdata.World(engine)
    e = emu.Emulator(a.rom, out, fps_target=a.fps or None)
    try:
        g = game.Game(e, info)
        d = drv.Driver(e, g, world, out / "events.jsonl")
        d.moves = game.MoveTable(a.rom, info)
        d.log("start", elf=info["elf_sha256"], rom=a.rom, phases=a.phases, new_game=a.new_game)
        boot(d, a.new_game)
        for p in a.phases:
            PHASES[p](d)
        d.shot("end")
    except Exception as exc:
        try:
            e.capture("error")
        except Exception:
            pass
        print("ERROR", type(exc).__name__, exc, file=sys.stderr)
        raise
    finally:
        e.close()


if __name__ == "__main__":
    main()
