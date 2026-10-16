#!/usr/bin/env python3
"""QA-only mGBA 0.10.2 read-only debugger and screenshot-gated NPC controller.

Never writes game memory, flags, items, saves or maps. Fails closed if source
symbol, debugger support, tile movement or dialogue observation is uncertain.
"""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import struct
import subprocess
import sys
import time


class Blocked(RuntimeError):
    pass


def elf_symbol(elf, name="gSaveBlock1Ptr"):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise Blocked("Invalid ELF symbol name")
    symbols = subprocess.check_output(
        ["arm-none-eabi-nm", "--defined-only", str(elf)], text=True)
    hits = re.findall(r"^([0-9a-fA-F]{8}) [A-Za-z] " + re.escape(name) + r"$",
                      symbols, re.M)
    if len(hits) != 1:
        raise Blocked(f"ELF {name} count must be one, found {len(hits)}")
    return int(hits[0], 16)


class ReadOnlyGdb:
    def __init__(self, port):
        end = time.monotonic() + 16
        while True:
            try:
                self.sock = socket.create_connection(("127.0.0.1", port), 5)
                break
            except OSError as exc:
                if time.monotonic() >= end:
                    raise Blocked(f"GDB port {port} inaccessible: {exc}") from exc
                time.sleep(0.3)
        self.sock.settimeout(8)

    def packet(self):
        while True:
            ch = self.sock.recv(1)
            if not ch:
                raise Blocked("GDB socket closed waiting for reply")
            if ch == b"$":
                break
        buf = bytearray()
        while True:
            ch = self.sock.recv(1)
            if not ch:
                raise Blocked("GDB socket closed during packet")
            if ch == b"#":
                self.sock.recv(2)
                self.sock.sendall(b"+")
                return bytes(buf).decode("ascii")
            if ch == b"}":
                buf.append(self.sock.recv(1)[0] ^ 0x20)
            else:
                buf.extend(ch)

    def command(self, command, reply=True):
        raw = command.encode("ascii")
        self.sock.sendall(b"$" + raw + b"#" + f"{sum(raw) & 255:02x}".encode())
        return self.packet() if reply else None

    def start(self):
        stop = self.command("?")
        if not stop.startswith(("S", "T")):
            raise Blocked(f"Debugger stop request unsupported: {stop[:70]}")
        self.command("c", reply=False)

    def menu_state(self, symbols):
        """Read actual start-menu selection and save callback, without writes."""
        self.sock.sendall(b"\x03")
        stop = self.packet()
        if not stop.startswith(("S", "T")):
            raise Blocked(f"Menu debugger interrupt failed: {stop[:70]}")
        try:
            def read(addr, size):
                data = bytes.fromhex(self.command(f"m{addr:x},{size:x}"))
                if len(data) != size:
                    raise Blocked(f"Short debugger menu read at 0x{addr:08X}")
                return data
            n = read(symbols["count"], 1)[0]
            index = read(symbols["cursor"], 1)[0]
            if n > 9:
                raise Blocked(f"Invalid start-menu action count {n}")
            actions = list(read(symbols["actions"], 9))
            if n and index >= n:
                raise Blocked(f"Invalid cursor {index} for {n} actions")
            cb = struct.unpack("<I", read(symbols["saveCallback"], 4))[0]
            phase = next(
                (name for name, addr in symbols["callbacks"].items()
                 if (cb & ~1) == (addr & ~1)), "unknown")
            return dict(count=n, cursor=index, actions=actions[:n],
                        selected=actions[index] if n else None,
                        saveCallback=f"0x{cb:08X}", savePhase=phase)
        finally:
            self.command("c", reply=False)

    def position(self, symbol, symbol2):
        self.sock.sendall(b"\x03")
        stop = self.packet()
        if not stop.startswith(("S", "T")):
            raise Blocked(f"Debugger interrupt failed: {stop[:70]}")
        try:
            pointer_bytes = bytes.fromhex(self.command(f"m{symbol:x},4"))
            if len(pointer_bytes) != 4:
                raise Blocked("Pointer response has wrong size")
            ptr = struct.unpack("<I", pointer_bytes)[0]
            if not 0x02000000 <= ptr < 0x02040000 - 12:
                raise Blocked(f"gSaveBlock1Ptr outside EWRAM: 0x{ptr:08X}")
            data = bytes.fromhex(self.command(f"m{ptr:x},c"))
            if len(data) != 12:
                raise Blocked("SaveBlock1 header response has wrong size")
            # Saved flags array starts at 0x1270 in QUEST global.h, and
            # flags.h allocates NOTES_STARTED=0x2A, RECORDED=0x2B,
            # REWARDED=0x2C. event_data.c uses flags[id/8], bit id&7.
            flags_byte = bytes.fromhex(self.command(f"m{ptr + 0x1270 + (0x2A // 8):x},1"))
            if len(flags_byte) != 1:
                raise Blocked("Quest flag byte response has wrong size")
            # global.h SaveBlock1.bag at 0x560; constants/global.h defines
            # 30 items + 30 key + 16 Balls + 64 TMs/HMs before 46 Berries.
            # ItemSlot is two little-endian u16s, 4 bytes each. Oran Berry
            # is item ID 520 from existing constants/items.h.
            berry_offset = 0x560 + (30 + 30 + 16 + 64) * 4
            if ptr + berry_offset + 46*4 > 0x02040000:
                raise Blocked("SaveBlock1 Berry Pocket exceeds EWRAM")
            p2_bytes = bytes.fromhex(self.command(f"m{symbol2:x},4"))
            if len(p2_bytes) != 4:
                raise Blocked("SaveBlock2 pointer response has wrong size")
            p2 = struct.unpack("<I", p2_bytes)[0]
            # Verified against QUEST global.h SaveBlock2.encryptionKey
            # at +0xAC and item.c BagPocket_GetSlotDataGeneric: the saved
            # quantity is XORed with the lower 16 bits of encryptionKey.
            if not 0x02000000 <= p2 <= 0x02040000 - 0xB0:
                raise Blocked(f"gSaveBlock2Ptr outside EWRAM: 0x{p2:08X}")
            key_bytes = bytes.fromhex(self.command(f"m{p2 + 0xAC:x},4"))
            if len(key_bytes) != 4:
                raise Blocked("Bag encryption key response wrong size")
            key = struct.unpack("<I", key_bytes)[0] & 0xFFFF
            berries = bytes.fromhex(
                self.command(f"m{ptr + berry_offset:x},{46*4:x}"))
            if len(berries) != 46 * 4:
                raise Blocked("Incomplete read-only Berry Pocket response")
            oran_qty = sum((saved ^ key) for item, saved in
                           struct.iter_unpack("<HH", berries) if item == 520)
            # Verified against QUEST source global.h: pos at offset 0,
            # location mapGroup/mapNum/warpId at offsets 4/5/6.
            x, y, group, number, warp = struct.unpack_from("<hhbbb", data)
            if not 0 <= x < 256 or not 0 <= y < 256:
                raise Blocked(f"Invalid tile ({x},{y})")
            return dict(x=x, y=y, mapGroup=group, mapNum=number,
                        warpId=warp, saveBlockPtr=f"0x{ptr:08X}",
                        notesStarted=bool(flags_byte[0] & (1 << (0x2A & 7))),
                        notesRecorded=bool(flags_byte[0] & (1 << (0x2B & 7))),
                        notesRewarded=bool(flags_byte[0] & (1 << (0x2C & 7))),
                        sketchStarted=bool(flags_byte[0] & (1 << (0x2D & 7))),
                        sketchFound=bool(flags_byte[0] & (1 << (0x2E & 7))),
                        sketchRewarded=bool(flags_byte[0] & (1 << (0x2F & 7))),
                        oranBerryQuantity=oran_qty)
        finally:
            self.command("c", reply=False)


