"""Synthetic, offline negative/positive checks for M1 evidence tools. No ROM data."""
import importlib.util
import json
from pathlib import Path
import subprocess
import struct
import tempfile
import sys
import zlib
import unittest
from unittest.mock import patch

COORDINATION = Path(__file__).resolve().parents[1] / "coordination"


def load(filename, module_name):
    spec = importlib.util.spec_from_file_location(module_name, COORDINATION / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL = load("toolchain_manifest.py", "averon_tool_provenance")
QA = load("qa_evidence_report.py", "averon_qa_reporting")


def png_chunk(name, content=b""):
    crc = zlib.crc32(content, zlib.crc32(name)) & 0xFFFFFFFF
    return struct.pack(">I", len(content)) + name + content + struct.pack(">I", crc)


def valid_one_pixel_png():
    # A real, tiny RGB PNG fixture; NOT an actual emulator screenshot.
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return (QA.PNG + png_chunk(b"IHDR", ihdr)
            + png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
            + png_chunk(b"IEND"))



class ToolPreflightTests(unittest.TestCase):
    def test_source_work_does_not_require_a_compiler_or_emulator(self):
        with patch.object(TOOL, "command_info", return_value={"available": True, "version": "fixture"}) as info:
            result = TOOL.preflight("source")
        self.assertEqual(result["missing"], [])
        self.assertEqual([call.args[0] for call in info.call_args_list], ["git"])

    def test_missing_coordination_dependencies_fail_early(self):
        with patch.object(TOOL, "command_info", side_effect=lambda name: {
                "available": name == "git", "version": None}):
            result = TOOL.preflight("source", ["node", "jq"])
        self.assertEqual(result["status"], "MISSING_REQUIRED_TOOLS")
        self.assertEqual(result["missing"], ["jq", "node"])

    def test_runtime_availability_is_not_display_acceptance(self):
        with patch.object(TOOL, "command_info", return_value={"available": True, "version": None}):
            result = TOOL.preflight("runtime", ["Xvfb"])
        self.assertEqual(result["status"], "TOOLS_AVAILABLE")
        self.assertIn("mgba", result["tools"])
        self.assertTrue(any("working display" in limit for limit in result["limitations"]))

    def test_preflight_cli_needs_no_rom_or_build_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "preflight.json"
            run = subprocess.run([sys.executable, str(COORDINATION / "toolchain_manifest.py"),
                                  "--preflight", "source", "--out", str(out)],
                                 capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(out.read_text())
        self.assertEqual(result["status"], "TOOLS_AVAILABLE")
        self.assertNotIn("rom", result)


class BuildProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.engine = self.root / "Pokemon Game" / "engine"
        self.engine.mkdir(parents=True)
        (self.engine / "Makefile").write_text("all:\n\t@true\n")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Fixture",
                        "-c", "user.email=fixture@example.invalid",
                        "commit", "-qm", "fixture"], cwd=self.root, check=True)
        self.rom = self.root / "fake.gba"
        self.rom.write_bytes(b"synthetic-test-not-commercial-rom")

    def good_tools(self, name, version_args=None):
        return {"available": True, "version": "fixture version 1.0"}

    def test_clean_provenance_never_claims_gameplay_pass(self):
        with patch.object(TOOL, "command_info", side_effect=self.good_tools):
            result = TOOL.collect(self.root, self.engine, self.rom)
        self.assertTrue(result["engine_clean"])
        self.assertEqual(result["status"], "COMPLETE_BUILD_PROVENANCE_NOT_GAMEPLAY_ACCEPTANCE")
        self.assertEqual(result["rom"]["bytes"], self.rom.stat().st_size)
        self.assertEqual(len(result["source_sha"]), 40)
        self.assertEqual(len(result["engine_tree_sha"]), 40)
        self.assertNotIn("GAMEPLAY_PASS", result["status"])

    def test_dirty_engine_is_not_marked_reproducible(self):
        (self.engine / "other.c").write_text("unsaved work\n")
        with patch.object(TOOL, "command_info", side_effect=self.good_tools):
            result = TOOL.collect(self.root, self.engine, self.rom)
        self.assertFalse(result["engine_clean"])
        self.assertEqual(result["status"], "INCOMPLETE_PROVENANCE")
        self.assertTrue(any("uncommitted" in issue for issue in result["problems"]))

    def test_dirty_generator_scripts_also_make_source_provenance_incomplete(self):
        scripts = self.engine.parent / "scripts"
        scripts.mkdir()
        (scripts / "build_source.py").write_text("print('changed generator')\n")
        with patch.object(TOOL, "command_info", side_effect=self.good_tools):
            result = TOOL.collect(self.root, self.engine, self.rom)
        self.assertTrue(result["engine_clean"])
        self.assertFalse(result["scripts_clean"])
        self.assertFalse(result["source_inputs_clean"])
        self.assertEqual(result["status"], "INCOMPLETE_PROVENANCE")
        self.assertTrue(any("generator" in issue for issue in result["problems"]))

    def test_source_without_rom_is_not_build_evidence(self):
        with patch.object(TOOL, "command_info", side_effect=self.good_tools):
            result = TOOL.collect(self.root, self.engine)
        self.assertIsNone(result["rom"])
        self.assertEqual(result["status"], "INCOMPLETE_PROVENANCE")

    def test_missing_compiler_is_not_silently_complete(self):
        def missing(name, version_args=None):
            return {"available": False, "version": None} if name == "arm-none-eabi-gcc" else self.good_tools(name)
        with patch.object(TOOL, "command_info", side_effect=missing):
            result = TOOL.collect(self.root, self.engine, self.rom)
        self.assertEqual(result["status"], "INCOMPLETE_PROVENANCE")

    def test_outside_engine_and_oversized_rom_rejected(self):
        with self.assertRaises(ValueError):
            TOOL.collect(self.root, self.root.parent, self.rom)
        big = self.root / "too_large.gba"
        with big.open("wb") as file:
            file.truncate(TOOL.ROM_LIMIT + 1)
        with self.assertRaisesRegex(ValueError, "32 MiB"):
            TOOL.collect(self.root, self.engine, big)


class QaEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "trace.txt").write_text("REAL INPUT EVENTS NEED INDEPENDENT REVIEW\n")
        (self.root / "scene.png").write_bytes(valid_one_pixel_png())
        (self.root / "saved_state.json").write_text(json.dumps({"badge": 1}))
        self.input = {
            "source_sha": "a" * 40, "rom_sha256": "b" * 64,
            "cases": [{
                "case_id": "Q1", "input_trace": "trace.txt",
                "screenshots": ["scene.png"], "state_observations": [{
                    "statement": "Badge flag observation, not independently verified",
                    "evidence_file": "saved_state.json",
                    "expected": 1, "observed": 1,
                }],
            }],
        }

    def test_complete_evidence_is_never_a_gameplay_pass(self):
        result = QA.inspect_package(self.input, self.root)
        self.assertEqual(result["ready_for_review"], 1)
        self.assertEqual(result["cases"][0]["evidence_status"], "READY_FOR_INDEPENDENT_REVIEW")
        self.assertEqual(result["independent_playtest_verdict"], "NOT_GRANTED_BY_THIS_TOOL")
        self.assertTrue(all(len(f["sha256"]) == 64 for f in result["cases"][0]["files"]))

    def test_missing_frame_trace_or_state_blocks_review_ready(self):
        for key, value in (("screenshots", []), ("input_trace", None), ("state_observations", [])):
            with self.subTest(key=key):
                inp = json.loads(json.dumps(self.input))
                inp["cases"][0][key] = value
                self.assertEqual(QA.inspect_package(inp, self.root)["ready_for_review"], 0)

    def test_incorrect_file_signature_and_traversal_rejected(self):
        inp = json.loads(json.dumps(self.input))
        (self.root / "bad.png").write_text("not actually an image")
        inp["cases"][0]["screenshots"] = ["bad.png"]
        self.assertEqual(QA.inspect_package(inp, self.root)["ready_for_review"], 0)
        inp["cases"][0]["screenshots"] = ["../other.png"]
        report = QA.inspect_package(inp, self.root)
        self.assertIn("path outside evidence root", " ".join(report["cases"][0]["issues"]))

    def test_png_signature_only_or_truncated_png_not_ready(self):
        original = (self.root / "scene.png").read_bytes()
        for payload in (QA.PNG, original[:-4], original[:-12]):
            with self.subTest(payload_len=len(payload)):
                (self.root / "scene.png").write_bytes(payload)
                report = QA.inspect_package(self.input, self.root)
                self.assertEqual(report["ready_for_review"], 0)
                self.assertIn("PNG", " ".join(report["cases"][0]["issues"]))

    def test_corrupt_png_chunk_checksum_fails_closed(self):
        png = bytearray(valid_one_pixel_png())
        png[22] ^= 1  # width/height/format header pixel metadata; CRC now wrong
        (self.root / "scene.png").write_bytes(png)
        report = QA.inspect_package(self.input, self.root)
        self.assertEqual(report["ready_for_review"], 0)
        self.assertIn("CRC", " ".join(report["cases"][0]["issues"]))

    def test_png_trailing_data_not_ready(self):
        (self.root / "scene.png").write_bytes(valid_one_pixel_png() + b"untrusted-tail")
        report = QA.inspect_package(self.input, self.root)
        self.assertEqual(report["ready_for_review"], 0)
        self.assertIn("unexpected bytes", " ".join(report["cases"][0]["issues"]))

    def test_assertion_mismatch_and_hash_absence_flagged(self):
        inp = json.loads(json.dumps(self.input))
        inp["source_sha"] = ""
        inp["cases"][0]["state_observations"][0]["observed"] = 2
        result = QA.inspect_package(inp, self.root)
        self.assertEqual(result["ready_for_review"], 0)
        self.assertIn("mismatch", " ".join(result["cases"][0]["issues"]))
        self.assertIn("source SHA", " ".join(result["cases"][0]["issues"]))

    def test_duplicate_ids_are_invalid(self):
        self.input["cases"].append(dict(self.input["cases"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            QA.inspect_package(self.input, self.root)

    def test_github_failure_not_mislabeled_game_bug(self):
        result = QA.classify_checks([
            {"name": "compile", "status": "completed", "conclusion": "success"},
            {"name": "wrapper diagnostic", "status": "completed", "conclusion": "failure"},
            {"name": "playtest", "status": "in_progress", "conclusion": None},
            {"name": "optional", "status": "completed", "conclusion": "skipped"},
        ])
        self.assertTrue(result["requires_review"])
        self.assertEqual(result["checks"][1]["classification"], "FAILURE_REQUIRES_LOG_REVIEW")
        self.assertEqual(result["checks"][0]["classification"], "CHECK_SUCCEEDED_NOT_GAMEPLAY_ACCEPTANCE")
        self.assertEqual(result["checks"][2]["classification"], "PENDING_OR_NOT_EXECUTED")
        self.assertEqual(result["checks"][3]["classification"], "SKIPPED_OR_INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
