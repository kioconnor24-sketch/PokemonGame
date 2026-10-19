"""Test the expensive combined GBA workflow's explicit-only dispatch policy."""
from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "averon-combined-build.yml"
RUNNER = ROOT / "Pokemon Game/scripts/coordination/run_combined_build.sh"


class CombinedBuildDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.events = cls.workflow.split("\npermissions:", 1)[0]

    def test_only_manual_dispatch_triggers_expensive_build(self):
        self.assertIn("on:\n  workflow_dispatch:", self.events)
        self.assertNotIn("issue_comment:", self.events)
        self.assertNotIn("pull_request:", self.events)
        self.assertNotIn("push:", self.events)
        self.assertNotIn("schedule:", self.events)

    def test_manual_pr_selection_and_main_only_mode_preserved(self):
        self.assertIn("first_pr:", self.events)
        self.assertIn("second_pr:", self.events)
        self.assertEqual(self.events.count('default: "0"'), 2)
        self.assertNotIn('default: "14"', self.events)
        self.assertNotIn('default: "25"', self.events)
        self.assertIn("FIRST_PR: ${{ inputs.first_pr }}", self.workflow)
        self.assertIn("SECOND_PR: ${{ inputs.second_pr }}", self.workflow)
        self.assertIn('bash "Pokemon Game/scripts/coordination/run_combined_build.sh" prepare', self.workflow)

    def test_optional_graphical_smoke_retained(self):
        self.assertIn("graphical_smoke:", self.events)
        self.assertIn("if: ${{ inputs.graphical_smoke }}", self.workflow)
        self.assertIn('run: bash "Pokemon Game/scripts/coordination/run_combined_build.sh" smoke', self.workflow)

    def test_checks_remain_real_and_read_only(self):
        self.assertIn("ref: main", self.workflow)
        self.assertIn("persist-credentials: false", self.workflow)
        self.assertIn('run: bash "Pokemon Game/scripts/coordination/run_combined_build.sh" test', self.workflow)
        self.assertIn('run: bash "Pokemon Game/scripts/coordination/run_combined_build.sh" report', self.workflow)
        self.assertIn("Verify SHA, real test counts", self.workflow)
        self.assertIn("Attach logs, checksums and screenshots ONLY", self.workflow)
        self.assertIn("contents: read", self.workflow)

    def test_retained_tests_are_wired_to_both_path_filters_and_execution(self):
        coordination = (WORKFLOW.parent / "averon-coordination-tests.yml").read_text()
        self.assertEqual(coordination.count('      - "Pokemon Game/scripts/tests/test_combined_dispatch.py"'), 2)
        self.assertIn('-p "test_combined_dispatch.py" -v', coordination)


