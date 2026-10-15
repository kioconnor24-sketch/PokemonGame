"""Compile and exercise the actual experimental C module on a host compiler.

Run in WSL: python3 scripts/test-averon-region-fixture.py
No engine/global header shim, save writes, persistent IDs or third-party packages.
"""
import ctypes
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVERON, SINNOH = 1, 2


class Badges(ctypes.Structure):
    _fields_ = [('averon', ctypes.c_uint8), ('sinnoh', ctypes.c_uint8)]


class RegionFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='averon-region-fixture-')
        cls.addClassCleanup(cls.temporary.cleanup)
        library = Path(cls.temporary.name) / 'region-fixture.so'
        compiler = shlex.split(os.environ.get('CC', 'cc'))
        subprocess.run([*compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic',
                        '-O2', '-shared', '-fPIC', '-I', str(ROOT / 'engine/include'),
                        str(ROOT / 'engine/src/averon_region_fixture.c'), '-o', str(library)], check=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.AveronRegionFixture_HasBadge.argtypes = [ctypes.POINTER(Badges), ctypes.c_int, ctypes.c_uint32]
        cls.lib.AveronRegionFixture_HasBadge.restype = ctypes.c_int
        cls.lib.AveronRegionFixture_CountBadges.argtypes = [ctypes.POINTER(Badges), ctypes.c_int]
        cls.lib.AveronRegionFixture_CountBadges.restype = ctypes.c_uint32

    def test_every_pair_of_badge_masks_has_independent_counts(self):
        for averon in range(256):
            for sinnoh in range(256):
                badges = Badges(averon, sinnoh)
                self.assertEqual(self.lib.AveronRegionFixture_CountBadges(ctypes.byref(badges), AVERON), averon.bit_count())
                self.assertEqual(self.lib.AveronRegionFixture_CountBadges(ctypes.byref(badges), SINNOH), sinnoh.bit_count())
                self.assertEqual(bytes(badges), bytes((averon, sinnoh)))

    def test_every_mask_and_badge_position(self):
        for mask in range(256):
            badges = Badges(mask, mask ^ 255)
            for number in range(1, 9):
                expected = bool(mask & (1 << (number - 1)))
                self.assertEqual(self.lib.AveronRegionFixture_HasBadge(ctypes.byref(badges), AVERON, number), expected)
                self.assertEqual(self.lib.AveronRegionFixture_HasBadge(ctypes.byref(badges), SINNOH, number), not expected)

    def test_invalid_badge_numbers(self):
        badges = Badges(255, 255)
        for number in (0, 9, 32, 255, 2**32 - 1):
            for region in (AVERON, SINNOH):
                self.assertEqual(self.lib.AveronRegionFixture_HasBadge(ctypes.byref(badges), region, number), 0)

    def test_changing_other_region_never_changes_membership(self):
        for other in range(256):
            for region, badges in ((AVERON, Badges(0x55, other)), (SINNOH, Badges(other, 0x55))):
                before = bytes(badges)
                for number in range(1, 9):
                    self.assertEqual(self.lib.AveronRegionFixture_HasBadge(ctypes.byref(badges), region, number), number % 2)
                self.assertEqual(bytes(badges), before)

    def test_invalid_regions_fail_closed(self):
        badges = Badges(255, 255)
        for region in (0, -1, 3, 255, 2**31 - 1):
            self.assertEqual(self.lib.AveronRegionFixture_HasBadge(ctypes.byref(badges), region, 1), 0)
            self.assertEqual(self.lib.AveronRegionFixture_CountBadges(ctypes.byref(badges), region), 0)

    def test_null_snapshot_fails_closed(self):
        for region in (AVERON, SINNOH, 0):
            self.assertEqual(self.lib.AveronRegionFixture_HasBadge(None, region, 1), 0)
            self.assertEqual(self.lib.AveronRegionFixture_CountBadges(None, region), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
