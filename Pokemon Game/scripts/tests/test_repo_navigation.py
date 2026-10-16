"""Isolated tests for the repository-documentation link checker."""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "check-repo-navigation.py"
SPEC = importlib.util.spec_from_file_location("averon_doclinks", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        (self.root / "docs").mkdir()
        (self.root / "README.md").write_text("# Root\n", encoding="utf-8")

    def write(self, text):
        (self.root / "docs" / "index.md").write_text(text, encoding="utf-8")

    def check(self):
        return MODULE.validate(self.root, ("docs/index.md",))

    def test_valid_relative_directory_percent_encoding_and_fragment(self):
        self.write("[root](../README.md) [directory](./) [encoded](my%20file.md#heading)")
        (self.root / "docs" / "my file.md").write_text("content", encoding="utf-8")
        self.assertEqual(self.check(), [])

    def test_missing_target_is_reported_with_line_number(self):
        self.write("Intro\n[bad](../missing.md)")
        problems = self.check()
        self.assertEqual(len(problems), 1)
        self.assertIn("docs/index.md:2:", problems[0])

    def test_http_mailto_and_anchor_are_ignored(self):
        self.write("[external](https://example.org/x) [mail](mailto:test@example.org) [anchor](#fragment)")
        self.assertEqual(self.check(), [])

    def test_fenced_code_is_not_scanned(self):
        self.write("```markdown\n[not a link](bad.md)\n```\n[valid](../README.md)")
        self.assertEqual(self.check(), [])

    def test_parent_traversal_is_rejected(self):
        self.write("[unsafe](../../outside.md)")
        problems = self.check()
        self.assertEqual(len(problems), 1)
        self.assertIn("escapes repository", problems[0])

    def test_missing_entry_document_is_reported(self):
        self.assertEqual(len(MODULE.validate(self.root, ("not-created.md",))), 1)

    def test_ordinary_inline_code_is_not_a_link(self):
        self.write("Use `[example](not-a-link.md)` carefully, then [root](../README.md)")
        # Deliberately restrict this checker to links outside both inline and fenced code.
        self.assertEqual(self.check(), [])


if __name__ == "__main__":
    unittest.main()
