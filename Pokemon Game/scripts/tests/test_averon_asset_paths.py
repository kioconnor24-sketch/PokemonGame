"""Fixtures for Pokémon folder graphics and following sprite file checks."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "audit-averon-asset-paths.py"
spec = importlib.util.spec_from_file_location("averon_asset_paths", SOURCE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AssetFileTests(unittest.TestCase):
    def make_folder(self, root, name, names):
        folder = root / name
        folder.mkdir(parents=True)
        for filename in names:
            (folder / filename).write_bytes(b"fixture")
        return folder

    def test_complete_base_and_partial_form(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_folder(root, "bulbasaur", [a[0] for a in audit.EXPECTED_BASE.values()])
            self.make_folder(root, "raichu/alola", ["back.png", "icon.png"])
            report = audit.inspect(root)
            self.assertEqual(report["counts"]["asset_directories"], 2)
            self.assertEqual(report["counts"]["base_directories"], 1)
            self.assertEqual(report["counts"]["form_directories"], 1)
            self.assertEqual(report["counts"]["follower_file_triplets"], 1)
            row = next(x for x in report["rows"] if x["asset_folder"] == "raichu/alola")
            self.assertIn("overworld_sheet", row["missing_files"])

    def test_front_variant_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_folder(root, "custom", ["front.png"])
            report = audit.inspect(root)
            self.assertEqual(report["rows"][0]["battle_front"], "front.png")

    def test_no_files_does_not_create_spurious_species(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "blank").mkdir()
            result = audit.inspect(root)
            self.assertEqual(result["rows"], [])

    def test_missing_root_is_error(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileNotFoundError):
                audit.inspect(Path(temp) / "does-not-exist")


if __name__ == "__main__":
    unittest.main()
