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


def title_input_ready(tasks, target_func):
    # task.h: 16 Task records, each 40 bytes: func u32 at +0,
    # isActive u8 at +4, prev/next/priority u8 then data[16] s16.
    if len(tasks) != 16 * 40:
        raise Blocked("Title task-array read must be exactly 640 bytes")
    return any(tasks[i*40 + 4] == 1 and
               (struct.unpack_from("<I", tasks, i*40)[0] & ~1)
               == (target_func & ~1) for i in range(16))


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

    def menu_state(self, symbols, include_tasks=False):
        """Read actual save/menu and optional title-task state, without writes."""
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
            callback2 = struct.unpack(
                "<I", read(symbols["main"] + 4, 4))[0]
            main_phase = next(
                (name for name, addr in symbols["mainCallbacks"].items()
                 if (callback2 & ~1) == (addr & ~1)), "other")
            save_status = struct.unpack(
                "<H", read(symbols["saveStatus"], 2))[0]
            save_attempt = struct.unpack(
                "<H", read(symbols["saveAttempt"], 2))[0]
            different = read(symbols["differentFile"], 1)[0]
            ready = None
            if include_tasks:
                tasks = read(symbols["taskArray"], 16 * 40)
                ready = title_input_ready(tasks, symbols["titleReadyFunc"])
            return dict(titleInputReady=ready,
                        count=n, cursor=index, actions=actions[:n],
                        selected=actions[index] if n else None,
                        saveCallback=f"0x{cb:08X}", savePhase=phase,
                        mainCallback2=f"0x{callback2:08X}",
                        mainPhase=main_phase, saveStatus=save_status,
                        saveAttemptStatus=save_attempt,
                        differentSaveFile=different)
        finally:
            self.command("c", reply=False)

    def title_state(self, symbols):
        """Only title-relevant globals: never read stale Start-menu RAM."""
        self.sock.sendall(b"\\x03")
        stop = self.packet()
        if not stop.startswith(("S", "T")):
            raise Blocked(f"Title debugger interrupt failed: {stop[:70]}")
        try:
            def read(name, addr, size):
                raw = self.command(f"m{addr:x},{size:x}")
                # GDB error responses (e.g., E14) are NOT packed game data.
                if raw.startswith("E") and len(raw) == 3:
                    raise Blocked(
                        f"title {name} read 0x{addr:08X}: GDB {raw}")
                try:
                    data = bytes.fromhex(raw)
                except ValueError as exc:
                    raise Blocked(
                        f"title {name} read 0x{addr:08X}: malformed GDB "
                        f"reply {raw[:24]!r}") from exc
                if len(data) != size:
                    raise Blocked(f"title {name} read size {len(data)}/{size}")
                return data
            cb = struct.unpack("<I", read(
                "main callback", symbols["main"] + 4, 4))[0]
            phase = next(
                (name for name, addr in symbols["mainCallbacks"].items()
                 if (cb & ~1) == (addr & ~1)), "other")
            status = struct.unpack("<H", read(
                "save file status", symbols["saveStatus"], 2))[0]
            tasks = read("title task array", symbols["taskArray"], 16 * 40)
            ready = title_input_ready(tasks, symbols["titleReadyFunc"])
            return dict(mainCallback2=f"0x{cb:08X}", mainPhase=phase,
                        saveStatus=status, titleInputReady=ready)
        finally:
            self.command("c", reply=False)

    def position(self, symbol, symbol2, parties_count_symbol=None, badge_probe=False, gym_probe=False, battle_main_symbol=None, heal_probe=False):
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
            badge_data = {}
            if badge_probe:
                # flags.h: SYSTEM_FLAGS=0x860; FLAG_BADGE01_GET=0x867.
                # Source SaveBlock1.flags begins at +0x1270.
                badge = bytes.fromhex(self.command(
                    f"m{ptr + 0x1270 + (0x867 // 8):x},1"))
                if len(badge) != 1:
                    raise Blocked("Incomplete saved Badge01 flag read")
                badge_data = dict(badge01=bool(
                    badge[0] & (1 << (0x867 & 7))))
            if gym_probe:
                sluices = bytes.fromhex(self.command(
                    f"m{ptr + 0x1270 + (0x25 // 8):x},1"))
                if len(sluices) != 1:
                    raise Blocked("Incomplete first-gym sluice saved flag read")
                badge_data.update(
                    gymWestSluice=bool(sluices[0] & (1 << (0x25 & 7))),
                    gymEastSluice=bool(sluices[0] & (1 << (0x26 & 7))))
            gift_data = {}
            if parties_count_symbol is not None:
                # flags[0x37 // 8] uses one more saved byte; do not
                # silently treat the sketch flag byte as the gift byte.
                gift_raw = bytes.fromhex(self.command(
                    f"m{ptr + 0x1270 + (0x37 // 8):x},1"))
                count_raw = bytes.fromhex(self.command(
                    f"m{parties_count_symbol:x},1"))
                if len(gift_raw) != 1 or len(count_raw) != 1:
                    raise Blocked("Incomplete gift/party count probe")
                if count_raw[0] > 6:
                    raise Blocked(f"Invalid actual party count {count_raw[0]}")
                gift_data = dict(
                    devGiftReceived=bool(
                        gift_raw[0] & (1 << (0x37 & 7))),
                    playerPartyCount=count_raw[0])
            battle_data = {}
            if battle_main_symbol is not None:
                # Source engine/include/main.h: gMain +0x439,
                # oamLoadDisabled bit0 and inBattle bit1.
                raw = bytes.fromhex(self.command(
                    f"m{battle_main_symbol + 0x439:x},1"))
                if len(raw) != 1:
                    raise Blocked("Incomplete source battle bit read")
                battle_data = dict(inBattle=bool(raw[0] & 2))
            heal_data = {}
            if heal_probe:
                # SaveBlock1.lastHealLocation at +0x1C, read only.
                # WarpData: s8 group,num,warp, pad; s16 x,y.
                raw = bytes.fromhex(self.command(f"m{ptr + 0x1c:x},8"))
                if len(raw) != 8:
                    raise Blocked("Incomplete actual last-heal warp data")
                hgroup, hnum, hwarp, hx, hy = struct.unpack("<bbbxhh", raw)
                heal_data = dict(lastHealMapGroup=hgroup, lastHealMapNum=hnum,
                                 lastHealWarpId=hwarp, lastHealX=hx,
                                 lastHealY=hy)
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
                        oranBerryQuantity=oran_qty,
                        **gift_data, **badge_data, **battle_data, **heal_data)
        finally:
            self.command("c", reply=False)


def reboot_transient(name, exc):
    """Only polling after real reset may retry unavailable debugger memory."""
    return (name.startswith("title-") and
            isinstance(exc, (ValueError, Blocked, OSError, socket.timeout)))



