"""Execute the proposed workflow profile selector without building a ROM."""
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / "Averon_Codex_Handoff/design/sinnoh/battle-frontier-dev/ci-workflow.proposal.yml"

class WorkflowProfiles(unittest.TestCase):
    def setUp(self):
        self.source = WORKFLOW.read_text()
        self.selector = next(line.strip() for line in self.source.splitlines() if 'case "$SCENE_PROFILE"' in line)

    def test_normal_and_release(self):
        for profile, expected in [("NORMAL", "0 pokeemerald.gba"), ("RELEASE", "1 pokeemerald-release.gba")]:
            with self.subTest(profile=profile):
                output = subprocess.check_output(["bash", "-euc", self.selector + '\nprintf "%s %s" "$scene_release" "$scene_rom"'], env={**os.environ, "SCENE_PROFILE": profile}, text=True)
                self.assertEqual(output, expected)

    def test_unknown_profile_fails(self):
        self.assertEqual(subprocess.run(["bash", "-euc", self.selector], env={**os.environ, "SCENE_PROFILE": "INVALID"}).returncode, 2)

    def test_all_evidence_uses_selected_rom(self):
        for command in ['test -s "$scene_rom"', 'sha256sum "$scene_rom"', "stat -c '%s' \"$scene_rom\"", '--rom "$scene_rom"']:
            self.assertIn(command, self.source)
        self.assertIn('FILE_NAME := $(FILE_NAME)-release', (ROOT / "engine/Makefile").read_text())

if __name__ == "__main__":
    unittest.main()
