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


def elf_symbol(elf):
    symbols = subprocess.check_output(
        ["arm-none-eabi-nm", "--defined-only", str(elf)], text=True)
    hits = re.findall(r"^([0-9a-fA-F]{8}) [A-Za-z] gSaveBlock1Ptr$", symbols, re.M)
    if len(hits) != 1:
        raise Blocked(f"ELF gSaveBlock1Ptr count must be one, found {len(hits)}")
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

    def position(self, symbol):
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
                        sketchRewarded=bool(flags_byte[0] & (1 << (0x2F & 7))))
        finally:
            self.command("c", reply=False)


def daemon(args):
    symbol = elf_symbol(args.elf)
    gdb = ReadOnlyGdb(args.port)
    gdb.start()
    Path(args.ready).write_text(f"read-only GDB: gSaveBlock1Ptr at 0x{symbol:08X}\n")
    while True:
        with open(args.fifo, encoding="ascii") as fifo:
            for line in fifo:
                name = line.strip()
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name):
                    continue
                try:
                    result = {"checkpoint": name, "position": gdb.position(symbol)}
                except Exception as exc:
                    result = {"checkpoint": name, "blocked": str(exc)}
                dest = Path(args.outdir) / f"{name}.json"
                temp = dest.with_suffix(".tmp")
                temp.write_text(json.dumps(result, sort_keys=True))
                os.replace(temp, dest)
                print("QA_POSITION", json.dumps(result, sort_keys=True), flush=True)
                if "blocked" in result:
                    return 2


def snapshot(args, name):
    dest = Path(args.outdir) / f"{name}.json"
    dest.unlink(missing_ok=True)
    with open(args.fifo, "w", encoding="ascii") as pipe:
        pipe.write(name + "\n")
    for _ in range(80):
        if dest.exists():
            result = json.loads(dest.read_text())
            if "blocked" in result:
                raise Blocked(result["blocked"])
            return result["position"]
        time.sleep(0.10)
    raise Blocked(f"Missing debugger reply for {name}")


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
    a = sub.add_parser("navigate-artist")
    a.add_argument("--fifo", required=True)
    a.add_argument("--outdir", required=True)
    a.add_argument("--window", required=True)
    q = sub.add_parser("q1-offer")
    q.add_argument("--fifo", required=True)
    q.add_argument("--outdir", required=True)
    q.add_argument("--window", required=True)
    u = sub.add_parser("assert-ui")
    u.add_argument("--kind", choices=["sidebar", "numeric"], required=True)
    u.add_argument("--frame", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.mode == "daemon":
            return daemon(args)
        if args.mode == "assert-ui":
            return assert_ui(args)
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
