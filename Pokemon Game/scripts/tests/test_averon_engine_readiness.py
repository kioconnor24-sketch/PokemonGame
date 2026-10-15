"""Tests for Averon's static configuration readiness gates."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "audit-averon-engine-readiness.py"
spec = importlib.util.spec_from_file_location("averon_engine_readiness", MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ParseTests(unittest.TestCase):
    def test_ignores_commented_and_blocked_definitions(self):
        text = ('// #define P_MEGA_EVOLUTIONS FALSE\n'
                '/* #define P_GEN_1_POKEMON FALSE */\n'
                '#define P_MEGA_EVOLUTIONS TRUE // works\n'
                '#define P_GEN_1_POKEMON TRUE\n')
        defs, duplicates, suspicious = audit.parse_config(text)
        self.assertEqual(defs["P_MEGA_EVOLUTIONS"][0]["value"], "TRUE")
        self.assertEqual(defs["P_GEN_1_POKEMON"][0]["value"], "TRUE")
        self.assertFalse(duplicates)
        self.assertEqual(len(suspicious), 1)

    def test_duplicate_macro_reports_both_lines(self):
        defs, duplicates, _ = audit.parse_config(
            "#define B_EV_CAP_VARIABLE 8\n#define B_EV_CAP_VARIABLE 12\n")
        self.assertEqual(len(defs["B_EV_CAP_VARIABLE"]), 2)
        self.assertEqual(duplicates[0]["line"], 2)
        self.assertEqual(duplicates[0]["previous_line"], 1)

    def test_run_on_comment_is_warning_not_active_definition(self):
        defs, _, suspicious = audit.parse_config(
            '#define B_EV_CAP_TYPE EV_CAP_NONE // documentation#define B_EV_CAP_VARIABLE 12\n'
            '#define B_EV_CAP_VARIABLE 8\n')
        self.assertEqual(len(defs["B_EV_CAP_VARIABLE"]), 1)
        self.assertEqual(len(suspicious), 1)

    def test_detects_failed_requirements_and_renders_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "include" / "config"
            root.mkdir(parents=True)
            expected_by_file = {}
            for filename, name, value, _ in audit.EXPECTED:
                expected_by_file.setdefault(filename, []).append(f"#define {name} {value}")
            for filename, lines in expected_by_file.items():
                (root / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = audit.inspect(directory)
            self.assertEqual(result["summary"]["blockers"], 0)
            self.assertEqual(result["summary"]["passed"], len(audit.EXPECTED))
            self.assertIn("static source check", audit.render_markdown(result))
            path = root / "item.h"
            path.write_text(path.read_text().replace(
                "#define I_EXP_SHARE_ITEM GEN_5", "#define I_EXP_SHARE_ITEM GEN_6"),
                encoding="utf-8")
            broken = audit.inspect(directory)
            self.assertEqual(broken["summary"]["blockers"], 1)
            self.assertIn("I_EXP_SHARE_ITEM", str(broken["issues"]))

    def test_missing_file_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            report = audit.inspect(directory)
            self.assertGreater(report["summary"]["blockers"], 0)


if __name__ == "__main__":
    unittest.main()
