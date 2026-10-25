"""W8 Lost Tower staging: Mt. Pyre stair graph copied exactly and reciprocal; one-portal Route 209 overlay."""
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/lost-tower"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("lost_tower", HERE / "build_lost_tower.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class LostTowerTest(unittest.TestCase):
    def setUp(self):
        self.maps, self.r209, self.script = b.build(ENGINE)

    def test_staged_matches_fresh_build(self):
        for name, hdr in self.maps.items():
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)
        self.assertEqual(json.loads((HERE / "staged/Route209-dev-overlay/map.json").read_text()), self.r209)

    def test_graph_is_mt_pyre_renamed(self):
        for f in b.FLOORS:
            src = json.loads((ENGINE / f"data/maps/MtPyre_{f}/map.json").read_text())["warp_events"]
            got = self.maps[f"LostTower_{f}"]["warp_events"]
            self.assertEqual([(w["x"], w["y"]) for w in src], [(w["x"], w["y"]) for w in got])
            for s, g in zip(src, got):
                if s["dest_map"] not in b.EXTERIOR:
                    self.assertEqual(g["dest_map"], s["dest_map"].replace("MT_PYRE", "LOST_TOWER"))
                    self.assertEqual(g["dest_warp_id"], s["dest_warp_id"])

    def test_every_tower_warp_lands_on_a_warp_back_to_its_floor(self):
        by_id = {h["id"]: h for h in self.maps.values()}
        for mid, h in by_id.items():
            for w in h["warp_events"]:
                if w["dest_map"] == "MAP_ROUTE209":
                    self.assertEqual(int(w["dest_warp_id"]), len(self.r209["warp_events"]) - 1)
                    continue
                target = by_id[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                self.assertIn(target["dest_map"], (mid,), (mid, w))

    def test_route209_overlay_adds_one_portal(self):
        source = json.loads((b.ROUTE209 / "map.json").read_text())
        self.assertEqual(self.r209["warp_events"][:-1], source["warp_events"])
        self.assertEqual(len(self.r209["coord_events"]) - len(source.get("coord_events") or []), 1)
        w, c = self.r209["warp_events"][-1], self.r209["coord_events"][-1]
        self.assertEqual((w["x"], w["y"]), (c["x"], c["y"]))                 # step-on portal: warp + trigger
        self.assertIn("warp MAP_LOST_TOWER_1F, 0", self.script)


if __name__ == "__main__":
    unittest.main()
