"""Local graphical mGBA under Xvfb, with read-only GDB observation.

Inputs are real key presses sent to the mGBA window with xdotool. Game state
is only ever READ through mGBA's GDB stub (memory-read packets); the driver
never writes emulator memory, registers or saves.
"""
import json
import os
import pathlib
import re
import shutil
import socket
import struct
import subprocess
import time

KEYS = {"A": "x", "B": "z", "START": "Return", "SELECT": "BackSpace",
        "L": "a", "R": "s", "UP": "Up", "DOWN": "Down", "LEFT": "Left", "RIGHT": "Right"}


class Blocked(RuntimeError):
    pass


# --- symbols, struct offsets and constants from the build -------------------

OFFSET_EXPRS = {
    "sb1.pos": "offsetof(struct SaveBlock1, pos)",
    "sb1.location": "offsetof(struct SaveBlock1, location)",
    "sb1.flags": "offsetof(struct SaveBlock1, flags)",
    "sb1.vars": "offsetof(struct SaveBlock1, vars)",
    "sb1.money": "offsetof(struct SaveBlock1, money)",
    "sb1.bag": "offsetof(struct SaveBlock1, bag)",
    "sb1.lastHealLocation": "offsetof(struct SaveBlock1, lastHealLocation)",
    "sb2.encryptionKey": "offsetof(struct SaveBlock2, encryptionKey)",
    "main.callback2": "offsetof(struct Main, callback2)",
    "mon.size": "sizeof(struct Pokemon)",
    "box.secure": "offsetof(struct BoxPokemon, secure)",
    "task.size": "sizeof(struct Task)",
    "mon.status": "offsetof(struct Pokemon, status)",
    "moveinfo.pp": "offsetof(struct MoveInfo, pp)",
    "oe.size": "sizeof(struct ObjectEvent)",
    "oe.localId": "offsetof(struct ObjectEvent, localId)",
    "oe.graphicsId": "offsetof(struct ObjectEvent, graphicsId)",
    "task.isActive": "offsetof(struct Task, isActive)",
    "task.data": "offsetof(struct Task, data)",
    "box.substruct": "sizeof(union PokemonSubstruct)",
    "mon.level": "offsetof(struct Pokemon, level)",
    "mon.hp": "offsetof(struct Pokemon, hp)",
    "mon.maxHP": "offsetof(struct Pokemon, maxHP)",
    "bm.size": "sizeof(struct BattlePokemon)",
    "bm.species": "offsetof(struct BattlePokemon, species)",
    "bm.moves": "offsetof(struct BattlePokemon, moves)",
    "bm.pp": "offsetof(struct BattlePokemon, pp)",
    "bm.hp": "offsetof(struct BattlePokemon, hp)",
    "bm.maxHP": "offsetof(struct BattlePokemon, maxHP)",
    "bm.level": "offsetof(struct BattlePokemon, level)",
    "bm.types": "offsetof(struct BattlePokemon, types)",
    "bm.statStages": "offsetof(struct BattlePokemon, statStages)",
    "pm.slotId": "offsetof(struct PartyMenu, slotId)",
    "pm.slotId2": "offsetof(struct PartyMenu, slotId2)",
    "typechart.elem": "sizeof(gTypeEffectivenessTable[0][0])",
    "move.size": "sizeof(struct MoveInfo)",
    "main.vblankCounter1": "offsetof(struct Main, vblankCounter1)",
    "slot.size": "sizeof(struct ItemSlot)",
    "slot.quantity": "offsetof(struct ItemSlot, quantity)",
    "bag.items": "offsetof(struct Bag, items)",
    "bag.pokeBalls": "offsetof(struct Bag, pokeBalls)",
    "bag.berries": "offsetof(struct Bag, berries)",
    "bagpos.pocket": "offsetof(struct BagPosition, pocket)",
    "bagpos.cursor": "offsetof(struct BagPosition, cursorPosition)",
    "bagpos.scroll": "offsetof(struct BagPosition, scrollPosition)",
}


