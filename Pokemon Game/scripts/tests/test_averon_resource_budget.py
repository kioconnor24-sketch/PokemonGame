"""Checks that GBA memory usage is parsed from actual linker output."""
import copy
import importlib.util
import json
import struct
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


class LinkedArtifactTests(unittest.TestCase):
    @staticmethod
    def image(segments=None):
        # (physical address, bytes, memory size); BSS bytes are empty.
        if segments is None:
            segments = [(tool.ROM_BASE, b'ABCD', 4),
                        (tool.ROM_BASE + 8, b'WXYZ', 4), (0x02000000, b'', 128)]
        elf = bytearray(52 + 32 * len(segments))
        elf[:7] = b'\x7fELF\x01\x01\x01'
        struct.pack_into('<HHIIIIIHHHHHH', elf, 16, 2, 40, 1, tool.ROM_BASE, 52, 0, 0,
                         52, 32, len(segments), 0, 0, 0)
        for index, (address, data, memsize) in enumerate(segments):
            offset = len(elf)
            struct.pack_into('<IIIIIIII', elf, 52 + 32 * index, 1, offset, address, address,
                             len(data), memsize, 5, 1)
            elf.extend(data)
        return bytes(elf)

    def test_multiple_segments_gaps_padding_and_ram_bss(self):
        rom = b'ABCD....WXYZ' + b'\xff' * 20
        result = tool.verify_linked_rom(self.image(), rom, 12, 32)
        self.assertEqual(result['matched_load_segments'], 2)
        self.assertEqual(result['matched_load_bytes'], 8)
        self.assertEqual(result['linked_rom_extent_bytes'], 12)
        self.assertEqual(len(result['elf_sha256']), 64)
        self.assertIn('not certified', result['scope'])

    def test_wrong_rom_bytes_fail_even_when_sizes_match(self):
        with self.assertRaisesRegex(ValueError, 'load bytes differ'):
            tool.verify_linked_rom(self.image(), b'ABCD....FAIL', 12, 32)

    def test_wrong_linker_log_extent_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'differs from linker log'):
            tool.verify_linked_rom(self.image(), b'ABCD....WXYZ', 11, 32)

    def test_truncated_or_wrong_elf_contract_fails_closed(self):
        for position, value in ((4, 2), (5, 2), (16, 1), (18, 3), (40, 51), (42, 31), (44, 0)):
            bad = bytearray(self.image()); bad[position] = value
            with self.subTest(position=position), self.assertRaises(ValueError):
                tool.verify_linked_rom(bytes(bad), b'ABCD....WXYZ', 12, 32)
        for bad in (b'not ELF', self.image()[:51], self.image()[:60], self.image()[:-1]):
            with self.subTest(size=len(bad)), self.assertRaises(ValueError):
                tool.verify_linked_rom(bad, b'ABCD....WXYZ', 12, 32)

    def test_segment_bounds_and_invalid_file_memory_sizes(self):
        for segments, rom in (([(tool.ROM_BASE, b'ABCD', 3)], b'ABCD'),
                              ([(tool.ROM_BASE - 1, b'ABCD', 4)], b'ABCD'),
                              ([(tool.ROM_BASE, b'ABCD', 4)], b'ABC'),
                              ([(tool.ROM_BASE, b'ABCD', 4), (tool.ROM_BASE + 32, b'Z', 1)], b'ABCD' + b'.' * 28 + b'Z')):
            with self.subTest(segments=segments), self.assertRaises(ValueError):
                tool.verify_linked_rom(self.image(segments), rom, len(rom), 32)

    def test_overlapping_segments_or_missing_rom_start_are_refused(self):
        for segments, rom in (([(tool.ROM_BASE, b'ABCD', 4), (tool.ROM_BASE + 2, b'CD', 2)], b'ABCD'),
                              ([(0x02000000, b'', 128)], b'ABCD'),
                              ([(tool.ROM_BASE + 1, b'BCD', 3)], b'ABCD')):
            with self.subTest(segments=segments), self.assertRaises(ValueError):
                tool.verify_linked_rom(self.image(segments), rom, 4, 32)

    def test_optional_report_binding_preserves_legacy_output(self):
        with tempfile.TemporaryDirectory() as directory:
            elf, rom = Path(directory) / 'game.elf', Path(directory) / 'game.gba'
            elf.write_bytes(self.image()); rom.write_bytes(b'ABCD....WXYZ')
            log = log_with_usage(rom=12)
            self.assertNotIn('linked_artifact_verification', tool.report(log, rom))
            result = tool.report(log, rom, elf=elf)
            self.assertEqual(result['linked_artifact_verification']['rom_sha256'], result['rom_artifact']['sha256'])
            with self.assertRaisesRegex(ValueError, 'requires --rom'):
                tool.report(log, elf=elf)

    def test_cli_refuses_mixed_artifacts_without_publishing_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'game.elf').write_bytes(self.image())
            (root / 'game.gba').write_bytes(b'ABCD....FAIL')
            (root / 'build.log').write_text(log_with_usage(rom=12))
            result = subprocess.run([sys.executable, str(FILE), '--log', str(root / 'build.log'),
                                     '--rom', str(root / 'game.gba'), '--elf', str(root / 'game.elf'),
                                     '--json', str(root / 'report.json')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('load bytes differ', result.stderr)
            self.assertFalse((root / 'report.json').exists())


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

    @staticmethod
    def linker_map(size=256, add=True):
        text = ('Discarded input sections\n .rodata 0x08000000 0x40 data/discarded.o\n'
                'Linker script and memory map\n'
                f'.rodata 0x08000000 0x{size+32:x}\n'
                f' .rodata 0x08000000 0x{size:x} build/emerald-release/data/maps.o\n'
                f' .rodata.named\n                0x{0x08000000+size:x} 0x20 data/layouts.o\n'
                ' .text 0x08001000 0x100 /tmp/abcd.ltrans0.ltrans.o\n'
                ' .bss 0x02000000 0x100 src/save.o\n')
        if add: text += ' .rodata 0x08002000 0x40 graphics/new_tiles.o\n'
        return text

    def test_contributions_exclude_outputs_discarded_ram_and_lto(self):
        row = tool.linked_inputs(self.linker_map(), 26722880, 32*1024*1024)
        self.assertEqual(row['objects'], {'data/maps.o': 256, 'data/layouts.o': 32, 'graphics/new_tiles.o': 64})
        self.assertEqual(row['attributed_bytes'], 352)
        self.assertEqual(row['unattributed_bytes'], 26722880-352)

    def test_contribution_growth_removal_and_residual(self):
        before = tool.report(LOG, profile=PROFILE, linker_map=self.linker_map(add=False))
        now = tool.report(log_with_usage(rom=26723040), profile=PROFILE,
                          linker_map=self.linker_map(352), baseline=before)
        c = now['comparison']['contributions']
        self.assertEqual(c['attributed_delta_bytes'], 160)
        self.assertEqual(c['unattributed_delta_bytes'], 0)
        self.assertEqual(c['changed_objects'][0]['object'], 'data/maps.o')
        back = tool.report(LOG, profile=PROFILE, linker_map=self.linker_map(add=False), baseline=now)
        self.assertEqual(back['comparison']['contributions']['changed_objects'][0]['delta_bytes'], -96)

    def test_missing_attribution_pair_does_not_fake_asset_removal(self):
        before = tool.report(LOG, profile=PROFILE)
        now = tool.report(LOG, profile=PROFILE, baseline=before, linker_map=self.linker_map())
        self.assertNotIn('contributions', now['comparison'])

    def test_invalid_map_and_out_of_range_inputs_fail(self):
        for text in ('bad map', 'Linker script and memory map\n .bss 0x02000000 0x10 src/foo.o',
                     'Linker script and memory map\n .rodata 0x09ffffff 0x20 data/foo.o'):
            with self.assertRaises(ValueError): tool.linked_inputs(text, 26722880, 32*1024*1024)

    def test_bad_baseline_contributions_fail(self):
        before = tool.report(LOG, profile=PROFILE, linker_map=self.linker_map())
        for mutation in (lambda r: r.update(objects=[]),
                         lambda r: r['objects'].update({'bad.o': True}),
                         lambda r: r.update(attributed_bytes=0),
                         lambda r: r.update(unattributed_bytes=-1),
                         lambda r: r.update(unattributed_bytes=r['unattributed_bytes']+1)):
            bad = copy.deepcopy(before)
            mutation(bad['linker_inputs'])
            with self.assertRaises(ValueError):
                tool.report(LOG, profile=PROFILE, baseline=bad, linker_map=self.linker_map())

    def test_cli_map_attribution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log, linker_map, output = root/'build.log', root/'build.map', root/'out.json'
            log.write_text(LOG);linker_map.write_text(self.linker_map())
            result = subprocess.run([sys.executable, str(FILE), '--log', str(log), '--json', str(output),
                                     '--linker-map', str(linker_map)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text())['linker_inputs']['attributed_bytes'], 352)

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
