"""W14 Jubilife institutional shells: every closed door opened once, stock stair graphs copied, reciprocal."""
import copy
import importlib.util
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/jubilife-shells"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("jubilife_shells", HERE / "build_jubilife_shells.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class JubilifeShellsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng, cls.maps, cls.jub, cls.blocks = b.build(ENGINE)
        cls.source = json.loads((ENGINE / "data/maps/JubilifeCity/map.json").read_text())

    def test_staged_files_match_a_fresh_build(self):
        for name, hdr in self.maps.items():
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)
            self.assertEqual((HERE / "staged" / name / "scripts.inc").read_text(), b.w1.scripts(name))
        self.assertEqual(json.loads((HERE / "staged/JubilifeCity-dev-overlay/map.json").read_text()), self.jub)
        self.assertEqual((HERE / "staged/JubilifeCity-dev-overlay/map.bin").read_bytes(),
                         struct.pack("<%dH" % len(self.blocks), *self.blocks))

    def test_hall_doors_become_enterable_and_nothing_else_changes(self):
        width, _, cells = self.eng.cells("JubilifeCity")
        changed = [(i % width, i // width) for i, (a, c) in enumerate(zip(cells, self.blocks)) if a != c]
        self.assertEqual(changed, sorted(b.SOLID_DOORS, key=lambda t: (t[1], t[0])))
        for x, y in b.SOLID_DOORS:
            old, new = cells[y * width + x], self.blocks[y * width + x]
            self.assertEqual((old & 1023, new & 1023, bool(old & 0xC00), bool(new & 0xC00)), (693, 693, True, False))

    def test_overlay_only_appends_one_warp_per_door(self):
        n = len(self.source["warp_events"])
        self.assertEqual({k: v for k, v in self.jub.items() if k != "warp_events"},
                         {k: v for k, v in self.source.items() if k != "warp_events"})
        self.assertEqual(self.jub["warp_events"][:n], self.source["warp_events"])
        added = [(w["x"], w["y"]) for w in self.jub["warp_events"][n:]]
        self.assertEqual(len(added), len(set(added)))
        self.assertEqual(b.closed_doors(self.eng, self.jub), [])               # no door left without a warp
        self.assertEqual(sorted(added), sorted(b.closed_doors(self.eng, self.source)))

    def test_stock_stair_graphs_are_copied_renamed(self):
        for name, stock, floors, _ in b.BUILDINGS:
            for f in floors:
                src = json.loads((ENGINE / f"data/maps/{stock}_{f}/map.json").read_text())
                got = self.maps[f"{name}_{f}"]
                self.assertEqual(got["layout"], src["layout"])
                self.assertEqual([(w["x"], w["y"]) for w in src["warp_events"]],
                                 [(w["x"], w["y"]) for w in got["warp_events"]])

    def test_every_warp_is_reciprocal_and_a_one_way_is_refused(self):
        self.assertTrue(b.check(self.maps, self.jub))
        maps = copy.deepcopy(self.maps)
        maps["JubilifeCity_TV_2F"]["warp_events"][0]["dest_warp_id"] = "0"     # stairs onto the street mat
        with self.assertRaises(AssertionError):
            b.check(maps, self.jub)

    def test_no_objects_services_or_sections(self):
        for hdr in self.maps.values():
            self.assertEqual(hdr["region_map_section"], "MAPSEC_PENDING_OWNER")
            self.assertEqual((hdr["object_events"], hdr["coord_events"], hdr["bg_events"]), ([], [], []))
            self.assertIn(hdr["layout"], self.eng.layout_ids)


if __name__ == "__main__":
    unittest.main()
