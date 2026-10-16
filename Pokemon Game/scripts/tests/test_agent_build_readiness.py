"""Build manifest regression checks; all data are synthetic, no copyrighted ROM."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "coordination" / "verify_build_readiness.py"
spec = importlib.util.spec_from_file_location("verify_build_readiness", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SUCCESS = "\033[32m- Tests PASSED: 7\033[0m\n- Tests TOTAL: 7\n"
BUDGET = {"rom_artifact": {}, "memory": {
    "ROM": {"used_bytes": 111}, "EWRAM": {"used_bytes": 22},
    "IWRAM": {"used_bytes": 33},
}}
SOURCE = {"mode": "combined", "main_sha": "a" * 40,
          "pull_requests": [{"number": 14, "sha": "b" * 40},
                            {"number": 25, "sha": "c" * 40}]}


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rom = Path(self.tmp.name) / "test.gba"
        self.rom.write_bytes(b"GBA fixture only\n" * 30)
        self.budget = {**BUDGET, "rom_artifact": {
            "size_bytes": self.rom.stat().st_size,
            "sha256": hashlib.sha256(self.rom.read_bytes()).hexdigest()}}
        self.source = {**SOURCE}

    def report(self, native=SUCCESS, save=SUCCESS):
        return mod.compute(self.rom, native, save, self.budget, self.source)

    def test_positive_evidence_and_no_distribution(self):
        r = self.report()
        self.assertEqual((r["native"]["passed"], r["save"]["total"]), (7, 7))
        self.assertIs(r["rom"]["distributed"], False)
        self.assertIn("NOT_GRAPHICALLY_ACCEPTED", r["status"])
        self.assertIn("Delta iOS compatibility", r["unverified"])

    def test_missing_native_count_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing actual runner"):
            self.report(native="make check finished exit 0")

    def test_zero_native_tests_rejected(self):
        with self.assertRaisesRegex(ValueError, "no native tests"):
            self.report(native="No tests found\n- Tests PASSED: 0\n- Tests TOTAL: 0")

    def test_partial_native_pass_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.report(native="- Tests PASSED: 6\n- Tests TOTAL: 7\n")

    def test_save_regression_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.report(save="- Tests FAILED: 1\n- Tests PASSED: 6\n- Tests TOTAL: 7")

    def test_rom_mismatch_rejected(self):
        self.rom.write_bytes(b"new bytes")
        with self.assertRaisesRegex(ValueError, "SHA/size"):
            self.report()

    def test_invalid_pr_hash_rejected(self):
        self.source["pull_requests"] = [{"number": 14, "sha": "not-a-sha"},
                                        {"number": 25, "sha": "c" * 40}]
        with self.assertRaisesRegex(ValueError, "Unverified PR SHA"):
            self.report()

    def test_unexpected_pr_count_rejected(self):
        self.source["pull_requests"] = self.source["pull_requests"][:1]
        with self.assertRaisesRegex(ValueError, "Wrong number"):
            self.report()

    def test_main_mode_requires_no_prs(self):
        self.source = {"mode": "main", "main_sha": "f" * 40, "pull_requests": []}
        self.assertEqual(self.report()["source"]["mode"], "main")

    def test_missing_budget_rejected(self):
        self.budget["memory"] = {}
        with self.assertRaisesRegex(ValueError, "Missing memory"):
            self.report()


if __name__ == "__main__":
    unittest.main()
