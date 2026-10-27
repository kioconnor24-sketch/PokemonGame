"""W23 Eterna Forest south tunnel: staging equals a fresh build; donor warps reciprocal; only the tunnel/mouth reopen."""
import importlib.util
import json
import pathlib
import struct
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/eterna-forest-gate"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("w23", HERE / "build_eterna_forest_gate.py")
w23 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w23)


def cells(raw):
    return struct.unpack("<%dH" % (len(raw) // 2), raw)


class EternaForestTunnelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.route, cls.forest, cls.house, cls.route_blocks, cls.forest_blocks, _ = w23.build(ENGINE)

    def test_committed_staging_equals_a_fresh_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            w23.write(ENGINE, tmp)
            fresh = sorted(p.relative_to(tmp) for p in pathlib.Path(tmp).rglob("*") if p.is_file())
            committed = sorted(p.relative_to(HERE) for p in HERE.rglob("*") if p.is_file() and p.suffix != ".py"
                               and "__pycache__" not in p.parts and p.name != "CHECKPOINT.md")
            self.assertEqual(fresh, committed)
            for rel in fresh:
                self.assertEqual((pathlib.Path(tmp) / rel).read_bytes(), (HERE / rel).read_bytes(), rel)

    def test_donor_warps_in_donor_order(self):
        self.assertEqual([(w["x"], w["y"], w["dest_map"]) for w in self.route["warp_events"]],
                         [(14, 12, "MAP_ETERNA_FOREST"), (15, 12, "MAP_ETERNA_FOREST"),
                          (21, 22, "MAP_ROUTE205_SOUTH_HOUSE")])
        source = json.loads((w23.FOREST / "staged/EternaForest/map.json").read_text())
        self.assertEqual(self.forest["warp_events"][:len(source["warp_events"])], source["warp_events"])
        self.assertEqual([(w["x"], w["y"], w["dest_warp_id"]) for w in self.forest["warp_events"][-2:]],
                         [(16, 80, "0"), (17, 80, "1")])

    def test_every_warp_is_reciprocal(self):
        self.assertTrue(w23.check(self.route, self.forest, self.house))

    def test_each_tunnel_warp_has_a_trigger_that_takes_it(self):
        # The tunnel floor is plain grass: without a coord trigger the engine never takes the warp (mGBA W23 gate).
        triggers = {(c["x"], c["y"]): c["script"] for c in self.route["coord_events"]}
        script = w23.portal_script(self.route)
        for w in self.route["warp_events"][:2]:
            label = triggers[(w["x"], w["y"])]
            self.assertIn(f"{label}::\n\twarp {w['dest_map']}, {w['dest_warp_id']}\n", script)

    def test_house_is_a_neutral_shell(self):
        self.assertEqual(self.house["layout"], "LAYOUT_HOUSE1")
        self.assertEqual((self.house["object_events"], self.house["coord_events"], self.house["bg_events"]),
                         ([], [], []))

    def test_route_changes_only_the_tunnel_and_keeps_elevations(self):
        before = cells((ENGINE / "data/layouts/Route205_South/map.bin").read_bytes())
        changed = {(i % 32, i // 32) for i, (a, b) in enumerate(zip(before, self.route_blocks)) if a != b}
        self.assertTrue(changed <= set(w23.TUNNEL_ART))
        for i, (a, b) in enumerate(zip(before, self.route_blocks)):
            self.assertEqual(a >> 12, b >> 12, i)
        walkable = {(i % 32, i // 32) for i, b in enumerate(self.route_blocks) if not (b >> 10) & 3
                    and (i % 32, i // 32) in w23.TUNNEL_ART}
        self.assertEqual(walkable, set(w23.FLOOR))

    def test_forest_changes_only_the_two_mouth_cells(self):
        raw = (w23.FOREST / "staged/EternaForest/averon-map.bin").read_bytes()
        changed = [(i % 82, i // 82, a ^ b) for i, (a, b) in enumerate(zip(cells(raw), self.forest_blocks)) if a != b]
        self.assertEqual([(x, y) for x, y, _ in changed], [(16, 80), (17, 80)])
        self.assertTrue(all(delta & ~0xC00 == 0 for _, _, delta in changed))

    def test_an_unexpected_route_tunnel_is_refused(self):
        orig = w23.route_inputs
        try:
            def tampered(engine):
                hdr, route_cells, hashes = orig(engine)
                route_cells[12 * 32 + 14] &= ~0xC00              # already open: not the production seal
                return hdr, route_cells, hashes
            w23.route_inputs = tampered
            with self.assertRaises(AssertionError):
                w23.build(ENGINE)
        finally:
            w23.route_inputs = orig


if __name__ == "__main__":
    unittest.main()
