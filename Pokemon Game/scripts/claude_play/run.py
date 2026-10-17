#!/usr/bin/env python3
"""Local Averon playthrough with ordinary inputs (EMULATOR-TESTED evidence).

  python3 run.py --engine ENGINE --rom ROM --out OUTDIR PHASE [PHASE ...]

The ROM is played from a scratch copy; mGBA keeps the game's own flash file
next to it, so each phase continues from the previous phase's in-game save.
No memory, flag, item, party or save is ever written by the driver.
"""
import argparse
import json
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
    # The save info box (map, name, BADGES, time) draws over several frames;
    # run17's capture 1.0 s after A caught it blank, so wait longer.
    d.e.tap("A", after=2.5)
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


def open_start_menu_action(d, action_id):
    """START, then move the cursor to the given start-menu action and press A."""
    gd, sym = d.g.gdb, d.g.sym
    d.settle()
    d.e.tap("START", after=0.8)
    for _ in range(12):
        n = gd.read(sym["sNumStartMenuActions"], 1)[0]
        cur = gd.read(sym["sStartMenuCursorPos"], 1)[0]
        actions = list(gd.read(sym["sCurrentStartMenuActions"], 9))[:n]
        if n and actions[cur] == action_id:
            d.e.tap("A", after=1.5)
            return
        d.e.tap("DOWN", after=0.25)
    raise drv.Stuck(f"start menu action {action_id} not found in {actions}")


def back_to_field(d, limit=12):
    for _ in range(limit):
        if d.field_ready(d.state()):
            return
        d.e.tap("B", after=0.6)
    raise drv.Stuck("menus did not close")


def phase_show_bag(d):
    """Start -> BAG, then a screenshot of every pocket (RIGHT through them).
    The pocket the Bag opens on is whatever was last used, so all are shown."""
    open_start_menu_action(d, 2)  # MENU_ACTION_BAG
    time.sleep(1.0)
    d.shot("bag-pocket-0")
    for i in range(1, 6):
        d.e.tap("RIGHT", after=0.9)
        d.shot(f"bag-pocket-{i}")
    back_to_field(d)
    observe(d, "bag-shown")


def phase_trainer_card(d):
    """Start -> player (trainer card): shows the badges actually earned."""
    open_start_menu_action(d, 4)  # MENU_ACTION_PLAYER
    time.sleep(1.5)
    d.shot("trainer-card")
    back_to_field(d)


def phase_q1_continued(d):
    """After a fresh emulator process and CONTINUE: Q1 state survived the save."""
    great = d.g.c["ITEM_GREAT_BALL"]
    observe(d, "q1-continued", {"FLAG_BADGE01_GET": True, "FLAG_AVERON_NOTES_REWARDED": True,
                                "greatBalls==2": lambda o: count_item(o["pokeBalls"], great) == 2})


def party_swap(d, a, b):
    """Field party menu: select slot a -> SWITCH -> slot b. Verified by order."""
    before = [dict(m) for m in d.state().party]
    open_start_menu_action(d, 1)  # MENU_ACTION_POKEMON

    def cursor_to(target, field="pm.slotId"):
        # In "Move to where?" the cursor is gPartyMenu.slotId2
        # (party_menu.c GetCurrentPartySlotPtr).
        slot_addr = d.g.sym["gPartyMenu"] + d.g.off[field]
        for _ in range(10):
            cur = struct.unpack("<b", d.g.gdb.read(slot_addr, 1))[0]
            if cur == target:
                return
            d.e.tap("DOWN" if cur < target else "UP", after=0.25)
        raise drv.Stuck(f"party cursor never reached {target}")

    cursor_to(a)
    d.e.tap("A", after=0.8)            # action list: SUMMARY ... SWITCH, ITEM, CANCEL
    for _ in range(3):
        d.e.tap("UP", after=0.2)       # wraps from SUMMARY to CANCEL, then ITEM, SWITCH
    d.shot(f"party-switch-{a}-{b}")
    d.e.tap("A", after=0.8)            # SWITCH: "Move to where?"
    cursor_to(b, "pm.slotId2")
    d.e.tap("A", after=1.5)            # swap animation
    for _ in range(6):
        s = d.state()
        if d.field_ready(s):
            break
        d.e.tap("B", after=0.6)
    after = d.state().party
    want = list(before)
    want[a], want[b] = want[b], want[a]
    observe(d, f"party-swapped-{a}-{b}", {"order": lambda o: [(m["level"], m["maxhp"]) for m in o["party"]]
                                          == [(m["level"], m["maxhp"]) for m in want]})


def debug_menu(d, rows, label):
    """DEV-ONLY ACCESS (disclosed in evidence): R+START opens the expansion
    debug menu; each entry of `rows` is a row index to select with A."""
    d.settle()
    d.e.key("R", True)
    time.sleep(0.5)
    d.e.tap("START", hold=0.14, after=0.35)
    d.e.key("R", False)
    time.sleep(0.8)
    d.shot(f"debug-{label}-root")
    for depth, row in enumerate(rows):
        for _ in range(row):
            d.e.tap("DOWN", after=0.25)
        d.shot(f"debug-{label}-{depth}")
        d.e.tap("A", after=1.0)
    d.log("debug-menu", label=label, rows=rows, dev_only=True)


