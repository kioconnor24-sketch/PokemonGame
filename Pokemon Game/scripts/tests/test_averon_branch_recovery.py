"""Real temporary Git histories, including squash, conflict and post-merge work."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'audit-averon-branch-recovery.py'
spec = importlib.util.spec_from_file_location('recovery', SCRIPT)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        self.write('base', 'old\n')
        self.base = self.commit('base')
        self.git('switch', '-qc', 'feature')
        self.write('feature', 'retained evidence\n')
        self.head = self.commit('feature')
        self.git('switch', '-q', 'main')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL).decode().strip()

    def write(self, path, text):
        (self.repo / path).write_text(text)

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-qm', message)
        return self.git('rev-parse', 'HEAD')

    def squash(self, changed=False):
        self.git('merge', '--squash', 'feature')
        if changed:
            self.write('feature', 'different combined result\n')
        self.merge = self.commit('squash')

    def classify(self, **changes):
        data = dict(branch={'name': 'feature', 'sha': self.head}, main=self.git('rev-parse', 'main'),
                    prs=[dict(number=1, state='closed', merged_at='fixture',
                              head={'ref': 'feature', 'sha': self.head}, merge_commit_sha=self.merge)])
        data.update(changes)
        return tool.classify(tool.Git(self.repo), **data)

    def test_squash_is_proven_without_ancestor_shortcut(self):
        self.squash()
        self.assertFalse(tool.Git(self.repo).ancestor(self.head, self.merge))
        row = self.classify()
        self.assertEqual(row['classification'], 'INTEGRATED_WITH_NO_UNIQUE_WORK')
        self.assertTrue(row['deletion_candidate'])

    def test_combined_changed_feature_is_unknown_not_deletable(self):
        self.squash(changed=True)
        row = self.classify()
        self.assertEqual(row['classification'], 'UNKNOWN')
        self.assertFalse(row['deletion_candidate'])
        self.assertIn('feature', row['unaccounted_paths'])

    def test_later_main_edit_does_not_erase_the_integration_receipt(self):
        self.squash()
        self.write('feature', 'later approved replacement\n')
        self.commit('later edit')
        self.assertTrue(self.classify()['deletion_candidate'])

    def test_post_merge_branch_work_is_retained(self):
        self.squash()
        old = self.head
        self.git('switch', '-q', 'feature')
        self.write('new', 'unmerged\n')
        newer = self.commit('new work')
        row = self.classify(branch={'name': 'feature', 'sha': newer}, prs=[dict(number=1,
            state='closed', merged_at='fixture', head={'ref': 'feature', 'sha': old}, merge_commit_sha=self.merge)])
        self.assertEqual(row['classification'], 'UNIQUE_UNMERGED_WORK')
        self.assertFalse(row['deletion_candidate'])

    def test_active_checkpoint_and_protection_override_integrated_status(self):
        self.squash()
        for changes, status in [({'active': ['feature']}, 'ACTIVE'),
                                ({'retained': ['feature']}, 'HISTORICAL_CHECKPOINT'),
                                ({'branch': {'name': 'feature', 'sha': self.head, 'protected': True}}, 'ACTIVE')]:
            with self.subTest(changes=changes):
                row = self.classify(**changes)
                self.assertEqual(row['classification'], status)
                self.assertFalse(row['deletion_candidate'])

    def test_missing_commit_never_authorizes_deletion(self):
        self.squash()
        row = self.classify(branch={'name': 'feature', 'sha': 'a' * 40})
        self.assertEqual(row['classification'], 'UNKNOWN')
        self.assertFalse(row['deletion_candidate'])

    def test_file_mode_difference_is_not_silently_accounted(self):
        self.squash()
        self.git('update-index', '--chmod=+x', 'feature')
        self.git('commit', '-qm', 'different executable mode')
        self.merge = self.git('rev-parse', 'HEAD')
        row = self.classify()
        self.assertEqual(row['classification'], 'UNKNOWN')
        self.assertIn('feature', row['unaccounted_paths'])

    def test_deleted_feature_path_must_also_be_deleted_at_receipt(self):
        self.git('switch', '-q', 'feature')
        self.git('rm', 'base')
        self.head = self.commit('remove old file')
        self.git('switch', '-q', 'main')
        self.git('merge', '--squash', 'feature')
        self.write('base', 'restored by integration\n')
        self.merge = self.commit('keep removed path')
        row = self.classify()
        self.assertEqual(row['classification'], 'UNKNOWN')
        self.assertIn('base', row['unaccounted_paths'])

    def test_ancestral_tip_history_is_retained_even_after_file_replacement(self):
        self.git('merge', '--ff-only', 'feature')
        self.merge = self.head
        self.write('feature', 'replacement\n')
        self.commit('later')
        self.assertTrue(self.classify(prs=[])['deletion_candidate'])

    def test_empty_unmerged_scope_stays_unknown(self):
        self.squash()
        row = self.classify(prs=[dict(number=2, state='closed', merged_at=None,
            head={'ref': 'feature', 'sha': self.head}, merge_commit_sha=None)])
        self.assertEqual(row['classification'], 'UNKNOWN')
        self.assertFalse(row['deletion_candidate'])


if __name__ == '__main__':
    unittest.main()
