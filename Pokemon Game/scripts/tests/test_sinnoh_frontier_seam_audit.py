"""Negative split-seam probes keep wall findings and cannot merge disconnected entries."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/frontier-seam-audit/run_seams.py'
spec = importlib.util.spec_from_file_location('frontier_seam_probe', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def world(disconnected=False, blocked=True):
    maps = {}
    for i, mid in enumerate(m.MAPS):
        item = object.__new__(m.mapdata.MapInfo)
        item.id = mid
        item.width, item.height = 2, 3
        item.warps, item.objects, item.triggers = [], [], set()
        item.connections = [('right' if i == 0 else 'left', m.MAPS[1-i], 0)]
        item.blocks = [0x3000] * 6
        if i and blocked:
            item.blocks[0] = item.blocks[4] = 0x3C00
        if disconnected:
            item.blocks[2] = item.blocks[3] = 0x3C00
        item.behaviors = ['MB_NORMAL'] * 6
        maps[mid] = item
    return SimpleNamespace(map=lambda key: maps[key])


class FrontierSeamAuditTest(unittest.TestCase):
    def test_adjacent_source_walls_remain_two_negative_probes(self):
        groups = m.groups(world())
        self.assertEqual(len(groups), 1)
        self.assertEqual([p['tile'] for p in groups[0]['faces']], [[1, 0], [1, 2]])
        self.assertTrue(all(p['target']['collision'] == 3 for p in groups[0]['faces']))
        self.assertEqual([p['dest_tile'] for p in groups[0]['faces']], [[0, 0], [0, 2]])

    def test_disconnected_faces_require_distinct_qualified_entries(self):
        groups = m.groups(world(disconnected=True))
        self.assertEqual([g['entry'] for g in groups], [[1, 0], [1, 2]])
        self.assertEqual([len(g['faces']) for g in groups], [1, 1])

    def test_open_reciprocal_seams_are_not_negative_probes(self):
        self.assertEqual(m.groups(world(blocked=False)), [])

    def fixture(self, root):
        (root / '.map_qa_throwaway').touch()
        files = {}
        for i in range(191):
            p = root / ('source' + str(i)); p.write_bytes(b'pinned')
            files[p.name] = hashlib.sha256(b'pinned').hexdigest()
        return dict(existing_map_names_preserved=list(range(30)), scene=dict.fromkeys(range(44)), files=files)

    def test_exact_receipt_and_marker_pass_changed_payload_fails(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); receipt = self.fixture(root)
            m.validate(root, receipt)
            (root / 'source0').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'source differs'):
                m.validate(root, receipt)

    def test_unmarked_and_wrong_scene_receipts_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); receipt = self.fixture(root)
            (root / '.map_qa_throwaway').unlink()
            with self.assertRaisesRegex(ValueError, 'marked disposable'):
                m.validate(root, receipt)
            (root / '.map_qa_throwaway').touch(); receipt['scene'] = {}
            with self.assertRaisesRegex(ValueError, r'30\+44'):
                m.validate(root, receipt)

    def test_parent_absolute_and_symlink_source_escape_fail(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); receipt = self.fixture(root)
            digest = receipt['files'].pop('source0')
            for path in ['../outside', '/tmp/outside']:
                receipt['files'][path] = digest
                with self.assertRaisesRegex(ValueError, 'escapes'):
                    m.validate(root, receipt)
                del receipt['files'][path]
            with tempfile.TemporaryDirectory() as other:
                (root / 'escape').symlink_to(Path(other), target_is_directory=True)
                receipt['files']['escape/source'] = digest
                with self.assertRaisesRegex(ValueError, 'escapes'):
                    m.validate(root, receipt)


if __name__ == '__main__':
    unittest.main()