def pc_deposit(d, slot):
    """DEV-ONLY ACCESS (disclosed): Averon maps have no PC, so the debug menu's
    Access PC opens Pokemon Storage. Its menu (Gen 7 order here: MOVE, DEPOSIT,
    WITHDRAW, MOVE ITEMS, SEE YA) and the storage cursor are driven by reading
    the game's own state (Task_PCMainMenu data, sCursorArea/sCursorPosition);
    nothing is written. Verified by the party shrinking by one."""
    g, gd, sym = d.g, d.g.gdb, d.g.sym
    before = len(d.state().party)
    debug_menu(d, [1, 0], "access-pc")          # PC/Bag... -> Access PC
    for _ in range(40):                          # "Storage System opened." -> menu
        t = g.task("Task_PCMainMenu")
        if t and t[0] == 2:                      # STATE_HANDLE_INPUT
            break
        if t is None:
            d.e.tap("A", after=0.5)              # close the "opened" message
        else:
            time.sleep(0.3)                      # menu loading or fading in
    else:
        raise drv.Stuck("PC main menu never took input")
    time.sleep(0.6)
    d.shot("pc-menu")
    labels = ["MOVE", "DEPOSIT", "WITHDRAW", "MOVE ITEMS", "SEE YA"]  # OW_PC_MOVE_ORDER >= GEN_7
    deposit = labels.index("DEPOSIT")
    for _ in range(8):
        t = g.task("Task_PCMainMenu")
        if t[1] == deposit:                      # tSelectedOption
            break
        d.e.tap("DOWN" if t[1] < deposit else "UP", after=0.35)
    d.log("pc-menu", selected=labels[g.task("Task_PCMainMenu")[1]])
    d.e.tap("A", after=3.0)                      # into storage, party shown
    area_addr, pos_addr = sym["sCursorArea"], sym["sCursorPosition"]
    for _ in range(20):
        if struct.unpack("<b", gd.read(area_addr, 1))[0] == 1:   # CURSOR_AREA_IN_PARTY
            break
        time.sleep(0.3)
    else:
        raise drv.Stuck("storage did not open in the party area (not DEPOSIT?)")
    for _ in range(10):
        pos = struct.unpack("<b", gd.read(pos_addr, 1))[0]
        if pos == slot:
            break
        d.e.tap("DOWN" if pos < slot else "UP", after=0.35)
    else:
        raise drv.Stuck(f"storage cursor never reached party slot {slot}")
    d.shot("pc-deposit-pick")
    d.e.tap("A", after=0.9)                      # selection menu: STORE first
    d.shot("pc-deposit-menu")
    d.e.tap("A", after=1.2)                      # "Deposit in which BOX?"
    d.shot("pc-deposit-box")
    d.e.tap("A", after=2.5)                      # current box
    d.shot("pc-deposited")
    for _ in range(14):
        s = d.state()
        if d.field_ready(s):
            break
        d.e.tap("B", after=0.9)
    observe(d, "pc-deposit", {"partyShrank": lambda o: len(o["party"]) == before - 1})


def phase_q4_gift(d):
    """Q4 developer gift. DEV-ONLY ACCESS, disclosed: the Field Lab has no
    ordinary entrance (debug Scripts -> Script 4) and Averon has no PC
    (debug Access PC). The party being full is NOT a fixture: it is the six
    Pokemon caught in play. Run this on a copy of the save, never the
    natural chain. Full party -> refusal; deposit one -> retry -> Wobbuffet;
    asking again gives nothing."""
    wob = d.g.c["SPECIES_WOBBUFFET"]
    count = lambda o: sum(m["species"] == wob for m in o["party"])
    debug_menu(d, [5, 3], "field-lab")  # Scripts -> Script 4 (AveronFieldLab_Enter)
    for _ in range(40):
        s = d.state()
        if d.here(s)[0] == "MAP_AVERONFIELDLAB" and d.field_ready(s):
            break
        time.sleep(0.25)
    observe(d, "q4-lab", {"map": "MAP_AVERONFIELDLAB", "FLAG_AVERON_SKETCH_REWARDED": True,
                          "party6": lambda o: len(o["party"]) == 6, "noWobbuffet": lambda o: count(o) == 0})
    d.talk("MAP_AVERONFIELDLAB", (25, 19))
    observe(d, "q4-full-refused", {"FLAG_AVERON_DEV_GIFT_RECEIVED": False,
                                   "party6": lambda o: len(o["party"]) == 6, "noWobbuffet": lambda o: count(o) == 0})
    pc_deposit(d, 5)
    d.talk("MAP_AVERONFIELDLAB", (25, 19))
    observe(d, "q4-gift", {"FLAG_AVERON_DEV_GIFT_RECEIVED": True,
                           "party6": lambda o: len(o["party"]) == 6, "oneWobbuffet": lambda o: count(o) == 1})
    d.talk("MAP_AVERONFIELDLAB", (25, 19))
    observe(d, "q4-no-duplicate", {"party6": lambda o: len(o["party"]) == 6, "oneWobbuffet": lambda o: count(o) == 1})


def weakest_move(d):
    """Losing on purpose with ordinary menu choices: always the move with the
    lowest power (status moves first)."""
    def choose(s):
        me = s.mons[0]
        options = [(d.moves.move(mv)["power"], slot) for slot, (mv, pp)
                   in enumerate(zip(me["moves"], me["pp"])) if mv and pp]
        return min(options)[1] if options else 0
    return choose