def daemon(args):
    symbol = elf_symbol(args.elf, "gSaveBlock1Ptr")
    symbol2 = elf_symbol(args.elf, "gSaveBlock2Ptr")
    menu_symbols = {
        "cursor": elf_symbol(args.elf, "sStartMenuCursorPos"),
        "count": elf_symbol(args.elf, "sNumStartMenuActions"),
        "actions": elf_symbol(args.elf, "sCurrentStartMenuActions"),
        "saveCallback": elf_symbol(args.elf, "sSaveDialogCallback"),
        "callbacks": {
            name: elf_symbol(args.elf, name)
            for name in ("SaveConfirmInputCallback",
                         "SaveOverwriteInputCallback",
                         "SaveSavingMessageCallback", "SaveDoSaveCallback",
                         "SaveSuccessCallback", "SaveReturnSuccessCallback",
                         "SaveErrorCallback")
        },
    }
    gdb = ReadOnlyGdb(args.port)
    gdb.start()
    Path(args.ready).write_text(
        f"read-only GDB: gSaveBlock1Ptr at 0x{symbol:08X}, "
        f"gSaveBlock2Ptr at 0x{symbol2:08X}\n")
    while True:
        with open(args.fifo, encoding="ascii") as fifo:
            for line in fifo:
                name = line.strip()
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name):
                    continue
                try:
                    result = {"checkpoint": name,
                              "position": gdb.position(symbol, symbol2)}
                    if name.startswith("save-"):
                        result["menu"] = gdb.menu_state(menu_symbols)
                except Exception as exc:
                    result = {"checkpoint": name, "blocked": str(exc)}
                dest = Path(args.outdir) / f"{name}.json"
                temp = dest.with_suffix(".tmp")
                temp.write_text(json.dumps(result, sort_keys=True))
                os.replace(temp, dest)
                print("QA_POSITION", json.dumps(result, sort_keys=True), flush=True)
                if "blocked" in result:
                    return 2


def snapshot_detail(args, name):
    dest = Path(args.outdir) / f"{name}.json"
    dest.unlink(missing_ok=True)
    with open(args.fifo, "w", encoding="ascii") as pipe:
        pipe.write(name + "\n")
    for _ in range(80):
        if dest.exists():
            result = json.loads(dest.read_text())
            if "blocked" in result:
                raise Blocked(result["blocked"])
            return result
        time.sleep(0.10)
    raise Blocked(f"Missing debugger reply for {name}")


def snapshot(args, name):
    return snapshot_detail(args, name)["position"]


def grab(window, dest):
    subprocess.run(["import", "-window", str(window), str(dest)],
                   check=True, stdout=subprocess.DEVNULL)


