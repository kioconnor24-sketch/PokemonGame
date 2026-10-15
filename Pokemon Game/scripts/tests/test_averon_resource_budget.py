"""Checks that GBA memory usage is parsed from actual linker output."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "check-averon-resource-budget.py"
spec = importlib.util.spec_from_file_location("averon_budget", FILE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

LOG = """Memory region         Used Size  Region Size  %age Used
           EWRAM:      226416 B       256 KB     86.37%
           IWRAM:       28376 B        32 KB     86.60%
             ROM:    26722880 B        32 MB     79.64%
"""

class ResourceTests(unittest.TestCase):
    def test_actual_linker_log_example(self):
        report = tool.report(LOG)
        self.assertEqual(report["memory"]["ROM"]["used_bytes"], 26722880)
        self.assertEqual(report["memory"]["EWRAM"]["capacity_bytes"], 262144)
        self.assertEqual(report["memory"]["IWRAM"]["used_percent"], 86.6)

    def test_reject_missing_or_inaccurate_linker_data(self):
        with self.assertRaisesRegex(ValueError, "Missing"):
            tool.parse_memory("ROM: 4 B 32 MB 0.0%")
        with self.assertRaisesRegex(ValueError, "Inconsistent"):
            tool.parse_memory(LOG.replace("79.64%", "10.00%"))

    def test_rom_checksum_and_size_are_derived_from_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.gba"
            path.write_bytes(b"source-test-fixture")
            result = tool.report(LOG, path)
            self.assertEqual(result["rom_artifact"]["size_bytes"], 19)
            self.assertEqual(len(result["rom_artifact"]["sha256"]), 64)

    def test_over_capacity_fails(self):
        with self.assertRaisesRegex(ValueError, "Out-of-bounds"):
            tool.parse_memory(LOG.replace("26722880 B", "50000000 B"))

if __name__ == "__main__":
    unittest.main()