def phase_q3_whiteout(d, map_id="MAP_COASTALBLUFFS", tiles=((8, 10), (9, 10))):
    """Q3: a genuine loss. Wild battles on Coastal Bluffs grass, choosing the
    weakest move every turn and never running, until the whole party faints.
    Then the whiteout message and the clinic nurse's after-whiteout script are
    screenshotted message by message, and the party must be fully healed."""
    before = observe(d, "q3-before")
    battles = 0
    while True:
        mid, pos = d.here()
        if mid == "MAP_ALDERFIELDCLINIC" and battles:
            break
        if mid != map_id or pos not in tiles:
            d.travel_to(map_id)
            d.walk_path(map_id, set(tiles), on_event=lambda s: d.battle(choose_move=weakest_move(d)))
            continue
        other = tiles[1] if pos == tiles[0] else tiles[0]
        direction = next(k for k, v in mapdata.DIRS.items() if (pos[0] + v[0], pos[1] + v[1]) == other)
        d.step(direction)
        for _ in range(8):
            time.sleep(0.08)
            s = d.state()
            if s.in_battle or s.cb2 != "CB2_Overworld":
                break
        if s.in_battle or s.cb2 != "CB2_Overworld":
            d.battle(choose_move=weakest_move(d), label=f"q3-loss{battles:02d}")
            battles += 1
            d.log("q3-party", party=d.state().party, map=d.here()[0])
    d.shot("q3-after-whiteout")
    d.clear_text(capture="q3-clinic", frames=16)
    observe(d, "q3-clinic", {"map": "MAP_ALDERFIELDCLINIC",
                             "partyHealed": lambda o: party_fully_restored(d, o),
                             "follower": lambda o: bool(o["follower"]) and o["follower"]["species"]
                             == o["party"][0]["species"],
                             "partySame": lambda o: [m["species"] for m in o["party"]]
                             == [m["species"] for m in before["party"]],
                             "moneyLost": lambda o: o["money"] < before["money"]})


def party_fully_restored(d, o):
    """Every party member at full HP, no status, every move at full PP."""
    for m in o["party"]:
        if m["hp"] != m["maxhp"] or m["status"]:
            return False
        for slot, (mv, pp) in enumerate(zip(m["moves"], m["pp"])):
            if mv and pp != d.moves.max_pp(mv, m["ppBonuses"], slot):
                return False
    return True


def phase_q3_continued(d):
    """After Save and a fresh emulator process: still in the clinic, healed.
    The follower is hidden on the player's tile after a warp or load; one
    ordinary step must bring it out, visible, as the lead's species."""
    observe(d, "q3-continued", {"map": "MAP_ALDERFIELDCLINIC",
                                "partyHealed": lambda o: party_fully_restored(d, o),
                                "follower": lambda o: bool(o["follower"]) and o["follower"]["species"]
                                == o["party"][0]["species"]})
    d.step("down")
    d.settle()
    time.sleep(0.8)
    observe(d, "q3-follower-after-step", {"follower": follower_ok})


def follower_ok(o):
    f = o["follower"]
    return bool(f) and not f["invisible"] and f["species"] == o["party"][0]["species"]


def phase_q5_field(d, map_id="MAP_ALDERFIELD"):
    """Q5 on existing approved maps (Alderfield and its clinic): collision,
    every ordinary Start-menu screen and the party Field Kit return control,
    NPC dialogue prints and closes, and the follower comes through a door
    both ways. Ordinary inputs only; each check is a state file."""
    d.travel_to(map_id)
    d.settle()
    m = d.live_map(map_id)
    walls = {}
    for y in range(m.height):
        for x in range(m.width):
            if not m.walkable(x, y):
                continue
            for name, (dx, dy) in mapdata.DIRS.items():
                if m.inside(x + dx, y + dy) and m.collision(x + dx, y + dy) and not m.warp_at(x + dx, y + dy):
                    walls[(x, y)] = name
    _, pos = d.walk_path(map_id, set(walls))
    into = walls[pos]
    d.e.tap(drv.KEY[into], hold=0.6, after=0.4)  # hold into the wall
    observe(d, "q5-collision", {"position": lambda o: (o["x"], o["y"]) == pos,
                                "fieldReady": lambda o: d.field_ready(d.state())})
    d.log("collision", map=map_id, at=pos, pushed=into)
    away = {"up": "down", "down": "up", "left": "right", "right": "left"}[into]
    dx, dy = mapdata.DIRS[away]
    if m.walkable(pos[0] + dx, pos[1] + dy):
        d.step(away)
        d.settle()
        observe(d, "q5-open-step", {"position": lambda o: (o["x"], o["y"]) == (pos[0] + dx, pos[1] + dy)})

    gd, sym = d.g.gdb, d.g.sym
    d.e.tap("START", after=0.8)
    n = gd.read(sym["sNumStartMenuActions"], 1)[0]
    actions = list(gd.read(sym["sCurrentStartMenuActions"], 9))[:n]
    d.shot("q5-start-menu")
    back_to_field(d)
    d.log("start-menu", actions=actions)
    names = {0: "pokedex", 1: "pokemon", 2: "bag", 4: "player", 6: "option"}
    for action in [a for a in actions if a in names]:
        open_start_menu_action(d, action)
        time.sleep(1.0)
        d.shot(f"q5-menu-{names[action]}")
        if action == 1:
            # Lead -> actions SUMMARY, [field moves], FIELD KIT, SWITCH, ITEM,
            # CANCEL (party_menu.c). UP wraps from SUMMARY: CANCEL, ITEM,
            # SWITCH, FIELD KIT (the lead knows no field-visible move).
            d.e.tap("A", after=0.8)
            for _ in range(4):
                d.e.tap("UP", after=0.25)
            d.shot("q5-menu-pokemon-actions")
            d.e.tap("A", after=1.0)
            d.shot("q5-menu-field-kit")
        back_to_field(d)
        observe(d, f"q5-menu-{names[action]}-closed", {"fieldReady": lambda o: d.field_ready(d.state())})

    d.talk(map_id, (12, 16))                 # researcher, Q1 already done
    observe(d, "q5-npc-closed", {"fieldReady": lambda o: d.field_ready(d.state()),
                                 "FLAG_AVERON_NOTES_REWARDED": True})
    observe(d, "q5-follower-outside", {"follower": follower_ok})
    d.travel_to("MAP_ALDERFIELDCLINIC")
    follower_after_door(d, "q5-follower-inside")
    d.travel_to(map_id)
    follower_after_door(d, "q5-follower-back-outside")


