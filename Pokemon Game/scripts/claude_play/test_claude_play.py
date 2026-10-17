#!/usr/bin/env python3
"""Offline tests for the playthrough harness (no emulator, no ROM).

Map tests use the repository's real map sources. Everything else uses
SYNTHETIC fixtures, which test the harness only and are never gameplay
evidence.
"""
import json
import pathlib
import struct
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parents[1] / "engine"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "coordination"))

import driver  # noqa: E402
import emu  # noqa: E402
import evidence  # noqa: E402
import mapdata  # noqa: E402
import game  # noqa: E402
import run  # noqa: E402

WORLD = mapdata.World(ENGINE)


def bare_driver():
    d = driver.Driver.__new__(driver.Driver)
    d.w = WORLD
    return d


class MapTests(unittest.TestCase):
    def test_route_exits_and_warps(self):
        self.assertTrue(mapdata.edge_exits(WORLD.map("MAP_SALTMERE"), "up"))
        self.assertFalse(mapdata.edge_exits(WORLD.map("MAP_SALTMERE"), "down"))
        d = bare_driver()
        clinic = WORLD.map("MAP_ALDERFIELDCLINIC")
        self.assertEqual(d.warp_push(clinic, (7, 8)), "down")
        self.assertEqual(d.warp_push(WORLD.map("MAP_ALDERFIELD"), (17, 12)), "up")

    def test_bfs_reaches_nurse_counter_and_refuses_walls(self):
        clinic = WORLD.map("MAP_ALDERFIELDCLINIC")
        self.assertIsNotNone(mapdata.bfs(clinic, (7, 7), {(7, 4)}))
        self.assertFalse(clinic.walkable(7, 3))  # the counter
        self.assertIsNone(mapdata.bfs(clinic, (7, 7), {(7, 1)}, allow_goal_unwalkable=False))

    def test_live_grid_opens_the_gym_gate(self):
        gym = WORLD.map("MAP_ALDERFIELDGYM")
        self.assertFalse(gym.walkable(4, 9))
        self.assertIsNone(mapdata.bfs(gym, (4, 14), {(4, 5)}))
        blocks = list(gym.blocks)
        blocks[9 * gym.width + 4] = 513  # setmetatile 4, 9, 513, FALSE
        live = gym.with_live_blocks(blocks)
        self.assertTrue(live.walkable(4, 9))
        self.assertIsNotNone(mapdata.bfs(live, (4, 14), {(4, 5)}))
        self.assertFalse(gym.walkable(4, 9))  # the static map is unchanged

    def test_map_route_and_unreachable_map(self):
        d = bare_driver()
        legs = d.map_route("MAP_SALTMEREHOME", "MAP_ALDERFIELDGYM")
        self.assertEqual(legs[0][0], "MAP_SALTMEREHOME")
        self.assertEqual(legs[-1][:2], ("MAP_ALDERFIELD", "warp"))
        with self.assertRaises(driver.Stuck):
            d.map_route("MAP_AVERONFIELDLAB", "MAP_SALTMERE")


class SymbolTests(unittest.TestCase):
    def test_duplicate_static_names_resolve_by_address(self):
        import game
        info = dict(symbols={"HandleInputChooseAction": 0x080581A0}, offsets={}, constants={},
                    all_symbols=[(0x080581A0, "HandleInputChooseAction"),
                                 (0x0805D22C, "HandleInputChooseAction")])
        g = game.Game.__new__(game.Game)
        game.Game.__init__(g, type("E", (), {"gdb": None})(), info)
        self.assertEqual(g.func_name(0x0805D22D), "HandleInputChooseAction")
        self.assertEqual(g.func_name(0x080581A1), "HandleInputChooseAction")


