"""Reject stale, changed, forged or incomplete native evidence without a ROM."""
import copy
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.request
import zipfile

spec = importlib.util.spec_from_file_location(
    "native_evidence", Path(__file__).resolve().parents[1] / "native-test-evidence.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
HEAD, BEFORE, MAIN, MERGE = (c * 40 for c in "abcd")
REPO = "kioconnor24-sketch/PokemonGame"
LOG = b"- Tests PASSED: 329\n- Tests TOTAL: 329\n"


def run():
    return dict(id=1, event="pull_request", conclusion="success", path=m.WORKFLOW,
                head_sha=BEFORE, head_branch="codex/work",
                head_repository={"full_name": REPO})


def proof():
    inputs = {"engine": "engine", "scripts": "scripts", "toolchain": {"arm": "12"}}
    return dict(schema=2, run_id=1, run_attempt=1, source_head=BEFORE, checkout=MERGE,
                executed=True, reusable=True, inputs=inputs, source_inputs=inputs,
                worktree_unchanged=True, execution_inputs_match_capture=True,
                native=m.native_counts(LOG.decode()), native_log_sha256=hashlib.sha256(LOG).hexdigest())


class ProofRules(unittest.TestCase):
    def valid(self, value, current=None, source=None, trusted=None):
        return m.valid_proof(value, run(), current or proof()["inputs"],
                             source or proof()["inputs"],
                             trusted or {m.WORKFLOW: "w", m.HELPER: "h"})

    def test_exact_full_success_is_reusable(self):
        self.assertTrue(self.valid(proof()))

    def test_changed_engine_scripts_and_toolchain_are_rejected(self):
        for field in ("engine", "scripts", "toolchain"):
            with self.subTest(field=field):
                current = copy.deepcopy(proof()["inputs"])
                current[field] = "changed"
                self.assertFalse(self.valid(proof(), current=current))

    def test_wrong_run_source_checkout_or_execution_claim_is_rejected(self):
        for key, value in (("run_id", 2), ("run_attempt", 2), ("source_head", HEAD),
                           ("checkout", "not-a-sha"), ("executed", False),
                           ("reusable", False), ("native_log_sha256", ""), ("schema", 1),
                           ("worktree_unchanged", False), ("execution_inputs_match_capture", False)):
            with self.subTest(key=key):
                item = proof(); item[key] = value
                self.assertFalse(self.valid(item))

    def test_source_and_merged_context_must_agree(self):
        item = proof(); item["source_inputs"] = {"engine": "old-base"}
        self.assertFalse(self.valid(item))
        self.assertFalse(self.valid(proof(), source={"engine": "other-source"}))

    def test_nonpositive_failed_skipped_and_malformed_counts_are_rejected(self):
        for counts in ({}, [], {"passed": True, "total": True},
                       {"passed": 0, "total": 0, "failed": 0, "skipped": 0},
                       {"passed": 328, "total": 329, "failed": 1, "skipped": 0},
                       {"passed": 329, "total": 329, "failed": 0, "skipped": 1}):
            with self.subTest(counts=counts):
                item = proof(); item["native"] = counts
                self.assertFalse(self.valid(item))

    def test_missing_trusted_definition_is_rejected(self):
        self.assertFalse(self.valid(proof(), trusted={m.WORKFLOW: "w", m.HELPER: None}))

    def test_log_parser_accepts_actual_colored_summary(self):
        log = "- Tests \x1b[32mPASSED\x1b[0m: 329\n- Tests TOTAL: 329\n"
        self.assertEqual(m.native_counts(log), proof()["native"])

    def test_log_parser_rejects_empty_partial_failed_and_skipped_runs(self):
        for text in ("", "- Tests PASSED: 1", "- Tests PASSED: 0\n- Tests TOTAL: 0",
                     "- Tests PASSED: 328\n- Tests TOTAL: 329",
                     LOG.decode() + "- Tests FAILED: 1\n",
                     LOG.decode() + "- Tests SKIPPED: 1\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                m.native_counts(text)


class RunScope(unittest.TestCase):
    def eligible(self, item, branch="codex/work"):
        return m.eligible_run(item, repo=REPO, branch=branch,
                              source_head=HEAD, current_run=2)

    def test_successful_branch_and_protected_main_are_candidates(self):
        self.assertTrue(self.eligible(run()))
        item = run(); item.update(event="push", head_branch="main")
        self.assertTrue(self.eligible(item))
        item["event"] = "workflow_dispatch"
        self.assertTrue(self.eligible(item))

    def test_failure_current_run_wrong_workflow_repo_or_event_is_rejected(self):
        for key, value in (("conclusion", "failure"), ("id", 2),
                           ("path", "other.yml"), ("event", "schedule"),
                           ("head_repository", None), ("head_sha", "invalid")):
            with self.subTest(key=key):
                item = run(); item[key] = value
                self.assertFalse(self.eligible(item))

    def test_other_branch_and_nonmain_push_are_rejected(self):
        item = run(); item["head_branch"] = "other"
        self.assertFalse(self.eligible(item))
        item["event"] = "push"
        self.assertFalse(self.eligible(item))


class ArtifactRules(unittest.TestCase):
    def archive(self, value, log=LOG, path=m.PROOF):
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr(path, json.dumps(value))
            z.writestr("averon-native-tests.log", log)
        return out.getvalue()

    def fetch(self, data, expired=False):
        api = m.GitHub(REPO)
        with patch.object(api, "get", side_effect=[
                {"artifacts": [{"id": 3, "name": m.ARTIFACT, "expired": expired}]}, data]):
            return api.proof(1)

    def test_real_log_hash_and_counts_must_match_receipt(self):
        self.assertEqual(self.fetch(self.archive(proof())), proof())
        self.assertIsNone(self.fetch(self.archive(proof(), b"changed")))

    def test_missing_expired_or_oversized_proof_is_not_usable(self):
        self.assertIsNone(self.fetch(self.archive(proof()), expired=True))
        self.assertIsNone(self.fetch(self.archive(proof(), path="unexpected.json")))
        value = proof(); value["padding"] = "x" * 65536
        self.assertIsNone(self.fetch(self.archive(value)))

    def test_auth_header_does_not_follow_storage_redirect(self):
        req = urllib.request.Request("https://api.github.com/example",
                                     headers={"Authorization": "Bearer test"})
        redirected = m.StripCrossOriginAuth().redirect_request(
            req, None, 302, "redirect", {}, "https://storage.example/file")
        self.assertIsNone(redirected.get_header("Authorization"))
        with self.assertRaises(ValueError):
            m.StripCrossOriginAuth().redirect_request(
                req, None, 302, "redirect", {}, "http://api.github.com/file")


class Selection(unittest.TestCase):
    def args(self):
        return SimpleNamespace(checkout=MERGE, source_head=HEAD, trusted_main=MAIN,
                               repo=REPO, branch="codex/work", run_id=2, run_attempt=1)

    def select(self, *, changed_base=False, changed_workflow=False,
               changed_old_workflow=False, comparison="ahead", prior_failure=False):
        api = m.GitHub(REPO)
        item = proof()
        def objects(ref, path, optional=False):
            return "changed" if ((changed_workflow and ref == MERGE)
                                  or (changed_old_workflow and ref == BEFORE)) else path
        def fingerprints(ref, compiler):
            return {"changed": True} if changed_base and ref == MERGE else item["inputs"]
        def response(path, **kwargs):
            if path.startswith("/compare/"):
                return {"status": comparison}
            previous = run()
            if prior_failure:previous["conclusion"] = "failure"
            return {"workflow_runs": [previous]}
        with patch.object(m, "inputs", side_effect=fingerprints), \
             patch.object(m, "object_id", side_effect=objects), \
             patch.object(m, "ensure_commit"), patch.object(m, "GitHub", return_value=api), \
             patch.object(api, "get", side_effect=response), patch.object(api, "proof", return_value=item):
            return m.select(self.args(), {})

    def test_complete_matching_history_reuses_full_run(self):
        self.assertEqual(self.select()[0], 1)

    def test_new_base_undeployed_workflow_and_divergent_history_fall_back(self):
        for option in ({"changed_base": True}, {"changed_workflow": True},
                       {"changed_old_workflow": True}, {"comparison": "diverged"}):
            with self.subTest(option=option):
                self.assertIsNone(self.select(**option)[0])

    def test_newer_matching_failure_and_rerun_attempts_require_fresh_tests(self):
        self.assertIsNone(self.select(prior_failure=True)[0])
        args = self.args();args.run_attempt = 2
        self.assertIsNone(m.select(args, {})[0])

    def test_newer_failure_with_unavailable_history_cannot_reuse_older_success(self):
        api = m.GitHub(REPO)
        failed = run()
        failed.update(id=3, head_sha="f" * 40, conclusion="failure",
                      updated_at="2026-11-02T01:00:00Z")
        passed = run()
        passed["updated_at"] = "2026-11-02T00:00:00Z"

        def response(path, **kwargs):
            if path.startswith("/compare/" + failed["head_sha"]):
                raise OSError("newer run ancestry is temporarily unavailable")
            if path.startswith("/compare/"):
                return {"status": "ahead"}
            return {"workflow_runs": [passed, failed]}

        with patch.object(m, "inputs", return_value=proof()["inputs"]), \
             patch.object(m, "object_id", side_effect=lambda ref, path, optional=False: path), \
             patch.object(m, "ensure_commit"), patch.object(m, "GitHub", return_value=api), \
             patch.object(api, "get", side_effect=response), \
             patch.object(api, "proof", return_value=proof()) as older_proof:
            self.assertIsNone(m.select(self.args(), {})[0])
            older_proof.assert_not_called()

    def test_lookup_budget_falls_back_without_waiting_for_old_runs(self):
        with patch.object(m.time, "monotonic", side_effect=[0, 31]):
            self.assertIsNone(self.select()[0])

    def test_cache_unavailable_does_not_block_native_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "receipt.json"
            args = ["evidence", "select", "--checkout", MERGE, "--source-head", HEAD,
                    "--run-id", "2", "--repo", REPO, "--branch", "codex/work", "--out", str(out)]
            with patch("sys.argv", args), patch.object(m, "toolchain", side_effect=OSError), \
                 patch("sys.stdout", new=io.StringIO()) as stdout:
                m.main()
            self.assertIn("reused=false", stdout.getvalue())
            self.assertFalse(json.loads(out.read_text())["reused"])


class RealGitInputs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.git("config", "user.name", "Native evidence fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        for path in ("Pokemon Game/engine/input.c", m.HELPER, m.WORKFLOW):
            p = self.root / path; p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("accepted input\n")
        self.before = self.commit("accepted native inputs")
        (self.root / "README.md").write_text("evidence-only revision\n")
        self.head = self.commit("publish evidence")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True,
                                       stderr=subprocess.DEVNULL).strip()

    def commit(self, message):
        self.git("add", "."); self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def test_real_immutable_git_inputs_reuse_only_equivalent_payload(self):
        with contextlib.chdir(self.root):
            compiler = {"fixture": "toolchain"}
            old = m.inputs(self.before, compiler)
            self.assertEqual(old, m.inputs(self.head, compiler))
            item = proof(); item.update(source_head=self.before, checkout=self.before,
                                        inputs=old, source_inputs=old)
            previous = run(); previous["head_sha"] = self.before
            api = m.GitHub(REPO)
            def response(path, **kwargs):
                if path.startswith("/compare/"):
                    self.assertEqual(path, f"/compare/{self.before}...{self.head}")
                    self.git("merge-base", "--is-ancestor", self.before, self.head)
                    return {"status": "ahead"}
                return {"workflow_runs": [previous]}
            args = SimpleNamespace(checkout=self.head, source_head=self.head,
                                   trusted_main=self.head, repo=REPO,
                                   branch="codex/work", run_id=2, run_attempt=1)
            with patch.object(m, "GitHub", return_value=api), \
                 patch.object(api, "get", side_effect=response), \
                 patch.object(api, "proof", return_value=item):
                self.assertEqual(m.select(args, compiler)[0], 1)
                (self.root / "Pokemon Game/engine/input.c").write_text("changed native input\n")
                changed = self.commit("real native change")
                args.checkout = args.source_head = args.trusted_main = changed
                self.assertIsNone(m.select(args, compiler)[0])

    def test_post_build_changes_or_flags_invalidate_the_prior_selection(self):
        with contextlib.chdir(self.root):
            expected = m.digest(m.inputs(self.head, {}))
            out = self.root / "receipt.json"
            args = ["evidence", "confirm", "--checkout", self.head, "--source-head", self.head,
                    "--run-id", "2", "--repo", REPO, "--branch", "codex/work",
                    "--fingerprint", expected, "--out", str(out)]
            def check(compiler=None):
                with patch("sys.argv", args), patch.object(m, "toolchain", return_value=compiler or {}), \
                     patch("sys.stdout", new=io.StringIO()):
                    m.main()
                return json.loads(out.read_text())["reused"]
            self.assertTrue(check())
            native = self.root / "Pokemon Game/engine/input.c"
            native.write_text("mutation after compilation\n")
            self.assertFalse(check())
            native.write_text("accepted input\n")
            extra = self.root / "Pokemon Game/engine/untracked.c"
            extra.write_text("extra compiler input\n")
            self.assertFalse(check())
            extra.unlink()
            self.assertFalse(check({"flags": "changed"}))

    def test_full_run_recorder_rejects_mutation_or_changed_execution_flags(self):
        with contextlib.chdir(self.root):
            expected = m.digest(m.inputs(self.head, {}))
            log = self.root / "native.log"
            log.write_bytes(LOG)
            out = self.root / "proof.json"
            args = ["evidence", "record", "--checkout", self.head, "--source-head", self.head,
                    "--run-id", "2", "--repo", REPO, "--branch", "codex/work",
                    "--fingerprint", expected, "--native-log", str(log), "--out", str(out)]
            def record(compiler=None):
                with patch("sys.argv", args), patch.object(m, "toolchain", return_value=compiler or {}):
                    m.main()
                return json.loads(out.read_text())
            args[1] = "capture"
            with patch("sys.argv", args), patch.object(m, "toolchain", return_value={}), \
                 patch("sys.stdout", new=io.StringIO()) as captured:
                m.main()
            self.assertIn("fingerprint=" + expected, captured.getvalue())
            args[1] = "record"
            self.assertTrue(record()["reusable"])
            native = self.root / "Pokemon Game/engine/input.c"
            native.write_text("changed during native execution\n")
            self.assertFalse(record()["reusable"])
            native.write_text("accepted input\n")
            extra = self.root / "Pokemon Game/engine/new.c"
            extra.write_text("added during native execution\n")
            self.assertFalse(record()["reusable"])
            extra.unlink()
            self.assertFalse(record({"flags": "changed after execution"})["reusable"])
            args[args.index("--fingerprint") + 1] = ""
            self.assertFalse(record()["reusable"])


if __name__ == "__main__":
    unittest.main()