def follower_after_door(d, label):
    """After a warp the expansion spawns the follower invisible on the
    player's tile (UpdateFollowingPokemon); it walks out on the first step.
    Record that, take one ordinary step, then require it visible."""
    d.settle()
    time.sleep(0.8)
    observe(d, f"{label}-arrived", {"followerSpawned": lambda o: bool(o["follower"])
                                    and o["follower"]["species"] == o["party"][0]["species"]})
    mid, pos = d.here()
    m = d.live_map(mid)
    for name, (dx, dy) in mapdata.DIRS.items():
        nxt = (pos[0] + dx, pos[1] + dy)
        if m.walkable(*nxt) and not m.warp_at(*nxt):
            d.step(name)
            break
    d.settle()
    time.sleep(0.8)
    observe(d, label, {"follower": follower_ok})


def phase_corrupt_fallback(d):
    """Save robustness on a COPY whose newest flash slot was deliberately
    damaged outside the game (one SaveBlock1 byte; disclosed test fixture).
    CONTINUE must load the whole older slot: run23's clinic save, healed
    party, no mixing with the newer slot's Alderfield position."""
    observe(d, "corrupt-fallback", {"map": "MAP_ALDERFIELDCLINIC",
                                    "position": lambda o: (o["x"], o["y"]) == (7, 4),
                                    "partyHealed": lambda o: party_fully_restored(d, o),
                                    "FLAG_AVERON_NOTES_REWARDED": True,
                                    "FLAG_AVERON_SKETCH_REWARDED": True})


def phase_clinic_continued(d):
    """Fresh process after saving on top of the fallback: still the clinic."""
    observe(d, "clinic-continued", {"map": "MAP_ALDERFIELDCLINIC",
                                    "partyHealed": lambda o: party_fully_restored(d, o)})


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


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo, *args):
    import subprocess
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def provenance(a, info, out, stage):
    """Source/ROM/ELF/save/driver identity, written at the start and end of a run."""
    import subprocess
    engine = pathlib.Path(a.engine)
    here = pathlib.Path(__file__).resolve().parent
    sav = pathlib.Path(a.rom).with_suffix(".sav")
    rec = dict(
        stage=stage,
        source_sha=git(engine, "rev-parse", "HEAD"),
        engine_tree=git(engine, "rev-parse", "HEAD:Pokemon Game/engine"),
        engine_dirty=bool(git(engine, "status", "--porcelain", "--", ".")),
        rom_sha256=sha256(a.rom),
        elf_sha256=info["elf_sha256"],
        save_sha256=sha256(sav) if sav.exists() else None,
        driver_sha=git(here, "rev-parse", "HEAD"),
        driver_dirty=bool(git(here, "status", "--porcelain", "--", ".")),
        mgba=subprocess.run(["mgba", "--version"], capture_output=True, text=True).stdout.strip(),
        phases=a.phases, new_game=a.new_game)
    (out / f"provenance-{stage}.json").write_text(json.dumps(rec, indent=1))
    return rec


class ExpectationFailed(RuntimeError):
    pass


def observe(d, label, expect=None):
    """Write state-<label>.json with read-only facts; fail closed on mismatches."""
    obs = d.g.observation()
    shot = d.shot(label)
    obs["screenshot"] = shot.name
    obs["label"] = label
    problems = []
    for key, want in (expect or {}).items():
        have = obs["flags"].get(key) if key.startswith("FLAG_") else obs.get(key)
        if callable(want):
            ok = bool(want(obs))
        else:
            ok = have == want
        if not ok:
            problems.append(f"{key}: expected {want}, observed {have}")
    obs["expected"] = {k: (v if not callable(v) else "check") for k, v in (expect or {}).items()}
    obs["problems"] = problems
    path = d.e.outdir / f"state-{label}.json"
    path.write_text(json.dumps(obs, indent=1))
    d.log("observe", label=label, problems=problems)
    if problems:
        raise ExpectationFailed(f"{label}: {problems}")
    return obs


def count_item(pocket, item):
    return sum(q for i, q in pocket if i == item)


def lead(d, s=None):
    s = s or d.state()
    return s.party[0] if s.party else dict(level=0, hp=0, maxhp=1)


def wild_low_hp(d):
    def run_if(s):
        trainer = s.battle_flags & d.g.c["BATTLE_TYPE_TRAINER"]
        me = s.mons[0]
        return not trainer and me["hp"] * 100 < me["maxhp"] * 35
    return run_if


