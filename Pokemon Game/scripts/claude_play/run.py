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
    """Pokemon Storage via the debug 'Access PC' entry (Averon maps have no PC):
    SOMEONE'S PC -> DEPOSIT -> party slot -> DEPOSIT -> box. Verified by party size."""
    before = len(d.state().party)
    debug_menu(d, [1, 0], "access-pc")          # PC/Bag... -> Access PC
    for _ in range(3):
        d.e.tap("A", after=1.0)                 # "booted up the PC" / SOMEONE'S PC
    d.shot("pc-storage-menu")
    d.e.tap("DOWN", after=0.3)                  # WITHDRAW -> DEPOSIT
    d.e.tap("A", after=2.5)                     # storage screen with the party
    for _ in range(slot):
        d.e.tap("DOWN", after=0.25)
    d.shot("pc-deposit-pick")
    d.e.tap("A", after=0.8)                     # submenu: DEPOSIT first
    d.e.tap("A", after=0.8)                     # "Deposit in which Box?"
    d.e.tap("A", after=2.0)                     # current box
    d.shot("pc-deposited")
    for _ in range(10):
        s = d.state()
        if d.field_ready(s):
            break
        d.e.tap("B", after=0.8)
    observe(d, "pc-deposit", {"partyShrank": lambda o: len(o["party"]) == before - 1})


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


def phase_q2_start(d):
    """Windrow artist asks for a berry sketch check; answer YES."""
    if not d.g.flag(d.state(), "FLAG_AVERON_SKETCH_STARTED"):
        d.travel_to("MAP_WINDROW")
        d.talk("MAP_WINDROW", (20, 14))
    observe(d, "q2-started", {"FLAG_AVERON_SKETCH_STARTED": True})


def phase_q2_observer(d):
    d.travel_to("MAP_COASTALMEADOW")
    d.talk("MAP_COASTALMEADOW", (10, 22))
    observe(d, "q2-observer", {"FLAG_AVERON_SKETCH_FOUND": True, "FLAG_AVERON_SKETCH_REWARDED": False})


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
          "q2_start": phase_q2_start, "q2_observer": phase_q2_observer, "q2_reward": phase_q2_reward,
          "gym1": phase_gym1, "q1_start": phase_q1_start, "q1_hiker": phase_q1_hiker,
          "q1_reward": phase_q1_reward,
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