def white_panel_ratio(path):
    size = subprocess.check_output(
        ["identify", "-format", "%wx%h", str(path)], text=True)
    if size != "480x320":
        raise Blocked(f"Unknown frame geometry {size}, no guessed crop")
    rgb = subprocess.check_output(
        ["convert", str(path), "-crop", "400x50+40+254", "+repage",
         "-depth", "8", "RGB:-"])
    if len(rgb) != 60000:
        raise Blocked("Wrong screenshot crop byte count")
    return sum(min(rgb[i:i+3]) >= 190 for i in range(0, len(rgb), 3)) / 20000


def assert_ui(args):
    if args.kind == "field":
        ratio = white_panel_ratio(args.frame)
        print(f"QA_UI field dialogue-bright={ratio:.4f} frame={args.frame}",
              flush=True)
        if ratio > 0.30:
            raise Blocked(f"Overworld field not ready; dialogue still open {ratio:.4f}")
        return
    # Source-run screenshots establish these two different menu locations.
    # This is an explicit graphic assertion, NOT OCR of the selected option.
    size = subprocess.check_output(
        ["identify", "-format", "%wx%h", str(args.frame)], text=True)
    if size != "480x320":
        raise Blocked(f"Unknown debug screenshot size: {size}")
    boxes = {
        "sidebar": ("220x200+25+35", 220*200),
        "numeric": ("140x90+310+28", 140*90),
    }
    crop, pixels = boxes[args.kind]
    rgb = subprocess.check_output(
        ["convert", str(args.frame), "-crop", crop, "+repage",
         "-depth", "8", "RGB:-"])
    if len(rgb) != pixels * 3:
        raise Blocked("Wrong debug UI crop size")
    ratio = sum(min(rgb[i:i+3]) >= 190 for i in range(0, len(rgb), 3)) / pixels
    print(f"QA_UI {args.kind} bright={ratio:.4f} frame={args.frame}", flush=True)
    if ratio < 0.55:
        raise Blocked(f"No visible {args.kind} debug UI, bright ratio={ratio:.4f}")


def navigate(args):
    directory = Path(args.outdir)
    directory.mkdir(parents=True, exist_ok=True)
    sequence = 0

    def read(stage):
        nonlocal sequence
        sequence += 1
        name = f"{sequence:03d}-{stage}"
        frame = directory / (name + ".png")
        grab(args.window, frame)
        pos = snapshot(args, name)
        print("QA_CHECK", name, json.dumps(pos), str(frame), flush=True)
        if (pos["mapGroup"], pos["mapNum"]) != (75, 9):
            raise Blocked(f"Not source Alderfield map 75/9: {pos}")
        return pos, frame

    def press(name, duration=0.09):
        subprocess.run(["xdotool", "windowactivate", str(args.window)],
                       check=False)
        subprocess.run(["xdotool", "keydown", name], check=True)
        time.sleep(duration)
        subprocess.run(["xdotool", "keyup", name], check=True)
        time.sleep(0.34)

    def axis(tag, coord, target):
        pos, _ = read("before-" + tag)
        stalled = 0
        for attempt in range(36):
            value = pos[coord]
            if value == target:
                return
            sign = 1 if target > value else -1
            key = ("Right" if sign > 0 else "Left") if coord == "x" else (
                "Down" if sign > 0 else "Up")
            press(key)
            after, _ = read(f"{tag}-{attempt+1}-{key}")
            delta = after[coord] - value
            other = "y" if coord == "x" else "x"
            if after[other] != pos[other] or delta not in (0, sign):
                raise Blocked(f"Uncontrolled tile change: {pos} -> {after}")
            stalled = stalled + 1 if delta == 0 else 0
            if stalled >= 4:
                raise Blocked(f"Blocked moving {key} toward {coord}={target}: {after}")
            pos = after
        raise Blocked(f"Exceeded bounded movement to {coord}={target}")

    start, _ = read("warp-entry")
    # Both coordinates originate from the unchanged Alderfield map.json.
    # Researcher (12,16); approach from (13,16), face LEFT.
    if abs(start["x"] - 13) > 12 or abs(start["y"] - 15) > 12:
        raise Blocked(f"Unexpected warp spawn: {start}")
    axis("y-to-15", "y", 15)
    axis("x-to-13", "x", 13)
    axis("y-to-16", "y", 16)
    pos, before = read("adjacent-before")
    if (pos["x"], pos["y"]) != (13, 16):
        raise Blocked(f"Cannot establish adjacent tile: {pos}")
    brightness_before = white_panel_ratio(before)
    if brightness_before > 0.30:
        raise Blocked(f"UI already open before pressing A: {brightness_before:.3f}")
    press("Left", 0.045)
    faced, _ = read("face-left")
    if (faced["x"], faced["y"]) != (13, 16):
        raise Blocked(f"Facing input moved player unexpectedly: {faced}")
    press("x", 0.10)  # mGBA default A; actual dialogue is asserted below
    end, after = read("after-A")
    brightness_after = white_panel_ratio(after)
    print(f"QA_DIALOGUE_PANEL before={brightness_before:.4f} "
          f"after={brightness_after:.4f}", flush=True)
    if ((end["x"], end["y"]) != (13, 16)
            or brightness_after < 0.50
            or brightness_after - brightness_before < 0.35):
        raise Blocked("NPC interaction produced no verified bottom dialogue panel")
    print("QA_DIALOGUE_OBSERVED: source-adjacent visible dialogue; "
          "NOT Q1 reward/decline/accept acceptance", flush=True)




