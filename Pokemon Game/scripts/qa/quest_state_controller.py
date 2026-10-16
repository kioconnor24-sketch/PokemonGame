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
            # Verified against QUEST source global.h: pos at offset 0,
            # location mapGroup/mapNum/warpId at offsets 4/5/6.
            x, y, group, number, warp = struct.unpack_from("<hhbbb", data)
            if not 0 <= x < 256 or not 0 <= y < 256:
                raise Blocked(f"Invalid tile ({x},{y})")
            return dict(x=x, y=y, mapGroup=group, mapNum=number,
                        warpId=warp, saveBlockPtr=f"0x{ptr:08X}")
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
        if (pos["mapGroup"], pos["mapNum"]) != (76, 9):
            raise Blocked(f"Not source Alderfield map 76/9: {pos}")
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
    args = parser.parse_args()
    try:
        return daemon(args) if args.mode == "daemon" else navigate(args)
    except (Blocked, OSError, ValueError, subprocess.CalledProcessError,
            socket.timeout) as exc:
        print("QA_ACCESS_BLOCKED:", exc, file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main() or 0)
