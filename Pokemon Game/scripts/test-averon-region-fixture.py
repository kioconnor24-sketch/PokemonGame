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
HealReader = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_uint32, ctypes.c_void_p,
                             ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32))


class MapBinding(ctypes.Structure):
    _fields_ = [('map_group', ctypes.c_uint8), ('map_num', ctypes.c_uint8), ('region', ctypes.c_uint32)]


class WarpMetadata(ctypes.Structure):
    _fields_ = [('width', ctypes.c_uint32), ('height', ctypes.c_uint32), ('warp_count', ctypes.c_uint32)]


class ProgressionPolicy(ctypes.Structure):
    _fields_ = [('region', ctypes.c_uint32), ('level_caps', ctypes.c_uint32 * 9),
                ('obedience_caps', ctypes.c_uint32 * 9)]


class Progression(ctypes.Structure):
    _fields_ = [('level_cap', ctypes.c_uint8), ('obedience_cap', ctypes.c_uint8)]


WarpReader = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32,
                             ctypes.c_void_p, ctypes.POINTER(WarpMetadata))


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
        cls.lib.AveronRegionFixture_IsFlyDestinationEligible.argtypes = [ctypes.POINTER(MapBinding), ctypes.c_size_t,
            ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int]
        cls.lib.AveronRegionFixture_IsFlyDestinationEligible.restype = ctypes.c_int
        cls.lib.AveronRegionFixture_SelectRegionalHeal.argtypes = [ctypes.POINTER(MapBinding), ctypes.c_size_t,
            ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
            HealReader, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        cls.lib.AveronRegionFixture_SelectRegionalHeal.restype = ctypes.c_int
        cls.lib.AveronRegionFixture_IsWarpRequestValid.argtypes = [ctypes.POINTER(MapBinding), ctypes.c_size_t,
            ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
            WarpReader, ctypes.c_void_p]
        cls.lib.AveronRegionFixture_IsWarpRequestValid.restype = ctypes.c_int
        cls.lib.AveronRegionFixture_SelectProgression.argtypes = [ctypes.POINTER(Badges), ctypes.c_uint32,
            ctypes.POINTER(ProgressionPolicy), ctypes.c_size_t, ctypes.POINTER(Progression)]
        cls.lib.AveronRegionFixture_SelectProgression.restype = ctypes.c_int

    def progression_policies(self):
        # Deliberately synthetic profiles; these are not proposed Gym caps.
        return (ProgressionPolicy * 2)(
            ProgressionPolicy(AVERON, (ctypes.c_uint32 * 9)(*range(1, 10)),
                              (ctypes.c_uint32 * 9)(*range(91, 100))),
            ProgressionPolicy(SINNOH, (ctypes.c_uint32 * 9)(*range(21, 30)),
                              (ctypes.c_uint32 * 9)(*range(41, 50))))

    def test_progression_uses_only_its_region_badge_bank(self):
        profiles = self.progression_policies()
        original = bytes(profiles)
        for mask in range(256):
            for other in (0, mask ^ 255, 255):
                badges = Badges(mask, other)
                for region, count, level, obedience in (
                        (AVERON, mask.bit_count(), 1, 91), (SINNOH, other.bit_count(), 21, 41)):
                    output = Progression(222, 173)
                    self.assertEqual(self.lib.AveronRegionFixture_SelectProgression(
                        ctypes.byref(badges), region, profiles, 2, ctypes.byref(output)), 1)
                    self.assertEqual((output.level_cap, output.obedience_cap), (level + count, obedience + count))
                self.assertEqual(bytes(badges), bytes(Badges(mask, other)))
        self.assertEqual(bytes(profiles), original)

    def test_progression_rejects_ambiguous_unknown_and_missing_inputs_atomically(self):
        profiles = self.progression_policies()
        badges = Badges(0xA5, 0x81)
        output = Progression(222, 173)
        for region in (0, 3, 257, 258, 2**32 - 1):
            self.assertEqual(self.lib.AveronRegionFixture_SelectProgression(
                ctypes.byref(badges), region, profiles, 2, ctypes.byref(output)), 0)
        for count in (0, 1):
            self.assertEqual(self.lib.AveronRegionFixture_SelectProgression(
                ctypes.byref(badges), SINNOH, profiles, count, ctypes.byref(output)), 0)
        profiles[1].region = AVERON
        self.assertEqual(self.lib.AveronRegionFixture_SelectProgression(
            ctypes.byref(badges), AVERON, profiles, 2, ctypes.byref(output)), 0)
        for b, p, out in ((None, profiles, ctypes.byref(output)), (ctypes.byref(badges), None, ctypes.byref(output)),
                           (ctypes.byref(badges), profiles, None)):
            self.assertEqual(self.lib.AveronRegionFixture_SelectProgression(b, AVERON, p, 2, out), 0)
        self.assertEqual(bytes(output), bytes(Progression(222, 173)))

    def test_progression_validates_every_full_width_cap_before_commit(self):
        profiles = self.progression_policies()
        badges = Badges(0, 255)
        output = Progression(222, 173)
        for bank in (0, 1):
            for field in ('level_caps', 'obedience_caps'):
                for index in range(9):
                    for invalid in (0, 101, 256, 2**32 - 1):
                        values = getattr(profiles[bank], field)
                        saved = values[index]
                        values[index] = invalid
                        self.assertEqual(self.lib.AveronRegionFixture_SelectProgression(
                            ctypes.byref(badges), bank + 1, profiles, 2, ctypes.byref(output)), 0)
                        self.assertEqual(bytes(output), bytes(Progression(222, 173)))
                        values[index] = saved
        profiles[0].level_caps[8] = 100
        profiles[0].obedience_caps[8] = 100
        badges.averon = 255
        self.assertEqual(self.lib.AveronRegionFixture_SelectProgression(
            ctypes.byref(badges), AVERON, profiles, 2, ctypes.byref(output)), 1)
        self.assertEqual((output.level_cap, output.obedience_cap), (100, 100))

    def test_warp_indexed_requests_enforce_event_count_and_signed_byte_limit(self):
        maps = (MapBinding * 1)(MapBinding(3, 7, AVERON))
        before = bytes(maps)
        for count in (0, 1, 127, 128, 255):
            for index in (0, 1, 126, 127, 128, 255, 256, 2**31 - 1):
                calls = []

                @WarpReader
                def read(group, number, context, metadata):
                    calls.append((group, number))
                    metadata[0] = WarpMetadata(32767, 32767, count)
                    return 1

                actual = self.lib.AveronRegionFixture_IsWarpRequestValid(
                    maps, 1, 3, 7, index, -1, -1, read, None)
                self.assertEqual(actual, 0 <= index <= 127 and index < count)
                self.assertEqual(calls, [(3, 7)] if index <= 127 else [])
        self.assertEqual(bytes(maps), before)

    def test_warp_coordinate_requests_enforce_dimensions_and_signed_byte_limit(self):
        maps = (MapBinding * 1)(MapBinding(127, 127, SINNOH))
        before = bytes(maps)
        for width, height in ((1, 1), (1, 128), (128, 1), (127, 127), (128, 128), (32767, 32767)):
            for x, y in itertools.product((-1, 0, 1, 126, 127, 128, 2**31 - 1), repeat=2):
                calls = []

                @WarpReader
                def read(group, number, context, metadata):
                    calls.append((group, number))
                    metadata[0] = WarpMetadata(width, height, 0)
                    return 1

                actual = self.lib.AveronRegionFixture_IsWarpRequestValid(
                    maps, 1, 127, 127, -1, x, y, read, None)
                representable = 0 <= x <= 127 and 0 <= y <= 127
                self.assertEqual(actual, representable and x < width and y < height)
                self.assertEqual(calls, [(127, 127)] if representable else [])
        self.assertEqual(bytes(maps), before)

    def test_warp_known_map_ids_must_fit_engine_signed_bytes(self):
        for group, number in ((0, 0), (127, 127), (128, 1), (1, 128), (255, 255)):
            maps = (MapBinding * 1)(MapBinding(group, number, SINNOH))
            calls = []

            @WarpReader
            def read(g, n, context, metadata):
                calls.append((g, n))
                metadata[0] = WarpMetadata(1, 1, 0)
                return 1

            valid = group <= 127 and number <= 127
            self.assertEqual(self.lib.AveronRegionFixture_IsWarpRequestValid(
                maps, 1, group, number, -1, 0, 0, read, None), valid)
            self.assertEqual(calls, [(group, number)] if valid else [])

    def test_warp_metadata_rejects_malformed_and_unwritten_fields(self):
        maps = (MapBinding * 1)(MapBinding(3, 7, AVERON))
        invalid = ((0, 1, 0), (1, 0, 0), (32768, 1, 0), (1, 32768, 0),
                   (1, 1, 256), (2**32 - 1, 1, 0), (1, 2**32 - 1, 0), (1, 1, 2**32 - 1),
                   (None, 1, 0), (1, None, 0), (1, 1, None), (None, None, None))
        for values in invalid:
            calls = []

            @WarpReader
            def read(group, number, context, metadata):
                calls.append((group, number))
                for field, value in zip(('width', 'height', 'warp_count'), values):
                    if value is not None:
                        setattr(metadata.contents, field, value)
                return 1

            self.assertEqual(self.lib.AveronRegionFixture_IsWarpRequestValid(
                maps, 1, 3, 7, -1, 0, 0, read, None), 0)
            self.assertEqual(calls, [(3, 7)])

    def test_warp_reader_requires_exact_success_and_preserves_context(self):
        maps = (MapBinding * 1)(MapBinding(3, 7, AVERON))
        marker = ctypes.c_uint32(0xA55A1234)
        for reply in (-1, 0, 1, 2, 2**31 - 1):
            for context in (None, ctypes.byref(marker)):
                calls = []

                @WarpReader
                def read(group, number, received, metadata):
                    calls.append((group, number, received))
                    metadata[0] = WarpMetadata(1, 1, 1)
                    return reply

                self.assertEqual(self.lib.AveronRegionFixture_IsWarpRequestValid(
                    maps, 1, 3, 7, -1, 0, 0, read, context), reply == 1)
                self.assertEqual(calls, [(3, 7, None if context is None else ctypes.addressof(marker))])
                self.assertEqual(marker.value, 0xA55A1234)
        self.assertEqual(self.lib.AveronRegionFixture_IsWarpRequestValid(
            maps, 1, 3, 7, -1, 0, 0, WarpReader(), None), 0)

    def test_warp_invalid_request_shape_never_calls_reader(self):
        maps = (MapBinding * 1)(MapBinding(3, 7, AVERON))
        calls = []

        @WarpReader
        def read(group, number, context, metadata):
            calls.append((group, number))
            metadata[0] = WarpMetadata(32767, 32767, 255)
            return 1

        invalid = ((-2, -1, -1), (-128, -1, -1), (-2**31, -1, -1),
                   (128, -1, -1), (255, -1, -1), (2**31 - 1, -1, -1),
                   (0, 0, -1), (0, -1, 0), (0, 0, 0), (127, 127, 127),
                   (-1, -1, 0), (-1, 0, -1), (-1, 128, 0), (-1, 0, 128),
                   (-1, -2**31, 0), (-1, 0, 2**31 - 1))
        for warp_id, x, y in invalid:
            self.assertEqual(self.lib.AveronRegionFixture_IsWarpRequestValid(
                maps, 1, 3, 7, warp_id, x, y, read, None), 0)
        self.assertEqual(calls, [])

    def test_warp_invalid_or_ambiguous_map_never_calls_reader(self):
        maps = (MapBinding * 2)(MapBinding(3, 7, AVERON), MapBinding(3, 7, SINNOH))
        calls = []

        @WarpReader
        def read(group, number, context, metadata):
            calls.append((group, number))
            metadata[0] = WarpMetadata(1, 1, 1)
            return 1

        for source, count, group, number in ((None, 1, 3, 7), (maps, 0, 3, 7), (maps, 2, 3, 7),
                                             (maps, 1, 3, 8), (maps, 1, 256, 7), (maps, 1, 3, 256),
                                             (maps, 1, 2**32 - 1, 7), (maps, 1, 3, 2**32 - 1)):
            self.assertEqual(self.lib.AveronRegionFixture_IsWarpRequestValid(
                source, count, group, number, -1, 0, 0, read, None), 0)
        for region in (0, 3, 257, 258, 2**32 - 1):
            maps[0].region = region
            self.assertEqual(self.lib.AveronRegionFixture_IsWarpRequestValid(
                maps, 1, 3, 7, -1, 0, 0, read, None), 0)
        self.assertEqual(calls, [])

    def test_heal_selection_prefers_valid_current_region_then_validates_fallback(self):
        entries = [(3, 7, AVERON), (3, 8, AVERON), (4, 1, SINNOH)]
        maps = (MapBinding * 3)(*(MapBinding(*entry) for entry in entries))
        metadata = {1: (3, 7), 2: (3, 8), 9: (4, 1)}
        regions = {(group, number): region for group, number, region in entries}
        for current in ((3, 7), (4, 1)):
            for preferred in (0, 1, 2, 9, 99, 2**32 - 1):
                for fallback in (0, 1, 2, 9, 99, 2**32 - 1):
                    calls = []

                    @HealReader
                    def read(identifier, context, group, number):
                        calls.append(identifier)
                        if identifier not in metadata:
                            return 0
                        group[0], number[0] = metadata[identifier]
                        return 1

                    expected = next((identifier for identifier in (preferred, fallback)
                                     if identifier in metadata and regions[metadata[identifier]] == regions[current]), 0)
                    selected = ctypes.c_uint32(0xDEADBEEF)
                    result = self.lib.AveronRegionFixture_SelectRegionalHeal(
                        maps, 3, *current, preferred, fallback, read, None, ctypes.byref(selected))
                    self.assertEqual(result, bool(expected))
                    self.assertEqual(selected.value, expected if expected else 0xDEADBEEF)
                    self.assertNotIn(0, calls)
                    self.assertLessEqual(len(calls), 1 if preferred == fallback else 2)

    def test_heal_selection_rejects_engine_argument_truncation(self):
        maps = (MapBinding * 4)(MapBinding(3, 7, AVERON), MapBinding(127, 127, AVERON),
                               MapBinding(128, 7, AVERON), MapBinding(3, 128, AVERON))
        for identifier, target, valid in ((255, (127, 127), True), (256, (3, 7), False),
                                          (65537, (3, 7), False), (2**32 - 1, (3, 7), False),
                                          (2, (128, 7), False), (2, (3, 128), False)):
            calls = []

            @HealReader
            def read(value, context, group, number):
                calls.append(value)
                group[0], number[0] = target if value == identifier else (3, 7)
                return 1

            selected = ctypes.c_uint32(0xDEADBEEF)
            self.assertEqual(self.lib.AveronRegionFixture_SelectRegionalHeal(
                maps, 4, 3, 7, identifier, 0, read, None, ctypes.byref(selected)), valid)
            self.assertEqual(selected.value, identifier if valid else 0xDEADBEEF)
            self.assertEqual(calls, [] if identifier > 255 else [identifier])
            if not valid:
                calls.clear()
                self.assertEqual(self.lib.AveronRegionFixture_SelectRegionalHeal(
                    maps, 4, 3, 7, identifier, 1, read, None, ctypes.byref(selected)), 1)
                self.assertEqual(selected.value, 1)
                self.assertEqual(calls, [1] if identifier > 255 else [identifier, 1])

    def test_heal_selection_refuses_invalid_or_unwritten_metadata(self):
        maps = (MapBinding * 1)(MapBinding(3, 7, AVERON))
        for reply, coordinates in ((0, None), (-1, None), (2, (3, 7)), (1, None),
                                    (1, (259, 7)), (1, (3, 263)), (1, (3, 8))):
            calls = []

            @HealReader
            def read(identifier, context, group, number):
                calls.append(identifier)
                if coordinates is not None:
                    group[0], number[0] = coordinates
                return reply

            selected = ctypes.c_uint32(0xDEADBEEF)
            self.assertEqual(self.lib.AveronRegionFixture_SelectRegionalHeal(
                maps, 1, 3, 7, 1, 0, read, None, ctypes.byref(selected)), 0)
            self.assertEqual(selected.value, 0xDEADBEEF)
            self.assertEqual(calls, [1])

    def test_heal_selection_validates_arguments_and_source_region_before_reading(self):
        maps = (MapBinding * 2)(MapBinding(3, 7, AVERON), MapBinding(3, 7, AVERON))
        calls = []

        @HealReader
        def read(identifier, context, group, number):
            calls.append(identifier)
            group[0], number[0] = 3, 7
            return 1

        selected = ctypes.c_uint32(0xDEADBEEF)
        self.assertEqual(self.lib.AveronRegionFixture_SelectRegionalHeal(
            maps, 1, 3, 7, 1, 2, HealReader(), None, ctypes.byref(selected)), 0)
        self.assertEqual(self.lib.AveronRegionFixture_SelectRegionalHeal(
            maps, 1, 3, 7, 1, 2, read, None, None), 0)
        for source, count, current in ((None, 1, (3, 7)), (maps, 0, (3, 7)),
                                       (maps, 1, (259, 7)), (maps, 2, (3, 7))):
            self.assertEqual(self.lib.AveronRegionFixture_SelectRegionalHeal(
                source, count, *current, 1, 2, read, None, ctypes.byref(selected)), 0)
        self.assertEqual(calls, [])
        self.assertEqual(selected.value, 0xDEADBEEF)

    def test_heal_selection_does_not_retry_an_identical_failed_identifier(self):
        maps = (MapBinding * 1)(MapBinding(3, 7, AVERON))
        calls = []

        @HealReader
        def read(identifier, context, group, number):
            calls.append(identifier)
            if len(calls) == 1:
                return 0
            group[0], number[0] = 3, 7
            return 1

        selected = ctypes.c_uint32(0xDEADBEEF)
        self.assertEqual(self.lib.AveronRegionFixture_SelectRegionalHeal(
            maps, 1, 3, 7, 1, 1, read, None, ctypes.byref(selected)), 0)
        self.assertEqual(calls, [1])
        self.assertEqual(selected.value, 0xDEADBEEF)
        calls.clear()
        self.assertEqual(self.lib.AveronRegionFixture_SelectRegionalHeal(
            maps, 1, 3, 7, 1, 2, read, None, ctypes.byref(selected)), 1)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(selected.value, 2)

    def test_fly_destination_policy_truth_table_and_immutable_inputs(self):
        entries = [(3, 1, AVERON), (3, 2, AVERON), (4, 1, SINNOH), (4, 2, SINNOH)]
        maps = (MapBinding * 4)(*(MapBinding(*entry) for entry in entries))
        before = bytes(maps)
        for current in entries:
            for destination in entries:
                for visited in (-1, 0, 1, 2):
                    actual = self.lib.AveronRegionFixture_IsFlyDestinationEligible(
                        maps, 4, *current[:2], *destination[:2], visited)
                    self.assertEqual(actual, visited == 1 and current[2] == destination[2])
        self.assertEqual(bytes(maps), before)

    def test_fly_destination_policy_rejects_invalid_current_or_target(self):
        maps = (MapBinding * 1)(MapBinding(3, 7, AVERON))
        self.assertEqual(self.lib.AveronRegionFixture_IsFlyDestinationEligible(None, 1, 3, 7, 3, 7, 1), 0)
        self.assertEqual(self.lib.AveronRegionFixture_IsFlyDestinationEligible(maps, 0, 3, 7, 3, 7, 1), 0)
        for invalid in ((3, 8), (259, 7), (3, 263), (2**32 - 1, 7), (3, 2**32 - 1)):
            self.assertEqual(self.lib.AveronRegionFixture_IsFlyDestinationEligible(maps, 1, *invalid, 3, 7, 1), 0)
            self.assertEqual(self.lib.AveronRegionFixture_IsFlyDestinationEligible(maps, 1, 3, 7, *invalid, 1), 0)

    def test_fly_destination_policy_rejects_ambiguous_or_unknown_regions(self):
        entries = [(3, 7, AVERON), (3, 8, AVERON)]
        for duplicate in entries:
            maps = (MapBinding * 3)(*(MapBinding(*entry) for entry in (*entries, duplicate)))
            self.assertEqual(self.lib.AveronRegionFixture_IsFlyDestinationEligible(maps, 3, 3, 7, 3, 8, 1), 0)
        for index in (0, 1):
            for region in (0, 3, 257, 258, 2**32 - 1):
                maps = (MapBinding * 2)(*(MapBinding(*entry) for entry in entries))
                maps[index].region = region
                self.assertEqual(self.lib.AveronRegionFixture_IsFlyDestinationEligible(maps, 2, 3, 7, 3, 8, 1), 0)

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