def grind_until(d, done, map_id="MAP_ORCHARDLANE", tiles=((27, 8), (28, 8)), heal_below=45):
    """Pace on grass with ordinary steps; fight wild Pokemon; heal at the clinic."""
    battles = 0
    while True:
        s = d.state()
        if done(d, s):
            return battles
        mon = lead(d, s)
        if mon["hp"] * 100 < mon["maxhp"] * heal_below:
            d.heal_at_clinic()
            continue
        mid, pos = d.here(s)
        if mid != map_id or pos not in tiles:
            d.travel_to(map_id)
            d.walk_path(map_id, set(tiles), on_event=lambda s: d.battle(run_if=wild_low_hp(d)))
            continue
        other = tiles[1] if pos == tiles[0] else tiles[0]
        direction = next(k for k, v in mapdata.DIRS.items() if (pos[0] + v[0], pos[1] + v[1]) == other)
        d.step(direction)
        for _ in range(8):
            time.sleep(0.08)
            s = d.state()
            if s.in_battle or s.cb2 != "CB2_Overworld":
                break
        if s.in_battle or s.cb2 != "CB2_Overworld":
            d.battle(run_if=wild_low_hp(d), label=f"wild{battles:03d}")
            battles += 1
            d.log("lead", **lead(d))


def make_train(level):
    def phase(d):
        n = grind_until(d, lambda d, s: lead(d, s)["level"] >= level)
        d.log("trained", level=level, battles=n, lead=lead(d))
        d.shot(f"trained-{level}")
    return phase


def trainer_beaten(d, trainer):
    c = d.g.c
    return d.g.flag(d.state(), c["TRAINER_FLAGS_START"] + c[trainer])


def make_trainer(name, map_id, tile, trainer):
    """Talk to a route trainer and fight the battle with ordinary inputs."""
    def phase(d):
        if trainer_beaten(d, trainer):
            d.log("trainer-already-beaten", trainer=name)
            return
        mon = lead(d)
        if mon["hp"] * 100 < mon["maxhp"] * 90:
            d.heal_at_clinic()
        d.travel_to(map_id)
        d.shot(f"{name}-before")
        s = d.talk(map_id, tile)
        if s.in_battle:
            s = d.battle(label=name)
            d.clear_text()
        mid, pos = d.here()
        beaten = trainer_beaten(d, trainer)
        d.log("trainer-done", trainer=name, map=mid, lead=lead(d), beaten=beaten,
              whiteout=mid != map_id)
        if mid != map_id:
            # A genuine loss: record where the whiteout put the player and
            # whether the party was restored (Q3 material).
            observe(d, f"{name}-whiteout", {"map": "MAP_ALDERFIELDCLINIC",
                                            "leadHealed": lambda o: o["party"] and
                                            o["party"][0]["hp"] == o["party"][0]["maxhp"]})
        else:
            observe(d, f"{name}-after")
    return phase


def heal_full(d):
    mon = lead(d)
    if mon["hp"] < mon["maxhp"]:
        d.heal_at_clinic()


def phase_gym1(d):
    """Alderfield Gym: both sluices (YES), then Elio. A loss is recorded, not hidden."""
    heal_full(d)
    d.travel_to("MAP_ALDERFIELDGYM")
    observe(d, "gym1-entered")
    s = d.state()
    if not d.g.flag(s, "FLAG_AVERON_WEST_SLUICE"):
        d.talk("MAP_ALDERFIELDGYM", (2, 12))
    if not d.g.flag(d.state(), "FLAG_AVERON_EAST_SLUICE"):
        d.talk("MAP_ALDERFIELDGYM", (6, 12))
    observe(d, "gym1-sluices", {"FLAG_AVERON_WEST_SLUICE": True, "FLAG_AVERON_EAST_SLUICE": True})
    s = d.talk("MAP_ALDERFIELDGYM", (4, 4))
    if s.in_battle:
        d.battle(choose_move=d.trainer_move, label="elio", switch_if=retaliate_switch(d))
        s = d.clear_text(limit=300)
    won = d.g.flag(d.state(), "FLAG_BADGE01_GET")
    d.log("gym1-result", won=won, map=d.here()[0], lead=lead(d))
    observe(d, "gym1-result", {"FLAG_BADGE01_GET": True})


def retaliate_switch(d):
    """Switch rule for one trainer battle. Retaliate doubles in power on the
    turn after one of its user's side faints, which is exactly the turn a
    replacement arrives (run15: Elio's Lillipup knocked out Piplup that
    way). When a new foe that knows Retaliate arrives, send in the
    lowest-level healthy member for that one turn; the forced replacement
    afterwards brings back the strongest."""
    seen = {"foe": None}
    retaliate = d.g.c["MOVE_RETALIATE"]

    def switch_if(s):
        foe = s.mons[1]
        key = (foe["species"], foe["level"])
        arrived = seen["foe"] is not None and key != seen["foe"]
        seen["foe"] = key
        fodder = [m for m in s.party if m["hp"] > 0 and m["level"] < s.mons[0]["level"]]
        return arrived and retaliate in foe["moves"] and bool(fodder)
    return switch_if


def phase_q1_start(d):
    """Researcher in Alderfield asks for field notes; answer YES."""
    if not d.g.flag(d.state(), "FLAG_AVERON_NOTES_STARTED"):
        d.travel_to("MAP_ALDERFIELD")
        d.talk("MAP_ALDERFIELD", (12, 16))
    observe(d, "q1-started", {"FLAG_AVERON_NOTES_STARTED": True})


def phase_q1_hiker(d):
    """Past the Badge01 gate into Coastal Bluffs; talk to the Hiker on the high path."""
    d.travel_to("MAP_COASTALBLUFFS")
    observe(d, "q1-bluffs-entered", {"FLAG_BADGE01_GET": True})
    d.talk("MAP_COASTALBLUFFS", (35, 7))
    observe(d, "q1-hiker", {"FLAG_AVERON_NOTES_RECORDED": True, "FLAG_AVERON_NOTES_REWARDED": False})


