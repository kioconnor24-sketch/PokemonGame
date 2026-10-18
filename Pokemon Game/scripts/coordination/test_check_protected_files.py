"""Exact Phase 2 map handoffs are narrow: retain default freeze and conflicts."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name("check_protected_files.py")
SPEC = importlib.util.spec_from_file_location("averon_map_guard", MODULE)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
ROOT = "Pokemon Game/"
MAP1 = ROOT + "engine/data/maps/SandgemTown/map.json"
MAP2 = ROOT + "engine/data/maps/SandgemTown_PokemonCenter_1F/map.json"
LAYOUT = ROOT + "engine/data/layouts/SandgemTown/map.bin"
SENSITIVE = ROOT + "engine/data/event_scripts.s"

def snapshot(paths, *, approval=(), association="MEMBER", number=131, peer_paths=()):
    return {
        "pull_request": {"number": number,
                         "files": [{"filename": p, "status": "added"} for p in paths]},
        "other_open_prs": [{"number": 999, "files": list(peer_paths)}] if peer_paths else [],
        "handoffs": [{"pr": number, "paths": list(approval), "association": association}]
                    if approval else [],
    }

class ExactHandoffTest(unittest.TestCase):
    def test_no_handoff_preserves_map_freeze(self):
        errors, _ = guard.validate(snapshot([MAP1, MAP2, LAYOUT]))
        self.assertEqual(len(errors), 1)
        self.assertIn("Map-file freeze", errors[0])
        for path in (MAP1, MAP2, LAYOUT):
            self.assertIn(path, errors[0])

    def test_exact_signed_handoff_allows_only_named_files(self):
        errors, _ = guard.validate(snapshot([MAP1, MAP2, LAYOUT], approval=[MAP1, MAP2, LAYOUT]))
        self.assertEqual(errors, [])

    def test_subset_and_directory_prefix_cannot_approve_missing_file(self):
        for approval in ([MAP1], [ROOT + "engine/data/maps/"],
                         [ROOT + "engine/data/maps/SandgemTown/"]):
            with self.subTest(approval=approval):
                errors, _ = guard.validate(snapshot([MAP1, MAP2], approval=approval))
                self.assertEqual(len(errors), 1)
                self.assertIn(MAP2, errors[0])

    def test_handoff_for_wrong_pr_or_untrusted_author_fails(self):
        for association in ("NONE", "CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR"):
            with self.subTest(association=association):
                errors, _ = guard.validate(snapshot([MAP1], approval=[MAP1], association=association))
                self.assertTrue(any("Map-file freeze" in e for e in errors))
        data = snapshot([MAP1], approval=[MAP1])
        data["handoffs"][0]["pr"] = 132
        self.assertTrue(guard.validate(data)[0])

    def test_protected_source_still_requires_separate_exact_approval(self):
        errors, _ = guard.validate(snapshot([MAP1, SENSITIVE], approval=[MAP1]))
        self.assertEqual(len(errors), 1)
        self.assertIn("Exclusive shared-file", errors[0])
        self.assertNotIn("Map-file freeze", errors[0])
        self.assertEqual(guard.validate(snapshot([MAP1, SENSITIVE], approval=[MAP1, SENSITIVE]))[0], [])

    def test_overlap_on_protected_file_cannot_be_waived(self):
        errors, _ = guard.validate(snapshot([SENSITIVE], approval=[SENSITIVE],
                                            peer_paths=[SENSITIVE]))
        self.assertEqual(len(errors), 1)
        self.assertIn("overlaps", errors[0])

    def test_unrelated_map_stays_frozen_even_with_a_sandgem_handoff(self):
        other = ROOT + "engine/data/maps/OldaleTown/map.json"
        errors, _ = guard.validate(snapshot([MAP1, other], approval=[MAP1]))
        self.assertEqual(len(errors), 1)
        self.assertIn(other, errors[0])

    def test_no_hidden_glob_or_parent_path_approval(self):
        data = snapshot([MAP1], approval=[ROOT + "engine/data/maps/*"])
        self.assertTrue(guard.validate(data)[0])
        data = snapshot([MAP1], approval=[MAP1])
        self.assertEqual(guard.validate(data)[0], [])

    def test_legacy_grandfathered_case_is_unchanged(self):
        data = snapshot([MAP1, SENSITIVE], number=14)
        self.assertEqual(guard.validate(data)[0], [])

if __name__ == "__main__":
    unittest.main()