def navigate_artist(args):
    """Prove the existing Windrow artist talks, without altering map/flags."""
    directory = Path(args.outdir)
    sequence = 200

    def read(stage):
        nonlocal sequence
        sequence += 1
        name = f"{sequence:03d}-q2-{stage}"
        frame = directory / (name + ".png")
        grab(args.window, frame)
        state = snapshot(args, name)
        print("QA_Q2_CHECK", name, json.dumps(state, sort_keys=True),
              str(frame), flush=True)
        if (state["mapGroup"], state["mapNum"]) != (75, 6):
            raise Blocked(f"Not source Windrow group75/map6: {state}")
        return state, frame

    def press(key, seconds=0.09):
        subprocess.run(["xdotool", "windowactivate", str(args.window)],
                       check=False)
        subprocess.run(["xdotool", "keydown", key], check=True)
        time.sleep(seconds)
        subprocess.run(["xdotool", "keyup", key], check=True)
        time.sleep(0.34)

    def move(coord, value):
        state, _ = read(f"before-{coord}-to-{value}")
        stalled = 0
        for n in range(35):
            if state[coord] == value:
                return
            sign = 1 if value > state[coord] else -1
            key = ("Right" if sign > 0 else "Left") if coord == "x" else (
                "Down" if sign > 0 else "Up")
            press(key)
            nxt, _ = read(f"{coord}-{n+1}-{key}")
            other = "y" if coord == "x" else "x"
            delta = nxt[coord] - state[coord]
            if delta not in (0, sign) or nxt[other] != state[other]:
                raise Blocked(f"Windrow uncontrolled step: {state} -> {nxt}")
            stalled = stalled + 1 if delta == 0 else 0
            if stalled >= 4:
                raise Blocked(f"Windrow collision on {key}; {state} -> {nxt}")
            state = nxt
        raise Blocked(f"Windrow exceeded bounded move to {coord}={value}")

    start, _ = read("existing-warp0-entry")
    if not (19 <= start["x"] <= 32 and 17 <= start["y"] <= 26):
        raise Blocked(f"Unexpected real Windrow existing-warp0 spawn: {start}")
    # Existing Windrow artist at (20,14). Target directly south (20,15),
    # then face north. This is developer fixture navigation, not route proof.
    move("x", 20)
    move("y", 15)
    at, before = read("artist-south-adjacent")
    if (at["x"], at["y"]) != (20, 15):
        raise Blocked(f"Not adjacent to source artist: {at}")
    if white_panel_ratio(before) > 0.30:
        raise Blocked("Dialogue already open before approaching artist")
    if at["sketchStarted"] or at["sketchFound"] or at["sketchRewarded"]:
        raise Blocked(f"Fresh artist already has story flags: {at}")
    press("Up", 0.04)
    face, _ = read("artist-face-up")
    if (face["x"], face["y"]) != (20, 15):
        raise Blocked(f"Face command moved player; unverified artist: {face}")
    press("x", 0.10)
    talked, after = read("artist-first-A")
    ratio = white_panel_ratio(after)
    print(f"QA_Q2_ARTIST_PANEL before={white_panel_ratio(before):.4f} "
          f"after={ratio:.4f}", flush=True)
    if (talked["x"], talked["y"]) != (20, 15) or ratio < 0.50:
        raise Blocked("No visible artist dialogue at source adjacent position")
    print("QA_Q2_ARTIST_DIALOGUE_OBSERVED: requires human source-text "
          "review; no claim of artist accept/tree/reward", flush=True)


def difference(first, second):
    if len(first) != len(second) or not first:
        raise Blocked('Cannot compare differently sized menu samples')
    return sum(abs(a-b) for a,b in zip(first,second))/(255.0*len(first))