def phase_q1_reward(d):
    """Back to the researcher: exactly two Great Balls, once."""
    great = d.g.c["ITEM_GREAT_BALL"]
    before = observe(d, "q1-before-reward")
    have = count_item(before["pokeBalls"], great)
    d.travel_to("MAP_ALDERFIELD")
    d.talk("MAP_ALDERFIELD", (12, 16))
    observe(d, "q1-reward", {"FLAG_AVERON_NOTES_REWARDED": True,
                             "greatBalls+2": lambda o: count_item(o["pokeBalls"], great) == have + 2})
    d.talk("MAP_ALDERFIELD", (12, 16))  # asking again must not pay twice
    observe(d, "q1-no-duplicate", {"greatBalls+2": lambda o: count_item(o["pokeBalls"], great) == have + 2})


def fill_pocket(d, row, label):
    """DEV FIXTURE (disclosed): debug PC/Bag -> Fill... -> Fill Pocket <row>.
    The expansion's debug fill adds 999 of every item of that pocket that
    fits (debug.c DebugAction_PCBag_Fill_Pocket*). It only prepares a full
    pocket; the quest reward that follows is the ordinary NPC script."""
    debug_menu(d, [1, 1, row], f"fill-{label}")
    back_to_field(d)


def toss_all(d, pocket, item, label):
    """BAG -> pocket -> item -> TOSS -> quantity DOWN once (wraps 1 -> all)
    -> YES. Ordinary Bag inputs, driven by reading gBagPosition. Verified by
    the item leaving the pocket."""
    g, gd, sym, off = d.g, d.g.gdb, d.g.sym, d.g.off
    want = g.c[pocket]
    field, count = {"POCKET_POKE_BALLS": ("pokeBalls", "BAG_POKEBALLS_COUNT"),
                    "POCKET_BERRIES": ("berries", "BAG_BERRIES_COUNT")}[pocket]
    items = [i for i, _ in g.bag_pocket(f"bag.{field}", count)]
    index = items.index(item)
    base = sym["gBagPosition"]
    open_start_menu_action(d, 2)  # MENU_ACTION_BAG
    time.sleep(1.0)
    for _ in range(8):
        cur = gd.read(base + off["bagpos.pocket"], 1)[0]
        if cur == want:
            break
        d.e.tap("RIGHT" if cur < want else "LEFT", after=0.9)
    else:
        raise drv.Stuck(f"bag never reached pocket {want}")
    for _ in range(len(items) + 4):
        cursor = struct.unpack("<H", gd.read(base + off["bagpos.cursor"] + 2 * want, 2))[0]
        scroll = struct.unpack("<H", gd.read(base + off["bagpos.scroll"] + 2 * want, 2))[0]
        if cursor + scroll == index:
            break
        d.e.tap("DOWN" if cursor + scroll < index else "UP", after=0.3)
    else:
        raise drv.Stuck(f"bag cursor never reached item index {index}")
    d.shot(f"{label}-item")
    d.e.tap("A", after=0.8)
    # Context menu, two columns (item_menu.c): Balls GIVE/-/TOSS/CANCEL,
    # Berries CHECK TAG/-/USE/GIVE/TOSS/CANCEL. TOSS is the left column.
    for _ in range(1 if pocket == "POCKET_POKE_BALLS" else 2):
        d.e.tap("DOWN", after=0.3)
    d.shot(f"{label}-menu")
    d.e.tap("A", after=0.8)
    d.e.tap("DOWN", after=0.5)      # quantity 1 -> wraps to everything held
    d.shot(f"{label}-quantity")
    d.e.tap("A", after=0.8)         # "Throw away ...?"
    d.shot(f"{label}-confirm")
    d.e.tap("A", after=1.0)         # YES
    d.shot(f"{label}-thrown")
    back_to_field(d)
    observe(d, label, {f"{field}-tossed": lambda o: count_item(o[field], item) == 0})


def phase_q1_full_pocket(d):
    """Q1 negative on a save COPY: the Hiker has recorded the notes; the Poke
    Balls pocket is filled by the disclosed debug fixture, so the two Great
    Balls cannot fit. The researcher must refuse (no balls, no reward flag),
    then pay exactly two once space is freed by tossing with the Bag."""
    great = d.g.c["ITEM_GREAT_BALL"]
    fill_pocket(d, 4, "balls")  # Fill Pocket Poke Balls
    full = observe(d, "q1-full-pocket", {"FLAG_AVERON_NOTES_RECORDED": True,
                                         "FLAG_AVERON_NOTES_REWARDED": False,
                                         "greatBalls==999": lambda o: count_item(o["pokeBalls"], great) == 999})
    d.travel_to("MAP_ALDERFIELD")
    d.talk("MAP_ALDERFIELD", (12, 16))
    observe(d, "q1-refused", {"FLAG_AVERON_NOTES_REWARDED": False,
                              "pocketUnchanged": lambda o: o["pokeBalls"] == full["pokeBalls"]})
    toss_all(d, "POCKET_POKE_BALLS", great, "q1-tossed")
    phase_q1_reward(d)


