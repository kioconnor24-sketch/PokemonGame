"""W10 Great Marsh staging: reproducible, attested ponds, reachable closed marsh, reciprocal Pastoria-gate-marsh."""
import importlib.util
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/great-marsh"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("great_marsh", HERE / "build_great_marsh.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
ti = importlib.util.spec_from_file_location("w1_tests", ROOT / "scripts/tests/test_sinnoh_iron_island.py")
t = importlib.util.module_from_spec(ti)
ti.loader.exec_module(t)


class GreatMarshTest(unittest.TestCase):
    def setUp(self):
        self.eng, self.cells, self.marsh, self.gate, self.past, self.door = b.build(ENGINE)

    def test_staged_matches_fresh_build(self):
        self.assertEqual((HERE / "staged/GreatMarsh/map.bin").read_bytes(), struct.pack("<%dH" % len(self.cells), *self.cells))
        for name, hdr in (("GreatMarsh", self.marsh), ("GreatMarsh_Gate", self.gate)):
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)

    def test_words_attested(self):
        known = set(self.eng.cells("LakeVerity")[2]) | set(self.eng.cells("DewfordTown")[2])
        self.assertFalse(set(self.cells) - known)

    def test_marsh_reachable_and_closed(self):
        beh = t.behaviours("general", "dewford")
        x, y = self.door
        got = t.reach(self.cells, b.W, beh, (x, y + 1))
        self.assertGreater(len(got), 600)
        for x0, y0, x1, y1 in b.PONDS:                      # every pond is reachable along its shore
            self.assertTrue(any((x, y1 + 1) in got for x in range(x0, x1 + 1)))
        self.assertFalse({p for p in got if p[0] in (0, b.W - 1) or p[1] in (0, b.H - 1)})

    def test_pastoria_gate_marsh_reciprocal(self):
        source = json.loads((b.PASTORIA / "map.json").read_text())
        n = len(source["warp_events"])
        self.assertEqual(self.past["warp_events"][:n], source["warp_events"])
        self.assertEqual(self.past["warp_events"][n]["dest_map"], "MAP_GREAT_MARSH_GATE")
        g = [(w["dest_map"], int(w["dest_warp_id"])) for w in self.gate["warp_events"]]
        self.assertEqual(g, [("MAP_PASTORIA_CITY", n)] * 2 + [("MAP_GREAT_MARSH", 0)] * 2)
        self.assertEqual(self.marsh["warp_events"][0]["dest_map"], "MAP_GREAT_MARSH_GATE")


if __name__ == "__main__":
    unittest.main()