def q1_offer(args):
    """Test only real researcher decline / re-offer / accept. Fail closed."""
    directory = Path(args.outdir)
    count = 100

    def sample_menu(frame):
        # Verified in artifact 12021269079: real source MSGBOX_YESNO
        # overlays x=323..429, y=130..220 on the 480x320 framebuffer.
        size = subprocess.check_output(
            ["identify", "-format", "%wx%h", str(frame)], text=True)
        if size != "480x320":
            raise Blocked(f"Unknown YESNO frame geometry: {size}")
        rgb = subprocess.check_output(
            ["convert", str(frame), "-crop", "106x90+323+130",
             "+repage", "-depth", "8", "RGB:-"])
        if len(rgb) != 106*90*3:
            raise Blocked("Corrupt YESNO crop")
        return sum(min(rgb[i:i+3]) >= 190
                   for i in range(0, len(rgb), 3)) / (106*90)

    def observe(tag, panel=None, menu=None):
        nonlocal count
        count += 1
        name = f"{count:03d}-q1-{tag}"
        frame = directory / (name + ".png")
        grab(args.window, frame)
        state = snapshot(args, name)
        print("QA_Q1_CHECK", name, json.dumps(state, sort_keys=True),
              str(frame), flush=True)
        if (state["mapGroup"], state["mapNum"],
                state["x"], state["y"]) != (75, 9, 13, 16):
            raise Blocked(f"Researcher adjacency lost at {tag}: {state}")
        panel_ratio = white_panel_ratio(frame)
        menu_ratio = sample_menu(frame)
        print("QA_Q1_UI", name,
              f"panel={panel_ratio:.4f} menu={menu_ratio:.4f}", flush=True)
        if panel is True and panel_ratio < 0.50:
            raise Blocked(f"Dialogue panel absent at {tag}")
        if panel is False and panel_ratio > 0.30:
            raise Blocked(f"Dialogue panel remains open at {tag}")
        if menu is True and menu_ratio < 0.52:
            raise Blocked(f"YESNO menu absent at {tag}")
        if menu is False and menu_ratio > 0.52:
            raise Blocked(f"Unexpected YESNO menu at {tag}")
        return state, frame

    def key(name):
        subprocess.run(["xdotool", "windowactivate", str(args.window)],
                       check=False)
        subprocess.run(["xdotool", "keydown", name], check=True)
        time.sleep(0.10)
        subprocess.run(["xdotool", "keyup", name], check=True)
        time.sleep(0.75)

    time.sleep(1)
    first, first_frame = observe("offer-yes-selected", panel=True, menu=True)
    if (first["notesStarted"] or first["notesRecorded"]
            or first["notesRewarded"]):
        raise Blocked("QUEST fresh offer has preexisting progress")

    # The real screenshot proves this is ALREADY the YES/NO choice menu.
    # Do not press A to 'finish text': that selects the default YES.
    key("Down")
    pre_no, selected = observe("offer-no-selected", panel=True, menu=True)
    if pre_no["notesStarted"]:
        raise Blocked("Direction changed quest flag unexpectedly")
    # A distinct frame at this point is necessary to verify menu input.
    raw_first = subprocess.check_output(
        ["convert", str(first_frame), "-crop", "106x90+323+130",
         "+repage", "-depth", "8", "RGB:-"])
    raw_selected = subprocess.check_output(
        ["convert", str(selected), "-crop", "106x90+323+130",
         "+repage", "-depth", "8", "RGB:-"])
    menu_delta = difference(raw_first, raw_selected)
    print(f"QA_Q1_SELECTOR_DELTA {menu_delta:.5f}", flush=True)
    if menu_delta < 0.001:
        raise Blocked("No observed menu cursor change after DOWN")
    key("x")
    declined, _ = observe("decline-text", panel=True, menu=False)
    if (declined["notesStarted"] or declined["notesRecorded"]
            or declined["notesRewarded"]):
        raise Blocked("NO selected but quest progress changed")
    key("x")
    cleared, _ = observe("decline-dismissed", panel=False, menu=False)
    if cleared["notesStarted"]:
        raise Blocked("Quest started while declining/dismissing")
    key("x")
    # In run 38843336625 the refreshed line was STILL drawing characters
    # at 0.75 seconds, with no selector yet. Do not send blind extra A.
    # Observe successive frames and wait for the real YES/NO to appear.
    again = None
    for attempt in range(10):
        current, frame = observe(f"return-menu-wait-{attempt+1}", panel=True)
        if (current["notesStarted"] or current["notesRecorded"]
                or current["notesRewarded"]):
            raise Blocked("Quest started before return YES choice")
        if sample_menu(frame) >= 0.52:
            again = current
            break
        time.sleep(0.75)
    if again is None:
        raise Blocked("Return YESNO never rendered without extra inputs")
    key("x")
    accepted, _ = observe("accept-waiting-text", panel=True, menu=False)
    if (not accepted["notesStarted"] or accepted["notesRecorded"]
            or accepted["notesRewarded"]):
        raise Blocked(f"YES failed STARTED-only state: {accepted}")
    print("QA_Q1_OFFER_PARTIAL_OBSERVED: decline saved no flags, "
          "returned YES sets STARTED only. Manual screenshot review required. "
          "Hiker/reward/Bag/save/whiteout remain unverified.", flush=True)



