"""Screenshot observation gate: source-independent deterministic math checks."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "coordination" / "qa_frame_gate.py"
SPEC = importlib.util.spec_from_file_location("qagate", SCRIPT)
QA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QA)


class QaFrameTests(unittest.TestCase):
    def test_identical_image_not_progress(self):
        self.assertEqual(QA.difference(bytes([0, 20, 255]), bytes([0, 20, 255])), 0.0)

    def test_known_difference(self):
        self.assertAlmostEqual(QA.difference(bytes([0, 0]), bytes([255, 255])), 1.0)

    def test_different_size_fails_closed(self):
        with self.assertRaises(ValueError):
            QA.difference(bytes([0]), bytes([0, 0]))

    def test_empty_fails_closed(self):
        with self.assertRaises(ValueError):
            QA.difference(b"", b"")


if __name__ == "__main__":
    unittest.main()
