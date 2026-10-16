#!/usr/bin/env python3
"""Local/CI no-ROM tests of the independent QUEST observer's fail-closed logic."""
import importlib.util
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest


module = Path(__file__).with_name("quest_state_controller.py")
spec = importlib.util.spec_from_file_location("quest_state_controller", module)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


class DummySocket:
    def __init__(self):
        self.sent = []

    def sendall(self, data):
        self.sent.append(data)


class ObserverTests(unittest.TestCase):
    def fake(self, payload, stop="S05"):
        gdb = object.__new__(qa.ReadOnlyGdb)
        gdb.sock = DummySocket()
        gdb.packet = lambda: stop
        queries = []
        def reply(q, reply=True):
            queries.append(q)
            if q == "m3000100,4":
                return struct.pack("<I", 0x02000100).hex()
            if q == "m2000100,c":
                return payload.hex()
            if q == "c":
                return None
            raise AssertionError(f"Unplanned remote command: {q}")
        gdb.command = reply
        return gdb, queries

    def test_actual_saveblock_offsets(self):
        # global.h: pos.x/y 0/2; location group/map/warp 4/5/6.
        header = struct.pack("<hhbbbxhh", 13, 16, 76, 9, 1, -1, -1)
        gdb, commands = self.fake(header)
        result = gdb.position(0x03000100)
        self.assertEqual((result["x"], result["y"]), (13, 16))
        self.assertEqual((result["mapGroup"], result["mapNum"], result["warpId"]), (76, 9, 1))
        self.assertEqual(commands, ["m3000100,4", "m2000100,c", "c"])
        self.assertEqual(gdb.sock.sent, [b"\x03"])

    def test_reject_non_ewram_pointer(self):
        gdb, commands = self.fake(b"\x00"*12)
        def invalid(q, reply=True):
            commands.append(q)
            return ("00000000" if q == "m3000100,4" else None)
        gdb.command = invalid
        with self.assertRaisesRegex(qa.Blocked, "outside EWRAM"):
            gdb.position(0x03000100)
        self.assertEqual(commands[-1], "c")

    def test_reject_debugger_without_interrupt(self):
        gdb, _ = self.fake(b"\x00"*12, stop="E00")
        with self.assertRaisesRegex(qa.Blocked, "interrupt failed"):
            gdb.position(0x03000100)

    def test_reject_invalid_coordinates(self):
        gdb, _ = self.fake(struct.pack("<hhbbbxhh", -9, 600, 76, 9, 1, -1, -1))
        with self.assertRaisesRegex(qa.Blocked, "Invalid tile"):
            gdb.position(0x03000100)

    def test_panel_detector_map_and_dialogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            dark = Path(tmp) / "field.png"
            panel = Path(tmp) / "dialogue.png"
            subprocess.run(["convert", "-size", "480x320", "xc:#282D42", str(dark)], check=True)
            subprocess.run(["convert", str(dark), "-fill", "white",
                            "-draw", "rectangle 3,236 475,312", str(panel)], check=True)
            self.assertLess(qa.white_panel_ratio(dark), 0.30)
            self.assertGreater(qa.white_panel_ratio(panel), 0.50)

    def test_reject_unknown_frame_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            frame = Path(tmp) / "bad.png"
            subprocess.run(["convert", "-size", "240x160", "xc:white", str(frame)], check=True)
            with self.assertRaisesRegex(qa.Blocked, "geometry"):
                qa.white_panel_ratio(frame)

    def test_elf_no_symbol_fails_closed(self):
        from unittest.mock import patch
        with patch.object(qa.subprocess, "check_output", return_value="03001000 D other\n"):
            with self.assertRaisesRegex(qa.Blocked, "gSaveBlock1Ptr"):
                qa.elf_symbol("fake.elf")


if __name__ == "__main__":
    unittest.main(verbosity=2)