class SpeciesDecodeTests(unittest.TestCase):
    """SYNTHETIC encrypted Pokemon: the decode must use the order table and key."""

    def make(self, personality, ot_id, species, order):
        secure, size = 32, 12
        raw = bytearray(100)
        struct.pack_into("<II", raw, 0, personality, ot_id)
        # Substruct 0 holds species (11 bits) + tera type; fill every other
        # word with a different value so a wrong slot or key is caught.
        for slot in range(4):
            for w in range(size // 4):
                struct.pack_into("<I", raw, secure + slot * size + w * 4, 0x0000ABCD + slot)
        struct.pack_into("<I", raw, secure + order[personality % 24] * size, (5 << 11) | species)
        key = personality ^ ot_id
        for off in range(secure, secure + 4 * size, 4):
            struct.pack_into("<I", raw, off, struct.unpack_from("<I", raw, off)[0] ^ key)
        return bytes(raw)

    def test_species_follows_personality_order_and_key(self):
        import game
        with tempfile.TemporaryDirectory() as tmp:
            rom = pathlib.Path(tmp) / "rom.gba"
            order = bytes((i * 7 + 1) % 4 for i in range(24))
            rom.write_bytes(bytes(0x100) + order)
            g = game.Game.__new__(game.Game)
            g.emu = type("E", (), {"rom": rom})()
            g.sym = {"sSubstructOffsets": 0x08000100}
            g.off = {"box.secure": 32, "box.substruct": 12}
            for personality, ot_id, species in ((0x1234FEDC, 0xA1B2C3D4, 202), (25, 0, 393), (7, 7, 661)):
                raw = self.make(personality, ot_id, species, order)
                self.assertEqual(g.box_species(raw), species)
            self.assertEqual(g.box_species(bytes(100)), 0)  # empty slot


class RomTableTests(unittest.TestCase):
    """Reads the real built ROM when one is present next to the engine."""

    def setUp(self):
        self.rom = ENGINE / "pokeemerald.gba"
        self.elf = ENGINE / "pokeemerald.elf"
        if not (self.rom.exists() and self.elf.exists()):
            self.skipTest("no built ROM/ELF in this checkout")

    def test_type_chart_matches_known_matchups(self):
        import game
        with tempfile.TemporaryDirectory() as tmp:
            info = emu.load_build_info(self.elf, ENGINE, tmp)
        c = info["constants"]
        mt = game.MoveTable(self.rom, info)
        self.assertEqual(mt.effectiveness(c["TYPE_WATER"], [c["TYPE_NORMAL"]]), 1.0)
        self.assertEqual(mt.effectiveness(c["TYPE_WATER"], [c["TYPE_FIRE"]]), 2.0)
        self.assertEqual(mt.effectiveness(c["TYPE_NORMAL"], [c["TYPE_GHOST"]]), 0.0)
        self.assertEqual(mt.effectiveness(c["TYPE_WATER"], [c["TYPE_GRASS"]]), 0.5)
        self.assertEqual(mt.move(c["MOVE_WATER_GUN"])["power"], 40)


class FakeGame:
    def __init__(self, flags, cb2="CB2_Overworld"):
        self.flags = flags
        self.cb2 = cb2

    def observation(self):
        return dict(cb2=self.cb2, flags=dict(self.flags), party=[], pokeBalls=[], berries=[])


class FakeEmu:
    def __init__(self, outdir):
        self.outdir = outdir
        self.n = 0

    def capture(self, label):
        self.n += 1
        path = self.outdir / f"{self.n:04d}-{label}.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"SYNTHETIC")
        return path


class FakeDriver:
    def __init__(self, outdir, flags, cb2="CB2_Overworld"):
        self.g = FakeGame(flags, cb2)
        self.e = FakeEmu(outdir)
        self.events = []

    def shot(self, label):
        return self.e.capture(label)

    def log(self, event, **data):
        self.events.append((event, data))


class ObserveTests(unittest.TestCase):
    def test_matching_expectation_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = FakeDriver(pathlib.Path(tmp), {"FLAG_BADGE01_GET": True})
            obs = run.observe(d, "badge", {"FLAG_BADGE01_GET": True})
            self.assertEqual(obs["problems"], [])

    def test_mismatch_fails_closed_and_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            d = FakeDriver(out, {"FLAG_BADGE01_GET": False})
            with self.assertRaises(run.ExpectationFailed):
                run.observe(d, "badge", {"FLAG_BADGE01_GET": True})
            state = json.loads((out / "state-badge.json").read_text())
            self.assertTrue(state["problems"])

    def test_missing_flag_is_a_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = FakeDriver(pathlib.Path(tmp), {})
            with self.assertRaises(run.ExpectationFailed):
                run.observe(d, "badge", {"FLAG_BADGE01_GET": True})

    def test_title_screen_is_not_gameplay(self):
        # The title screen already holds the loaded save's flags.
        with tempfile.TemporaryDirectory() as tmp:
            d = FakeDriver(pathlib.Path(tmp), {"FLAG_BADGE01_GET": True}, cb2="CB2_InitTitleScreen")
            with self.assertRaises(run.ExpectationFailed):
                run.observe(d, "badge", {"FLAG_BADGE01_GET": True})

    def test_empty_party_is_not_fully_restored(self):
        self.assertFalse(run.party_fully_restored(None, {"party": []}))


class FakeGdb:
    """SYNTHETIC memory: {address: bytes}."""
    def __init__(self, mem):
        self.mem = mem

    def read(self, addr, size):
        for base, data in self.mem.items():
            if base <= addr and addr + size <= base + len(data):
                return data[addr - base:addr - base + size]
        raise AssertionError(f"unmapped read {addr:#x}+{size}")


class DecoderTests(unittest.TestCase):
    def game(self, mem, sym, off=None, consts=None, sections=None):
        g = game.Game.__new__(game.Game)
        g.gdb, g.sym, g.off, g.c = FakeGdb(mem), sym, off or {}, consts or {}
        g.sections = sections or {}
        return g

    def test_bag_quantity_uses_the_low_half_of_the_key(self):
        key = 0x1234ABCD
        sb1, sb2 = 0x02001000, 0x02002000
        slots = struct.pack("<HHHH", 26, 999 ^ 0xABCD, 0, 0 ^ 0xABCD)
        g = self.game({0x03000000: struct.pack("<II", sb1, sb2), sb1: b"\0" * 16 + slots,
                       sb2: b"\0" * 8 + struct.pack("<I", key)},
                      {"gSaveBlock1Ptr": 0x03000000, "gSaveBlock2Ptr": 0x03000004},
                      {"sb2.encryptionKey": 8, "sb1.bag": 16, "bag.pokeBalls": 0,
                       "slot.size": 4, "slot.quantity": 2}, {"BAG_POKEBALLS_COUNT": 2})
        self.assertEqual(g.bag_pocket("bag.pokeBalls", "BAG_POKEBALLS_COUNT"), [(26, 999)])

    def test_stack_high_water_finds_the_deepest_written_byte(self):
        low, top = 0x03006000, 0x03008000 - 0x1C0
        region = bytearray(top - low)
        region[0x300] = 7                           # deepest write
        g = self.game({low: bytes(region)}, {"IWRAM_END": 0x03008000},
                      sections={".iwram.bss": dict(vma=0x03005000, size=0x1000)})
        self.assertEqual(g.stack_high_water(),
                         dict(regionBytes=top - low, usedBytes=top - low - 0x300, freeBytes=0x300))

    def test_async_stop_reply_during_a_read_fails_closed(self):
        gdb = emu.Gdb.__new__(emu.Gdb)
        gdb._cmd = lambda text, reply=True: "T05thread:01;"
        with self.assertRaises(emu.Blocked):
            gdb._read_chunk(0x02000000, 4)


class TraceTests(unittest.TestCase):
    def test_every_key_transition_is_traced_with_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = emu.Emulator.__new__(emu.Emulator)
            sent = []
            e._key = lambda name, down: sent.append((name, down))
            frames = iter([100, 107])
            e.frame = lambda: next(frames)
            e.start_trace(pathlib.Path(tmp) / "inputs.jsonl", 0)
            e.key("A", True)
            e.key("A", False)
            e.trace.close()
            lines = [json.loads(l) for l in (pathlib.Path(tmp) / "inputs.jsonl").read_text().splitlines()]
            self.assertEqual(sent, [("A", True), ("A", False)])
            self.assertEqual([(l["key"], l["down"], l["frame"]) for l in lines],
                             [("A", True, 100), ("A", False, 107)])


class GdbReadTests(unittest.TestCase):
    def make(self, replies):
        g = emu.Gdb.__new__(emu.Gdb)
        g.running = True
        g.calls = []
        it = iter(replies)
        g._cmd = lambda text, reply=True: (g.calls.append(text), next(it))[1] if reply else g.calls.append(text)
        g.halt = lambda: setattr(g, "running", False) or g.calls.append("HALT")
        g.resume = lambda: setattr(g, "running", True) or g.calls.append("RESUME")
        return g

    def test_transient_error_is_retried(self):
        g = self.make(["E06", "0102"])
        self.assertEqual(g.read(0x02000000, 2), b"\x01\x02")
        self.assertNotIn("HALT", g.calls)

    def test_persistent_error_falls_back_to_a_halted_read(self):
        g = self.make(["E06", "E06", "E06", "0304"])
        self.assertEqual(g.read(0x02000000, 2), b"\x03\x04")
        self.assertEqual(g.calls[-2:], ["m2000000,2", "RESUME"])
        self.assertTrue(g.running)

    def test_unreadable_memory_still_fails_closed(self):
        g = self.make(["E06"] * 4)
        with self.assertRaises(emu.Blocked):
            g.read(0x02000000, 2)
        self.assertTrue(g.running)


class AudioReportTests(unittest.TestCase):
    def test_silence_and_tone_are_distinguished(self):
        import math
        with tempfile.TemporaryDirectory() as tmp:
            raw = pathlib.Path(tmp) / "audio.raw"
            rate = 1000
            silence = [0] * (rate * 2)  # 1 s of stereo silence (SYNTHETIC)
            tone = []
            for i in range(rate):
                v = int(3000 * math.sin(i / 5))
                tone += [v, v]
            raw.write_bytes(struct.pack(f"<{len(silence) + len(tone)}h", *(silence + tone)))
            rep = emu.audio_report(raw, pathlib.Path(tmp) / "a.wav", rate=rate)
            self.assertEqual(rep["windows"], 2)
            self.assertEqual(rep["audible_windows"], 1)
            self.assertEqual(rep["timeline"][0]["rms"], 0.0)
            self.assertTrue((pathlib.Path(tmp) / "a.wav").stat().st_size > 44)


def synthetic_run(root, name, *, source="a" * 40, rom="b" * 64, dirty=False,
                  problems=(), screenshot=True, trace=True, elf="e" * 64, engine_rom=None,
                  dev_only=False):
    """SYNTHETIC run directory for harness tests only."""
    run_dir = root / name
    run_dir.mkdir(parents=True)
    (run_dir / "provenance-start.json").write_text(json.dumps(dict(
        source_sha=source, rom_sha256=rom, elf_sha256=elf, engine_rom_sha256=engine_rom or rom,
        engine_dirty=dirty, driver_sha="d" * 40, driver_dirty=False, synthetic=True)))
    events = [dict(event="start")]
    if dev_only:
        events.append(dict(event="debug-menu", label="fill-balls", rows=[1, 1, 4], dev_only=True))
    (run_dir / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    if trace:
        (run_dir / "inputs.jsonl").write_text('{"key": "A", "down": true, "frame": 1}\n')
    if screenshot:
        (run_dir / "0001-badge.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"SYNTHETIC")
    (run_dir / "state-badge.json").write_text(json.dumps(dict(
        label="badge", screenshot="0001-badge.png", flags={"FLAG_BADGE01_GET": True},
        expected={"FLAG_BADGE01_GET": True}, problems=list(problems))))
    return run_dir


class EvidenceTests(unittest.TestCase):
    def test_complete_package_is_ready_for_review_not_pass(self):
        import qa_evidence_report
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            synthetic_run(root, "r1")
            manifest = evidence.build({"Q1": [("r1", ["badge"])]}, root)
            report = qa_evidence_report.inspect_package(manifest, root)
            status = report["cases"][0]["evidence_status"]
            self.assertEqual(status, "READY_FOR_INDEPENDENT_REVIEW")
            self.assertNotIn("PASS", status)

    def test_missing_pieces_fail_closed(self):
        cases = [dict(screenshot=False), dict(trace=False), dict(dirty=True),
                 dict(problems=["FLAG_BADGE01_GET: expected True, observed False"])]
        for kwargs in cases:
            with self.subTest(**{k: str(v) for k, v in kwargs.items()}):
                with tempfile.TemporaryDirectory() as tmp:
                    root = pathlib.Path(tmp)
                    synthetic_run(root, "r1", **kwargs)
                    with self.assertRaises(evidence.EvidenceError):
                        evidence.build({"Q1": [("r1", ["badge"])]}, root)

    def test_runs_from_different_builds_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            synthetic_run(root, "r1")
            synthetic_run(root, "r2", rom="c" * 64)
            with self.assertRaises(evidence.EvidenceError):
                evidence.build({"Q1": [("r1", ["badge"]), ("r2", ["badge"])]}, root)

    def test_debug_menu_use_marks_the_case_dev_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            synthetic_run(root, "r1")
            synthetic_run(root, "r2", dev_only=True)
            manifest = evidence.build({"PLAIN": [("r1", ["badge"])], "FIX": [("r2", ["badge"])]}, root)
            plain, fix = manifest["cases"]
            self.assertEqual(plain["scope"], "ORDINARY_PLAY")
            self.assertEqual(fix["scope"], "DEV_FIXTURE")
            self.assertEqual(fix["dev_fixtures"], ["r2: fill-balls"])
            self.assertTrue(all("DEV-ONLY" in o["statement"] for o in fix["state_observations"]))
            self.assertFalse(any("DEV-ONLY" in o["statement"] for o in plain["state_observations"]))

    def test_rom_that_is_not_the_engine_build_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            synthetic_run(root, "r1", engine_rom="f" * 64)
            with self.assertRaises(evidence.EvidenceError):
                evidence.build({"Q1": [("r1", ["badge"])]}, root)

    def test_runs_with_different_elves_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            synthetic_run(root, "r1")
            synthetic_run(root, "r2", elf="0" * 64)
            with self.assertRaises(evidence.EvidenceError):
                evidence.build({"Q1": [("r1", ["badge"]), ("r2", ["badge"])]}, root)

    def test_missing_state_label_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            synthetic_run(root, "r1")
            with self.assertRaises(evidence.EvidenceError):
                evidence.build({"Q1": [("r1", ["badge", "reward"])]}, root)


if __name__ == "__main__":
    unittest.main()
