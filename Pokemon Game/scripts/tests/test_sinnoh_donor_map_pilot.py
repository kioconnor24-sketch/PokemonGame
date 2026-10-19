"""Isolated host tests for source-pinned, fail-closed Sinnoh donor map staging."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "sinnoh-donor-map-pilot.py"
spec = importlib.util.spec_from_file_location("sinnoh_donor_pilot", SCRIPT)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class DonorPilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.donor = self.root / "donor"
        (self.donor / "data/maps/Route202").mkdir(parents=True)
        (self.donor / "data/layouts/Route202").mkdir(parents=True)
        header = {
            "id": "MAP_ROUTE202", "layout": "LAYOUT_ROUTE202",
            "object_events": [{"script": "STORY_SCRIPT_NEVER_IMPORT"}],
            "warp_events": [{"map": "SANDGEM"}],
            "connections": [{"map": "MAP_SANDGEM_TOWN", "direction": "down", "offset": -2}],
        }
        layout = {
            "id": "LAYOUT_ROUTE202", "width": 3, "height": 2,
            "primary_tileset": "gTileset_General",
            "secondary_tileset": "gTileset_Petalburg",
            "blockdata_filepath": "data/layouts/Route202/map.bin",
        }
        self.blocks = [0x3400 | 0, 0x5400 | 512, 0x7400 | 1,
                       0x1400 | 1, 0x2400 | 0, 0x8400 | 512]
        (self.donor / "data/maps/Route202/map.json").write_text(json.dumps(header))
        (self.donor / "data/layouts/layouts.json").write_text(json.dumps({"layouts": [layout]}))
        self.binary = self.donor / "data/layouts/Route202/map.bin"
        self.binary.write_bytes(struct.pack("<6H", *self.blocks))
        self.revision = "a" * 40
        self.audit = pilot.analyze(self.donor, "Route202", self.revision)
        self.manifest = pilot.draft_manifest(self.audit)
        self.manifest.update({
            "target_map_id": "MAP_ROUTE202",
            "target_primary_tileset": "gTileset_General",
            "target_secondary_tileset": "gTileset_Petalburg",
        })
        for original, target in [(0, 4), (1, 6), (512, 518)]:
            self.manifest["metatiles"][str(original)] = {
                "target": target, "behavior_verified": True, "graphics_verified": True,
            }
        self.output = self.root / "scratch/map.bin"

    def test_inspect_has_geometry_and_event_counts_only(self):
        a = self.audit
        self.assertEqual(a["dimensions"], [3, 2])
        self.assertEqual(a["source_map_id"], "MAP_ROUTE202")
        self.assertEqual(a["event_counts"]["object_events"], 1)
        self.assertEqual(a["connection_count"], 1)
        self.assertEqual(a["metatile_frequency"], {"0": 2, "512": 2, "1": 2})
        self.assertIn("block_sha256", a)

    def test_manifest_defaults_to_unverified(self):
        m = pilot.draft_manifest(self.audit)
        self.assertIsNone(m["target_map_id"])
        for entry in m["metatiles"].values():
            self.assertIsNone(entry["target"])
            self.assertFalse(entry["behavior_verified"])
            self.assertFalse(entry["graphics_verified"])

    def test_convert_only_remaps_lower_ten_bits(self):
        receipt = pilot.convert(self.donor, "Route202", self.manifest, self.output)
        self.assertEqual(receipt["status"], "STAGED_NOT_INTEGRATED_OR_PLAYTESTED")
        result = struct.unpack("<6H", self.output.read_bytes())
        self.assertEqual([v & 1023 for v in result], [4, 518, 6, 6, 4, 518])
        self.assertEqual([v & 0xFC00 for v in result],
                         [v & 0xFC00 for v in self.blocks])
        self.assertTrue(self.output.with_suffix(".receipt.json").exists())
        receipt_raw = self.output.with_suffix(".receipt.json").read_text()
        self.assertNotIn("STORY_SCRIPT_NEVER_IMPORT", receipt_raw)
        self.assertEqual(receipt["mapped_unique_metatiles"], 3)

    def test_missing_mapping_refused(self):
        m = copy.deepcopy(self.manifest)
        del m["metatiles"]["512"]
        with self.assertRaisesRegex(ValueError, "unmapped"):
            pilot.convert(self.donor, "Route202", m, self.output)
        self.assertFalse(self.output.exists())

    def test_unverified_behavior_refused(self):
        m = copy.deepcopy(self.manifest)
        m["metatiles"]["1"]["behavior_verified"] = False
        with self.assertRaisesRegex(ValueError, "unverified"):
            pilot.convert(self.donor, "Route202", m, self.output)

    def test_unverified_graphics_refused(self):
        m = copy.deepcopy(self.manifest)
        m["metatiles"]["1"]["graphics_verified"] = False
        with self.assertRaisesRegex(ValueError, "unverified"):
            pilot.convert(self.donor, "Route202", m, self.output)

    def test_cross_bank_refused(self):
        m = copy.deepcopy(self.manifest)
        m["metatiles"]["1"]["target"] = 600
        with self.assertRaisesRegex(ValueError, "crosses"):
            pilot.convert(self.donor, "Route202", m, self.output)

    def test_wrong_sha_refused(self):
        m = copy.deepcopy(self.manifest)
        m["block_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "blob hash"):
            pilot.convert(self.donor, "Route202", m, self.output)

    def test_wrong_source_and_layout_refused(self):
        for key in ("source_map", "source_map_id", "source_layout_id"):
            m = copy.deepcopy(self.manifest)
            m[key] = "OTHER"
            with self.assertRaises(ValueError):
                pilot.convert(self.donor, "Route202", m, self.output)

    def test_bad_dimensions_refused(self):
        self.binary.write_bytes(self.binary.read_bytes()[:-2])
        with self.assertRaisesRegex(ValueError, "length"):
            pilot.read_donor_map(self.donor, "Route202")

    def test_no_overwrite(self):
        pilot.convert(self.donor, "Route202", self.manifest, self.output)
        with self.assertRaises(FileExistsError):
            pilot.convert(self.donor, "Route202", self.manifest, self.output)

    def test_reject_in_engine_output(self):
        with self.assertRaisesRegex(ValueError, "off-engine"):
            pilot.convert(self.donor, "Route202", self.manifest,
                          self.root / "engine/data/layouts/map.bin")

    def test_path_escape_refused(self):
        layout_file = self.donor / "data/layouts/layouts.json"
        original = json.loads(layout_file.read_text())
        original["layouts"][0]["blockdata_filepath"] = "../../../../outside.bin"
        layout_file.write_text(json.dumps(original))
        with self.assertRaisesRegex(ValueError, "escapes"):
            pilot.read_donor_map(self.donor, "Route202")

    def test_oversized_buffer_refused(self):
        layout_file = self.donor / "data/layouts/layouts.json"
        info = json.loads(layout_file.read_text())
        info["layouts"][0]["width"], info["layouts"][0]["height"] = 100, 76
        layout_file.write_text(json.dumps(info))
        self.binary.write_bytes(struct.pack("<7600H", *([0] * 7600)))
        a = pilot.analyze(self.donor, "Route202", self.revision)
        m = pilot.draft_manifest(a)
        m.update({
            "target_map_id": "MAP_ROUTE202",
            "target_primary_tileset": "gTileset_General",
            "target_secondary_tileset": "gTileset_Petalburg",
            "metatiles": {
                "0": {"target": 0, "behavior_verified": True, "graphics_verified": True}
            },
        })
        with self.assertRaisesRegex(ValueError, "field buffer"):
            pilot.convert(self.donor, "Route202", m, self.output)

    def test_inspect_cli_generates_unverified_template(self):
        template = self.root / "scratch/template.json"
        with contextlib.redirect_stdout(io.StringIO()) as out:
            pilot.main(["inspect", "--donor-root", str(self.donor), "--map", "Route202",
                        "--donor-revision", self.revision, "--template-out", str(template)])
        self.assertIn("SOURCE_ANALYSIS_ONLY", out.getvalue())
        self.assertFalse(json.loads(template.read_text())["metatiles"]["0"]["graphics_verified"])


if __name__ == "__main__":
    unittest.main()