def q2_artist_offer(args):
    """Observe Windrow artist refusal/reoffer/accept with saved flag reads only."""
    directory = Path(args.outdir)
    num = 300

    def menu_ratio(frame):
        if subprocess.check_output(
                ["identify", "-format", "%wx%h", str(frame)],
                text=True) != "480x320":
            raise Blocked("Q2 unexpected screenshot dimensions")
        return sum(min(rgb[i:i+3]) >= 190
                   for rgb in [subprocess.check_output(
                       ["convert", str(frame), "-crop", "106x90+323+130",
                        "+repage", "-depth", "8", "RGB:-"])]
                   for i in range(0, len(rgb), 3)) / (106*90)

    def menu_bytes(frame):
        return subprocess.check_output(
            ["convert", str(frame), "-crop", "106x90+323+130",
             "+repage", "-depth", "8", "RGB:-"])

    def see(tag, expected_menu=None, expected_panel=None):
        nonlocal num
        num += 1
        name = f"{num:03d}-q2-{tag}"
        pic = directory / (name + ".png")
        grab(args.window, pic)
        state = snapshot(args, name)
        if (state["mapGroup"], state["mapNum"],
                state["x"], state["y"]) != (75, 6, 20, 15):
            raise Blocked(f"Q2 artist adjacency changed: {state}")
        mr = menu_ratio(pic)
        pr = white_panel_ratio(pic)
        print("QA_Q2_OFFER", name, json.dumps(state, sort_keys=True),
              f"menu={mr:.4f} panel={pr:.4f}", flush=True)
        if expected_menu is True and mr < 0.52:
            raise Blocked(f"Q2 YESNO absent at {tag}")
        if expected_menu is False and mr > 0.52:
            raise Blocked(f"Q2 YESNO unexpectedly open at {tag}")
        if expected_panel is True and pr < 0.50:
            raise Blocked(f"Q2 dialogue not visible at {tag}")
        if expected_panel is False and pr > 0.30:
            raise Blocked(f"Q2 dialogue not closed at {tag}")
        return state, pic, mr

    def key(k):
        subprocess.run(["xdotool", "windowactivate", str(args.window)],
                       check=False)
        subprocess.run(["xdotool", "keydown", k], check=True)
        time.sleep(0.1)
        subprocess.run(["xdotool", "keyup", k], check=True)
        time.sleep(0.75)

    def get_menu(label):
        for i in range(12):
            state, frame, mr = see(f"{label}-wait-{i+1}", expected_panel=True)
            if state["sketchStarted"] or state["sketchFound"] or state["sketchRewarded"]:
                raise Blocked(f"Q2 changed stage before YES choice: {state}")
            if mr >= 0.52:
                return frame
            time.sleep(0.75)
        raise Blocked(f"Q2 artist YESNO did not render for {label}")

    time.sleep(0.75)
    before = get_menu("first-offer")
    key("Down")
    state, selected, _ = see("select-no", expected_menu=True, expected_panel=True)
    selector_delta = difference(menu_bytes(before), menu_bytes(selected))
    print(f"QA_Q2_SELECTOR_DELTA {selector_delta:.5f}", flush=True)
    if selector_delta < 0.001:
        raise Blocked("Q2 did not observe selector move to NO")
    key("x")
    declined, _, _ = see("decline-text", expected_menu=False, expected_panel=True)
    if declined["sketchStarted"] or declined["sketchFound"] or declined["sketchRewarded"]:
        raise Blocked(f"Q2 refusal changed flags: {declined}")
    key("x")
    closed, _, _ = see("decline-dismissed", expected_menu=False,
                       expected_panel=False)
    if closed["sketchStarted"]:
        raise Blocked("Q2 stage advanced while leaving refusal")
    key("x")
    get_menu("return-offer")
    key("x")
    accepted, _, _ = see("accept-waiting-text", expected_menu=False,
                         expected_panel=True)
    if (not accepted["sketchStarted"]
            or accepted["sketchFound"] or accepted["sketchRewarded"]):
        raise Blocked(f"Q2 YES not STARTED-only: {accepted}")
    if not accepted["notesStarted"]:
        raise Blocked("Q2 unexpectedly lost unrelated Q1 STARTED state")
    print("QA_Q2_OFFER_PARTIAL_OBSERVED: NO leaves sketch flags clear; "
          "return YES sets SKETCH_STARTED only. Tree, reward, inventory, "
          "whiteout and flash NOT TESTED. Human screenshot review needed.",
          flush=True)




