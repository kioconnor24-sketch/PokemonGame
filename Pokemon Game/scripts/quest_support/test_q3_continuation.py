#!/usr/bin/env python3
"""Fail-closed regression tests for q3_continuation.sh.

Runs the real script in a scratch directory with stub mgba, xdotool,
flash decoder and frame matcher, so no ROM, emulator or display is needed.
Each missing piece of evidence must give a non-zero exit; the complete
case must still reach Q3X_DONE.
"""
import os
import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name("q3_continuation.sh").resolve()

DECODER = '''
def decode_flash_q2(data):
    if data.startswith(b"GARBAGE"):
        raise ValueError("no valid slot")
    group, num = (75, 11) if data.startswith(b"CLINIC") else (75, 3)
    return {"slot": 0, "saveCounter": 2, "mapGroup": group, "mapNum": num,
            "x": 7, "y": 4, "warpId": 255}
'''

PRELUDE = '''
set -e
sleep() { :; }
capture() { : > "$RUNNER_TEMP/averon-playtest/$1.png"; }
press() { :; }
'''

OBSERVER_OK = '''qa_q3_outcome=REAL_ELIO_BATTLE_EXIT_SCOPED
python3() { if [ "$2" = "$Q3X" ]; then return 0; fi; command python3 "$@"; }
'''


class Q3ContinuationTest(unittest.TestCase):
    def run_script(self, flash=None, window=True, frame_rc=0, observer_ok=True):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "Pokemon Game/engine").mkdir(parents=True)
            qa = root / "Pokemon Game/scripts/qa"
            qa.mkdir(parents=True)
            (qa / "quest_state_controller.py").write_text(DECODER)
            if flash is not None:
                (root / "Pokemon Game/engine/pokeemerald.sav").write_bytes(flash)
            support = root / "support"
            support.mkdir()
            (support / "frame_match.py").write_text(
                f"import sys\nprint('score=0.99')\nsys.exit({frame_rc})\n")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            (bin_dir / "mgba").write_text("#!/bin/sh\nexit 0\n")
            (bin_dir / "xdotool").write_text(
                "#!/bin/sh\necho 4242\n" if window else "#!/bin/sh\nexit 1\n")
            for f in bin_dir.iterdir():
                f.chmod(0o755)
            (root / "temp/averon-playtest").mkdir(parents=True)
            emu = subprocess.Popen(["sleep", "30"])
            env = dict(os.environ,
                       PATH=f"{bin_dir}:{os.environ['PATH']}",
                       RUNNER_TEMP=str(root / "temp"),
                       Q3X=str(support / "q3_post_battle_observer.py"),
                       qa_q3_outcome="NOT_REACHED", qa_fifo="", win="",
                       emu_pid=str(emu.pid), qa_pid="")
            try:
                result = subprocess.run(
                    ["bash", "-c", PRELUDE + (OBSERVER_OK if observer_ok else "") + SCRIPT.read_text()],
                    cwd=root, env=env, capture_output=True, text=True, timeout=60)
            finally:
                emu.kill()
                emu.wait()
            return result.returncode, result.stdout + result.stderr

    def test_missing_flash_fails(self):
        rc, out = self.run_script(flash=None)
        self.assertEqual(rc, 4, out)
        self.assertIn("Q3X_FLASH_MISSING", out)
        self.assertNotIn("Q3X_DONE", out)

    def test_empty_flash_fails(self):
        rc, out = self.run_script(flash=b"")
        self.assertEqual(rc, 4, out)

    def test_undecodable_flash_fails(self):
        rc, out = self.run_script(flash=b"GARBAGE")
        self.assertEqual(rc, 6, out)
        self.assertIn("Q3X_SAVED_SLOT_INVALID", out)

    def test_flash_saved_elsewhere_fails(self):
        rc, out = self.run_script(flash=b"ELSEWHERE")
        self.assertEqual(rc, 6, out)
        self.assertIn("Q3X_SAVED_SLOT_NOT_CLINIC", out)

    def test_missing_relaunch_window_fails(self):
        rc, out = self.run_script(flash=b"CLINIC", window=False)
        self.assertEqual(rc, 5, out)
        self.assertIn("Q3X_RELAUNCH_BLOCKED", out)
        self.assertNotIn("Q3X_DONE", out)

    def test_continue_not_shown_fails(self):
        rc, out = self.run_script(flash=b"CLINIC", frame_rc=1)
        self.assertEqual(rc, 3, out)

    def test_observer_not_reached_fails_even_with_full_evidence(self):
        rc, out = self.run_script(flash=b"CLINIC", observer_ok=False)
        self.assertEqual(rc, 99, out)  # Q3X_RC=99: observer never ran

    def test_complete_evidence_passes(self):
        rc, out = self.run_script(flash=b"CLINIC")
        self.assertEqual(rc, 0, out)
        self.assertIn("Q3X_CONTINUE_RESULT CLINIC_FIELD", out)
        self.assertIn("Q3X_DONE", out)

if __name__ == "__main__":
    unittest.main()
