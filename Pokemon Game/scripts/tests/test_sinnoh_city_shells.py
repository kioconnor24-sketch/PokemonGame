"""W12 neutral building shells: append-only overlays, one reciprocal LAYOUT_HOUSE1 shell per warp-less door."""
import importlib.util
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/city-shells"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("city_shells", HERE / "build_city_shells.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class CityShellsTest(unittest.TestCase):
    def setUp(self):
        self.overlays, self.shells, self.bins = b.build(ENGINE)

    def test_staged_matches_fresh_build(self):
        for name, hdr in self.overlays.items():
            self.assertEqual(json.loads((HERE / "staged" / f"{name}-dev-overlay/map.json").read_text()), hdr)
        for name, hdr in self.shells.items():
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)
        for name, cells in self.bins.items():
            self.assertEqual((HERE / "staged" / f"{name}-dev-overlay/map.bin").read_bytes(),
                             struct.pack("<%dH" % len(cells), *cells))

    def test_overlays_append_only_and_every_warp_reciprocal(self):
        by_id = {h["id"]: h for h in self.shells.values()}
        entered = set()
        for family, name, prefix, _ in b.TARGETS:
            source = json.loads((b.SINNOH / family / "staged" / name / "map.json").read_text())
            hdr = self.overlays[name]
            by_id[prefix] = hdr
            n = len(source["warp_events"])
            self.assertEqual(hdr["warp_events"][:n], source["warp_events"])
            self.assertEqual({k: v for k, v in hdr.items() if k != "warp_events"},
                             {k: v for k, v in source.items() if k != "warp_events"})
            for w in hdr["warp_events"][n:]:
                entered.add(w["dest_map"])
                civic = b.CIVIC.get((name, (w["x"], w["y"])))
                layout = by_id[w["dest_map"]]["layout"]
                self.assertEqual(layout, "LAYOUT_HOUSE1" if civic is None else
                                 json.loads((ENGINE / f"data/maps/{civic[0][1]}/map.json").read_text())["layout"])
        for mid, h in by_id.items():                  # every warp lands on a warp that leads back
            for w in h["warp_events"]:
                if w["dest_map"] in by_id:
                    back = by_id[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                    self.assertEqual(back["dest_map"], mid, (mid, w))
        floors = {b.const(n) for fl in b.CIVIC.values() for n, _ in fl[1:]}
        self.assertEqual(entered | floors, set(h["id"] for h in self.shells.values()))

    def test_civic_floors_copy_the_stock_stairs(self):
        for floors in b.CIVIC.values():
            for n, stock in floors:
                src = json.loads((ENGINE / f"data/maps/{stock}/map.json").read_text())
                got = [(w["x"], w["y"]) for w in self.shells[n]["warp_events"]]
                self.assertTrue(set(got) <= {(w["x"], w["y"]) for w in src["warp_events"]}, n)
                dropped = [w for w in src["warp_events"] if (w["x"], w["y"]) not in got]
                self.assertTrue(all("ELEVATOR" in w["dest_map"] or "_2F" in w["dest_map"] for w in dropped), n)

    def test_veilstone_opens_one_door_picture(self):
        width, src = b.map_bin("eastern-loop", "VeilstoneCity")
        got = self.bins["VeilstoneCity"]
        self.assertEqual([(i % width, i // width) for i, (a, c) in enumerate(zip(src, got)) if a != c], [(18, 10)])
        self.assertEqual(got[10 * width + 18], src[14 * width + 41])

    def test_solaceon_opens_its_door_picture_with_the_family_door(self):
        width, src = b.map_bin("hearthome-solaceon", "SolaceonTown")
        got = self.bins["SolaceonTown"]
        self.assertEqual([(i % width, i // width) for i, (a, c) in enumerate(zip(src, got)) if a != c], [(11, 11)])
        dwidth, donor = b.map_bin("hearthome-solaceon", "Route210_South")
        self.assertEqual(got[11 * width + 11], donor[47 * dwidth + 30])
        self.assertIn("MAP_SOLACEON_TOWN_HOUSE3", {w["dest_map"] for w in self.overlays["SolaceonTown"]["warp_events"]})

    def test_a_donor_door_with_other_surroundings_is_refused(self):
        saved = dict(b.OPEN)
        try:
            b.OPEN["SolaceonTown"] = {(11, 11): ("HearthomeCity", (14, 19))}     # a door between other pieces
            with self.assertRaises(AssertionError):
                b.opened(ENGINE, "hearthome-solaceon", "SolaceonTown")
        finally:
            b.OPEN.clear()
            b.OPEN.update(saved)

    def test_no_door_left_closed(self):
        for family, name, _, _ in b.TARGETS:
            hdr, doors = b.closed_doors(ENGINE, family, name)
            added = {(w["x"], w["y"]) for w in self.overlays[name]["warp_events"]}
            self.assertLessEqual(set(doors), added)


if __name__ == "__main__":
    unittest.main()
