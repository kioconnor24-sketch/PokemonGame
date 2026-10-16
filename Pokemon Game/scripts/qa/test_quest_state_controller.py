#!/usr/bin/env python3
"""Local/CI no-ROM tests of the independent QUEST observer's fail-closed logic."""
import importlib.util
import json
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

    def test_actual_bag_berry_tab_is_third_right_not_fourth(self):
        # Real screenshot sequence in graphical run 38870779185:
        # right1 POKE BALLS, right2 TMs & HMs, right3 BERRIES,
        # right4 KEY ITEMS. Stop at the actual Oran Berry x3 evidence.
        self.assertEqual(qa.BAG_POCKET_ORDER, (
            "ITEMS", "POKE BALLS", "TMS & HMS", "BERRIES", "KEY ITEMS"))
        self.assertEqual(qa.bag_pocket_right_steps("ITEMS", "BERRIES"), 3)
        self.assertEqual(qa.bag_pocket_right_steps("ITEMS", "KEY ITEMS"), 4)
        self.assertEqual(qa.bag_pocket_right_steps("BERRIES", "BERRIES"), 0)
        self.assertEqual(qa.bag_pocket_right_steps("BERRIES", "ITEMS"), 2)
        with self.assertRaisesRegex(qa.Blocked, "Unknown original Bag pocket"):
            qa.bag_pocket_right_steps("INJECTED", "BERRIES")

    def test_visual_reboot_title_signature_rejects_copyright_blank(self):
        # Synthetic color fractions from the independently reviewed actual
        # Emerald title vs preceding black copyright frame.
        pixels = 480 * 320
        half = 480 * 160
        # Representative title has YELLOW logo, PURPLE outlines above
        # middle, GREEN water below. Forest cutscene has no upper logo.
        title = bytearray(bytes((0, 145, 50)) * pixels)
        for index in range(int(half * .15)):
            title[index*3:index*3+3] = bytes((245, 195, 44))
        for index in range(int(half * .2)):
            offset = (index + int(half * .2)) * 3
            title[offset:offset+3] = bytes((100, 60, 180))
        score = qa.visual_title_score(title)
        self.assertTrue(score["present"])
        self.assertGreater(score["yellow"], 0.06)
        self.assertGreater(score["purple"], 0.10)
        self.assertGreater(score["green"], 0.25)
        # Actual regression: previously incorrectly accepted forest, with
        # yellow/orange character BELOW center but no logo in upper half.
        forest = bytearray(bytes((235, 245, 242)) * half
                           + bytes((40, 165, 60)) * half)
        for index in range(int(half * .10)):
            offset = (index + half) * 3
            forest[offset:offset+3] = bytes((245, 185, 40))
        self.assertFalse(qa.visual_title_score(forest)["present"])
        black = bytes((0, 0, 0)) * pixels
        self.assertFalse(qa.visual_title_score(black)["present"])
        self.assertLess(qa.pixel_distance(title, title), 1e-6)
        self.assertGreater(qa.pixel_distance(title, black), 0.1)
        # Emerald saved main menu is pale boxes over purple.
        menu = bytearray(bytes((140, 120, 240)) * pixels)
        for i in range(int(half * .6)):
            menu[i*3:i*3+3] = bytes((245, 245, 245))
        self.assertTrue(qa.visual_saved_main_menu(menu)["present"])
        self.assertFalse(qa.visual_saved_main_menu(title)["present"])
        self.assertFalse(qa.visual_saved_main_menu(forest)["present"])
        with self.assertRaisesRegex(qa.Blocked, "exact emulator framebuffer"):
            qa.visual_title_score(b"tiny")

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

    def test_original_gym_whiteout_candidate_preserves_source_route(self):
        # Independent fixture CONTRACT, not a gameplay whiteout PASS:
        # all paths are existing engine files. Actual movement/battle must
        # still be performed and visually checked.
        base = Path(__file__).resolve().parents[2] / "engine"
        blockdata = (base / "data/layouts/AlderfieldGym/map.bin").read_bytes()
        self.assertEqual(len(blockdata), 9 * 16 * 2)
        def original_metatile(x, y):
            return struct.unpack_from("<H", blockdata, 2*(y*9+x))[0] & 0x3ff
        gym_map = json.loads((base / "data/maps/AlderfieldGym/map.json").read_text())
        self.assertEqual((gym_map["warp_events"][0]["x"],
                          gym_map["warp_events"][0]["y"]), (4, 15))
        self.assertEqual(original_metatile(4, 14), 513) # true floor after warp0
        self.assertEqual(original_metatile(2, 13), 513) # western sluice face-up
        self.assertEqual(original_metatile(6, 13), 513) # eastern sluice face-up
        self.assertEqual(original_metatile(4, 9), 548)  # genuine blocked leader gate
        self.assertEqual(original_metatile(4, 5), 513)  # Elio adjacency
        script = (base / "data/maps/AlderfieldGym/scripts.inc").read_text()
        self.assertIn("trainerbattle_no_intro TRAINER_AVERON_ELIO", script)
        self.assertIn("setflag FLAG_AVERON_WEST_SLUICE", script)
        self.assertIn("setflag FLAG_AVERON_EAST_SLUICE", script)
        self.assertIn("setflag FLAG_BADGE01_GET", script)
        trainer = (base / "src/data/trainers.party").read_text()
        elio = trainer.split("=== TRAINER_AVERON_ELIO ===", 1)[1].split(
            "===",1)[0]
        self.assertIn("Bunnelby\nLevel: 12", elio)
        self.assertIn("Lechonk\nLevel: 13", elio)
        self.assertIn("Lillipup @ Oran Berry\nLevel: 15", elio)

    def test_original_gym_sluice_flags_read_only(self):
        header = struct.pack("<hhbbbxhh", 4, 15, 75, 10, 0, -1, -1)
        gdb, commands = self.fake(header)
        old = gdb.command
        def reply(q, reply=True):
            if q in ("m2001374,1", "m200147c,1"):
                commands.append(q)
                return "60" if q == "m2001374,1" else "00"
            return old(q, reply)
        gdb.command = reply
        data = gdb.position(0x03000100, 0x03000104,
                            badge_probe=True, gym_probe=True)
        self.assertTrue(data["gymWestSluice"])
        self.assertTrue(data["gymEastSluice"])
        self.assertFalse(data["badge01"])
        self.assertIn("m2001374,1", commands)
        self.assertIn("m200147c,1", commands)

    def test_real_badge01_source_flag_read_only(self):
        header = struct.pack("<hhbbbxhh", 37, 16, 75, 9, -1, -1, -1)
        gdb, observed = self.fake(header)
        orig = gdb.command
        def reply(q, reply=True):
            if q == "m200147c,1":
                observed.append(q)
                return "80"
            return orig(q, reply)
        gdb.command = reply
        result = gdb.position(0x03000100, 0x03000104,
                              badge_probe=True)
        self.assertTrue(result["badge01"])
        self.assertIn("m200147c,1", observed)

    def test_missing_badge01_flag_rejected_without_faking_source(self):
        header = struct.pack("<hhbbbxhh", 37, 16, 75, 9, -1, -1, -1)
        gdb, observed = self.fake(header)
        orig = gdb.command
        gdb.command = lambda q, reply=True: (
            "00" if q == "m200147c,1" else orig(q, reply))
        result = gdb.position(0x03000100, 0x03000104,
                              badge_probe=True)
        self.assertFalse(result["badge01"])

    def test_existing_lab_land_corridor_is_source_backed(self):
        # This is a read-only contract against original lab blockdata,
        # not a new map or gameplay modification.
        layout = (Path(__file__).resolve().parents[2]
                  / "engine/data/layouts/AveronFieldLab/map.bin")
        raw = layout.read_bytes()
        self.assertEqual(len(raw), 28*22*2)
        def metatile(x,y):
            return struct.unpack_from("<H", raw, 2*(y*28+x))[0] & 0x3ff
        self.assertEqual(metatile(24,5), 161)  # real impassable water
        self.assertEqual(metatile(25,5), 1)    # adjacent land corridor
        self.assertEqual(metatile(25,18), 1)   # land south of water
        self.assertEqual(metatile(24,18), 1)   # west of gift scientist
        self.assertEqual(metatile(24,19), 1)   # tested adjacency tile

    def test_gift_source_flag_and_player_party_read_only(self):
        header = struct.pack("<hhbbbxhh", 24, 19, 75, 14, -1, -1, -1)
        gdb, commands = self.fake(header)
        old = gdb.command
        def reply(cmd, reply=True):
            if cmd in ("m2001376,1", "m3000108,1"):
                commands.append(cmd)
                return "80" if cmd.startswith("m200") else "02"
            return old(cmd, reply)
        gdb.command = reply
        state = gdb.position(0x03000100, 0x03000104,
                             parties_count_symbol=0x03000108)
        self.assertEqual(state["playerPartyCount"], 2)
        self.assertTrue(state["devGiftReceived"])
        self.assertIn("m2001376,1", commands)
        self.assertIn("m3000108,1", commands)
        self.assertEqual(gdb.sock.sent, [bytes([3])])

    def test_gift_rejects_invalid_six_slot_party_count(self):
        header = struct.pack("<hhbbbxhh", 24, 19, 75, 14, -1, -1, -1)
        gdb, commands = self.fake(header)
        old = gdb.command
        def reply(cmd, reply=True):
            if cmd in ("m2001376,1", "m3000108,1"):
                return "80" if cmd.startswith("m200") else "07"
            return old(cmd, reply)
        gdb.command = reply
        with self.assertRaisesRegex(qa.Blocked, "Invalid actual party count"):
            gdb.position(0x03000100, 0x03000104,
                         parties_count_symbol=0x03000108)

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
