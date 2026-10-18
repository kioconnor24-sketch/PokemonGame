"""Checks that GBA memory usage is parsed from actual linker output."""
import copy
import importlib.util
import json
import subprocess
import sys
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
PROFILE = "release-cries-off-experimental"


def log_with_usage(rom=26722880, ewram=226416, iwram=28376, rom_mb=32):
    return "\n".join(
        f"{name}: {used} B {capacity} {unit} {100 * used / maximum:.2f}%"
        for name, used, capacity, unit, maximum in (
            ("ROM", rom, rom_mb, "MB", rom_mb * 1024 * 1024),
            ("EWRAM", ewram, 256, "KB", 256 * 1024),
            ("IWRAM", iwram, 32, "KB", 32 * 1024)))


class ResourceTests(unittest.TestCase):
    def test_actual_linker_log_example(self):
        report = tool.report(LOG)
        self.assertEqual(report["memory"]["ROM"]["used_bytes"], 26722880)
        self.assertEqual(report["memory"]["EWRAM"]["capacity_bytes"], 262144)
        self.assertEqual(report["memory"]["IWRAM"]["used_percent"], 86.6)
        self.assertNotIn("build_labels", report)
        self.assertNotIn("comparison", report)

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

    def test_signed_linker_growth_and_decrease_for_all_regions(self):
        baseline = tool.report(LOG, profile=PROFILE, source_revision="before")
        current = tool.report(log_with_usage(rom=26723136, ewram=226400, iwram=28376),
                              profile=PROFILE, source_revision="after", baseline=baseline)
        changes = current["comparison"]["memory"]
        self.assertEqual(changes["ROM"]["used_bytes_delta"], 256)
        self.assertEqual(changes["EWRAM"]["used_bytes_delta"], -16)
        self.assertEqual(changes["IWRAM"]["used_bytes_delta"], 0)
        self.assertEqual(changes["ROM"]["baseline_used_bytes"], 26722880)
        self.assertEqual(current["comparison"]["baseline_labels"]["source_revision"], "before")
        self.assertIn("not verified", current["build_labels"]["scope"])

    def test_comparison_needs_matching_nonempty_profiles(self):
        baseline = tool.report(LOG, profile=PROFILE)
        for profile in (None, "", "   ", "release-cries-on"):
            with self.subTest(current_profile=profile), self.assertRaises(ValueError):
                tool.report(LOG, profile=profile, baseline=baseline)
        for labels in (None, {}, {"profile": ""}, {"profile": "   "}):
            malformed = copy.deepcopy(baseline)
            if labels is None:
                malformed.pop("build_labels")
            else:
                malformed["build_labels"] = labels
            with self.subTest(baseline_labels=labels), self.assertRaisesRegex(ValueError, "profile"):
                tool.report(LOG, profile=PROFILE, baseline=malformed)

    def test_comparison_rejects_different_capacity_even_with_matching_profile(self):
        for region, source in (("ROM", log_with_usage(rom_mb=64)),
                               ("EWRAM", LOG.replace("256 KB     86.37%", "512 KB     43.19%")),
                               ("IWRAM", LOG.replace("32 KB     86.60%", "64 KB     43.30%"))):
            baseline = tool.report(source, profile=PROFILE)
            with self.subTest(region=region), self.assertRaisesRegex(ValueError, f"{region} capacity differs"):
                tool.report(LOG, profile=PROFILE, baseline=baseline)

    def test_comparison_rejects_malformed_baseline_objects(self):
        baseline = tool.report(LOG, profile=PROFILE)
        cases = [[], "report", {}, {"scope": tool.REPORT_SCOPE, "build_labels": []}]
        for change in (lambda report: report["memory"].pop("EWRAM"),
                       lambda report: report["memory"].update({"ROM": []}),
                       lambda report: report["memory"]["ROM"].update(used_bytes=True),
                       lambda report: report["memory"]["ROM"].update(used_bytes=-1),
                       lambda report: report["memory"]["ROM"].update(remaining_bytes=0),
                       lambda report: report["memory"]["ROM"].pop("linker_reported_percent"),
                       lambda report: report["memory"]["ROM"].update(used_percent=float("nan")),
                       lambda report: report["memory"]["ROM"].update(used_percent=10**1000),
                       lambda report: report["memory"]["ROM"].update(used_percent=10.0)):
            malformed = copy.deepcopy(baseline)
            change(malformed)
            cases.append(malformed)
        for malformed in cases:
            with self.subTest(baseline=malformed), self.assertRaises(ValueError):
                tool.report(LOG, profile=PROFILE, baseline=malformed)

    def test_padded_rom_file_size_is_not_linked_growth(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "padded.gba"
            with path.open("wb") as fp:
                fp.truncate(32 * 1024 * 1024)
            baseline = tool.report(LOG, path, profile=PROFILE)
            current = tool.report(log_with_usage(rom=26722884), path,
                                  profile=PROFILE, baseline=baseline)
            self.assertEqual(current["rom_artifact"], baseline["rom_artifact"])
            self.assertEqual(current["rom_artifact"]["size_bytes"], 32 * 1024 * 1024)
            self.assertEqual(current["comparison"]["memory"]["ROM"]["used_bytes_delta"], 4)

    def test_optional_labels_without_comparison(self):
        result = tool.report(LOG, source_revision=" descriptive-source-label ")
        self.assertEqual(result["build_labels"]["source_revision"], "descriptive-source-label")
        self.assertNotIn("comparison", result)
        with self.assertRaisesRegex(ValueError, "source_revision"):
            tool.report(LOG, source_revision=" ")

    def test_cli_previous_report_comparison_and_old_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "build.log"
            log.write_text(LOG, encoding="utf-8")
            previous = root / "previous.json"
            result = subprocess.run(
                [sys.executable, str(FILE), "--log", str(log), "--json", str(previous)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("build_labels", json.loads(previous.read_text(encoding="utf-8")))
            baseline = tool.report(LOG, profile=PROFILE, source_revision="before")
            previous.write_text(json.dumps(baseline), encoding="utf-8")
            log.write_text(log_with_usage(rom=26723136), encoding="utf-8")
            output = root / "nested" / "current.json"
            result = subprocess.run(
                [sys.executable, str(FILE), "--log", str(log), "--json", str(output),
                 "--baseline", str(previous), "--profile", PROFILE, "--source-revision", "after"],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ROM: linked usage change +256 bytes", result.stdout)
            current = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(current["comparison"]["memory"]["ROM"]["used_bytes_delta"], 256)
            self.assertEqual(current["build_labels"]["source_revision"], "after")

    def test_cli_invalid_baselines_fail_without_writing_a_report(self):
        baseline = tool.report(LOG, profile=PROFILE)
        for name, content, options in (
                ("bad-json", "{broken", ["--profile", PROFILE]),
                ("null", "null", ["--profile", PROFILE]),
                ("array", "[]", ["--profile", PROFILE]),
                ("no-current-profile", json.dumps(baseline), []),
                ("wrong-profile", json.dumps(baseline), ["--profile", "release-cries-on"]),
                ("no-baseline-profile", json.dumps(tool.report(LOG)), ["--profile", PROFILE])):
            with self.subTest(case=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                log, previous, output = root / "build.log", root / "baseline.json", root / "out.json"
                log.write_text(LOG, encoding="utf-8")
                previous.write_text(content, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(FILE), "--log", str(log), "--json", str(output),
                     "--baseline", str(previous), *options], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(output.exists())

if __name__ == "__main__":
    unittest.main()