def phase_q2_full_pocket(d):
    """Q2 negative on a save COPY: the tree sketch is FOUND; the Berries
    pocket is filled by the disclosed debug fixture. The artist must refuse
    (no berries, no reward flag), then pay exactly three once space is freed."""
    oran = d.g.c["ITEM_ORAN_BERRY"]
    fill_pocket(d, 6, "berries")  # Fill Pocket Berries
    full = observe(d, "q2-full-pocket", {"FLAG_AVERON_SKETCH_FOUND": True,
                                         "FLAG_AVERON_SKETCH_REWARDED": False,
                                         "oran==999": lambda o: count_item(o["berries"], oran) == 999})
    d.travel_to("MAP_WINDROW")
    d.talk("MAP_WINDROW", (20, 14))
    observe(d, "q2-refused", {"FLAG_AVERON_SKETCH_REWARDED": False,
                              "pocketUnchanged": lambda o: o["berries"] == full["berries"]})
    toss_all(d, "POCKET_BERRIES", oran, "q2-tossed")
    phase_q2_reward(d)


def phase_q2_start(d):
    """Windrow artist asks for a berry sketch check; answer YES."""
    if not d.g.flag(d.state(), "FLAG_AVERON_SKETCH_STARTED"):
        d.travel_to("MAP_WINDROW")
        d.talk("MAP_WINDROW", (20, 14))
    observe(d, "q2-started", {"FLAG_AVERON_SKETCH_STARTED": True})


def phase_q2_observer(d):
    """The Coastal Meadow boy only hints (QUEST #14): nothing is found yet."""
    d.travel_to("MAP_COASTALMEADOW")
    d.talk("MAP_COASTALMEADOW", (10, 22))
    observe(d, "q2-observer", {"FLAG_AVERON_SKETCH_FOUND": False, "FLAG_AVERON_SKETCH_REWARDED": False})


def phase_q2_tree(d):
    """The tree sign at (12,27), looked at from its west side, records the
    sketch; looking again changes nothing."""
    d.travel_to("MAP_COASTALMEADOW")
    d.talk("MAP_COASTALMEADOW", (12, 27))
    observe(d, "q2-tree", {"FLAG_AVERON_SKETCH_FOUND": True, "FLAG_AVERON_SKETCH_REWARDED": False})
    d.talk("MAP_COASTALMEADOW", (12, 27))
    observe(d, "q2-tree-repeat", {"FLAG_AVERON_SKETCH_FOUND": True, "FLAG_AVERON_SKETCH_REWARDED": False})


def phase_q2_continued(d):
    """After a fresh emulator process and CONTINUE: Q2 state survived the save."""
    observe(d, "q2-continued", {"FLAG_AVERON_SKETCH_REWARDED": True,
                                "oranBerries==3": lambda o: count_item(o["berries"], d.g.c["ITEM_ORAN_BERRY"]) == 3})


def phase_q2_reward(d):
    """Back to the artist: exactly three Oran Berries, once."""
    oran = d.g.c["ITEM_ORAN_BERRY"]
    before = observe(d, "q2-before-reward")
    have = count_item(before["berries"], oran)
    d.travel_to("MAP_WINDROW")
    d.talk("MAP_WINDROW", (20, 14))
    observe(d, "q2-reward", {"FLAG_AVERON_SKETCH_REWARDED": True,
                             "oranBerries+3": lambda o: count_item(o["berries"], oran) == have + 3})
    d.talk("MAP_WINDROW", (20, 14))
    observe(d, "q2-no-duplicate", {"oranBerries+3": lambda o: count_item(o["berries"], oran) == have + 3})


def balls(d):
    return sum(q for _, q in d.g.bag_pocket("bag.pokeBalls", "BAG_POKEBALLS_COUNT"))


def phase_buy_balls(d, qty=5):
    """Alderfield Supply: BUY -> Poke Ball (first in the list) -> quantity -> YES."""
    before = observe(d, "shop-before")
    have, money = balls(d), before["money"]
    d.travel_to("MAP_ALDERFIELDSUPPLY")
    d.talk("MAP_ALDERFIELDSUPPLY", (6, 4), clear=False)  # "How may I serve you?"
    time.sleep(1.2)
    d.shot("shop-menu")
    d.e.tap("A", after=1.5)   # BUY -> item list, cursor on Poke Ball
    d.shot("shop-list")
    d.e.tap("A", after=1.0)   # Poke Ball -> "How many?"
    for _ in range(qty - 1):
        d.e.tap("UP", after=0.15)
    d.shot("shop-quantity")
    d.e.tap("A", after=1.0)   # quantity -> "That will be ... OK?"
    d.e.tap("A", after=1.0)   # YES
    for _ in range(4):
        d.e.tap("A", after=0.8)  # "Here you go!" and any bonus message
    for _ in range(12):
        s = d.state()
        if d.field_ready(s):
            break
        d.e.tap("B", after=0.5)
    observe(d, "shop-after", {"ballsBought": lambda o: balls(d) == have + qty,
                              "moneySpent": lambda o: o["money"] == money - 200 * qty})


