"""Fail-closed regression fixtures for one-line scripted-core staging."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from stage_scripted_core import (
    REGISTRY, REGISTRATION, StageError, prepare, strip_registration,
    verify_core_files,
)


class StageScriptedCoreTests(unittest.TestCase):
    BASE = b'header\n\t.include "data/averon_optional_sidequests.inc"\nfooter\n'

    def test_accepts_only_one_registration(self):
        full = self.BASE.replace(b"footer\n", REGISTRATION + b"footer\n")
        self.assertEqual(strip_registration(full, self.BASE), self.BASE)

    def test_missing_registration_rejected(self):
        with self.assertRaisesRegex(StageError, "found 0"):
            strip_registration(self.BASE, self.BASE)

    def test_duplicate_registration_rejected(self):
        with self.assertRaisesRegex(StageError, "found 2"):
            strip_registration(REGISTRATION * 2 + self.BASE, self.BASE)

    def test_unanticipated_shared_source_change_rejected(self):
        full = self.BASE.replace(b"header\n", b"unexpected\n") + REGISTRATION
        with self.assertRaisesRegex(StageError, "differs from main"):
            strip_registration(full, self.BASE)

    def test_wrong_registration_layout_rejected(self):
        with self.assertRaisesRegex(StageError, "found 0"):
            strip_registration(self.BASE + b' .include "data/scripts/averon_scripted_battle.inc"\n', self.BASE)

    def test_unexpected_inline_registration_rejected(self):
        with self.assertRaisesRegex(StageError, "standalone"):
            strip_registration(self.BASE + b"junk" + REGISTRATION, self.BASE)

    def fixture(self, directory: Path):
        engine = directory / "Pokemon Game/engine"
        for f in (
            "src/averon_scripted_battle.c", "include/averon_scripted_battle.h",
            "test/averon_scripted_battle.c", "test/averon_scripted_battle_engine.c",
        ):
            (engine / f).parent.mkdir(parents=True, exist_ok=True)
            (engine / f).write_text("source fixture\n")
        p = engine / "data/scripts/averon_scripted_battle.inc"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\t.macro averon_scripted_battle\n\t.endm\n"
                     "\t.macro averon_recover_in_place\n\t.endm\n"
                     "\t.macro averon_respawn\n\t.endm\n")
        p = engine / "include/config/battle.h"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("#define B_FLAG_NO_WHITEOUT FLAG_SPECIAL_FLAG_UNUSED_0x4003\n")
        return engine

    def test_core_files_missing_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(StageError, "Missing staged core"):
                verify_core_files(Path(tmp))

    def test_unsafe_production_macro_usage_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = self.fixture(Path(tmp))
            (engine / "data/scene.inc").write_text("Thing::\n    averon_scripted_battle 1, 2\n")
            with self.assertRaisesRegex(StageError, "Real script invokes"):
                verify_core_files(Path(tmp))

    def test_missing_ram_flag_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = self.fixture(Path(tmp))
            (engine / "include/config/battle.h").write_text("/* bad */\n")
            with self.assertRaisesRegex(StageError, "RAM-only"):
                verify_core_files(Path(tmp))

    def test_end_to_end_real_git_baseline_and_disposable_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = self.fixture(root)
            reg = root / REGISTRY
            reg.parent.mkdir(parents=True, exist_ok=True)
            reg.write_bytes(self.BASE)
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE).decode().strip()
            git("init")
            git("config", "user.email", "staged@example.invalid")
            git("config", "user.name", "staged CI")
            git("add", ".")
            git("commit", "-m", "original")
            base_sha = git("rev-parse", "HEAD")
            reg.write_bytes(REGISTRATION + self.BASE)
            out = root / "result.json"
            result = prepare(root, base_sha, out)
            self.assertTrue(out.is_file())
            self.assertEqual(reg.read_bytes(), self.BASE)
            self.assertTrue(result["registration_removed_in_disposable_worktree"])
            self.assertFalse(result["actual_quest_qa_accepted"])
            self.assertFalse(result["protected_file_handoff_or_merge_approval"])

    def test_unexpected_registration_does_not_mutate_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = self.fixture(root)
            reg = root / REGISTRY
            reg.parent.mkdir(parents=True, exist_ok=True)
            reg.write_bytes(self.BASE + REGISTRATION + b"unapproved\n")
            before = reg.read_bytes()
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE).decode().strip()
            git("init")
            git("config", "user.email", "staged@example.invalid")
            git("config", "user.name", "staged CI")
            git("add", ".")
            git("commit", "-m", "original")
            sha = git("rev-parse", "HEAD")
            with self.assertRaises(StageError):
                prepare(root, sha, root / "result.json")
            self.assertEqual(reg.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