CONSTANTS = [
    "FLAG_BADGE01_GET", "FLAG_BADGE02_GET", "FLAG_AVERON_STARTER", "FLAG_AVERON_WEST_SLUICE",
    "FLAG_AVERON_EAST_SLUICE", "FLAG_AVERON_GYM1_TM", "FLAG_SYS_POKEMON_GET",
    "VAR_AVERON_INTRO", "VAR_AVERON_FIRST_HOUSE", "VAR_AVERON_GREENHOUSE", "VAR_AVERON_WORKSHOP",
    "VAR_AVERON_HARBOR", "VARS_START", "B_TRAINER_PLAYER", "PARTY_SIZE",
    "SPECIES_PIPLUP", "SPECIES_SNIVY", "SPECIES_FENNEKIN", "ITEM_POKE_BALL", "ITEM_GREAT_BALL",
    "ITEM_POTION", "ITEM_ORAN_BERRY", "B_ACTION_USE_MOVE", "NUMBER_OF_MON_TYPES",
    "MOVE_TACKLE", "MOVE_WATER_GUN", "MOVE_GROWL", "SAVE_STATUS_OK",
    "BATTLE_TYPE_TRAINER", "BATTLE_TYPE_DOUBLE", "FLAG_AVERON_EXP_SHARE",
    "FLAG_AVERON_NOTES_STARTED", "FLAG_AVERON_NOTES_RECORDED", "FLAG_AVERON_NOTES_REWARDED",
    "FLAG_AVERON_SKETCH_STARTED", "FLAG_AVERON_SKETCH_FOUND", "FLAG_AVERON_SKETCH_REWARDED",
    "FLAG_AVERON_DEV_GIFT_RECEIVED", "SPECIES_WOBBUFFET", "OBJ_EVENT_ID_FOLLOWER",
    "BAG_ITEMS_COUNT", "BAG_POKEBALLS_COUNT", "BAG_BERRIES_COUNT", "ITEM_EXP_SHARE",
    "TRAINER_FLAGS_START", "TRAINER_AVERON_FARMER", "TRAINER_AVERON_PICNIC", "TRAINER_AVERON_ORCHARD",
    "TRAINER_AVERON_GYM1", "TRAINER_AVERON_ELIO", "TRAINER_AVERON_MEADOW",
    "STAT_ATK", "DEFAULT_STAT_STAGE", "MOVE_BABY_DOLL_EYES", "MOVE_CHARM", "MOVE_RETALIATE",
    "TYPE_NORMAL", "TYPE_WATER", "TYPE_FIRE", "TYPE_GRASS", "TYPE_GHOST",
    "POCKET_POKE_BALLS", "POCKET_BERRIES",
]


def probe_offsets(engine, workdir):
    """Struct offsets as the game's own compiler lays them out.

    The normal build has no DWARF for game code, so compile a probe with the
    engine's flags that turns each offset into an absolute symbol.
    """
    engine = pathlib.Path(engine)
    workdir = pathlib.Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    names = list(OFFSET_EXPRS)
    names += [f"const.{c}" for c in CONSTANTS]
    exprs = dict(OFFSET_EXPRS, **{f"const.{c}": c for c in CONSTANTS})
    lines = ['#include "global.h"', '#include "main.h"', '#include "pokemon.h"', '#include "battle.h"',
             '#include "constants/flags.h"', '#include "constants/vars.h"', '#include "constants/items.h"',
             '#include "constants/species.h"', '#include "constants/battle.h"',
             '#include "move.h"', '#include "save.h"', '#include "constants/moves.h"',
             '#include "constants/opponents.h"', '#include "party_menu.h"', '#include "fpmath.h"',
             '#include "task.h"', '#include "constants/event_objects.h"', '#include "item_menu.h"',
             'extern const uq4_12_t gTypeEffectivenessTable[NUMBER_OF_MON_TYPES][NUMBER_OF_MON_TYPES];',
             '#define P(n, v) asm volatile(".globl AVPROBE_" #n "\\n.equ AVPROBE_" #n ", %c0" :: "i"(v))',
             "void AvProbe(void)", "{"]
    lines += [f"    P(p{i}, {exprs[n]});" for i, n in enumerate(names)]
    lines.append("}")
    src = workdir / "probe.c"
    obj = workdir / "probe.o"
    src.write_text("\n".join(lines) + "\n")
    subprocess.run(["arm-none-eabi-gcc", "-mthumb", "-mthumb-interwork", "-O2", "-mabi=apcs-gnu",
                    "-mtune=arm7tdmi", "-march=armv4t", "-std=gnu17", "-iquote", "include",
                    "-I", "tools/agbcc/include", "-DMODERN=1", "-DTESTING=0", "-DEMERALD",
                    "-c", str(src), "-o", str(obj)], cwd=engine, check=True)
    found = {}
    for line in subprocess.check_output(["arm-none-eabi-nm", str(obj)], text=True).splitlines():
        m = re.match(r"([0-9a-f]+) A AVPROBE_p(\d+)$", line)
        if m:
            found[names[int(m.group(2))]] = int(m.group(1), 16)
    if len(found) != len(set(names)):
        raise Blocked(f"offset probe found {len(found)} of {len(names)}")
    return found


