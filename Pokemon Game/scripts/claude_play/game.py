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
        for addr, name in info.get("all_symbols") or [(a, n) for n, a in self.sym.items()]:
            if 0x08000000 <= addr < 0x0A000000:
                self.by_addr.setdefault(addr & ~1, name)

    def _u(self, fmt, addr):
        return struct.unpack(fmt, self.gdb.read(addr, struct.calcsize(fmt)))

    def box_species(self, raw):
        """Species of a party Pokemon, decoded read-only like GetSubstruct():
        the secure words are XORed with otId ^ personality, and substruct 0
        (species in its low 11 bits) sits where sSubstructOffsets[0][p % 24]
        says. The table is read from the ROM file."""
        if not hasattr(self, "_substruct_order"):
            addr = self.sym["sSubstructOffsets"] - 0x08000000
            with open(self.emu.rom, "rb") as f:
                f.seek(addr)
                self._substruct_order = f.read(24)
        personality, ot_id = struct.unpack_from("<II", raw, 0)
        if not personality and not ot_id:
            return 0
        base = self.off["box.secure"] + self._substruct_order[personality % 24] * self.off["box.substruct"]
        key = personality ^ ot_id
        word = struct.unpack_from("<I", raw, base)[0] ^ key
        return word & 0x7FF

    def task(self, func):
        """Data words (s16[16]) of the active task running `func`, or None.
        Read-only: lets a menu be driven by its own state and cursor."""
        size, data = self.off["task.size"], self.off["task.data"]
        raw = self.gdb.read(self.sym["gTasks"], 16 * size)
        for i in range(16):
            rec = raw[i * size:(i + 1) * size]
            ptr = struct.unpack_from("<I", rec, 0)[0]
            if rec[self.off["task.isActive"]] and self.func_name(ptr) == func:
                return list(struct.unpack_from("<16h", rec, data))
        return None

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
                    s.party.append(dict(species=self.box_species(raw),
                                        level=raw[self.off["mon.level"]],
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
                        types=list(raw[self.off["bm.types"]:self.off["bm.types"] + 2]),
                        stages=list(raw[self.off["bm.statStages"]:self.off["bm.statStages"] + 8])))
            return s
        finally:
            g.resume()

    def bag_pocket(self, field, count_name):
        """[(itemId, quantity)] of one SaveBlock1 bag pocket; quantities are
        stored XORed with SaveBlock2.encryptionKey (item.c)."""
        g = self.gdb
        sb1 = self._u("<I", self.sym["gSaveBlock1Ptr"])[0]
        sb2 = self._u("<I", self.sym["gSaveBlock2Ptr"])[0]
        key = self._u("<I", sb2 + self.off["sb2.encryptionKey"])[0] & 0xFFFF
        size = self.off["slot.size"]
        n = self.c[count_name]
        raw = g.read(sb1 + self.off["sb1.bag"] + self.off[field], size * n)
        out = []
        for i in range(n):
            item = struct.unpack_from("<H", raw, i * size)[0]
            qty = struct.unpack_from("<H", raw, i * size + self.off["slot.quantity"])[0] ^ key
            if item:
                out.append((item, qty))
        return out

    map_names = {}

    def emu_map_name(self, s):
        return self.map_names.get((s.group, s.num))

    def observation(self):
        """Plain facts for an evidence state file."""
        s = self.snapshot(battle=False)
        names = ["FLAG_BADGE01_GET", "FLAG_BADGE02_GET", "FLAG_AVERON_STARTER",
                 "FLAG_AVERON_WEST_SLUICE", "FLAG_AVERON_EAST_SLUICE", "FLAG_AVERON_GYM1_TM",
                 "FLAG_AVERON_NOTES_STARTED", "FLAG_AVERON_NOTES_RECORDED",
                 "FLAG_AVERON_NOTES_REWARDED", "FLAG_AVERON_EXP_SHARE",
                 "FLAG_AVERON_SKETCH_STARTED", "FLAG_AVERON_SKETCH_FOUND",
                 "FLAG_AVERON_SKETCH_REWARDED", "FLAG_AVERON_DEV_GIFT_RECEIVED"]
        return dict(
            map=self.emu_map_name(s), cb2=s.cb2, mapGroup=s.group, mapNum=s.num, x=s.x, y=s.y,
            frame=self.emu.frame(),
            flags={n: self.flag(s, n) for n in names},
            party=s.party,
            pokeBalls=self.bag_pocket("bag.pokeBalls", "BAG_POKEBALLS_COUNT"),
            berries=self.bag_pocket("bag.berries", "BAG_BERRIES_COUNT"),
            money=self.money(),
            saveAttemptStatus=self.gdb.read(self.sym["gSaveAttemptStatus"], 1)[0])

    def money(self):
        sb1 = self._u("<I", self.sym["gSaveBlock1Ptr"])[0]
        sb2 = self._u("<I", self.sym["gSaveBlock2Ptr"])[0]
        key = self._u("<I", sb2 + self.off["sb2.encryptionKey"])[0]
        return self._u("<I", sb1 + self.off["sb1.money"])[0] ^ key

    def live_blocks(self, width, height, border=7):
        """Current map grid from gBackupMapLayout, without the MAP_OFFSET border."""
        g = self.gdb
        vw, vh, ptr = struct.unpack("<iiI", g.read(self.sym["gBackupMapLayout"], 12))
        if vw != width + 2 * border + 1:  # MAP_OFFSET_W (fieldmap.h)
            # Map sizes disagree: the player is not on the map we were asked about.
            return None
        raw = g.read(ptr, vw * vh * 2)
        grid = struct.unpack(f"<{vw * vh}H", raw)
        return [grid[(y + border) * vw + (x + border)] for y in range(height) for x in range(width)]

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
        elem = info["offsets"]["typechart.elem"]  # uq4_12_t is 32-bit (fpmath.h)
        raw = self._rom(info["symbols"]["gTypeEffectivenessTable"], self.ntypes * self.ntypes * elem)
        self.chart = struct.unpack(f"<{self.ntypes * self.ntypes}{'I' if elem == 4 else 'H'}", raw)
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