def q2_meadow(args):
    """Natural Windrow -> Meadow -> Windrow route on unchanged maps.

    All movement is ordinary controller input gated by per-step read-only
    mGBA SaveBlock1 position/flags and a rendered screenshot.  Map crossing
    and berry count are observable; no memory or save writes.
    """
    out = Path(args.outdir)
    count = 400
    windrow = (75, 6)
    meadow = (75, 5)

    def check(stage, target_map=None, field=False):
        nonlocal count
        count += 1
        name = f"{count:03d}-q2-meadow-{stage}"
        frame = out / (name + ".png")
        grab(args.window, frame)
        pos = snapshot(args, name)
        print("QA_MEADOW_STATE", name, json.dumps(pos, sort_keys=True),
              str(frame), flush=True)
        if target_map is not None and (
                pos["mapGroup"], pos["mapNum"]) != target_map:
            raise Blocked(f"Unexpected map at {stage}: {pos}")
        # No unstated quest progression is inserted or permitted.
        if not pos["sketchStarted"] or not pos["notesStarted"]:
            raise Blocked(f"Previously accepted quests disappeared: {pos}")
        if pos["notesRecorded"] or pos["notesRewarded"]:
            raise Blocked(f"Unrelated Field Notes progressed on Q2 walk: {pos}")
        if field and white_panel_ratio(frame) > 0.30:
            raise Blocked(f"Unexpected dialogue/battle while walking {stage}")
        return pos, frame

    def press(key, duration=0.09, wait=0.40):
        subprocess.run(["xdotool", "windowactivate", str(args.window)],
                       check=False)
        subprocess.run(["xdotool", "keydown", key], check=True)
        time.sleep(duration)
        subprocess.run(["xdotool", "keyup", key], check=True)
        time.sleep(wait)

    def move(coord, target, target_map):
        current, _ = check(f"before-{coord}-{target}", target_map, field=True)
        stalled = 0
        for i in range(90):
            if current[coord] == target:
                return
            sign = 1 if target > current[coord] else -1
            key = ("Right" if sign > 0 else "Left") if coord == "x" else (
                "Down" if sign > 0 else "Up")
            press(key)
            after, _ = check(f"{coord}-{target}-{i+1}-{key}",
                             target_map, field=True)
            other = "y" if coord == "x" else "x"
            delta = after[coord] - current[coord]
            if after[other] != current[other] or delta not in (0, sign):
                raise Blocked(f"Uncontrolled Q2 route tile {current} -> {after}")
            stalled = stalled + 1 if delta == 0 else 0
            if stalled >= 4:
                raise Blocked(f"Q2 collision or lost controls at {after}")
            current = after
        raise Blocked(f"Q2 route exceeded 90 steps to {coord}={target}")

    def cross(source, dest, key, x, source_y, dest_y):
        first, _ = check(f"before-cross-{key}", source, field=True)
        if (first["x"], first["y"]) != (x, source_y):
            raise Blocked(f"Wrong tile for natural map connection: {first}")
        state = first
        for i in range(7):
            press(key, wait=0.85)
            state, _ = check(f"cross-{key}-{i+1}", field=True)
            group = (state["mapGroup"], state["mapNum"])
            if group == dest:
                if (state["x"], state["y"]) != (x, dest_y):
                    raise Blocked(f"Crossed to unexpected destination tile: {state}")
                print("QA_MEADOW_NATURAL_CONNECTION", source, dest,
                      "at", state["x"], state["y"], flush=True)
                return
            if group != source or state["x"] != x:
                raise Blocked(f"Natural connection diverged: {state}")
            if (key == "Down" and not source_y <= state["y"] <= source_y + 2):
                raise Blocked(f"Unexpected move before southern exit: {state}")
            if (key == "Up" and not source_y - 2 <= state["y"] <= source_y):
                raise Blocked(f"Unexpected move before northern exit: {state}")
        raise Blocked(f"Natural map transition {source}->{dest} not observed")

    def face(key, tile, target_map):
        initial, _ = check(f"before-face-{key}", target_map, field=True)
        if (initial["x"], initial["y"]) != tile:
            raise Blocked(f"Wrong facing origin: {initial} expected {tile}")
        press(key, duration=0.045)
        after, _ = check(f"face-{key}", target_map, field=True)
        if (after["x"], after["y"]) != tile:
            raise Blocked(f"Facing toward object moved player: {after}")

    def talk(tag, target_map, tile):
        prior, prior_frame = check(f"{tag}-before-A", target_map, field=True)
        if (prior["x"], prior["y"]) != tile:
            raise Blocked(f"Not source-adjacent for {tag}: {prior}")
        press("x", wait=1.3)
        msg, screenshot = check(f"{tag}-after-A", target_map)
        ratio = white_panel_ratio(screenshot)
        if (msg["x"], msg["y"]) != tile or ratio < 0.50:
            raise Blocked(f"No visible {tag} dialogue after A: {msg} {ratio:.3f}")
        print("QA_MEADOW_DIALOGUE", tag, f"panel={ratio:.4f}",
              str(screenshot), flush=True)
        return prior, msg

    def close_text(tag, target_map):
        # Check before pressing. No extra A is sent after the panel closes.
        for i in range(5):
            before, pic = check(f"{tag}-dismiss-pre-{i}", target_map)
            if white_panel_ratio(pic) <= 0.30:
                return before
            press("x", wait=1.0)
        after, pic = check(f"{tag}-dismiss-post", target_map)
        if white_panel_ratio(pic) > 0.30:
            raise Blocked(f"Cannot safely dismiss {tag} without blind input")
        return after

    start, frame = check("artist-waiting", windrow)
    if (start["x"], start["y"]) != (20, 15):
        raise Blocked(f"Must start adjacent to Windrow artist: {start}")
    if (start["sketchFound"] or start["sketchRewarded"]):
        raise Blocked(f"Cannot fake fresh Meadow prerequisite: {start}")
    before_berries = start["oranBerryQuantity"]
    close_text("artist-waiting", windrow)
    move("x", 19, windrow)
    move("y", 25, windrow)
    cross(windrow, meadow, "Down", 19, 25, 0)
    move("x", 18, meadow)
    move("y", 22, meadow)
    move("x", 11, meadow)
    face("Left", (11, 22), meadow)
    boy_before, boy_after = talk("boy-hint", meadow, (11, 22))
    if (boy_after["sketchFound"] or boy_after["sketchRewarded"]
            or boy_after["oranBerryQuantity"] != before_berries):
        raise Blocked("Meadow boy improperly granted sketch progress/reward")
    print("QA_MEADOW_BOY_HINT_NO_PROGRESS: visible dialogue, FOUND false",
          flush=True)
    close_text("boy-hint", meadow)
    move("y", 27, meadow)
    face("Right", (11, 27), meadow)
    tree_before, tree_after = talk("real-tree", meadow, (11, 27))
    if tree_before["sketchFound"] or tree_before["sketchRewarded"]:
        raise Blocked("FOUND/reward state already set before tree")
    if (not tree_after["sketchFound"] or tree_after["sketchRewarded"]
            or tree_after["oranBerryQuantity"] != before_berries):
        raise Blocked(f"Tree did not set FOUND alone: {tree_after}")
    print("QA_MEADOW_TREE_FOUND_ONLY: source BG_EVENT at (12,27), "
          "ordinary interaction from west", flush=True)
    close_text("tree-found", meadow)
    again_before, again_after = talk("tree-repeat", meadow, (11, 27))
    if (not again_after["sketchFound"] or again_after["sketchRewarded"]
            or again_after["oranBerryQuantity"] != before_berries):
        raise Blocked(f"Repeat tree gave premature reward/changed flag: {again_after}")
    print("QA_MEADOW_TREE_REPEAT_NO_REWARD", flush=True)
    close_text("tree-repeat", meadow)

    # Return along the identical source-verified connection. This tests
    # actual game navigation; a collision, wild encounter or map mismatch
    # stops without granting any quest prerequisites.
    move("y", 22, meadow)
    move("x", 18, meadow)
    move("y", 0, meadow)
    move("x", 19, meadow)
    cross(meadow, windrow, "Up", 19, 0, 25)
    move("y", 14, windrow)
    face("Right", (19, 14), windrow)
    reward_before, reward_after = talk("artist-reward", windrow, (19, 14))
    delta = reward_after["oranBerryQuantity"] - before_berries
    print("QA_MEADOW_REWARD_QUANTITY", "before", before_berries,
          "after", reward_after["oranBerryQuantity"], "delta", delta,
          flush=True)
    if (not reward_after["sketchStarted"] or not reward_after["sketchFound"]
            or not reward_after["sketchRewarded"] or delta != 3):
        raise Blocked("Artist did not add exactly three Oran Berries once "
                      f"with REWARDED flag: {reward_after}")
    print("QA_MEADOW_Q2_POSITIVE_BOUNDED: boy hint no effect, real tree "
          "FOUND only, repeat tree no duplication, return artist granted "
          "exactly +3 ORAN BERRIES by source-backed Bag read-only observer. "
          "Requires independent screenshot review; full-pocket, flash and "
          "whiteout remain NOT RUN.", flush=True)
    # Complete the reward/fanfare and the source's following DONE message
    # before a second normal interaction. Never modify saved reward flags.
    # The check does not infer 'done' merely from a short blank interlude.
    press("x", wait=4.0)
    saw_later_message = False
    released = False
    for i in range(8):
        now, panel_frame = check(f"reward-release-{i+1}", windrow)
        if (not now["sketchRewarded"] or
                now["oranBerryQuantity"] != before_berries + 3):
            raise Blocked(f"Reward mutated during fanfare/close: {now}")
        if white_panel_ratio(panel_frame) > 0.50:
            saw_later_message = True
            press("x", wait=1.2)
            continue
        if saw_later_message:
            # Re-check that dialogue remains closed after a full second;
            # only then attempt an independent second A against the artist.
            time.sleep(1.2)
            settled, _ = check(f"reward-release-settled-{i+1}",
                               windrow, field=True)
            if (settled["x"], settled["y"]) != (19, 14):
                raise Blocked(f"Changed tile while closing reward: {settled}")
            released = True
            break
        time.sleep(1.2)
    if not saw_later_message or not released:
        raise Blocked("Could not verify complete reward/fanfare/DONE dialogue "
                      "was released before duplicate attempt")
    duplicate_before, duplicate_after = talk(
        "artist-duplicate-claim", windrow, (19, 14))
    if (not duplicate_after["sketchRewarded"] or
            duplicate_after["oranBerryQuantity"] != before_berries + 3 or
            not duplicate_after["sketchFound"]):
        raise Blocked("Repeated artist interaction duplicated reward or "
                      f"changed quest flag: {duplicate_after}")
    print("QA_MEADOW_ARTIST_REPEAT_NO_DUPLICATE: same saved flags and "
          "Oran quantity before/after revisit; dialogue visually present. "
          "Human screenshot text review required.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    d = sub.add_parser("daemon")
    d.add_argument("--elf", type=Path, required=True)
    d.add_argument("--port", type=int, default=2345)
    d.add_argument("--fifo", required=True)
    d.add_argument("--ready", required=True)
    d.add_argument("--outdir", required=True)
    n = sub.add_parser("navigate")
    n.add_argument("--fifo", required=True)
    n.add_argument("--outdir", required=True)
    n.add_argument("--window", required=True)
    meadow = sub.add_parser("q2-meadow")
    meadow.add_argument("--fifo", required=True)
    meadow.add_argument("--outdir", required=True)
    meadow.add_argument("--window", required=True)
    b = sub.add_parser("q2-artist-offer")
    b.add_argument("--fifo", required=True)
    b.add_argument("--outdir", required=True)
    b.add_argument("--window", required=True)
    a = sub.add_parser("navigate-artist")
    a.add_argument("--fifo", required=True)
    a.add_argument("--outdir", required=True)
    a.add_argument("--window", required=True)
    q = sub.add_parser("q1-offer")
    q.add_argument("--fifo", required=True)
    q.add_argument("--outdir", required=True)
    q.add_argument("--window", required=True)
    u = sub.add_parser("assert-ui")
    u.add_argument("--kind", choices=["sidebar", "numeric", "field"], required=True)
    u.add_argument("--frame", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.mode == "daemon":
            return daemon(args)
        if args.mode == "assert-ui":
            return assert_ui(args)
        if args.mode == "q2-meadow":
            return q2_meadow(args)
        if args.mode == "q2-artist-offer":
            return q2_artist_offer(args)
        if args.mode == "navigate-artist":
            return navigate_artist(args)
        if args.mode == "q1-offer":
            return q1_offer(args)
        return navigate(args)
    except (Blocked, OSError, ValueError, subprocess.CalledProcessError,
            socket.timeout) as exc:
        print("QA_ACCESS_BLOCKED:", exc, file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main() or 0)