def daemon(args):
    symbol = elf_symbol(args.elf, "gSaveBlock1Ptr")
    symbol2 = elf_symbol(args.elf, "gSaveBlock2Ptr")
    parties_count = elf_symbol(args.elf, "gPartiesCount")
    menu_symbols = {
        "cursor": elf_symbol(args.elf, "sStartMenuCursorPos"),
        "count": elf_symbol(args.elf, "sNumStartMenuActions"),
        "actions": elf_symbol(args.elf, "sCurrentStartMenuActions"),
        "saveCallback": elf_symbol(args.elf, "sSaveDialogCallback"),
        "main": elf_symbol(args.elf, "gMain"),
        "saveStatus": elf_symbol(args.elf, "gSaveFileStatus"),
        "saveAttempt": elf_symbol(args.elf, "gSaveAttemptStatus"),
        "differentFile": elf_symbol(args.elf, "gDifferentSaveFile"),
        "taskArray": elf_symbol(args.elf, "gTasks"),
        "titleReadyFunc": elf_symbol(args.elf, "Task_TitleScreenPhase3"),
        "mainCallbacks": {
            name: elf_symbol(args.elf, name)
            for name in ("CB2_InitTitleScreen", "CB2_InitMainMenu",
                         "CB2_MainMenu", "CB2_ContinueSavedGame",
                         "CB2_Overworld")
        },
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
                    result = {"checkpoint": name}
                    if not name.startswith("title-"):
                        result["position"] = gdb.position(
                            symbol, symbol2,
                            parties_count_symbol=parties_count
                            if name.startswith(("q4-", "q3-")) else None,
                            badge_probe=name.startswith(("q1-gate", "q3-")),
                            gym_probe=name.startswith("q3-"),
                            battle_main_symbol=menu_symbols["main"]
                            if name.startswith(("q3-battle-", "q3-play-")) else None,
                            heal_probe=name.startswith(("q3-clinic-", "q3-play-")))
                    if name.startswith("title-"):
                        result["menu"] = gdb.title_state(menu_symbols)
                    elif name.startswith("save-"):
                        result["menu"] = gdb.menu_state(menu_symbols)
                except Exception as exc:
                    if reboot_transient(name, exc):
                        # Expected possibility while GBA's CPU resets and
                        # gTasks/menu globals are not initialized. Preserve
                        # a non-accepting, observable retry state; do not
                        # silently declare a title, save, or Continue PASS.
                        result = {"checkpoint": name, "transient": str(exc),
                                  "menu": {"mainPhase": "unavailable",
                                           "mainCallback2": None,
                                           "saveStatus": None,
                                           "titleInputReady": False}}
                    else:
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
    # O_NONBLOCK guarantees a failed debugger daemon cannot hang the
    # entire Actions job waiting for a reader that has already exited.
    try:
        fd = os.open(args.fifo, os.O_WRONLY | os.O_NONBLOCK)
    except OSError as exc:
        raise Blocked(f"Debugger daemon not reading FIFO at {name}: {exc}") from exc
    try:
        os.write(fd, (name + "\n").encode("ascii"))
    finally:
        os.close(fd)
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



def save_probe(args, stage, require_position=True):
    """Visible screenshot + read-only source-derived save/menu telemetry."""
    frame = Path(args.outdir) / (stage + ".png")
    grab(args.window, frame)
    obj = snapshot_detail(args, stage)
    ui = obj.get("menu")
    if ui is None:
        raise Blocked(f"No read-only save menu response for {stage}")
    pos = obj.get("position")
    if require_position and pos is None:
        raise Blocked(f"No game position read for {stage}")
    print("QA_SAVE_PROBE", stage, json.dumps(obj, sort_keys=True),
          str(frame), flush=True)
    return obj, frame


def qa_key(window, name, duration=0.11, wait=0.8):
    subprocess.run(["xdotool", "windowactivate", str(window)], check=False)
    subprocess.run(["xdotool", "keydown", name], check=True)
    time.sleep(duration)
    subprocess.run(["xdotool", "keyup", name], check=True)
    time.sleep(wait)


def require_q2_complete(pos, expected_qty=3):
    if (pos["mapGroup"], pos["mapNum"], pos["x"], pos["y"]
            ) != (75, 6, 19, 14):
        raise Blocked(f"Unexpected Q2 artist save/continue tile: {pos}")
    expected = dict(notesStarted=True, notesRecorded=False,
                    notesRewarded=False, sketchStarted=True,
                    sketchFound=True, sketchRewarded=True,
                    oranBerryQuantity=expected_qty)
    for key, value in expected.items():
        if pos.get(key) != value:
            raise Blocked(f"Q2 save/reload state mismatch for {key}: "
                          f"expected {value}, got {pos.get(key)}")


def q2_save(args):
    """Perform ordinary Start/SAVE/YES; prove actual success callback."""
    state, frame = save_probe(args, "save-001-artist-done")
    require_q2_complete(state["position"])
    if white_panel_ratio(frame) < 0.50:
        raise Blocked("Expected completed-quest dialogue before save")
    qa_key(args.window, "x", wait=1.7)
    state, frame = save_probe(args, "save-002-done-dismissed")
    require_q2_complete(state["position"])
    if white_panel_ratio(frame) > 0.30:
        raise Blocked("DONE dialogue did not close: can't open Start menu")
    qa_key(args.window, "Return", wait=1.5)
    state, frame = save_probe(args, "save-003-start-menu-open")
    require_q2_complete(state["position"])
    menu = state["menu"]
    # start_menu.c: enum MENU_ACTION_SAVE = 5; actual ordered actions and
    # cursor are read from same binary's EWRAM symbols on every step.
    if not (3 <= menu["count"] <= 9 and
            menu["actions"].count(5) == 1 and
            menu["selected"] in menu["actions"]):
        raise Blocked(f"Ordinary Start menu not observed: {menu}")
    destination = menu["actions"].index(5)
    for attempt in range(9):
        if menu["selected"] == 5:
            break
        if menu["cursor"] == destination:
            raise Blocked(f"Selection inconsistent despite matching cursor: {menu}")
        # Use the monotone path through the known source action list,
        # never blindly hold Down or rely on one keypress being one row.
        direction = "Down" if menu["cursor"] < destination else "Up"
        old_index = menu["cursor"]
        qa_key(args.window, direction, wait=0.65)
        state, _ = save_probe(args, f"save-004-choice-{attempt+1}")
        menu = state["menu"]
        if menu["cursor"] not in (old_index, old_index +
                                  (1 if direction == "Down" else -1)):
            raise Blocked(f"Uncontrolled Start cursor after {direction}: {menu}")
    if menu["selected"] != 5:
        raise Blocked(f"Could not select exactly source action SAVE=5: {menu}")
    print("QA_SAVE_START_ACTION_SELECTED", menu, flush=True)
    qa_key(args.window, "x", wait=0.9)
    # Wait for source SaveYesNoCallback to install the real Yes/No handler.
    for attempt in range(20):
        state, frame = save_probe(args, f"save-005-confirm-wait-{attempt+1}")
        menu = state["menu"]
        if menu["savePhase"] == "SaveConfirmInputCallback":
            if white_panel_ratio(frame) < 0.5:
                raise Blocked("Save-confirm callback but no visible dialogue")
            break
        time.sleep(0.35)
    else:
        raise Blocked("Source SAVE confirm callback never observed")
    # First explicit Yes uses source DisplayYesNoMenuDefaultYes().
    qa_key(args.window, "x", wait=0.8)
    confirmed_success = False
    for attempt in range(50):
        state, frame = save_probe(args, f"save-006-write-stage-{attempt+1}")
        menu = state["menu"]
        phase = menu["savePhase"]
        if phase == "SaveOverwriteInputCallback":
            # Existing file prompts default YES except when the game reports
            # gDifferentSaveFile, whose default NO must not be guessed.
            if menu["differentSaveFile"] != 0:
                raise Blocked("Different-save overwrite requires independent owner approval")
            qa_key(args.window, "x", wait=0.9)
        elif phase in ("SaveSuccessCallback", "SaveReturnSuccessCallback"):
            confirmed_success = True
            print("QA_SAVE_SUCCESS_CALLBACK", phase, flush=True)
            break
        elif phase == "SaveErrorCallback":
            raise Blocked("Actual in-game save error callback")
        time.sleep(0.30)
    if not confirmed_success:
        raise Blocked("Never observed real successful Save callback")
    # Keep emulator running; allow on-screen saving success and automatic
    # Start-menu dismissal.  Only a prior seen successful callback counts.
    for i in range(30):
        state, frame = save_probe(args, f"save-007-return-field-{i+1}")
        require_q2_complete(state["position"])
        if white_panel_ratio(frame) <= 0.30:
            # save.c TrySavingData sets gSaveAttemptStatus=SAVE_STATUS_OK.
            # gSaveFileStatus is a LOAD status, and can remain EMPTY until
            # a real reset/Continue. Do not conflate the two.
            if state["menu"]["saveAttemptStatus"] != 1:
                raise Blocked("Actual save attempt did not report STATUS_OK=1")
            print("QA_SAVE_REAL_SUCCESS: game callback confirmed; "
                  "completed Q2 flags and exactly 3 Oran observed; "
                  "reset/Continue remains a separate checkpoint", flush=True)
            return
        time.sleep(0.45)
    raise Blocked("Save success message never visibly closed")


def q2_reset_continue(args):
    """Soft-reset with ordinary keys and accept only real saved Continue."""
    before, frame = save_probe(args, "save-101-before-softreset")
    require_q2_complete(before["position"])
    if white_panel_ratio(frame) > 0.30:
        raise Blocked("Cannot reset until field is visibly idle")
    # GBA A+B+START+SELECT soft-reset is a normal input, never a GDB
    # write or savestate.  An observed title callback is REQUIRED before
    # any claim that RAM has reloaded from game flash.
    subprocess.run(["xdotool", "windowactivate", str(args.window)], check=False)
    for key in ("x", "z", "Return", "BackSpace"):
        subprocess.run(["xdotool", "keydown", key], check=True)
        time.sleep(0.12)
    time.sleep(1.0)
    for key in ("BackSpace", "Return", "z", "x"):
        subprocess.run(["xdotool", "keyup", key], check=True)
    time.sleep(2.0)

    observed_title = False
    observed_main = False
    requested_menu = False
    before_callback = before["menu"]["mainCallback2"]
    # Source title_screen.c Task_TitleScreenPhase3 only exists when
    # Press Start is available; wait for ACTUAL active TaskFunc rather
    # than guessing how long copyright, logos or fade animations take.
    for i in range(110):
        sample, frame = save_probe(
            args, f"title-102-title-poll-{i+1}", require_position=False)
        phase = sample["menu"]["mainPhase"]
        if sample.get("transient"):
            print("QA_TITLE_TRANSIENT_RETRY", sample["transient"], flush=True)
            time.sleep(0.60)
            continue
        if phase in ("CB2_InitTitleScreen", "CB2_InitMainMenu"):
            observed_title = True
        if sample["menu"]["titleInputReady"]:
            observed_title = True
        if (phase == "other" and
                sample["menu"]["mainCallback2"] != before_callback):
            # title_screen.c uses a local MainCB2 name that multiple
            # source files share. Never guess one of their ELF addresses;
            # require distinct main callback + saved Continue below.
            observed_title = True
        if phase == "CB2_MainMenu":
            if not observed_title:
                raise Blocked("Main menu reached with no observed soft reset/title")
            if sample["menu"]["saveStatus"] != 1:
                raise Blocked("Main menu did not detect a valid saved game")
            observed_main = True
            break
        if (not requested_menu and sample["menu"]["titleInputReady"]
                and sample["menu"]["saveStatus"] == 1):
            print("QA_TITLE_INPUT_READY: Task_TitleScreenPhase3 active "
                  "and saved-file status OK; press START once", flush=True)
            requested_menu = True
            qa_key(args.window, "Return", wait=1.7)
        time.sleep(0.60)
    if not (observed_title and observed_main):
        raise Blocked("Soft reset did not visibly enter saved-game main menu")
    print("QA_SAVE_REBOOT_TITLE_AND_CONTINUE_MENU", flush=True)
    time.sleep(1.5)
    qa_key(args.window, "x", wait=2.0)
    # main_menu.c: for SAVE_STATUS_OK, entry #0 is ACTION_CONTINUE.
    # We do not try a second A while the selection is uncertain.
    for i in range(40):
        sample, frame = save_probe(
            args, f"title-103-continue-poll-{i+1}",
            require_position=False)
        phase = sample["menu"]["mainPhase"]
        if phase == "CB2_MainMenu" and i >= 9:
            raise Blocked("Continue A did not transition out of main menu")
        if phase == "CB2_Overworld":
            # A non-menu field callback is expected only AFTER the
            # graphical Continue action; now check reloaded gameplay RAM.
            try:
                fresh, scene = save_probe(
                    args, f"save-104-after-continue-{i+1}")
                require_q2_complete(fresh["position"])
                if white_panel_ratio(scene) <= 0.30:
                    print("QA_Q2_FLASH_ROUNDTRIP_PASS: observed title and "
                          "Continue after actual soft reset, reloaded "
                          "source map/position, QUEST flags and Oran=3 "
                          "without debugger writes", flush=True)
                    return
            except Blocked:
                # Field may still be initializing; bounded retry.
                pass
        time.sleep(0.6)
    raise Blocked("Never observed resumed field with persistent Q2 state")


def q2_continue_relaunch(args):
    """Fresh GBA process, original flash file, genuine Continue; no savestate.

    The previous in-process soft reset rendered the real Emerald title but
    mGBA 0.10.2's GDB socket ceased answering. An emulator process restart
    is a stronger persistence boundary: this controller never copies a RAM
    image or inserts quest flags; the game must load its own flash.
    """
    last = None
    saw_title = False
    saw_main = False
    sent_start = False
    for i in range(100):
        state, frame = save_probe(
            args, f"title-relaunch-before-continue-{i+1}",
            require_position=False)
        menu = state["menu"]
        if state.get("transient"):
            print("QA_RELAUNCH_GDB_TRANSIENT", state["transient"], flush=True)
            time.sleep(0.5)
            continue
        phase = menu["mainPhase"]
        last = menu
        if phase in ("CB2_InitTitleScreen", "CB2_InitMainMenu"):
            saw_title = True
        if menu["titleInputReady"]:
            saw_title = True
        if phase == "CB2_MainMenu":
            if menu["saveStatus"] != 1:
                raise Blocked(
                    "Fresh emulator main menu did not load valid flash save")
            saw_main = True
            break
        if not sent_start and menu["titleInputReady"]:
            if menu["saveStatus"] != 1:
                raise Blocked(
                    "Title ready but original on-disk save is invalid/missing")
            print("QA_RELAUNCH_REAL_TITLE_READY", menu, flush=True)
            sent_start = True
            qa_key(args.window, "Return", wait=1.4)
        time.sleep(0.55)
    if not saw_title or not saw_main:
        raise Blocked(f"No independently verified title/menu after "
                      f"fresh emulator restart: {last}")
    print("QA_RELAUNCH_VALID_FLASH_MAIN_MENU", last, flush=True)
    # A single A to default main-menu option CONTINUE is permissible only
    # after source CB2_MainMenu and SAVE_STATUS_OK are actually observed.
    qa_key(args.window, "x", wait=1.5)
    left_menu = False
    for i in range(65):
        state, frame = save_probe(
            args, f"title-relaunch-continue-{i+1}",
            require_position=False)
        menu = state["menu"]
        if state.get("transient"):
            time.sleep(0.45)
            continue
        phase = menu["mainPhase"]
        if phase == "CB2_MainMenu":
            if i >= 12:
                raise Blocked("Continue input never left valid main menu")
        else:
            left_menu = True
        if phase == "CB2_Overworld" and left_menu:
            # Wait for restored field RAM to be safely accessible.
            for j in range(30):
                try:
                    fresh, image = save_probe(
                        args, f"save-relaunch-restored-field-{j+1}")
                    require_q2_complete(fresh["position"], expected_qty=3)
                    if white_panel_ratio(image) <= 0.30:
                        print("QA_Q2_FLASH_POWER_CYCLE_PASS: new emulator "
                              "instance loaded genuine flash SAVE, valid "
                              "CONTINUE, exact original map/position, Q1/Q2 "
                              "flags and ORAN=3; no savestate/memory write",
                              flush=True)
                        return
                except Blocked as exc:
                    print("QA_RELAUNCH_FIELD_NOT_YET_READY", str(exc), flush=True)
                time.sleep(0.6)
            raise Blocked("Continue transition observed but field state "
                          "did not match saved source conditions")
        time.sleep(0.5)
    raise Blocked(f"Continue never returned to verified game field: {last}")



def q4_lab_gift(args):
    """Actual existing lab Script4 gift, no item/flag/party writes."""
    directory = Path(args.outdir)
    n = 600

    def read(label, field=False):
        nonlocal n
        n += 1
        tag = f"q4-{n:03d}-{label}"
        image = directory / (tag + ".png")
        grab(args.window, image)
        state = snapshot(args, tag)
        print("QA_GIFT_STATE", tag, json.dumps(state, sort_keys=True),
              str(image), flush=True)
        if (state["mapGroup"], state["mapNum"]) != (75, 14):
            raise Blocked(f"Script4 did not enter actual AveronFieldLab: {state}")
        if not state["sketchRewarded"]:
            raise Blocked(f"Existing sketch prerequisite missing: {state}")
        if field and white_panel_ratio(image) > 0.30:
            raise Blocked(f"Unexpected lab textbox on route {tag}")
        return state, image

    def key(k, duration=0.095, delay=0.42):
        subprocess.run(["xdotool", "windowactivate", str(args.window)],
                       check=False)
        subprocess.run(["xdotool", "keydown", k], check=True)
        time.sleep(duration)
        subprocess.run(["xdotool", "keyup", k], check=True)
        time.sleep(delay)

    def move(axis, target):
        here, _ = read(f"before-{axis}-{target}", field=True)
        idle = 0
        for i in range(60):
            if here[axis] == target:
                return
            sign = 1 if target > here[axis] else -1
            k = (("Right" if sign > 0 else "Left") if axis == "x"
                 else ("Down" if sign > 0 else "Up"))
            key(k)
            next_state, _ = read(f"{axis}-{target}-{i+1}", field=True)
            other = "y" if axis == "x" else "x"
            delta = next_state[axis] - here[axis]
            if delta not in (0, sign) or next_state[other] != here[other]:
                raise Blocked(f"Uncontrolled lab movement: {here}->{next_state}")
            idle = idle+1 if delta == 0 else 0
            if idle >= 4:
                raise Blocked(f"Original lab collision at {next_state}")
            here = next_state
        raise Blocked(f"Lab route >60 steps for {axis}={target}")

    def panel_ratio(path):
        return white_panel_ratio(path)

    def menu_ratio(path):
        pixels = subprocess.check_output([
            "convert", str(path), "-crop", "106x90+323+130",
            "+repage", "-depth", "8", "RGB:-"])
        if len(pixels) != 106*90*3:
            raise Blocked("Malformed lab YesNo crop")
        return sum(min(pixels[i:i+3]) >= 190
                   for i in range(0, len(pixels), 3))/(106*90)

    state, _ = read("script4-entry")
    if not (2 <= state["x"] <= 8 and 2 <= state["y"] <= 8):
        raise Blocked(f"Unexpected Script4 lab arrival tile: {state}")
    if state["devGiftReceived"]:
        raise Blocked("Gift was already received at start; cannot test fresh gift")
    original_party = state["playerPartyCount"]
    if original_party >= 6:
        raise Blocked("Gift positive branch needs a genuinely nonfull party")
    # Verified against unchanged data/layouts/AveronFieldLab/map.bin:
    # water occupies x17..24, rows5..16; original land corridor x25
    # remains metatile 0x01. Do NOT walk down from (24,4) into water.
    move("x", 25)
    move("y", 18)
    move("x", 24)
    move("y", 19)
    at, empty = read("scientist-west", field=True)
    if (at["x"], at["y"]) != (24, 19):
        raise Blocked(f"Not beside existing scientist (25,19): {at}")
    key("Right", duration=0.045)
    faced, _ = read("scientist-face-right", field=True)
    if (faced["x"], faced["y"]) != (24, 19):
        raise Blocked("Facing scientist unexpectedly moved player")
    key("x", delay=1.4)
    open_state, offer = read("offer-first")
    if panel_ratio(offer) < 0.5:
        raise Blocked("No visible source scientist dialogue")
    if open_state["devGiftReceived"] or open_state["playerPartyCount"] != original_party:
        raise Blocked("Gift incorrectly triggered before ordinary YES")
    for i in range(12):
        current, picture = read(f"offer-menu-{i+1}")
        if menu_ratio(picture) >= 0.52:
            offer = picture
            break
        time.sleep(0.6)
    else:
        raise Blocked("Scientist YESNO menu not visually observed")
    key("Down")
    no_state, no_pic = read("selected-NO")
    if menu_ratio(no_pic) < 0.52:
        raise Blocked("Scientist NO menu missing")
    key("x")
    refused, refuse_pic = read("refuse-message")
    if (refused["devGiftReceived"] or
            refused["playerPartyCount"] != original_party):
        raise Blocked("Scientist refusal altered party/flag")
    print("QA_Q4_SCIENTIST_REFUSAL_NO_GIFT: observed source lab event",
          flush=True)
    # The source NO branch usually closes directly into the field.
    # First OBSERVE refusal postcondition; blindly pressing A here
    # reopened the offer and then selected default YES in run38862320655.
    here, pic = read("refuse-postcondition")
    if here["devGiftReceived"] or here["playerPartyCount"] != original_party:
        raise Blocked("Gift mutated after NO (before re-interaction)")
    if panel_ratio(pic) > 0.30:
        for i in range(5):
            key("x",delay=0.8)
            here, pic = read(f"refuse-dismiss-{i+1}")
            if here["devGiftReceived"] or here["playerPartyCount"] != original_party:
                raise Blocked("Unexpected grant while dismissing refusal")
            if panel_ratio(pic) <= 0.30:
                break
        else:
            raise Blocked("Could not close original scientist refusal text")
    # A is issued exactly once ONLY after the returned field is verified.
    key("x", delay=1.4)
    for i in range(12):
        candidate, pic = read(f"reoffer-menu-{i+1}")
        if menu_ratio(pic) >= 0.52:
            break
        time.sleep(0.6)
    else:
        raise Blocked("Scientist reoffer YESNO did not render")
    key("x",delay=1.8)
    accepted, granted_pic = read("gift-accepted")
    if (not accepted["devGiftReceived"] or
            accepted["playerPartyCount"] != original_party + 1):
        raise Blocked(f"Source-gift YES did not add ONE party member: {accepted}")
    if panel_ratio(granted_pic) < 0.50:
        raise Blocked("Gift success message absent")
    print("QA_Q4_GIFT_POSITIVE_FLAG_PARTY_PASS: only after actual YES, "
          "DEV_GIFT_RECEIVED=true, player-party count +1; species/level "
          "still require party-menu screenshot review.", flush=True)
    for i in range(7):
        key("x",delay=0.9)
        here, pic = read(f"gift-dismiss-{i+1}")
        if panel_ratio(pic) < 0.30:
            break
    else:
        raise Blocked("Could not dismiss success text for duplicate test")
    key("x",delay=1.2)
    repeated, repeat_pic = read("gift-duplicate-dialogue")
    if (not repeated["devGiftReceived"] or
            repeated["playerPartyCount"] != original_party + 1 or
            panel_ratio(repeat_pic) < 0.5):
        raise Blocked("Scientist repeat interaction changed gift or failed UI")
    print("QA_Q4_GIFT_REPEAT_NO_DUPLICATE: source completion dialogue, "
          "flag and party count stable. Full-party and save-reload still "
          "NOT ACCEPTED.", flush=True)
    # Q5 bounded runtime input-release evidence after an actual scripted
    # gift. Adjacent original lab tile (23,19) is 0x01 land in source
    # blockdata and has no defined NPC. This is not a follower PASS claim.
    for i in range(5):
        key("x", delay=0.7)
        idle, pic = read(f"gift-repeat-dismiss-{i+1}")
        if white_panel_ratio(pic) <= 0.30:
            break
    else:
        raise Blocked("Gift done message never released normal field controls")
    # The first direction press in Emerald may only turn the avatar.
    # Require exact legal single-tile movement, accepting a facing-only
    # frame as an observed retry, without guessing a timed button batch.
    for direction, destination in (("Left", 23), ("Right", 24)):
        origin = 24 if direction == "Left" else 23
        for attempt in range(5):
            key(direction)
            stepped, step_frame = read(
                f"post-gift-{direction.lower()}-{attempt+1}", field=True)
            if (not stepped["devGiftReceived"]
                    or stepped["playerPartyCount"] != original_party + 1
                    or stepped["y"] != 19
                    or stepped["x"] not in (origin, destination)):
                raise Blocked(
                    f"Invalid post-gift movement/flag transition: {stepped}")
            if stepped["x"] == destination:
                break
        else:
            raise Blocked(
                f"Field never moved from x{origin} to x{destination} "
                f"after observed facing-only attempts")
    print("QA_Q5_POST_GIFT_CONTROL_RECOVERY: script/dialogue exited; "
          "real left/right D-pad restored; party and gift flags stable. "
          "Follower/audio remain visually/aurally unverified.", flush=True)



def q1_badge_gate(args):
    """Observe the real pre-Badge01 Bluffs denial from ordinary Alderfield.

    No badge writes, battle skips, waypoint insertion, or synthetic warp.
    """
    out = Path(args.outdir)
    n = 700

    def read(label, require_field=False):
        nonlocal n
        n += 1
        name = f"q1-gate-{n:03d}-{label}"
        image = out / (name + ".png")
        grab(args.window, image)
        data = snapshot(args, name)
        print("QA_BLuffs_GATE", name, json.dumps(data, sort_keys=True),
              str(image), flush=True)
        if (data["mapGroup"], data["mapNum"]) != (75, 9):
            raise Blocked(f"Q1 gate left original Alderfield map: {data}")
        if data["badge01"]:
            raise Blocked("Refuse to label badge-gate denial: actual Badge01 is set")
        if (not data["notesStarted"] or data["notesRecorded"]
                or data["notesRewarded"]):
            raise Blocked(f"Q1 stage changed unexpectedly approaching gate: {data}")
        if require_field and white_panel_ratio(image) > 0.30:
            raise Blocked(f"Q1 unexpected dialogue during gate navigation: {data}")
        return data, image

    def key(k, duration=0.09, wait=0.46):
        subprocess.run(["xdotool", "windowactivate", str(args.window)],
                       check=False)
        subprocess.run(["xdotool", "keydown", k], check=True)
        time.sleep(duration)
        subprocess.run(["xdotool", "keyup", k], check=True)
        time.sleep(wait)

    start, image = read("researcher-accepted")
    if (start["x"], start["y"]) != (13, 16):
        raise Blocked(f"Q1 gate starts from researcher-adjacent tile: {start}")
    if white_panel_ratio(image) > 0.50:
        for page in range(6):
            key("x", wait=1.0)
            clear, image = read(f"researcher-accepted-dismissed-{page+1}")
            if white_panel_ratio(image) <= 0.30:
                break
        else:
            raise Blocked("Researcher waiting text never dismissed after "
                          "six observed pages")
    last, _ = read("start-east", require_field=True)
    stationary = 0
    for i in range(58):
        if last["x"] == 37:
            break
        key("Right")
        state, _ = read(f"east-{i+1}", require_field=True)
        dx = state["x"] - last["x"]
        if state["y"] != 16 or dx not in (0, 1):
            raise Blocked(f"Unverified ordinary Alderfield movement: {last}->{state}")
        stationary = stationary + 1 if dx == 0 else 0
        if stationary >= 4:
            raise Blocked(f"Collision/blocked before source trigger x38: {state}")
        last = state
    else:
        raise Blocked("Could not approach legal badge-gate x37")
    if last["x"] != 37:
        raise Blocked(f"Wrong gate adjacency: {last}")
    # Actual Alderfield original coord-event at (38,16), with source
    # CoastalBluffs_BadgeGate giving text and walk_left when no badge.
    key("Right", wait=1.5)
    active, prompt = read("no-badge-gate-triggered")
    if white_panel_ratio(prompt) < 0.50:
        raise Blocked("Badge gate produced no visibly active denial dialogue")
    if active["x"] not in (37, 38):
        raise Blocked(f"Unexpected trigger destination: {active}")
    print("QA_Q1_BADGE_GATE_DENIAL_DIALOGUE_OBSERVED", flush=True)
    key("x", wait=2.0)
    for i in range(12):
        post, frame = read(f"post-gate-walk-left-{i+1}")
        if (post["x"], post["y"]) == (37, 16) and white_panel_ratio(frame) < 0.30:
            print("QA_Q1_BADGE_GATE_NEGATIVE_PASS: actual no-badge field "
                  "trigger, real denial dialogue and forced walk_left; "
                  "Q1 started/recorded/rewarded unchanged, no invented map",
                  flush=True)
            return
        time.sleep(0.5)
    raise Blocked("Gate denial message seen but script did not regain field "
                  "at original Alderfield tile (37,16)")



# Verified Emerald Bag order from actual mGBA run 38870779185:
# Items -> Poke Balls -> TMs & HMs -> Berries -> Key Items.
# The third (not fourth) RIGHT press reaches the visible Oran Berry x3.
BAG_POCKET_ORDER = ("ITEMS", "POKE BALLS", "TMS & HMS", "BERRIES", "KEY ITEMS")


def bag_pocket_right_steps(start, target):
    """Calculate actual visible right-tab inputs; reject unknown pockets."""
    if start not in BAG_POCKET_ORDER or target not in BAG_POCKET_ORDER:
        raise Blocked(f"Unknown original Bag pocket: {start!r} -> {target!r}")
    return (BAG_POCKET_ORDER.index(target) - BAG_POCKET_ORDER.index(start)) % len(BAG_POCKET_ORDER)


def visual_frame_data(path):
    """Source screenshot geometry only; reads pixels, never emulator memory."""
    wh = subprocess.check_output(
        ["identify", "-format", "%wx%h", str(path)], text=True)
    if wh != "480x320":
        raise Blocked(f"Unexpected actual mGBA frame geometry {wh}")
    rgb = subprocess.check_output(
        ["convert", str(path), "-depth", "8", "RGB:-"])
    if len(rgb) != 480*320*3:
        raise Blocked("Malformed actual emulator frame")
    return rgb


def pixel_distance(a, b):
    if len(a) != len(b) or len(a) == 0:
        raise Blocked("Cannot compare differently sized render frames")
    return sum(abs(x-y) for x,y in zip(a,b))/(255.0*len(a))


def visual_title_score(rgb):
    """Title-logo-specific signature; reject green outdoor intro scenes.

    Based on independently viewed mGBA run38862320655 title frame:
    yellow+purple upper POKEMON logo over a green lower background.
    The previous whole-frame yellow/green signature falsely matched
    the earlier forest/character intro frame on run38868936415.
    """
    if len(rgb) != 480*320*3:
        raise Blocked("Title scoring requires exact emulator framebuffer")
    upper = rgb[:480*160*3]
    lower = rgb[480*160*3:]
    logo_yellow = sum(upper[i] > 170 and upper[i+1] > 120
                      and upper[i+2] < 120
                      for i in range(0, len(upper), 3))/(480*160)
    logo_purple = sum(upper[i+2] > upper[i]*0.5
                      and upper[i+2] > upper[i+1]*1.2
                      and upper[i] > 40 and upper[i+2] > 80
                      for i in range(0, len(upper), 3))/(480*160)
    lower_green = sum(lower[i+1] > 100
                      and lower[i+1] > lower[i]*1.2
                      and lower[i+1] > lower[i+2]*0.8
                      for i in range(0, len(lower), 3))/(480*160)
    return dict(yellow=logo_yellow, purple=logo_purple,
                green=lower_green,
                present=(logo_yellow > 0.06 and logo_purple > 0.10
                         and lower_green > 0.25))


def visual_saved_main_menu(rgb):
    """Observe actual white menu panels over Emerald's purple backing."""
    if len(rgb) != 480*320*3:
        raise Blocked("Menu scoring requires exact emulator framebuffer")
    upper = rgb[:480*160*3]
    purple = sum(upper[i+2] > upper[i]*0.5
                 and upper[i+2] > upper[i+1]*1.2
                 and upper[i] > 40 and upper[i+2] > 80
                 for i in range(0, len(upper), 3))/(480*160)
    pale = sum(min(upper[i:i+3]) > 180
               for i in range(0, len(upper), 3))/(480*160)
    return dict(purple=purple, pale=pale,
                present=purple > 0.12 and pale > 0.25)


def q2_visual_relaunch(args):
    """Real flash-fed emulator reboot with screenshot-gated user controls.

    This is NOT a memory-only flash flag acceptance; capture actual in-game
    Continue and the completed artist dialogue for independent inspection.
    """
    out = Path(args.outdir)
    index = 0

    def shot(label):
        nonlocal index
        index += 1
        name = f"visual-{index:03d}-{label}"
        path = out / (name + ".png")
        grab(args.window, path)
        raw = visual_frame_data(path)
        stats = visual_title_score(raw)
        print("QA_VISUAL_REBOOT_FRAME", name, json.dumps(stats), str(path),
              flush=True)
        return path, raw, stats

    def press(key):
        subprocess.run(["xdotool", "windowactivate", str(args.window)],
                       check=False)
        subprocess.run(["xdotool", "keydown", key], check=True)
        time.sleep(0.13)
        subprocess.run(["xdotool", "keyup", key], check=True)
        time.sleep(1.3)

    original_field = out / "save-007-return-field-5.png"
    if not original_field.exists():
        raise Blocked("Source-backed pre-powercycle field screenshot missing")
    baseline = visual_frame_data(original_field)
    title_frame = None
    # Observed mGBA artifact 12030325106: after the first 80 samples
    # the authentic Kyogre introductory animation was STILL playing.
    # Do not mistake animated intro for invalid flash/title.
    for i in range(220):
        frame, raw, score = shot(f"title-wait-{i+1}")
        if score["present"]:
            title_frame = raw
            print("QA_VISUAL_REBOOT_TITLE_RENDERED", str(frame), flush=True)
            break
        time.sleep(0.45)
    if title_frame is None:
        raise Blocked("Reboot did not render the previous verified Emerald logo")
    press("Return")  # physical START
    menu_frame, menu_raw, title_after = shot("real-menu-after-start")
    scene_delta = pixel_distance(title_frame, menu_raw)
    print("QA_VISUAL_MAIN_MENU_CHANGE", f"{scene_delta:.5f}", flush=True)
    if scene_delta < 0.08:
        raise Blocked("START did not visibly leave title screen")
    menu_score = visual_saved_main_menu(menu_raw)
    print("QA_VISUAL_SAVED_MENU_GATE", menu_score, flush=True)
    if not menu_score["present"]:
        raise Blocked("START did not visibly reach verified saved menu: "
                      f"{menu_score}")
    # Candidate CONTINUE is first option only on a valid-source real save;
    # manual screenshot inspection remains mandatory for Q2 acceptance.
    press("x")
    closest = (1.0, "")
    field_ready = False
    for i in range(60):
        frame, raw, _ = shot(f"field-after-continue-{i+1}")
        delta = pixel_distance(baseline, raw)
        print("QA_VISUAL_FIELD_MATCH", str(frame), f"{delta:.5f}", flush=True)
        if delta < closest[0]:
            closest = (delta,str(frame))
        if delta < 0.18:
            print("QA_VISUAL_RESTORED_FIELD_MATCH", str(frame),
                  f"delta={delta:.5f}", flush=True)
            field_ready = True
            break
        time.sleep(0.5)
    if not field_ready:
        raise Blocked(f"Continue never matched the source-saved Windrow "
                      f"field (closest={closest})")
    # The source image saved the avatar adjacent west of the artist, facing
    # east, so A here must show completed artist DONE, not a fresh offer.
    press("x")
    done_frame, _, _ = shot("saved-artist-done-dialogue")
    if white_panel_ratio(done_frame) < 0.50:
        raise Blocked("Saved artist did not produce completed-quest textbox")
    # A YESNO choice menu after actual player A would mean uncompleted Q2.
    crop = subprocess.check_output([
        "convert", str(done_frame), "-crop", "106x90+323+130",
        "+repage", "-depth", "8", "RGB:-"])
    choices = sum(min(crop[i:i+3]) >= 190
                  for i in range(0,len(crop),3))/(106*90)
    print("QA_VISUAL_ARTIST_MENU_RATIO", f"{choices:.4f}", flush=True)
    if choices > 0.52:
        raise Blocked("Artist produced YESNO instead of expected Q2 DONE")
    print("QA_Q2_FLASH_VISUAL_ARTIST_DONE: completed artist text seen "
          "after genuine emulator process restart", flush=True)
    # Check Bag visibly rather than pretending title-stage GDB still works.
    # Actual source Start actions before save were [BAG(2), PLAYER(4),
    # SAVE(5), OPTION(6), EXIT(7)], making BAG the default first choice.
    press("x")
    closed, _, _ = shot("artist-done-closed")
    if white_panel_ratio(closed) > 0.30:
        raise Blocked("Cannot open restored Bag while artist dialogue active")
    press("Return")
    start_frame, _, _ = shot("restored-start-menu")
    press("x")
    bag_frame, bag_raw, _ = shot("restored-bag-open")
    if pixel_distance(visual_frame_data(start_frame), bag_raw) < 0.05:
        raise Blocked("No observed field Start-menu-to-Bag transition")
    # Real mGBA run38870779185 visibly proved that three D-pad RIGHT
    # presses reach BERRIES from ITEMS (four would overshoot to KEY ITEMS).
    # xdotool 's' did not cycle these tabs; require a fresh screenshot and
    # changed header after EVERY ordinary D-pad RIGHT input.
    before_header = subprocess.check_output([
        "convert", str(bag_frame), "-crop", "170x30+18+0",
        "+repage", "-depth", "8", "RGB:-"])
    for i in range(bag_pocket_right_steps("ITEMS", "BERRIES")):
        press("Right")
        frame, raw, _ = shot(f"restored-bag-pocket-after-RIGHT-{i+1}")
        new_header = subprocess.check_output([
            "convert", str(frame), "-crop", "170x30+18+0",
            "+repage", "-depth", "8", "RGB:-"])
        delta = pixel_distance(before_header, new_header)
        print("QA_VISUAL_BAG_HEADER_CHANGED", i+1,
              f"delta={delta:.5f}", flush=True)
        if delta < 0.012:
            raise Blocked("Actual D-pad RIGHT did not visibly cycle Bag pocket")
        before_header = new_header
    print("QA_Q2_FLASH_VISUAL_PARTIAL: genuine saved process restart, "
          "title/Continue-like menu, saved Windrow field, completed artist "
          "DONE dialogue and Bag/Berry pocket screenshots captured. "
          "Require manual verification of visible ORAN BERRY x3; source "
          "flags cannot be asserted from broken reboot GDB.", flush=True)



def q3_gym_entry(args):
    """QA-only staged genuine Gym1 challenge setup: no battle victory claim.

    Verify existing source sluices through ordinary YES inputs. Attempt
    leader dialogue via original event NPC, not developer NPC party/spoof.
    Stop upon observable battle transition, do not declare whiteout.
    """
    folder = Path(args.outdir)
    seq = 800

    def see(label, require_field=False):
        nonlocal seq
        seq += 1
        key = f"q3-{seq:03d}-{label}"
        frame = folder / (key + ".png")
        grab(args.window, frame)
        state = snapshot(args, key)
        print("QA_Q3_GYM", key, json.dumps(state, sort_keys=True),
              str(frame), flush=True)
        if (state["mapGroup"], state["mapNum"]) != (75, 10):
            raise Blocked(f"Not original AlderfieldGym source map: {state}")
        if state["badge01"]:
            raise Blocked("Do not run defeat fixture with first badge already won")
        if (not state["devGiftReceived"] or state["playerPartyCount"] != 1
                or not state["sketchRewarded"] or not state["notesStarted"]):
            raise Blocked(f"Original story/party not ready for real Gym1: {state}")
        if require_field and white_panel_ratio(frame) > 0.30:
            raise Blocked(f"Unclosed dialogue on Gym1 walk: {state}")
        return state, frame

    def press(key, duration=0.10, delay=0.55):
        subprocess.run(["xdotool", "windowactivate", str(args.window)],
                       check=False)
        subprocess.run(["xdotool", "keydown", key], check=True)
        time.sleep(duration)
        subprocess.run(["xdotool", "keyup", key], check=True)
        time.sleep(delay)

    def walk(axis, target):
        pos, _ = see(f"before-{axis}-{target}", require_field=True)
        stalled = 0
        for i in range(35):
            if pos[axis] == target:
                return pos
            direction = 1 if target > pos[axis] else -1
            key = ("Right" if direction > 0 else "Left") if axis=="x" else (
                "Down" if direction > 0 else "Up")
            press(key)
            after, _ = see(f"{axis}-{target}-{i+1}", require_field=True)
            other = "y" if axis=="x" else "x"
            delta = after[axis]-pos[axis]
            if delta not in (0, direction) or pos[other] != after[other]:
                raise Blocked(f"Uncontrolled gym movement {pos}->{after}")
            stalled = stalled + 1 if delta==0 else 0
            if stalled>=4:
                raise Blocked(f"Blocked by unchanged gym collision {after}")
            pos=after
        raise Blocked("Unbounded gym walk")

    def activate(what,x,y,flag):
        walk("x", x)
        walk("y", y)
        pos,_=see(what+"-before-yes",require_field=True)
        press("Up",duration=0.045)
        faced,_=see(what+"-face-up",require_field=True)
        if (faced["x"],faced["y"])!=(x,y):
            raise Blocked(f"Gym sluice facing moved avatar: {faced}")
        press("x",delay=1.15)
        offered,frame=see(what+"-yesno-visible")
        if white_panel_ratio(frame)<0.50:
            raise Blocked(f"Original {what} script not visible")
        press("x",delay=1.1)
        switched,_=see(what+"-selected-yes")
        if not switched[flag]:
            raise Blocked(f"YES did not set actual {flag} flag: {switched}")
        for i in range(5):
            curr,frame=see(what+f"-dismiss-{i+1}")
            if white_panel_ratio(frame)<=0.30:
                break
            press("x",delay=0.9)
        else:
            raise Blocked(f"{what} script never returned field control")
        print(f"QA_Q3_ORIGINAL_{what.upper()}_ACTIVATED", flush=True)

    start,_=see("actual-warp-entry")
    # The *actual* unchanged AlderfieldGym warp0 is (4,15), as observed
    # with read-only GDB in run38871202223 and declared in map.json.
    # Step onto known original floor at (4,14) before moving west;
    # never confuse the interior approach tile with the warp itself.
    if (start["x"],start["y"])!=(4,15) or start["warpId"] != 0:
        raise Blocked(f"Unexpected original Gym1 warp0 spawn: {start}")
    if start["gymWestSluice"] or start["gymEastSluice"]:
        raise Blocked("Sluice state is not fresh; cannot prove YES branches")
    walk("y",14); walk("x",2); walk("y",13)
    activate("west",2,13,"gymWestSluice")
    walk("x",6)
    activate("east",6,13,"gymEastSluice")
    enabled,_=see("both-switches-after",require_field=True)
    if not(enabled["gymWestSluice"] and enabled["gymEastSluice"]):
        raise Blocked("Original pair of sluices did not both activate")
    walk("x",4);walk("y",5)
    pos,_=see("elio-adjacent",require_field=True)
    if (pos["x"],pos["y"])!=(4,5):
        raise Blocked("Could not reach original Elio with source gate opened")
    press("Up",duration=0.045)
    turned,_=see("elio-face-north",require_field=True)
    if (turned["x"],turned["y"])!=(4,5):
        raise Blocked("Facing original leader moved player")
    press("x",delay=1.5)
    leader,frame=see("elio-original-intro")
    if white_panel_ratio(frame)<0.5:
        raise Blocked("No original Elio trainer pre-battle dialogue visible")
    print("QA_Q3_GYM_ORIGINAL_LEADER_INTRO: genuine sluices and leader "
          "interaction observed. BATTLE/WHITEOUT/HEAL NOT YET PROVEN.",
          flush=True)


def q3_clinic_entry(args):
    """Actual original clinic map must set heal point via its own script."""
    out = Path(args.outdir)
    frame = out / "q3-clinic-rendered-entry.png"
    if not frame.exists():
        raise Blocked("Actual AlderfieldClinic entry screenshot missing")
    state = snapshot(args, "q3-clinic-source-heal")
    if (state["mapGroup"], state["mapNum"]) != (75, 11):
        raise Blocked(f"Expected original AlderfieldClinic(75,11): {state}")
    # HEAL_LOCATION_ALDERFIELD stores the OUTDOOR town position; its
    # distinct respawn_map is the clinic. Source: src/data/heal_locations.json.
    # A matching saved location may predate this entry and does not, alone,
    # prove the MAP_SCRIPT_ON_TRANSITION actually executed.
    heal = (state["lastHealMapGroup"], state["lastHealMapNum"],
            state["lastHealWarpId"], state["lastHealX"], state["lastHealY"])
    if heal != (75, 9, -1, 17, 13):
        raise Blocked(f"Source-defined Alderfield heal warp missing "
                      f"(expected town 75/9 at 17,13, not clinic 75/11): {state}")
    if white_panel_ratio(frame) > 0.3:
        raise Blocked("Clinic entry screenshot not clear field")
    print("QA_Q3_SOURCE_HEAL_WARP_PRESENT: entered original clinic and "
          "saved warp matches HEAL_LOCATION_ALDERFIELD's outdoor map; "
          "source transition execution and subsequent real whiteout "
          "into clinic/nurse healing still require independent proof.",
          json.dumps(state, sort_keys=True), flush=True)


def q3_battle_start(args):
    """Start real original Elio battle with ordinary A; do not force defeat.

    Battle whiteout, heal, and follower acceptance require later snapshots.
    """
    out = Path(args.outdir)
    matches = sorted(out.glob("q3-*-elio-original-intro.png"))
    # The per-input checkpoint number varies legitimately with turn-only
    # D-pad presses. Never hardcode q3-850 or accept an ambiguous fixture.
    if len(matches) != 1:
        raise Blocked(f"Expected exactly one real Elio intro frame, got {len(matches)}")
    prior = matches[0]
    source_intro = visual_frame_data(prior)
    if white_panel_ratio(prior) < 0.5:
        raise Blocked("Source leader dialogue not visibly open before battle")

    def snap(label):
        key = f"q3-battle-{label}"
        shot = out / f"{key}.png"
        grab(args.window, shot)
        state = snapshot(args, key)
        if (state["mapGroup"], state["mapNum"]) != (75, 10):
            raise Blocked(f"Battle fixture left original Gym1 map: {state}")
        if not (state["gymWestSluice"] and state["gymEastSluice"]):
            raise Blocked(f"Real sluice flags vanished before battle: {state}")
        if state["badge01"] or not state["devGiftReceived"] or state["playerPartyCount"] != 1:
            raise Blocked(f"Original badge/party prerequisite mismatch: {state}")
        print("QA_Q3_BATTLE", key, json.dumps(state, sort_keys=True),
              str(shot), flush=True)
        return state, shot

    before,_ = snap("leader-dialogue-held")
    if before["inBattle"]:
        raise Blocked("Already in battle before exiting real Elio intro")
    subprocess.run(["xdotool", "windowactivate", str(args.window)],
                   check=False)
    subprocess.run(["xdotool", "keydown", "x"], check=True)
    time.sleep(0.12)
    subprocess.run(["xdotool", "keyup", "x"], check=True)
    for i in range(60):
        time.sleep(0.55)
        state, frame = snap(f"after-ordinary-A-{i+1}")
        if state["inBattle"]:
            time.sleep(2.0)
            after, visible = snap("first-reachable-battle-screen")
            delta = pixel_distance(source_intro, visual_frame_data(visible))
            if not after["inBattle"] or delta < 0.08:
                raise Blocked(f"Battle bit set but no distinct rendered battle screen: {delta:.5f}")
            print("QA_Q3_ORIGINAL_BATTLE_STARTED: actual Elio trainer encounter; "
                  "BATTLE DEFEAT/WHITEOUT/HEAL NOT YET ACCEPTED.", flush=True)
            return
    raise Blocked("Original leader dialogue never transitioned to actual battle")


def q3_battle_play(args):
    """Real battle UI A presses; never alter player HP, trainer or save state.

    A battle result is reported only after a witnessed inBattle transition and
    its actual original-map/first-badge state. No assumed heal/whiteout PASS.
    """
    out = Path(args.outdir)
    prior = out / "q3-battle-first-reachable-battle-screen.png"
    if not prior.is_file():
        raise Blocked("No rendered original Elio battle startup in this run")

    def record(label):
        tag = f"q3-play-{label}"
        frame = out / (tag + ".png")
        grab(args.window, frame)
        state = snapshot(args, tag)
        if not state["devGiftReceived"] or state["playerPartyCount"] != 1:
            raise Blocked(f"Unexpected real gifted party during trainer battle: {state}")
        if not state["gymWestSluice"] or not state["gymEastSluice"]:
            raise Blocked(f"Source sluice states vanished during battle: {state}")
        if not state.get("inBattle", False) and state["badge01"]:
            print("QA_Q3_REAL_BADGE_EARNED_CANDIDATE", json.dumps(state), flush=True)
        print("QA_Q3_BATTLE_PROGRESS", tag,
              json.dumps(state, sort_keys=True), str(frame), flush=True)
        return state, frame

    start, _ = record("initial")
    if not start["inBattle"] or start["badge01"] or (
            start["mapGroup"], start["mapNum"]) != (75, 10):
        raise Blocked(f"Original Elio battle start not verified: {start}")
    # Actual Wobbuffet is level 5 from the game's Script4; the opponent is
    # the unchanged Elio. Repeated ordinary A selects player Fight/move and
    # advances dialogue. Neither HP nor results are injected or controlled.
    for i in range(160):
        subprocess.run(["xdotool", "windowactivate", str(args.window)],
                       check=False)
        subprocess.run(["xdotool", "keydown", "x"], check=True)
        time.sleep(0.12)
        subprocess.run(["xdotool", "keyup", "x"], check=True)
        time.sleep(0.58)
        # Read-only battle probe and screenshot every second interaction;
        # do not keep sending A once the battle has actually concluded.
        if i % 2 != 1:
            continue
        state, frame = record(f"real-A-{i+1:03d}")
        if state["inBattle"]:
            continue
        time.sleep(1.3)
        after, image = record("after-battle-transition")
        if after["inBattle"]:
            continue
        if after["badge01"]:
            print("QA_Q3_ORIGINAL_BADGE_VICTORY_CANDIDATE: actual source "
                  "Badge01, but verify fanfare/leader reward screenshots.",
                  flush=True)
        else:
            print("QA_Q3_ORIGINAL_BATTLE_EXIT_NO_BADGE: battle ended without "
                  "Badge01; require visible defeat/whiteout and clinic "
                  "before claiming healed whiteout.", flush=True)
        if (after["mapGroup"], after["mapNum"]) == (75, 11):
            print("QA_Q3_ORIGINAL_CLINIC_MAP_CANDIDATE: player on original "
                  "AlderfieldClinic after trainer battle, examine actual "
                  "frame and verify nurse healing before full PASS.", flush=True)
        return
    raise Blocked("No observed real Elio battle conclusion in 160 actual A "
                  "presses; review last rendered frame, not a game failure")


# SAVE sector definitions are taken verbatim from engine/include/save.h
# and engine/src/save.c of the pinned QUEST source (not a guessed .sav
# layout). This is an offline, read-only flash observer after emulator exit.
FLASH_SECTOR_BYTES = 4096
FLASH_SECTOR_DATA_BYTES = 3968
FLASH_SIGNATURE = 0x08012025
FLASH_VALIDATED_CHECKSUM_LENGTHS = {
    **{i: FLASH_SECTOR_DATA_BYTES for i in
       (*range(1, 4), *range(5, 13))},
    0: 0xF2C,  # SaveBlock2 sizeof in source global.h
}


def flash_sector_checksum(data, size):
    """Exact u32-folded checksum from pinned engine/src/save.c."""
    if size % 4 or len(data) < size:
        raise Blocked("Invalid saved flash sector checksum length")
    total = sum(struct.unpack_from("<I", data, i)[0]
                for i in range(0, size, 4)) & 0xFFFFFFFF
    return ((total >> 16) + total) & 0xFFFF


def decode_flash_q2(image):
    """Decode independently CRC-verified *on-disk* Q2 flash, no emulator RAM.

    Each 14-sector slot is rotated on flash. Match source sector IDs, not
    physical offsets. The SaveBlock3 extension/footer must not be included in
    reconstructed SaveBlock1 or SaveBlock2. Refuse incomplete/mixed counters.
    """
    if len(image) < 32 * FLASH_SECTOR_BYTES:
        raise Blocked("Physical 128 KiB flash image incomplete")
    candidates = []
    for slot in range(2):
        sectors = {}
        for i in range(14):
            start = (slot * 14 + i) * FLASH_SECTOR_BYTES
            raw = image[start:start + FLASH_SECTOR_BYTES]
            sid, checksum, signature, counter = struct.unpack_from(
                "<HHII", raw, FLASH_SECTOR_BYTES - 12)
            if signature != FLASH_SIGNATURE or sid > 13 or sid in sectors:
                continue
            size = FLASH_VALIDATED_CHECKSUM_LENGTHS.get(sid)
            if size is not None and flash_sector_checksum(raw, size) != checksum:
                continue
            sectors[sid] = (raw[:FLASH_SECTOR_DATA_BYTES], counter)
        if len(sectors) != 14 or len({v[1] for v in sectors.values()}) != 1:
            continue
        block1 = b"".join(sectors[id][0] for id in range(1, 5))
        block2 = sectors[0][0]
        x, y, map_group, map_num, warp = struct.unpack_from(
            "<hhbbb", block1)
        flags = block1[0x1270 + 0x2A // 8]
        raw_flags = tuple(bool(flags & (1 << (n & 7)))
                          for n in range(0x2A, 0x30))
        key = struct.unpack_from("<I", block2, 0xAC)[0] & 0xFFFF
        base = 0x560 + (30 + 30 + 16 + 64) * 4
        pocket = block1[base:base + 46 * 4]
        oran = sum(saved ^ key for item_id, saved in
                   struct.iter_unpack("<HH", pocket) if item_id == 520)
        candidates.append(dict(slot=slot, saveCounter=sectors[0][1],
                               x=x, y=y, mapGroup=map_group,
                               mapNum=map_num, warpId=warp,
                               notesStarted=raw_flags[0],
                               notesRecorded=raw_flags[1],
                               notesRewarded=raw_flags[2],
                               sketchStarted=raw_flags[3],
                               sketchFound=raw_flags[4],
                               sketchRewarded=raw_flags[5],
                               oranBerryQuantity=oran))
    if not candidates:
        raise Blocked("No complete signed and checksum-valid 14-sector flash slot")
    newest = candidates[0]
    for candidate in candidates[1:]:
        delta = (candidate["saveCounter"] -
                 newest["saveCounter"]) & 0xFFFFFFFF
        if 0 < delta < 0x80000000:
            newest = candidate
        elif delta == 0:
            raise Blocked("Two complete flash slots have ambiguous counters")
    return newest


def q2_flash_sector(args):
    """Independently assert Q2 stored on *disk* after real normal in-game SAVE."""
    data = args.flash.read_bytes()
    state = decode_flash_q2(data)
    expected = dict(x=19, y=14, mapGroup=75, mapNum=6, warpId=-1,
                    notesStarted=True, notesRecorded=False,
                    notesRewarded=False, sketchStarted=True,
                    sketchFound=True, sketchRewarded=True,
                    oranBerryQuantity=3)
    wrong = {key: (state.get(key), value) for key, value in expected.items()
             if state.get(key) != value}
    if wrong:
        raise Blocked(f"On-disk Q2 flash state does not match actual source "
                      f"pre-save field: {wrong}")
    print("QA_Q2_PHYSICAL_FLASH_FLAGS_ORAN3_PASS:",
          json.dumps(state, sort_keys=True),
          "signed/CRC-valid full slot loaded from real .sav; "
          "not a claim that post-restart GDB worked", flush=True)


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
    for command in ("q2-save", "q2-continue"):
        sp = sub.add_parser(command)
        sp.add_argument("--fifo", required=True)
        sp.add_argument("--outdir", required=True)
        sp.add_argument("--window", required=True)
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
    visual = sub.add_parser("q2-visual-relaunch")
    visual.add_argument("--outdir", required=True)
    visual.add_argument("--window", required=True)
    gate = sub.add_parser("q1-badge-gate")
    gate.add_argument("--fifo", required=True)
    gate.add_argument("--outdir", required=True)
    gate.add_argument("--window", required=True)
    gym = sub.add_parser("q3-gym-entry")
    gym.add_argument("--fifo", required=True)
    gym.add_argument("--outdir", required=True)
    gym.add_argument("--window", required=True)
    clinic = sub.add_parser("q3-clinic-entry")
    clinic.add_argument("--fifo", required=True)
    clinic.add_argument("--outdir", required=True)
    clinic.add_argument("--window", required=True)
    battle = sub.add_parser("q3-battle-start")
    battle.add_argument("--fifo", required=True)
    battle.add_argument("--outdir", required=True)
    battle.add_argument("--window", required=True)
    play = sub.add_parser("q3-battle-play")
    play.add_argument("--fifo", required=True)
    play.add_argument("--outdir", required=True)
    play.add_argument("--window", required=True)
    flash = sub.add_parser("q2-flash-sector")
    flash.add_argument("--flash", type=Path, required=True)
    gift = sub.add_parser("q4-lab-gift")
    gift.add_argument("--fifo", required=True)
    gift.add_argument("--outdir", required=True)
    gift.add_argument("--window", required=True)
    reload = sub.add_parser("q2-relaunch-continue")
    reload.add_argument("--fifo", required=True)
    reload.add_argument("--outdir", required=True)
    reload.add_argument("--window", required=True)
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
        if args.mode == "q2-save":
            return q2_save(args)
        if args.mode == "q2-continue":
            return q2_reset_continue(args)
        if args.mode == "q2-meadow":
            return q2_meadow(args)
        if args.mode == "q2-artist-offer":
            return q2_artist_offer(args)
        if args.mode == "navigate-artist":
            return navigate_artist(args)
        if args.mode == "q2-visual-relaunch":
            return q2_visual_relaunch(args)
        if args.mode == "q1-badge-gate":
            return q1_badge_gate(args)
        if args.mode == "q3-gym-entry":
            return q3_gym_entry(args)
        if args.mode == "q3-clinic-entry":
            return q3_clinic_entry(args)
        if args.mode == "q3-battle-start":
            return q3_battle_start(args)
        if args.mode == "q3-battle-play":
            return q3_battle_play(args)
        if args.mode == "q2-flash-sector":
            return q2_flash_sector(args)
        if args.mode == "q4-lab-gift":
            return q4_lab_gift(args)
        if args.mode == "q2-relaunch-continue":
            return q2_continue_relaunch(args)
        if args.mode == "q1-offer":
            return q1_offer(args)
        return navigate(args)
    except (Blocked, OSError, ValueError, subprocess.CalledProcessError,
            socket.timeout) as exc:
        print("QA_ACCESS_BLOCKED:", exc, file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main() or 0)