def load_build_info(elf, engine, cache_dir):
    """Symbols (nm), struct offsets (probe) and constants, cached by ELF hash."""
    elf = pathlib.Path(elf)
    digest = subprocess.check_output(["sha256sum", str(elf)], text=True).split()[0]
    import hashlib
    probe_key = hashlib.sha256(json.dumps([OFFSET_EXPRS, CONSTANTS, "all_symbols", "sections"]).encode()).hexdigest()[:8]
    cache = pathlib.Path(cache_dir) / f"buildinfo-{digest[:16]}-{probe_key}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    symbols = {}
    all_symbols = []  # static functions can share a name (two HandleInputChooseAction)
    for line in subprocess.check_output(["arm-none-eabi-nm", "--defined-only", str(elf)], text=True).splitlines():
        parts = line.split()
        if len(parts) == 3:
            addr = int(parts[0], 16)
            symbols.setdefault(parts[2], addr)
            all_symbols.append((addr, parts[2]))
    probed = probe_offsets(engine, pathlib.Path(cache_dir) / "probe")
    sections = {}
    for line in subprocess.check_output(["arm-none-eabi-objdump", "-h", str(elf)], text=True).splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0].isdigit():
            sections[parts[1]] = dict(size=int(parts[2], 16), vma=int(parts[3], 16))
    info = {"elf_sha256": digest, "symbols": symbols, "all_symbols": all_symbols, "sections": sections,
            "offsets": {k: v for k, v in probed.items() if not k.startswith("const.")},
            "constants": {k[6:]: v for k, v in probed.items() if k.startswith("const.")}}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(info))
    return info


# --- GDB remote protocol, reads only -------------------------------------------

class Gdb:
    def __init__(self, port, timeout=20):
        end = time.monotonic() + timeout
        while True:
            try:
                self.sock = socket.create_connection(("127.0.0.1", port), 5)
                break
            except OSError as exc:
                if time.monotonic() > end:
                    raise Blocked(f"GDB port {port}: {exc}")
                time.sleep(0.3)
        self.sock.settimeout(10)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.running = False

    def _packet(self):
        while self.sock.recv(1) != b"$":
            pass
        buf = bytearray()
        while True:
            ch = self.sock.recv(1)
            if ch == b"#":
                self.sock.recv(2)
                self.sock.sendall(b"+")
                return bytes(buf).decode("ascii")
            if ch == b"}":
                buf.append(self.sock.recv(1)[0] ^ 0x20)
            else:
                buf.extend(ch)

    def _cmd(self, text, reply=True):
        raw = text.encode("ascii")
        self.sock.sendall(b"$" + raw + b"#" + f"{sum(raw) & 255:02x}".encode())
        return self._packet() if reply else None

    def resume(self):
        if not self.running:
            self._cmd("c", reply=False)
            self.running = True

    def halt(self):
        if self.running:
            self.sock.sendall(b"\x03")
            stop = self._packet()
            if not stop.startswith(("S", "T")):
                raise Blocked(f"interrupt: {stop[:40]}")
            self.running = False
        else:
            stop = self._cmd("?")

    def _read_chunk(self, addr, n):
        raw = self._cmd(f"m{addr:x},{n:x}")
        if raw.startswith("E") and len(raw) == 3:
            return None, raw
        if raw.startswith(("S", "T", "W", "X")):
            # An asynchronous stop reply (the core stopped on its own) is not
            # memory: fail closed instead of misreading it as data.
            raise Blocked(f"unexpected stop reply during a read: {raw[:40]}")
        data = bytes.fromhex(raw)
        return (data, None) if len(data) == n else (None, "short")

    def read(self, addr, size, chunk=0x100):
        """Read memory. mGBA answers reads while running, but a live read was
        seen to fail (E06) mid-run; retry, then fall back to a brief halt."""
        out = bytearray()
        while size:
            n = min(size, chunk)
            data, err = None, None
            for attempt in range(3):
                data, err = self._read_chunk(addr, n)
                if data is not None:
                    break
                time.sleep(0.02)
            if data is None:
                was_running = self.running
                self.halt()
                try:
                    data, err = self._read_chunk(addr, n)
                finally:
                    if was_running:
                        self.resume()
            if data is None:
                raise Blocked(f"read 0x{addr:08X}+{n}: {err}")
            out += data
            addr += n
            size -= n
        return bytes(out)


