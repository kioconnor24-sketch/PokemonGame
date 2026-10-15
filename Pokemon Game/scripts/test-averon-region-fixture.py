"""Compile and exercise the actual experimental C module on a host compiler.

Run in WSL: python3 scripts/test-averon-region-fixture.py
No engine/global header shim, save writes, persistent IDs or third-party packages.
"""
import ctypes
import itertools
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


BadgeReader = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p)


class MapBinding(ctypes.Structure):
    _fields_ = [('map_group', ctypes.c_uint8), ('map_num', ctypes.c_uint8), ('region', ctypes.c_uint32)]


class RegionFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='averon-region-fixture-')
        cls.addClassCleanup(cls.temporary.cleanup)
        library = Path(cls.temporary.name) / 'region-fixture.so'
        compiler = shlex.split(os.environ.get('CC', 'cc'))
        # ctypes uses c_int for the returned enum. Pin only this host-library ABI;
        # ARM native tests independently compile with the engine's own ABI.
        subprocess.run([*compiler, '-std=c11', '-fno-short-enums', '-Wall', '-Wextra', '-Werror', '-pedantic',
                        '-O2', '-shared', '-fPIC', '-I', str(ROOT / 'engine/include'),
                        str(ROOT / 'engine/src/averon_region_fixture.c'), '-o', str(library)], check=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.AveronRegionFixture_HasBadge.argtypes = [ctypes.POINTER(Badges), ctypes.c_uint32, ctypes.c_uint32]
        cls.lib.AveronRegionFixture_HasBadge.restype = ctypes.c_int
        cls.lib.AveronRegionFixture_CountBadges.argtypes = [ctypes.POINTER(Badges), ctypes.c_uint32]
        cls.lib.AveronRegionFixture_CountBadges.restype = ctypes.c_uint32
        cls.lib.AveronRegionFixture_ResolveMap.argtypes = [ctypes.POINTER(MapBinding), ctypes.c_size_t,
                                                         ctypes.c_uint32, ctypes.c_uint32]
        cls.lib.AveronRegionFixture_ResolveMap.restype = ctypes.c_int
        cls.lib.AveronRegionFixture_CaptureBadges.argtypes = [BadgeReader, ctypes.c_void_p, ctypes.POINTER(Badges)]
        cls.lib.AveronRegionFixture_CaptureBadges.restype = ctypes.c_int

    def test_capture_reads_both_banks_once_and_allows_aliasing(self):
        for averon, sinnoh in ((0, 255), (255, 0), (0x55, 0xAA), (0xA5, 0x81)):
            source = Badges(averon, sinnoh)
            output = Badges(0xAA, 0x55)
            requests = []

            @BadgeReader
            def read(region, number, context):
                requests.append((region, number))
                if not context or region not in (AVERON, SINNOH) or not 1 <= number <= 8:
                    return -1
                state = ctypes.cast(context, ctypes.POINTER(Badges)).contents
                mask = state.averon if region == AVERON else state.sinnoh
                return int(bool(mask & (1 << (number - 1))))

            self.assertEqual(self.lib.AveronRegionFixture_CaptureBadges(read, ctypes.byref(source), ctypes.byref(output)), 1)
            self.assertEqual(bytes(output), bytes((averon, sinnoh)))
            self.assertEqual(bytes(source), bytes((averon, sinnoh)))
            self.assertEqual(len(requests), 16)
            for region in (AVERON, SINNOH):
                for number in range(1, 9):
                    self.assertEqual(requests.count((region, number)), 1)
            requests.clear()
            self.assertEqual(self.lib.AveronRegionFixture_CaptureBadges(read, ctypes.byref(output), ctypes.byref(output)), 1)
            self.assertEqual(bytes(output), bytes((averon, sinnoh)))
            self.assertEqual(len(requests), 16)

    def test_capture_failure_is_atomic_at_every_read_boundary(self):
        for fail_at in range(1, 17):
            for bad_value in (-1, 2):
                calls = []

                @BadgeReader
                def read(region, number, context):
                    calls.append((region, number))
                    return bad_value if len(calls) == fail_at else 1

                output = Badges(0xA5, 0x81)
                self.assertEqual(self.lib.AveronRegionFixture_CaptureBadges(read, None, ctypes.byref(output)), 0)
                self.assertEqual(bytes(output), bytes((0xA5, 0x81)))
                self.assertEqual(len(calls), fail_at)

    def test_capture_checks_required_arguments_but_accepts_null_context(self):
        calls = []

        @BadgeReader
        def read(region, number, context):
            calls.append((region, number))
            return 1

        output = Badges(0xA5, 0x81)
        self.assertEqual(self.lib.AveronRegionFixture_CaptureBadges(BadgeReader(), None, ctypes.byref(output)), 0)
        self.assertEqual(self.lib.AveronRegionFixture_CaptureBadges(read, None, None), 0)
        self.assertEqual(calls, [])
        self.assertEqual(bytes(output), bytes((0xA5, 0x81)))
        self.assertEqual(self.lib.AveronRegionFixture_CaptureBadges(read, None, ctypes.byref(output)), 1)
        self.assertEqual(len(calls), 16)
        self.assertEqual(bytes(output), bytes((255, 255)))

    def test_map_lookup_checks_every_group_number_pair(self):
        expected = {(0, 0): AVERON, (0, 1): SINNOH, (1, 0): SINNOH, (255, 255): AVERON}
        maps = (MapBinding * len(expected))(*(MapBinding(group, number, region)
                                               for (group, number), region in expected.items()))
        before = bytes(maps)
        for group in range(256):
            for number in range(256):
                self.assertEqual(self.lib.AveronRegionFixture_ResolveMap(maps, len(maps), group, number),
                                 expected.get((group, number), 0))
        self.assertEqual(bytes(maps), before)

    def test_map_order_does_not_change_identity(self):
        fixtures = [(4, 7, AVERON), (5, 7, SINNOH), (4, 8, SINNOH), (255, 254, AVERON)]
        for order in itertools.permutations(fixtures):
            maps = (MapBinding * len(order))(*(MapBinding(*entry) for entry in order))
            for group, number, region in fixtures:
                self.assertEqual(self.lib.AveronRegionFixture_ResolveMap(maps, len(maps), group, number), region)

    def test_ambiguous_and_unknown_regions_fail_closed(self):
        for left in (AVERON, SINNOH, 0, -1, 99):
            for right in (AVERON, SINNOH, 0, -1, 99):
                maps = (MapBinding * 2)(MapBinding(3, 7, left), MapBinding(3, 7, right))
                self.assertEqual(self.lib.AveronRegionFixture_ResolveMap(maps, 2, 3, 7), 0)
        for region in (0, -1, 3, 255, 257, 258, 65537, 2**32 - 1):
            maps = (MapBinding * 1)(MapBinding(3, 7, region))
            self.assertEqual(self.lib.AveronRegionFixture_ResolveMap(maps, 1, 3, 7), 0)

    def test_null_empty_and_oversized_map_identity_fail_closed(self):
        maps = (MapBinding * 1)(MapBinding(0, 0, AVERON))
        self.assertEqual(self.lib.AveronRegionFixture_ResolveMap(None, 0, 0, 0), 0)
        self.assertEqual(self.lib.AveronRegionFixture_ResolveMap(None, 2**32 - 1, 0, 0), 0)
        self.assertEqual(self.lib.AveronRegionFixture_ResolveMap(maps, 0, 0, 0), 0)
        for value in (256, 65536, 2**32 - 1):
            self.assertEqual(self.lib.AveronRegionFixture_ResolveMap(maps, 1, value, 0), 0)
            self.assertEqual(self.lib.AveronRegionFixture_ResolveMap(maps, 1, 0, value), 0)

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
        for region in (0, -1, 3, 255, 257, 258, 65537, 2**31 - 1):
            self.assertEqual(self.lib.AveronRegionFixture_HasBadge(ctypes.byref(badges), region, 1), 0)
            self.assertEqual(self.lib.AveronRegionFixture_CountBadges(ctypes.byref(badges), region), 0)

    def test_null_snapshot_fails_closed(self):
        for region in (AVERON, SINNOH, 0):
            self.assertEqual(self.lib.AveronRegionFixture_HasBadge(None, region, 1), 0)
            self.assertEqual(self.lib.AveronRegionFixture_CountBadges(None, region), 0)

    def test_short_enums_reject_large_region_inputs_before_truncation(self):
        probe = Path(self.temporary.name) / 'short-enum-probe.c'
        executable = probe.with_suffix('')
        probe.write_text('''#include <stdio.h>
#include "averon_region_fixture.h"
int main(void)
{
    struct AveronFixtureBadges badges = {255, 255};
    struct AveronFixtureMapBinding map = {3, 7, AVERON_FIXTURE_UNKNOWN};
    const uint32_t invalid[] = {257, 258, 65537, UINT32_MAX};
    for (size_t i = 0; i < sizeof(invalid) / sizeof(invalid[0]); ++i)
    {
        if (AveronRegionFixture_HasBadge(&badges, invalid[i], 1)
            || AveronRegionFixture_CountBadges(&badges, invalid[i]))
        {
            fprintf(stderr, "Region %u aliased a badge bank\\n", invalid[i]);
            return 1;
        }
        map.region = invalid[i];
        if (AveronRegionFixture_ResolveMap(&map, 1, 3, 7) != AVERON_FIXTURE_UNKNOWN)
        {
            fprintf(stderr, "Region %u aliased a map identity\\n", invalid[i]);
            return 2;
        }
    }
    return 0;
}
''', encoding='utf-8')
        compiler = shlex.split(os.environ.get('CC', 'cc'))
        subprocess.run([*compiler, '-std=c11', '-fshort-enums', '-Wall', '-Wextra', '-Werror',
                        '-I', str(ROOT / 'engine/include'), str(probe),
                        str(ROOT / 'engine/src/averon_region_fixture.c'), '-o', str(executable)], check=True)
        result = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
