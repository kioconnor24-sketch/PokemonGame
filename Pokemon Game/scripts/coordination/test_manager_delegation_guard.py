"""Fail-closed tests for owner-delegated, explicitly labeled manager handoffs."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "averon_guard", Path(__file__).with_name("check_protected_files.py")
)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

ROOT = "Pokemon Game/"
MAP = ROOT + "engine/data/maps/LakeVerity/map.json"
OTHER = ROOT + "engine/data/maps/Route205_North/map.json"
SCRIPT = ROOT + "engine/data/event_scripts.s"
REGION_IDS = ROOT + "engine/src/data/region_map/region_map_sections.json"
SAVE = ROOT + "engine/src/save.c"
WORKFLOW = ".github/workflows/averon-shared-file-guard.yml"
HEAD = "a" * 40


def snapshot(paths, *, active=True, signed_paths=None, signed_head=HEAD,
             signed_pr=203, peers=()):
    return {
        "pull_request": {
            "number": 203, "head_sha": HEAD,
            "files": [{"filename": p, "status": "modified"} for p in paths],
        },
        "other_open_prs": (
            [{"number": 999, "files": list(peers)}] if peers else []
        ),
        "handoffs": [],
        "manager_delegation_active": active,
        "manager_handoffs": [{
            "pr": signed_pr, "head_sha": signed_head,
            "paths": list(paths if signed_paths is None else signed_paths),
        }],
    }


class ManagerDelegationTest(unittest.TestCase):
    def test_exact_routine_map_and_script_approved(self):
        self.assertEqual(guard.validate(snapshot([MAP, SCRIPT]))[0], [])

    def test_no_active_owner_directive_is_fail_closed(self):
        self.assertTrue(guard.validate(snapshot([MAP], active=False))[0])

    def test_wrong_pr_and_old_sha_cannot_be_replayed(self):
        self.assertTrue(guard.validate(snapshot([MAP], signed_pr=204))[0])
        self.assertTrue(guard.validate(snapshot([MAP], signed_head="b" * 40))[0])

    def test_new_or_unlisted_path_still_requires_handoff(self):
        errors, _ = guard.validate(snapshot([MAP, OTHER], signed_paths=[MAP]))
        self.assertTrue(any(OTHER in e for e in errors))

    def test_glob_or_directory_is_not_authorization(self):
        errors, _ = guard.validate(snapshot([MAP], signed_paths=[
            ROOT + "engine/data/maps/*"
        ]))
        self.assertTrue(any("Map-file freeze" in e for e in errors))

    def test_reserved_id_and_save_changes_cannot_use_manager_handoff(self):
        for path in (REGION_IDS, SAVE):
            with self.subTest(path=path):
                errors, _ = guard.validate(snapshot([MAP, path]))
                self.assertTrue(any("Manager delegation excludes" in e for e in errors))
                self.assertFalse(any("Map-file freeze" in e for e in errors))

    def test_omitting_changed_reserved_path_cannot_launder_mixed_pr(self):
        for path in (REGION_IDS, SAVE, WORKFLOW):
            with self.subTest(path=path):
                errors, _ = guard.validate(snapshot([MAP, path], signed_paths=[MAP]))
                self.assertTrue(any("Manager delegation excludes" in e and path in e
                                    for e in errors))

    def test_removed_reserved_path_cannot_use_routine_manager_marker(self):
        data = snapshot([MAP, WORKFLOW], signed_paths=[MAP])
        data["pull_request"]["files"][1]["status"] = "removed"
        self.assertTrue(any("Manager delegation excludes" in e for e in guard.validate(data)[0]))

    def test_separate_legacy_handoff_can_cover_reserved_change(self):
        data = snapshot([MAP, SAVE], signed_paths=[MAP])
        data["handoffs"] = [{"pr": 203, "paths": [SAVE], "association": "OWNER"}]
        self.assertEqual(guard.validate(data)[0], [])

    def test_governance_and_security_are_reserved(self):
        for path in (WORKFLOW, ROOT + "scripts/coordination/check_protected_files.py"):
            self.assertTrue(guard.manager_reserved(path))

    def test_protected_overlap_remains_blocked(self):
        errors, _ = guard.validate(snapshot([SCRIPT], peers=[SCRIPT]))
        self.assertTrue(any("overlaps" in e for e in errors))

    def test_owner_exact_handoff_preserved_without_delegation(self):
        data = snapshot([MAP], active=False)
        data["handoffs"] = [{"pr": 203, "paths": [MAP], "association": "OWNER"}]
        self.assertEqual(guard.validate(data)[0], [])


if __name__ == "__main__":
    unittest.main()