# --- emulator process, window, input and capture ---------------------------------

def audio_report(raw_path, wav_path, rate=44100, window=1.0):
    """Wrap the SDL disk capture (S16 LE stereo) as WAV and summarise loudness."""
    import math
    import wave
    raw = pathlib.Path(raw_path).read_bytes()
    raw = raw[:len(raw) // 4 * 4]
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(raw)
    samples = struct.unpack(f"<{len(raw) // 2}h", raw)
    step = int(rate * window) * 2
    timeline = []
    for i in range(0, len(samples), step):
        seg = samples[i:i + step]
        rms = math.sqrt(sum(x * x for x in seg) / len(seg)) if seg else 0.0
        timeline.append(dict(t=round(i / 2 / rate, 1), rms=round(rms, 1), peak=max(map(abs, seg)) if seg else 0))
    audible = sum(1 for w in timeline if w["rms"] > 100)
    return dict(seconds=round(len(samples) / 2 / rate, 1), assumed_format="S16LE stereo",
                assumed_rate=rate, audible_windows=audible, windows=len(timeline), timeline=timeline)


class Emulator:
    # mGBA's -g always listens on 2345; one emulator per machine at a time.
    def __init__(self, rom, outdir, display=77, port=2345, scale=2, fps_target=None, save=None,
                 audio=False):
        self.rom = pathlib.Path(rom)
        self.outdir = pathlib.Path(outdir)
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.display = f":{display}"
        self.port = port
        self.env = dict(os.environ, DISPLAY=self.display, SDL_AUDIODRIVER="dummy")
        self.audio_raw = None
        if audio:
            # SDL2's "disk" driver writes the emulator's real mixed output to a
            # file: genuine audio capture without a sound server.
            self.audio_raw = self.outdir / "audio.raw"
            self.env.update(SDL_AUDIODRIVER="disk", SDL_DISKAUDIOFILE=str(self.audio_raw))
        self.xvfb = subprocess.Popen(["Xvfb", self.display, "-screen", "0", "800x600x24", "-nolisten", "tcp"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0)
        args = ["mgba", "-g", f"-{scale}"]
        if fps_target:
            args += ["-C", f"fpsTarget={fps_target}"]
        args.append(str(self.rom))
        self.log = open(self.outdir / "mgba.log", "a")
        self.proc = subprocess.Popen(args, env=self.env, stdout=self.log, stderr=subprocess.STDOUT)
        try:
            self._attach(port)
        except BaseException:
            self.close()  # never leak an emulator or X server on a failed start
            raise

    def _attach(self, port):
        self.window = None
        for _ in range(60):
            out = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "mGBA"],
                                 env=self.env, capture_output=True, text=True).stdout.split()
            if out:
                self.window = out[0]
                break
            time.sleep(0.5)
        if not self.window:
            raise Blocked("no mGBA window")
        self.gdb = Gdb(port)
        self.gdb.halt()
        self.gdb.resume()
        self.shots = 0

    def start_trace(self, path, frame_addr):
        """Record every key transition with wall time and the game's frame counter."""
        self.trace = open(path, "a")
        self.frame_addr = frame_addr

    def frame(self):
        if getattr(self, "frame_addr", None) is None:
            return None
        return struct.unpack("<I", self.gdb.read(self.frame_addr, 4))[0]

    def key(self, name, down):
        if getattr(self, "trace", None):
            self.trace.write(json.dumps(dict(t=round(time.monotonic(), 4), frame=self.frame(),
                                             key=name, down=bool(down))) + "\n")
            self.trace.flush()
        self._key(name, down)

    def _key(self, name, down):
        subprocess.run(["xdotool", "keydown" if down else "keyup", "--window", self.window, KEYS[name]],
                       env=self.env, check=True)

    def tap(self, name, hold=0.12, after=0.15):
        self.key(name, True)
        time.sleep(hold)
        self.key(name, False)
        time.sleep(after)

    def capture(self, label):
        self.shots += 1
        path = self.outdir / f"{self.shots:04d}-{label}.png"
        subprocess.run(["import", "-window", self.window, str(path)], env=self.env, check=True,
                       capture_output=True)
        return path

    def close(self):
        for p in (getattr(self, "proc", None), getattr(self, "xvfb", None)):
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(10)
                except subprocess.TimeoutExpired:
                    p.kill()
        if getattr(self, "log", None):
            self.log.close()
        if getattr(self, "trace", None):
            self.trace.close()
