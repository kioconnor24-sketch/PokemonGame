"""Regression tests for native Averon flag and variable ID inspection."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "audit-averon-event-ids.py"
spec = importlib.util.spec_from_file_location("averon_event_ids", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class EventIdsTests(unittest.TestCase):
    def test_detects_collision_inside_averon(self):
        sample = ("#define FLAG_AVERON_A 0x20\n"
                  "#define FLAG_AVERON_B (0x10 + 0x10)\n")
        report = mod.scan(sample, "FLAG_", "FLAG_AVERON_")
        self.assertEqual(len(report["registered"]), 2)
        self.assertEqual(sum(x["severity"] == "blocker" for x in report["issues"]), 2)

    def test_distinguishes_non_averon_alias(self):
        sample = ("#define FLAG_OTHER 0x35\n"
                  "#define FLAG_AVERON_A 0x35\n")
        result = mod.scan(sample, "FLAG_", "FLAG_AVERON_")
        self.assertEqual([x["severity"] for x in result["issues"]], ["warning"])

    def test_unsupported_macro_is_not_assumed_free(self):
        sample = "#define VAR_AVERON_Q (UNKNOWN_BASE + 4)\n"
        result = mod.scan(sample, "VAR_", "VAR_AVERON_")
        self.assertEqual(result["registered"], {})
        self.assertEqual(result["issues"][0]["severity"], "blocker")

    def test_invalid_expression_rejected(self):
        with self.assertRaises(ValueError):
            mod.evaluate("__import__('os').system('echo unsafe')", {})

    def test_realistic_native_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "include" / "constants"
            root.mkdir(parents=True)
            (root / "flags.h").write_text(
                "#define FLAG_AVERON_STARTER 0x20\n#define FLAG_AVERON_BERRIES 0x21\n",
                encoding="utf-8")
            (root / "vars.h").write_text(
                "#define VAR_AVERON_FIRST_HOUSE 0x404E\n",
                encoding="utf-8")
            report = mod.audit(directory)
            self.assertEqual(report["summary"]["blockers"], 0)
            self.assertEqual(len(report["flags"]["registered"]), 2)
            self.assertEqual(len(report["vars"]["registered"]), 1)


if __name__ == "__main__":
    unittest.main()
