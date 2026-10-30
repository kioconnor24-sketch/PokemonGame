"""Negative and legitimate-source cases for the Sinnoh identity preflight."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

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


def check(pr, peers=(), main=(), production=()):
    return guard.validate(dict(candidate=pr, other_open_prs=list(peers),
                               main_maps=list(main), main_engine_maps=list(production)))


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

    def test_repair_cannot_introduce_new_geometry(self):
        p = candidate(mode="repair", sources="#351")
        self.assertTrue(any("repair cannot introduce" in e for e in check(p)))

    def test_reuse_cannot_invent_existing_source(self):
        p = candidate(mode="reuse", sources="main")
        self.assertTrue(any("reuse source does not contain" in e for e in check(p)))
        self.assertEqual(check(p, main=["NewRoute"]), [])

    def test_reuse_source_must_contain_actual_map_file(self):
        p = candidate(mode="reuse", sources="#351")
        claimed_only = candidate(mode="construct", number=351, files=[
            dict(filename=STAGED.replace("staged/", "stage.py"), status="added")])
        self.assertTrue(any("reuse source does not contain" in e for e in
                            check(p, peers=[claimed_only])))
        with_map = dict(number=351, files=[
            dict(filename=STAGED + "NewRoute/map.json", status="added")])
        self.assertEqual(check(p, peers=[with_map]), [])

    def test_production_requires_real_engine_output(self):
        p = candidate(mode="integrate", sources="#351")
        self.assertTrue(any("requires actual engine" in e for e in check(p)))

    def test_cannot_reinstall_production_identity(self):
        p = candidate(mode="integrate", sources="#351", files=[
            dict(filename=ENGINE + "NewRoute/map.json", status="added")])
        self.assertTrue(any("already installed in production" in e for e in
                            check(p, production=["NewRoute"])))

    def test_dev_overlay_name_is_same_map(self):
        p = candidate(files=[dict(filename=STAGED+"NewRoute-dev-overlay/map.json",
                                  status="added")])
        self.assertEqual(check(p), [])

    def test_engine_additions_cannot_bypass_integration_classification(self):
        for mode in ("construct", "reuse", "repair"):
            with self.subTest(mode=mode):
                p = candidate(mode=mode, sources="#351", files=[
                    dict(filename=ENGINE + "NewRoute/map.json", status="added")])
                self.assertTrue(any("requires integrate mode" in e for e in check(p)))
                if mode == "construct":
                    self.assertTrue(any("requires added staged" in e for e in check(p)))

    def test_staged_output_cannot_hide_added_engine_map(self):
        p = candidate(files=[
            dict(filename=STAGED + "NewRoute/map.json", status="added"),
            dict(filename=ENGINE + "NewRoute/map.json", status="added")])
        self.assertTrue(any("requires integrate mode" in e for e in check(p)))

    def test_renamed_maps_cannot_hide_new_source_or_engine_identities(self):
        for root, expected in ((STAGED, "repair cannot introduce"),
                               (ENGINE, "requires integrate mode")):
            with self.subTest(root=root):
                p = candidate(mode="repair", sources="main", files=[
                    dict(filename=root + "NewRoute/map.json", status="renamed",
                         previous_filename=root + "OldRoute/map.json")])
                self.assertTrue(any(expected in e for e in check(p)))

    def test_readme_only_upstream_cannot_prove_reused_geometry(self):
        p = candidate(mode="reuse", sources="#351")
        peer = dict(number=351, files=[
            dict(filename=STAGED + "NewRoute/README.md", status="added")])
        self.assertTrue(any("reuse source does not contain" in e for e in
                            check(p, peers=[peer])))

    def test_file_rename_inside_existing_map_remains_a_repair(self):
        p = candidate(mode="repair", sources="main", files=[
            dict(filename=ENGINE + "NewRoute/movement.inc", status="renamed",
                 previous_filename=ENGINE + "NewRoute/scripts.inc")])
        self.assertEqual(check(p), [])

    def test_integration_can_update_an_existing_neighbours_return(self):
        p = candidate(mode="integrate", maps="NewRoute,OldTown", sources="main",
                      files=[
                          dict(filename=ENGINE + "NewRoute/map.json", status="added"),
                          dict(filename=ENGINE + "OldTown/map.json", status="modified")])
        peer = candidate(mode="integrate", maps="OtherRoute,OldTown",
                         sources="main", number=400, files=[
                             dict(filename=ENGINE + "OtherRoute/map.json", status="added"),
                             dict(filename=ENGINE + "OldTown/map.json", status="modified")])
        self.assertEqual(check(p, production=["OldTown"], peers=[peer]), [])

    def test_adding_scripts_to_existing_maps_remains_a_repair(self):
        for root in (STAGED, ENGINE):
            with self.subTest(root=root):
                p = candidate(mode="repair", sources="main", files=[
                    dict(filename=root + "NewRoute/scripts.inc", status="added")])
                self.assertEqual(check(p, main=["NewRoute"], production=["NewRoute"]), [])

    def test_repair_rejects_unregistered_payload_without_definition(self):
        for root in (STAGED, ENGINE):
            for status in ("added", "renamed"):
                with self.subTest(root=root, status=status):
                    p = candidate(mode="repair", sources="main", files=[
                        dict(filename=root + "NewRoute/map.bin", status=status,
                             previous_filename=root + "OldRoute/map.bin")])
                    self.assertTrue(check(p))

    def test_cited_definition_allows_supporting_payload_repair(self):
        for root in (STAGED, ENGINE):
            with self.subTest(root=root):
                p = candidate(mode="repair", sources="#400", files=[
                    dict(filename=root + "NewRoute/map.bin", status="added")])
                peer = dict(number=400, files=[
                    dict(filename=root + "NewRoute/map.json", status="added")])
                self.assertEqual(check(p, peers=[peer]), [])
                peer["files"][0]["filename"] = root + "NewRoute/README.md"
                self.assertTrue(check(p, peers=[peer]))

    def test_moving_same_map_from_source_to_engine_is_an_integration(self):
        for filename in ("map.json", "map.bin"):
            with self.subTest(filename=filename):
                p = candidate(mode="repair", sources="main", files=[
                    dict(filename=ENGINE + "NewRoute/" + filename, status="renamed",
                         previous_filename=STAGED + "NewRoute/" + filename)])
                self.assertTrue(any("requires integrate mode" in e for e in
                                    check(p, main=["NewRoute"])))

    def test_construction_can_update_an_existing_neighbours_return(self):
        p = candidate(maps="NewRoute,OldTown", files=[
            dict(filename=STAGED + "NewRoute/map.json", status="added"),
            dict(filename=STAGED + "OldTown/map.json", status="modified")])
        self.assertEqual(check(p, main=["OldTown"]), [])

    def test_live_repair_fetches_cited_definition_without_scanning_unrelated_files(self):
        def pages(path):
            if path == "pulls?state=open":
                return [dict(number=400), dict(number=500)]
            if path == "pulls/400/files":
                return [dict(filename=ENGINE + "NewRoute/map.json", status="added")]
            self.fail("unexpected unrelated file request: " + path)
        with patch.object(guard, "fetch_live", return_value={"tree": []}), \
                patch.object(guard, "pages", side_effect=pages):
            snapshot = guard.preflight("repair", "NewRoute", "#400")
        self.assertEqual(snapshot["candidate"]["number"], 501)
        self.assertEqual([p["number"] for p in snapshot["other_open_prs"]], [400])
        snapshot["candidate"]["files"] = [
            dict(filename=ENGINE + "NewRoute/map.bin", status="added")]
        self.assertEqual(guard.validate(snapshot), [])


if __name__ == "__main__":
    unittest.main()

