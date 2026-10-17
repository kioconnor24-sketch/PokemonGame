"""Read-only game state for the playthrough driver.

Snapshots read memory while the emulator runs (mGBA serves GDB reads live;
halting it between key presses was found to drop held directions). All
addresses, struct offsets and constants come from the exact build being
played (see emu.load_build_info), never from guesses.
"""
import struct


class State(dict):
    __getattr__ = dict.get


class Game:
    def __init__(self, emulator, info):
        self.emu = emulator
        self.gdb = emulator.gdb
        self.sym = info["symbols"]
        self.off = info["offsets"]
        self.c = info["constants"]
        self.by_addr = {}
        for name, addr in self.sym.items():
            if 0x08000000 <= addr < 0x0A000000:
                self.by_addr.setdefault(addr & ~1, name)

    def _u(self, fmt, addr):
        return struct.unpack(fmt, self.gdb.read(addr, struct.calcsize(fmt)))

    def func_name(self, ptr):
        return self.by_addr.get(ptr & ~1, f"0x{ptr:08X}")

    def snapshot(self, battle=True, halt=False):
        g = self.gdb
        if halt:
            g.halt()
        try:
            s = State()
            cb2 = self._u("<I", self.sym["gMain"] + self.off["main.callback2"])[0]
            s.cb2 = self.func_name(cb2)
            sb1 = self._u("<I", self.sym["gSaveBlock1Ptr"])[0]
            s.valid = 0x02000000 <= sb1 < 0x02040000
            if s.valid:
                head = g.read(sb1, 12)
                s.x, s.y, s.group, s.num, s.warp = struct.unpack_from("<hhbbb", head)
                s.flags = g.read(sb1 + self.off["sb1.flags"], 300)
                s.vars = g.read(sb1 + self.off["sb1.vars"], 512)
            s.locked = g.read(self.sym["sLockFieldControls"], 1)[0]
            count = g.read(self.sym["gPartiesCount"] + self.c["B_TRAINER_PLAYER"], 1)[0]
            s.party = []
            if count <= 6:
                base = self.sym["gParties"]
                size = self.off["mon.size"]
                for i in range(count):
                    raw = g.read(base + i * size, size)
                    s.party.append(dict(level=raw[self.off["mon.level"]],
                                        hp=struct.unpack_from("<H", raw, self.off["mon.hp"])[0],
                                        maxhp=struct.unpack_from("<H", raw, self.off["mon.maxHP"])[0]))
            s.in_battle = s.cb2 == "BattleMainCB2"
            if battle and s.in_battle:
                s.battle_flags = self._u("<I", self.sym["gBattleTypeFlags"])[0]
                s.controller = self.func_name(self._u("<I", self.sym["gBattlerControllerFuncs"])[0])
                s.action_cursor = g.read(self.sym["gActionSelectionCursor"], 1)[0]
                s.move_cursor = g.read(self.sym["gMoveSelectionCursor"], 1)[0]
                s.mons = []
                for b in range(4):
                    raw = g.read(self.sym["gBattleMons"] + b * self.off["bm.size"], self.off["bm.size"])
                    s.mons.append(dict(
                        species=struct.unpack_from("<H", raw, self.off["bm.species"])[0],
                        moves=list(struct.unpack_from("<4H", raw, self.off["bm.moves"])),
                        pp=list(raw[self.off["bm.pp"]:self.off["bm.pp"] + 4]),
                        hp=struct.unpack_from("<H", raw, self.off["bm.hp"])[0],
                        maxhp=struct.unpack_from("<H", raw, self.off["bm.maxHP"])[0],
                        level=raw[self.off["bm.level"]],
                        types=list(raw[self.off["bm.types"]:self.off["bm.types"] + 2])))
            return s
        finally:
            g.resume()

    def flag(self, s, name):
        fid = self.c[name] if isinstance(name, str) else name
        return bool(s.flags[fid // 8] & (1 << (fid % 8)))

    def var(self, s, name):
        vid = (self.c[name] if isinstance(name, str) else name) - self.c["VARS_START"]
        return struct.unpack_from("<H", s.vars, vid * 2)[0]


class MoveTable:
    """Move power/type/category and the type chart, read from the ROM file itself.

    struct MoveInfo (include/move.h): two pointers, then one 32-bit word of
    bitfields: effect:16, type:5, category:2, power:9 (LSB first on ARM).
    """
    def __init__(self, rom_path, info):
        self.rom = open(rom_path, "rb").read()
        self.base = info["symbols"]["gMovesInfo"]
        self.size = info["offsets"]["move.size"]
        self.ntypes = info["constants"]["NUMBER_OF_MON_TYPES"]
        raw = self._rom(info["symbols"]["gTypeEffectivenessTable"], self.ntypes * self.ntypes * 2)
        self.chart = struct.unpack(f"<{self.ntypes * self.ntypes}H", raw)
        self.cache = {}

    def move(self, move_id):
        if move_id not in self.cache:
            word = struct.unpack("<I", self._rom(self.base + move_id * self.size + 8, 4))[0]
            self.cache[move_id] = dict(effect=word & 0xFFFF, type=(word >> 16) & 0x1F,
                                       category=(word >> 21) & 3, power=word >> 23)
        return self.cache[move_id]

    def _rom(self, addr, size):
        off = addr - 0x08000000
        return self.rom[off:off + size]

    def effectiveness(self, atk_type, def_types):
        mult = 1.0
        for t in set(def_types):
            if t < self.ntypes and atk_type < self.ntypes:
                mult *= self.chart[atk_type * self.ntypes + t] / 0x1000
        return mult
