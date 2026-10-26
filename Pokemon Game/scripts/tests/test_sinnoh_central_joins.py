"""W24 central donor joins: staging equals a fresh build; joins reciprocal; only matching Codex closures reopen."""
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/central-joins"
spec = importlib.util.spec_from_file_location("w24", HERE / "build_central_joins.py")
w24 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w24)


class CentralJoinsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maps = w24.build()

    def test_committed_staging_equals_a_fresh_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            w24.write(tmp)
            fresh = sorted(p.relative_to(tmp) for p in pathlib.Path(tmp).rglob("*") if p.is_file())
            committed = sorted(p.relative_to(HERE) for p in HERE.rglob("*") if p.is_file() and p.suffix != ".py"
                               and "__pycache__" not in p.parts and p.name != "CHECKPOINT.md")
            self.assertEqual(fresh, committed)
            for rel in fresh:
                self.assertEqual((pathlib.Path(tmp) / rel).read_bytes(), (HERE / rel).read_bytes(), rel)

    def test_joins_are_reciprocal(self):
        self.assertTrue(w24.check(self.maps))

    def test_codex_headers_only_gain_appended_warps_and_connections(self):
        for name, m in self.maps.items():
            src = json.loads((w24.SINNOH / w24.FAMILY[name] / "staged" / name / "map.json").read_text())
            self.assertEqual(m.header["warp_events"][:len(src["warp_events"])], src["warp_events"])
            self.assertEqual((m.header["connections"] or [])[:len(src["connections"] or [])], src["connections"] or [])
            self.assertEqual({k: v for k, v in m.header.items() if k not in ("warp_events", "connections")},
                             {k: v for k, v in src.items() if k not in ("warp_events", "connections")})

    def test_only_codex_closures_with_walkable_sources_reopen(self):
        for name, m in self.maps.items():
            for i, (a, b) in enumerate(zip(m.cells, m.blocks)):
                if a != b:
                    xy = (i % m.width, i // m.width)
                    self.assertIn(xy, m.closed, (name, xy))
                    self.assertEqual(a ^ b, a & 0xC00, (name, xy))
                    self.assertFalse((m.closed[xy] >> 10) & 3, (name, xy))

    def test_edge_reopenings_face_each_other(self):
        reopened = {n: {(i % m.width, i // m.width) for i, (a, b) in enumerate(zip(m.cells, m.blocks)) if a != b}
                    for n, m in self.maps.items()}
        self.assertEqual(sorted(x for x, y in reopened["Route210_South"] if y == 0), [26, 27, 28, 29])
        self.assertEqual(sorted(x for x, y in reopened["Route210_North"]), [83, 84, 85, 86])
        self.assertEqual(sorted(y for x, y in reopened["Route210_South"] if x == 41), list(range(48, 57)))
        self.assertEqual(sorted(y for x, y in reopened["Route215"]), list(range(22, 31)))

    def test_hearthome_gate_warps_follow_the_donor(self):
        h, a = self.maps["HearthomeCity"].header, self.maps["Route212_Access"].header
        gate = [w for w in h["warp_events"] if w["dest_map"] == "MAP_ROUTE212_ACCESS"]
        self.assertEqual([(w["x"], w["y"]) for w in gate], [(8, 46), (9, 46)])
        back = a["warp_events"][int(gate[0]["dest_warp_id"])]
        self.assertEqual((back["x"], back["y"], back["dest_map"]), (4, 1, "MAP_HEARTHOME_CITY"))

    def test_coronet_west_entrance_follows_the_donor(self):
        w, r = self.maps["Route211_West"].header, self.maps["MtCoronet_1F_North_Room1"].header
        self.assertEqual([(x["x"], x["y"], x["dest_map"]) for x in w["warp_events"]],
                         [(29, 8, "MAP_MT_CORONET_1F_NORTH_ROOM1")])
        back = r["warp_events"][int(w["warp_events"][0]["dest_warp_id"])]
        self.assertEqual((back["x"], back["y"], back["dest_map"]), (3, 33, "MAP_ROUTE211_WEST"))


if __name__ == "__main__":
    unittest.main()