def make_catch(target_party):
    """Wild battles on Orchard Lane, throwing Poke Balls (R) at new species."""
    def phase(d):
        def caught_species(s):
            return len(s.party)
        def catch_if(s):
            trainer = s.battle_flags & d.g.c["BATTLE_TYPE_TRAINER"]
            return not trainer and len(d.state().party) < target_party and balls(d) > 0
        tries = 0
        while len(d.state().party) < target_party and tries < 60:
            if balls(d) == 0:
                phase_buy_balls(d)
            heal_full(d) if lead(d)["hp"] * 2 < lead(d)["maxhp"] else None
            mid, pos = d.here()
            tiles = ((27, 8), (28, 8))
            if mid != "MAP_ORCHARDLANE" or pos not in tiles:
                d.travel_to("MAP_ORCHARDLANE")
                d.walk_path("MAP_ORCHARDLANE", set(tiles))
                continue
            other = tiles[1] if pos == tiles[0] else tiles[0]
            direction = "right" if other[0] > pos[0] else "left"
            d.step(direction)
            for _ in range(8):
                time.sleep(0.08)
                s = d.state()
                if s.in_battle or s.cb2 != "CB2_Overworld":
                    break
            if s.in_battle or s.cb2 != "CB2_Overworld":
                tries += 1
                before = len(d.state().party)
                d.battle(run_if=wild_low_hp(d), catch_if=catch_if, label=f"catch{tries:02d}")
                after = len(d.state().party)
                if after > before:
                    observe(d, f"caught-{after}", {"partyGrew": lambda o, n=after: len(o["party"]) == n})
        observe(d, f"party-{target_party}", {"partySize": lambda o: len(o["party"]) >= target_party})
    return phase


def make_train_slot(level):
    """Train whichever Pokemon leads the party up to `level`."""
    def phase(d):
        n = grind_until(d, lambda d, s: lead(d, s)["level"] >= level)
        d.log("trained", level=level, battles=n, lead=lead(d))
        observe(d, f"lead-trained-{level}")
    return phase


PHASES = {"piplup_lead": lambda d: party_swap(d, 1, 0),
          "fletchling_lead": lambda d: (party_swap(d, 2, 0), party_swap(d, 2, 1)),
          "lead_train10": make_train_slot(10), "lead_train13": make_train_slot(13),
          "lead_train15": make_train_slot(15),
          "buy_balls": phase_buy_balls, "catch2": make_catch(2), "catch6": make_catch(6),
          "q2_start": phase_q2_start, "q2_observer": phase_q2_observer, "q2_tree": phase_q2_tree,
          "q2_continued": phase_q2_continued, "q2_reward": phase_q2_reward,
          "gym1": phase_gym1, "q1_start": phase_q1_start, "q1_hiker": phase_q1_hiker,
          "q1_reward": phase_q1_reward, "q1_continued": phase_q1_continued,
          "show_bag": phase_show_bag, "q3_whiteout": phase_q3_whiteout,
          "q3_continued": phase_q3_continued, "q4_gift": phase_q4_gift, "trainer_card": phase_trainer_card,
          "q5_field": phase_q5_field, "q1_full_pocket": phase_q1_full_pocket,
          "q2_full_pocket": phase_q2_full_pocket, "corrupt_fallback": phase_corrupt_fallback,
          "clinic_continued": phase_clinic_continued,
          "sam": make_trainer("sam", "MAP_ORCHARDLANE", (16, 9), "TRAINER_AVERON_FARMER"),
          "lina": make_trainer("lina", "MAP_ORCHARDLANE", (21, 17), "TRAINER_AVERON_PICNIC"),
          "milo": make_trainer("milo", "MAP_ORCHARDLANE", (24, 12), "TRAINER_AVERON_ORCHARD"),
          "train8": make_train(8), "train10": make_train(10), "train12": make_train(12),
          "train13": make_train(13), "train14": make_train(14), "train15": make_train(15),
          "heal": lambda d: d.heal_at_clinic(),
          "observe": lambda d: observe(d, "checkpoint"),
          "opening": phase_opening, "save": phase_save, "to_alderfield": phase_to_alderfield}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", required=True)
    ap.add_argument("--rom", required=True, help="scratch ROM copy; its .sav sits next to it")
    ap.add_argument("--out", required=True)
    ap.add_argument("--new-game", action="store_true")
    ap.add_argument("--fps", type=int, default=0)
    ap.add_argument("--audio", action="store_true", help="capture real audio via SDL's disk driver")
    ap.add_argument("phases", nargs="*")
    a = ap.parse_args()
    engine = pathlib.Path(a.engine)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    info = emu.load_build_info(engine / "pokeemerald.elf", engine, out.parent / "play-cache")
    world = mapdata.World(engine)
    e = emu.Emulator(a.rom, out, fps_target=a.fps or None, audio=a.audio)
    try:
        g = game.Game(e, info)
        d = drv.Driver(e, g, world, out / "events.jsonl")
        d.moves = game.MoveTable(a.rom, info)
        g.map_names = world.by_num
        e.start_trace(out / "inputs.jsonl", info["symbols"]["gMain"] + info["offsets"]["main.vblankCounter1"])
        prov = provenance(a, info, out, "start")
        d.log("start", source=prov["source_sha"], rom_sha256=prov["rom_sha256"], elf=info["elf_sha256"], rom=a.rom, phases=a.phases, new_game=a.new_game)
        boot(d, a.new_game)
        for p in a.phases:
            PHASES[p](d)
        observe(d, "end")
    except Exception as exc:
        try:
            e.capture("error")
        except Exception:
            pass
        print("ERROR", type(exc).__name__, exc, file=sys.stderr)
        raise
    finally:
        e.close()
        if a.audio and e.audio_raw and e.audio_raw.exists():
            report = emu.audio_report(e.audio_raw, out / "audio.wav")
            (out / "audio-report.json").write_text(json.dumps(report, indent=1))
            print("audio", report["seconds"], "s,", report["audible_windows"], "audible windows", file=sys.stderr)
        try:
            provenance(a, info, out, "end")  # save hash after mGBA wrote its flash file
        except Exception as exc:
            print("provenance-end failed:", exc, file=sys.stderr)


if __name__ == "__main__":
    main()
