"""Isolated boundaries of the preserved North converter; no production maps/IDs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[2]
HERE = PROJECT / "Averon_Codex_Handoff/design/sinnoh/route205-donor"
spec = importlib.util.spec_from_file_location("north", HERE / "build_route205n.py")
north = importlib.util.module_from_spec(spec)
spec.loader.exec_module(north)
spec = importlib.util.spec_from_file_location("connected_scratch", HERE / "prepare_connected_scratch.py")
scratch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scratch)


class NorthConversionTests(unittest.TestCase):
    def fixture(self):
        cells = [0x3001] * (north.W * north.H)
        for x, y in north.SIGNS:
            cells[y * north.W + x] = 0x3403
        return cells

    def convert(self, cells, *, blob=None, width=None):
        raw = struct.pack("<%dH" % len(cells), *cells)
        header = {"warp_events": [{"x": 44, "y": 10, "dest_map": "MAP_ETERNAL_FOREST"}]}
        layout = {"width": width or north.W, "height": north.H}
        expected_blob = hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()
        # A real synthetic blob pin: invalid bytes/dimensions remain rejected.
        with patch.object(north, "BLOB", blob or expected_blob), patch.object(
                north.pilot, "read_donor_map", return_value=(header, layout, raw, tuple(cells))):
            return north.convert(Path("unused-synthetic-root"))

    def test_walkway_keeps_all_collision_and_elevation_combinations(self):
        cells = self.fixture()
        indices = []
        for tile in north.WALKWAY:
            for bits in range(64):
                i = len(indices)
                cells[i] = (bits << 10) | tile
                indices.append(i)
        data, _ = self.convert(cells)
        result = struct.unpack("<%dH" % len(cells), data)
        for i in indices:
            self.assertEqual(result[i] & 0xFC00, cells[i] & 0xFC00)
            self.assertLess(result[i] & 1023, 512)
        # These replacement path metatiles really have NORMAL movement behavior.
        attrs = (PROJECT / "engine/data/tilesets/primary/general/metatile_attributes.bin").read_bytes()
        for tile in north.WALKWAY.values():
            self.assertEqual(struct.unpack_from("<H", attrs, tile * 2)[0] & 0xFF, 0)

    def test_cliff_edges_preserve_elevation_and_distinguish_solid_from_floor(self):
        cells = self.fixture()
        for i, bits in enumerate(range(64)):
            cells[i] = (bits << 10) | 516
        data, _ = self.convert(cells)
        result = struct.unpack("<%dH" % len(cells), data)
        for bits in range(64):
            self.assertEqual(result[bits] & 0xFC00, bits << 10)
            self.assertEqual(result[bits] & 1023, 137 if bits & 3 else 268)

    def test_only_unbuilt_gatehouse_changes_collision_and_removes_its_warps(self):
        cells = self.fixture()
        for x, y in north.GATEHOUSE:
            cells[y * north.W + x] = 0x4001
        data, receipt = self.convert(cells)
        result = struct.unpack("<%dH" % len(cells), data)
        changed = {i for i, (a, b) in enumerate(zip(cells, result)) if (a ^ b) & 0xFC00}
        self.assertEqual(changed, {y * north.W + x for x, y in north.GATEHOUSE})
        for i in changed:
            self.assertEqual(result[i] >> 12, cells[i] >> 12)
            self.assertEqual((result[i] >> 10) & 3, 1)
        self.assertEqual(len(receipt["excluded_donor_warps"]), 1)

    def test_unknown_secondary_never_silently_becomes_a_primary_tile(self):
        cells = self.fixture()
        cells[0] = 0x3000 | 841
        with self.assertRaises(AssertionError):
            self.convert(cells)

    def test_wrong_blob_or_dimensions_are_rejected(self):
        with self.assertRaises(AssertionError):
            self.convert(self.fixture(), blob="0" * 40)
        with self.assertRaises(AssertionError):
            self.convert(self.fixture(), width=79)

    def test_neutral_headers_keep_pending_identity_and_exclude_source_gameplay(self):
        header, scripts = north.headers(north.PENDING)
        header = json.loads(header)
        self.assertEqual(header["region_map_section"], "MAPSEC_PENDING_OWNER")
        self.assertEqual(header["connections"], [
            {"map": "MAP_ROUTE205_SOUTH", "offset": -20, "direction": "down"}])
        for name in ("object_events", "warp_events", "coord_events"):
            self.assertEqual(header[name], [])
        self.assertNotIn("wildbattle", scripts)
        self.assertNotIn("setflag", scripts)

    def test_preserved_north_has_no_unmapped_bank_or_open_gatehouse(self):
        data = (HERE / "staged/Route205_North.bin").read_bytes()
        self.assertEqual(len(data), 2 * north.W * north.H)
        cells = struct.unpack("<%dH" % (north.W * north.H), data)
        self.assertTrue(all((c & 1023) < 512 for c in cells))
        for x, y in north.GATEHOUSE:
            self.assertEqual((cells[y * north.W + x] >> 10) & 3, 1)
        receipt = json.loads((HERE / "route205n-convert-receipt.json").read_text())
        self.assertEqual(hashlib.sha256(data).hexdigest(), receipt["output_sha256"])

    def test_preserved_north_south_seam_is_reciprocal(self):
        north_header = json.loads((HERE / "staged/Route205_North/map.json").read_text())
        south_header = json.loads((HERE / "staged/Route205_South/map.json").read_text())
        down = next(c for c in north_header["connections"] if c["direction"] == "down")
        up = next(c for c in south_header["connections"] if c["direction"] == "up")
        self.assertEqual(down["map"], "MAP_ROUTE205_SOUTH")
        self.assertEqual(up["map"], "MAP_ROUTE205_NORTH")
        self.assertEqual(down["offset"], -up["offset"])
        self.assertEqual(down["offset"], -20)

    def test_connected_helper_refuses_production_branches_without_writes(self):
        with tempfile.TemporaryDirectory() as root:
            repo = Path(root)
            engine = repo / "Pokemon Game/engine"
            engine.mkdir(parents=True)
            (engine / ".map_qa_throwaway").touch()
            with patch.object(scratch.subprocess, "check_output", return_value="main\n"):
                with self.assertRaisesRegex(ValueError, "disposable engine marker"):
                    scratch.prepare(repo)
            self.assertEqual(sorted(p.name for p in engine.iterdir()), [".map_qa_throwaway"])

    def test_connected_helper_refuses_unmarked_scratch_without_writes(self):
        with tempfile.TemporaryDirectory() as root:
            repo = Path(root)
            with patch.object(scratch.subprocess, "check_output", return_value="codex/north-scratch-fixture\n"):
                with self.assertRaisesRegex(ValueError, "disposable engine marker"):
                    scratch.prepare(repo)
            self.assertEqual(list(repo.iterdir()), [])

    def test_connected_helper_stops_before_editing_when_identity_decision_changes(self):
        with tempfile.TemporaryDirectory() as root:
            repo = Path(root)
            engine = repo / "Pokemon Game/engine"
            files = {
                ".map_qa_throwaway": "",
                "data/maps/map_groups.json": json.dumps({"gMapGroup_Sinnoh": [
                    "JubilifeCity", "Route203", "OreburghGate_1F", "LakeVerity", "VerityLakefront"]}),
                "data/layouts/layouts.json": '{"layouts": []}',
                "src/data/region_map/region_map_sections.json": json.dumps({"map_sections": [
                    {"id": "MAPSEC_ROUTE_201", "value": 217}, {"id": "MAPSEC_FIXTURE", "value": 224}]}),
            }
            for name, text in files.items():
                p = engine / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
            before = {p.relative_to(engine): p.read_bytes() for p in engine.rglob("*") if p.is_file()}
            with patch.object(scratch.subprocess, "check_output", return_value="codex/north-scratch-fixture\n"):
                with self.assertRaisesRegex(ValueError, "refresh the owner decision"):
                    scratch.prepare(repo)
            self.assertEqual(before, {p.relative_to(engine): p.read_bytes() for p in engine.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