class CombinedPrepareTests(unittest.TestCase):
    """Run the real prepare shell with local Git and fixture-only API replies.

    Only gh and the downstream engine-contract checker are fixtures. Fetch,
    merge, head pinning and refusals execute the production prepare code. No
    network, GBA builds or gameplay acceptance are involved in these tests.
    """

    def git(self, *args, cwd=None):
        return subprocess.check_output(
            ["git", *args], cwd=cwd or self.clone, text=True,
            stderr=subprocess.PIPE).strip()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.origin = self.root / "origin"
        self.clone = self.origin
        self.origin.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Dispatch Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        checker = self.origin / "Pokemon Game/scripts/coordination/check_integration_contract.py"
        checker.parent.mkdir(parents=True)
        checker.write_text("from pathlib import Path\nPath('contract-called').touch()\n")
        self.git("add", ".")
        self.git("commit", "-m", "fixture main")
        self.base = self.git("rev-parse", "HEAD")
        self.heads = {}
        for number in (1, 2):
            self.git("checkout", "-b", f"feature-{number}", self.base)
            (self.origin / f"feature-{number}.txt").write_text(f"fixture {number}\n")
            self.git("add", ".")
            self.git("commit", "-m", f"fixture {number}")
            self.heads[number] = self.git("rev-parse", "HEAD")
            self.git("update-ref", f"refs/pull/{number}/head", self.heads[number])
        self.git("checkout", "main")
        self.clone = self.root / "checkout"
        self.git("clone", str(self.origin), str(self.clone), cwd=self.root)
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.api = self.root / "api"
        self.api.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        gh = self.bin / "gh"
        gh.write_text("#!/usr/bin/env python3\nimport os,sys\nfrom pathlib import Path\n"
                      "number=sys.argv[2].rsplit('/',1)[-1]\n"
                      "print((Path(os.environ['FIXTURE_API'])/(number+'.json')).read_text())\n")
        gh.chmod(0o755)
        for number in self.heads:
            self.reply(number)
        self.remote_refs = self.git("show-ref", cwd=self.origin)

    def reply(self, number, *, state="open", head_repo="owner/repo", base_repo="owner/repo", sha=None):
        data = dict(state=state, head=dict(sha=sha or self.heads[number], repo=dict(full_name=head_repo)),
                    base=dict(repo=dict(full_name=base_repo)))
        (self.api / f"{number}.json").write_text(json.dumps(data))

    def prepare(self, first="1", second="2"):
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                   FIRST_PR=first, SECOND_PR=second, RUNNER_TEMP=str(self.root / "runner"),
                   GITHUB_REPOSITORY="owner/repo", FIXTURE_API=str(self.api))
        result = subprocess.run(["bash", str(RUNNER), "prepare"], cwd=self.clone, env=env,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=15)
        self.assertEqual(self.remote_refs, self.git("show-ref", cwd=self.origin))
        return result

    def assert_refused(self, result, message):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(message, result.stdout)
        self.assertFalse((self.clone / "contract-called").exists())
        self.assertFalse((self.root / "runner/averon-integration/source-pins.json").exists())

    def test_main_only_pins_real_main_without_pr_fetch(self):
        result = self.prepare("0", "0")
        self.assertEqual(result.returncode, 0, result.stdout)
        pins = json.loads((self.root / "runner/averon-integration/source-pins.json").read_text())
        self.assertEqual(pins, dict(mode="main", main_sha=self.base, pull_requests=[], combined_local_sha=self.base))
        self.assertTrue((self.clone / "contract-called").exists())

    def test_two_open_same_repo_prs_merge_and_pin_actual_heads(self):
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stdout)
        pins = json.loads((self.root / "runner/averon-integration/source-pins.json").read_text())
        self.assertEqual(pins["mode"], "combined")
        self.assertEqual(pins["main_sha"], self.base)
        self.assertEqual(pins["pull_requests"], [dict(number=n, sha=self.heads[n]) for n in (1, 2)])
        self.assertEqual(pins["combined_local_sha"], self.git("rev-parse", "HEAD"))
        for n in (1, 2):
            self.assertTrue((self.clone / f"feature-{n}.txt").exists())
        self.assertTrue((self.clone / "contract-called").exists())

    def test_mixed_main_pr_selection_is_refused(self):
        self.assert_refused(self.prepare("0", "1"), "Select two distinct PRs")

    def test_duplicate_pr_selection_is_refused(self):
        self.assert_refused(self.prepare("1", "1"), "Select two distinct PRs")

    def test_non_numeric_input_is_refused_without_shell_execution(self):
        self.assert_refused(self.prepare("1; touch injected"), "Bad first PR")
        self.assertFalse((self.clone / "injected").exists())

    def test_closed_pr_is_refused(self):
        self.reply(1, state="closed")
        self.assert_refused(self.prepare(), "Only open PRs from this repository")

    def test_fork_head_is_refused(self):
        self.reply(1, head_repo="other/repo")
        self.assert_refused(self.prepare(), "Only open PRs from this repository")

    def test_wrong_base_repository_is_refused(self):
        self.reply(1, base_repo="other/repo")
        self.assert_refused(self.prepare(), "Only open PRs from this repository")

    def test_head_moved_between_api_and_fetch_is_refused(self):
        self.reply(1, sha=self.base)
        self.assert_refused(self.prepare(), "PR head changed during fetch")

    def test_malformed_sha_is_refused(self):
        self.reply(1, sha="not-a-sha")
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.clone / "contract-called").exists())


if __name__ == "__main__":
    unittest.main()
