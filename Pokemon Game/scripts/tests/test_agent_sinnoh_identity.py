"""Negative and legitimate-source cases for the Sinnoh identity preflight."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "coordination/check_sinnoh_work_identity.py"
spec = importlib.util.spec_from_file_location("sinnoh_identity", MODULE)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
STAGED = "Pokemon Game/Averon_Codex_Handoff/design/sinnoh/example/staged/"
ENGINE = "Pokemon Game/engine/data/maps/"


def candidate(mode="construct", maps="NewRoute", sources="", number=355,
              files=None):
    body = f"Sinnoh-Work: {mode}\nSinnoh-Maps: {maps}\n"
    if sources:
        body += f"Sinnoh-Sources: {sources}\n"
    return dict(number=number, body=body, files=files if files is not None else
                [dict(filename=STAGED + "NewRoute/map.json", status="added")])


def check(pr, peers=(), main=()):
    return guard.validate(dict(candidate=pr, other_open_prs=list(peers), main_maps=list(main)))


class SinnohWorkIdentityTests(unittest.TestCase):
    def test_new_unclaimed_map_is_allowed(self):
        self.assertEqual(check(candidate()), [])

    def test_main_source_map_reconstruction_refused(self):
        self.assertTrue(any("already on main" in e for e in
                            check(candidate(), main=["NewRoute"])))

    def test_existing_independent_pr_map_refused(self):
        other = dict(number=200, files=[dict(filename=STAGED + "NewRoute/map.json", status="added")])
        self.assertTrue(any("PR #200" in e for e in check(candidate(), peers=[other])))

    def test_shared_map_claim_even_if_peer_has_only_script(self):
        old = candidate(maps="NewRoute", number=400,
                        files=[dict(filename=STAGED.replace("staged/", "stage.py"),
                                    status="added")])
        self.assertTrue(any("PR #400" in e for e in check(candidate(), peers=[old])))

    def test_construction_requires_actual_new_staged_output(self):
        data = candidate(files=[dict(filename=STAGED.replace("staged/", "stage.py"), status="added")])
        self.assertTrue(any("requires added staged" in e for e in check(data)))

    def test_misdeclared_map_output_refused(self):
        self.assertTrue(any("missing from Sinnoh-Maps" in e for e in
                            check(candidate(maps="OtherRoute"))))

    def test_reuse_with_actual_upstream_allowed(self):
        p = candidate(mode="reuse", sources="#351")
        self.assertEqual(check(p, main=["NewRoute"], peers=[
            dict(number=351, files=[dict(filename=STAGED+"NewRoute/map.json", status="added")])]), [])

    def test_reuse_without_source_ref_refused(self):
        self.assertTrue(any("Sinnoh-Sources" in e for e in check(candidate(mode="reuse"))))

    def test_two_production_integrations_same_map_refused(self):
        p = candidate(mode="integrate", sources="main", files=[
            dict(filename=ENGINE + "NewRoute/map.json", status="added")])
        old = dict(number=337, files=[dict(filename=ENGINE + "NewRoute/map.json", status="added")])
        self.assertTrue(any("registration already proposed" in e for e in check(p, peers=[old])))

    def test_repair_with_upstream_can_touch_same_map(self):
        p = candidate(mode="repair", sources="#337", files=[
            dict(filename=ENGINE+"NewRoute/map.json", status="modified")])
        self.assertEqual(check(p, peers=[
            dict(number=337, files=[dict(filename=ENGINE+"NewRoute/map.json", status="added")])]), [])

    def test_missing_and_duplicate_claim_fields_fail_closed(self):
        p = candidate()
        p["body"] = "Sinnoh-Work: construct\nSinnoh-Work: reuse\nSinnoh-Maps: NewRoute"
        self.assertTrue(any("duplicate" in e for e in check(p)))
        p["body"] = ""
        self.assertTrue(check(p))

    def test_legacy_prs_preserved_and_coordination_only_ignored(self):
        p = candidate(number=351)
        p["body"] = ""
        self.assertEqual(check(p), [])
        p["number"] = 400
        p["files"] = [dict(filename="Pokemon Game/scripts/coordination/anything.py", status="added")]
        self.assertEqual(check(p), [])

    def test_dev_overlay_name_is_same_map(self):
        p = candidate(files=[dict(filename=STAGED+"NewRoute-dev-overlay/map.json",
                                  status="added")])
        self.assertEqual(check(p), [])


if __name__ == "__main__":
    unittest.main()
