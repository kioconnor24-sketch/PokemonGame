"""Synthetic-image tests for frame_match.py (needs ImageMagick, no ROM)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).with_name("frame_match.py")


def image(path, spec, size="480x320"):
    subprocess.run(["convert", "-size", size, *spec, str(path)], check=True)


def run(*args):
    result = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


class FrameMatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        root = Path(cls.tmp.name)
        cls.white, cls.half, cls.black, cls.small = (root / n for n in ("w.png", "h.png", "b.png", "s.png"))
        image(cls.white, ["xc:white"])
        image(cls.black, ["xc:black"])
        image(cls.half, ["xc:white", "-fill", "black", "-draw", "rectangle 0,0 239,319"])
        image(cls.small, ["xc:white"], size="240x160")

    def test_identical_frames_match(self):
        self.assertEqual(run(self.white, self.white), (0, "same_pixels=1.000 mean_abs_diff=0.00"))

    def test_threshold_decides(self):
        self.assertEqual(run(self.white, self.half)[0], 1)
        self.assertEqual(run("--min", "0.5", self.white, self.half)[0], 0)
        self.assertEqual(run(self.white, self.black), (1, "same_pixels=0.000 mean_abs_diff=255.00"))

    def test_missing_or_mismatched_frames_are_unavailable(self):
        self.assertEqual(run(self.white, self.small), (2, "unavailable: frame sizes differ"))
        self.assertEqual(run(self.white, Path(self.tmp.name) / "none.png"), (2, "unavailable: missing frame"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
