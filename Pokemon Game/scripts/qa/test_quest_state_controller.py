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
            if q == "m2001375,1":
                return "00"
            if q == "m3000104,4":
                return struct.pack("<I", 0x02000200).hex()
            if q == "m20002ac,4":
                return struct.pack("<I", 0xA33A).hex()
            if q == "m2000890,b8":
                return "00" * (46 * 4)
            if q == "c":
                return None
            raise AssertionError(f"Unplanned remote command: {q}")
        gdb.command = reply
        return gdb, queries

    def test_read_only_source_start_menu_save_action(self):
        # start_menu.c MENU_ACTION_SAVE == 5, selected at index 2.
        from types import SimpleNamespace
        g = object.__new__(qa.ReadOnlyGdb)
        g.sock = DummySocket()
        g.packet = lambda: "S05"
        symbols = dict(cursor=0x02001000, count=0x02001001,
                       actions=0x02001002, saveCallback=0x02001010,
                       main=0x02001020, saveStatus=0x02001030,
                       saveAttempt=0x02001050, differentFile=0x02001040,
                       callbacks={"SaveConfirmInputCallback": 0x08005000},
                       mainCallbacks={"CB2_MainMenu": 0x08006000})
        contents = {
            "m2001000,1": b"\x02",
            "m2001001,1": b"\x03",
            "m2001002,9": bytes([2, 4, 5, 0, 0, 0, 0, 0, 0]),
            "m2001010,4": struct.pack("<I", 0x08005001),
            "m2001024,4": struct.pack("<I", 0x08006001),
            "m2001030,2": struct.pack("<H", 0),
            "m2001050,2": struct.pack("<H", 1),
            "m2001040,1": b"\x00",
        }
        commands = []
        def reply(command, reply=True):
            commands.append(command)
            if command == "c":
                return None
            return contents[command].hex()
        g.command = reply
        state = g.menu_state(symbols)
        self.assertEqual(state["selected"], 5)
        self.assertEqual(state["actions"], [2, 4, 5])
        self.assertEqual(state["savePhase"], "SaveConfirmInputCallback")
        self.assertEqual(state["mainPhase"], "CB2_MainMenu")
        self.assertEqual(state["saveStatus"], 0)  # load status still EMPTY
        self.assertEqual(state["saveAttemptStatus"], 1)  # write succeeded
        self.assertEqual(state["differentSaveFile"], 0)
        self.assertEqual(g.sock.sent, [b"\x03"])
        self.assertEqual(commands[-1], "c")

    def test_invalid_start_cursor_fails_closed(self):
        from unittest.mock import patch
        g = object.__new__(qa.ReadOnlyGdb)
        g.sock = DummySocket()
        g.packet = lambda: "S05"
        symbols = dict(cursor=0x02001000, count=0x02001001,
                       actions=0x02001002, saveCallback=0x02001010)
        calls = []
        def reply(q, reply=True):
            calls.append(q)
            if q == "c":
                return None
            return {"m2001001,1": "03", "m2001000,1": "09",
                    "m2001002,9": "020405000000000000"}[q]
        g.command = reply
        with self.assertRaisesRegex(qa.Blocked, "Invalid cursor"):
            g.menu_state(symbols)
        self.assertEqual(calls[-1], "c")

    def test_actual_saved_q2_state_contract(self):
        exact = dict(mapGroup=75, mapNum=6, x=19, y=14,
                     notesStarted=True, notesRecorded=False,
                     notesRewarded=False, sketchStarted=True,
                     sketchFound=True, sketchRewarded=True,
                     oranBerryQuantity=3)
        qa.require_q2_complete(exact)
        for key, bad in [("oranBerryQuantity", 6),
                         ("sketchRewarded", False),
                         ("notesRecorded", True), ("mapNum", 5)]:
            with self.subTest(key=key):
                changed = dict(exact, **{key: bad})
                with self.assertRaises(qa.Blocked):
                    qa.require_q2_complete(changed)

    def test_title_ready_requires_exact_active_title_phase_three_task(self):
        tasks = bytearray(16 * 40)
        target = 0x08006000
        struct.pack_into("<I", tasks, 2*40, target | 1)
        tasks[2*40 + 4] = 0
        self.assertFalse(qa.title_input_ready(tasks, target))
        tasks[2*40 + 4] = 1
        self.assertTrue(qa.title_input_ready(tasks, target))
        self.assertFalse(qa.title_input_ready(tasks, 0x08006020))
        tasks[2*40 + 4] = 0
        struct.pack_into("<I", tasks, 12*40, target)
        tasks[12*40 + 4] = 1
        self.assertTrue(qa.title_input_ready(tasks, target | 1))

    def test_title_ready_rejects_unverified_task_record_size(self):
        with self.assertRaisesRegex(qa.Blocked, "exactly 640"):
            qa.title_input_ready(b"\x00" * 639, 0x08006000)

    def test_actual_saveblock_offsets(self):
        # global.h: pos.x/y 0/2; location group/map/warp 4/5/6.
        header = struct.pack("<hhbbbxhh", 13, 16, 76, 9, 1, -1, -1)
        gdb, commands = self.fake(header)
        result = gdb.position(0x03000100, 0x03000104)
        self.assertEqual((result["x"], result["y"]), (13, 16))
        self.assertEqual((result["mapGroup"], result["mapNum"], result["warpId"]), (76, 9, 1))
        self.assertEqual(commands, ["m3000100,4", "m2000100,c", "m2001375,1",
                         "m3000104,4", "m20002ac,4", "m2000890,b8", "c"])
        self.assertEqual(gdb.sock.sent, [b"\x03"])

    def test_saved_flag_bit_masks(self):
        header = struct.pack("<hhbbbxhh", 13, 16, 75, 9, 1, -1, -1)
        gdb, commands = self.fake(header)
        old = gdb.command
        gdb.command = lambda q, reply=True: "1c" if q == "m2001375,1" else old(q, reply)
        state = gdb.position(0x03000100, 0x03000104)
        self.assertTrue(state["notesStarted"])
        self.assertTrue(state["notesRecorded"])
        self.assertTrue(state["notesRewarded"])

    def test_sketch_flags_use_same_saved_byte_distinct_bits(self):
        header = struct.pack("<hhbbbxhh", 20, 15, 75, 6, 0, -1, -1)
        gdb, _ = self.fake(header)
        old = gdb.command
        gdb.command = lambda q, reply=True: "e0" if q == "m2001375,1" else old(q, reply)
        state = gdb.position(0x03000100, 0x03000104)
        self.assertTrue(state["sketchStarted"])
        self.assertTrue(state["sketchFound"])
        self.assertTrue(state["sketchRewarded"])
        self.assertFalse(state["notesStarted"])
        self.assertFalse(state["notesRecorded"])
        self.assertFalse(state["notesRewarded"])

    def test_berry_pocket_quantity_reads_item520_without_memory_writes(self):
        header = struct.pack("<hhbbbxhh", 11, 27, 75, 5, -1, -1, -1)
        gdb, commands = self.fake(header)
        source = gdb.command
        slots = bytearray(46 * 4)
        struct.pack_into("<HH", slots, 0, 520, 3 ^ 0xA33A)
        struct.pack_into("<HH", slots, 4, 519, 9)
        struct.pack_into("<HH", slots, 8, 520, 2 ^ 0xA33A)
        def bag_reply(q, reply=True):
            if q == "m2000890,b8":
                commands.append(q)
                return slots.hex()
            return source(q, reply)
        gdb.command = bag_reply
        state = gdb.position(0x03000100, 0x03000104)
        self.assertEqual(state["oranBerryQuantity"], 5)
        self.assertIn("m2000890,b8", commands)
        self.assertEqual(gdb.sock.sent, [b"\x03"])

    def test_title_probe_skips_overworld_start_menu_memory(self):
        gdb = object.__new__(qa.ReadOnlyGdb)
        gdb.sock = DummySocket()
        gdb.packet = lambda: "S05"
        tasks = bytearray(16 * 40)
        struct.pack_into("<I", tasks, 0, 0x08001235)
        tasks[4] = 1
        asked = []
        def reply(cmd, reply=True):
            asked.append(cmd)
            if cmd == "m3001004,4":
                return struct.pack("<I", 0x08001201).hex()
            if cmd == "m3002000,2":
                return "0100"
            if cmd == "m3003000,280":
                return tasks.hex()
            if cmd == "c":
                return None
            raise AssertionError(f"Unexpected stale menu read: {cmd}")
        gdb.command = reply
        symbols = dict(main=0x03001000, saveStatus=0x03002000,
                       taskArray=0x03003000, titleReadyFunc=0x08001235,
                       mainCallbacks={"CB2_MainMenu": 0x08001201})
        state = gdb.title_state(symbols)
        self.assertTrue(state["titleInputReady"])
        self.assertEqual(state["mainPhase"], "CB2_MainMenu")
        self.assertEqual(state["saveStatus"], 1)
        self.assertEqual(asked, ["m3001004,4", "m3002000,2",
                                 "m3003000,280", "c"])

    def test_title_probe_gdb_error_identifies_specific_symbol(self):
        gdb = object.__new__(qa.ReadOnlyGdb)
        gdb.sock = DummySocket()
        gdb.packet = lambda: "S05"
        calls = []
        def reply(cmd, reply=True):
            calls.append(cmd)
            return "E14" if cmd != "c" else None
        gdb.command = reply
        with self.assertRaisesRegex(
                qa.Blocked, "title main callback read 0x03001004: GDB E14"):
            gdb.title_state(dict(main=0x03001000))
        self.assertEqual(calls, ["m3001004,4", "c"])

    def test_reset_transient_is_allowed_only_for_title_poll(self):
        self.assertTrue(qa.reboot_transient(
            "title-102-title-poll-1", ValueError("non-hexadecimal debugger reply")))
        self.assertTrue(qa.reboot_transient(
            "title-102-title-poll-1", qa.Blocked("uninitialized title globals")))
        self.assertFalse(qa.reboot_transient(
            "save-006-write-stage-1", ValueError("non-hexadecimal reply")))
        self.assertFalse(qa.reboot_transient(
            "401-q2-meadow-step", ValueError("non-hexadecimal reply")))
        self.assertFalse(qa.reboot_transient(
            "title-102-title-poll-2", RuntimeError("unexpected reader defect")))

    def test_reject_non_ewram_pointer(self):
        gdb, commands = self.fake(b"\x00"*12)
        def invalid(q, reply=True):
            commands.append(q)
            return ("00000000" if q == "m3000100,4" else None)
        gdb.command = invalid
        with self.assertRaisesRegex(qa.Blocked, "outside EWRAM"):
            gdb.position(0x03000100, 0x03000104)
        self.assertEqual(commands[-1], "c")

    def test_reject_invalid_saveblock2_pointer_before_berry_read(self):
        header = struct.pack("<hhbbbxhh", 13, 16, 75, 9, 1, -1, -1)
        gdb, commands = self.fake(header)
        orig = gdb.command
        def invalid(q, reply=True):
            if q == "m3000104,4":
                commands.append(q)
                return "00000000"
            return orig(q, reply)
        gdb.command = invalid
        with self.assertRaisesRegex(qa.Blocked, "gSaveBlock2Ptr outside EWRAM"):
            gdb.position(0x03000100, 0x03000104)
        self.assertNotIn("m2000890,b8", commands)
        self.assertEqual(commands[-1], "c")

    def test_reject_debugger_without_interrupt(self):
        gdb, _ = self.fake(b"\x00"*12, stop="E00")
        with self.assertRaisesRegex(qa.Blocked, "interrupt failed"):
            gdb.position(0x03000100, 0x03000104)

    def test_reject_invalid_coordinates(self):
        gdb, _ = self.fake(struct.pack("<hhbbbxhh", -9, 600, 76, 9, 1, -1, -1))
        with self.assertRaisesRegex(qa.Blocked, "Invalid tile"):
            gdb.position(0x03000100, 0x03000104)

    def test_panel_detector_map_and_dialogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            dark = Path(tmp) / "field.png"
            panel = Path(tmp) / "dialogue.png"
            subprocess.run(["convert", "-size", "480x320", "xc:#282D42", str(dark)], check=True)
            subprocess.run(["convert", str(dark), "-fill", "white",
                            "-draw", "rectangle 3,236 475,312", str(panel)], check=True)
            self.assertLess(qa.white_panel_ratio(dark), 0.30)
            self.assertGreater(qa.white_panel_ratio(panel), 0.50)

    def test_field_ui_requires_message_closed(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            field = Path(tmp) / "field.png"
            message = Path(tmp) / "message.png"
            subprocess.run(["convert", "-size", "480x320", "xc:#282D42", str(field)], check=True)
            subprocess.run(["convert", str(field), "-fill", "white",
                            "-draw", "rectangle 4,236 475,312", str(message)], check=True)
            self.assertIsNone(qa.assert_ui(SimpleNamespace(frame=field, kind="field")))
            with self.assertRaisesRegex(qa.Blocked, "field not ready"):
                qa.assert_ui(SimpleNamespace(frame=message, kind="field"))

    def test_reject_unknown_frame_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            frame = Path(tmp) / "bad.png"
            subprocess.run(["convert", "-size", "240x160", "xc:white", str(frame)], check=True)
            with self.assertRaisesRegex(qa.Blocked, "geometry"):
                qa.white_panel_ratio(frame)

    def test_debug_ui_requires_correct_panel(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            dark = Path(tmp) / "map.png"
            menu = Path(tmp) / "menu.png"
            subprocess.run(["convert", "-size", "480x320", "xc:#282D42", str(dark)], check=True)
            subprocess.run(["convert", str(dark), "-fill", "white",
                            "-draw", "rectangle 4,4 295,314", str(menu)], check=True)
            with self.assertRaisesRegex(qa.Blocked, "sidebar"):
                qa.assert_ui(SimpleNamespace(frame=dark, kind="sidebar"))
            self.assertIsNone(qa.assert_ui(SimpleNamespace(frame=menu, kind="sidebar")))

    def test_elf_no_symbol_fails_closed(self):
        from unittest.mock import patch
        with patch.object(qa.subprocess, "check_output", return_value="03001000 D other\n"):
            with self.assertRaisesRegex(qa.Blocked, "gSaveBlock1Ptr"):
                qa.elf_symbol("fake.elf")


if __name__ == "__main__":
    unittest.main(verbosity=2)
