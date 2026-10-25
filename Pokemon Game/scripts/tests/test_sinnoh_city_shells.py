"""W12 neutral building shells: append-only overlays, one reciprocal LAYOUT_HOUSE1 shell per warp-less door."""
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/city-shells"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("city_shells", HERE / "build_city_shells.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class CityShellsTest(unittest.TestCase):
    def setUp(self):
        self.overlays, self.shells = b.build(ENGINE)

    def test_staged_matches_fresh_build(self):
        for name, hdr in self.overlays.items():
            self.assertEqual(json.loads((HERE / "staged" / f"{name}-dev-overlay/map.json").read_text()), hdr)
        for name, hdr in self.shells.items():
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)

    def test_overlays_append_only_and_shells_reciprocal(self):
        by_id = {h["id"]: h for h in self.shells.values()}
        total = 0
        for family, name, prefix, _ in b.TARGETS:
            source = json.loads((b.SINNOH / family / "staged" / name / "map.json").read_text())
            hdr = self.overlays[name]
            n = len(source["warp_events"])
            self.assertEqual(hdr["warp_events"][:n], source["warp_events"])
            self.assertEqual({k: v for k, v in hdr.items() if k != "warp_events"},
                             {k: v for k, v in source.items() if k != "warp_events"})
            for i, w in enumerate(hdr["warp_events"][n:], n):
                shell = by_id[w["dest_map"]]
                self.assertEqual(shell["layout"], "LAYOUT_HOUSE1")
                self.assertEqual({(x["dest_map"], int(x["dest_warp_id"])) for x in shell["warp_events"]}, {(prefix, i)})
                total += 1
        self.assertEqual(total, len(self.shells))

    def test_no_door_left_closed(self):
        for family, name, _, _ in b.TARGETS:
            hdr, doors = b.closed_doors(ENGINE, family, name)
            added = {(w["x"], w["y"]) for w in self.overlays[name]["warp_events"]}
            self.assertLessEqual(set(doors), added)


if __name__ == "__main__":
    unittest.main()
