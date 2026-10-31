"""Negative and legitimate-source cases for the Sinnoh identity preflight."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
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
            for status in ("added", "renamed", "copied"):
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


class RequiredGuardIdentityTests(unittest.TestCase):
    """Exercise the actual required workflow's inert API collector and CLI."""

    def workflow_snapshot(self, pr, peers=(), fresh=None):
        workflow = MODULE.parents[3] / ".github/workflows/averon-shared-file-guard.yml"
        source = workflow.read_text()
        script = textwrap.dedent(source.split("          script: |\n", 1)[1]
                                 .split("      - name:", 1)[0])
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node is required to exercise the trusted collector")
        harness = r'''
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
let captured,gets=0;
const calls=[];
const github={rest:{pulls:{get:async()=>({data:++gets===1?input.pr:input.fresh}),
                         listFiles:'files',list:'prs'},issues:{listComments:'comments'}},
 paginate:async(method,args)=>{
  calls.push([method,args.pull_number||null]);
  if(method==='files')return args.pull_number===input.pr.number?input.pr.files:
    input.peers.find(p=>p.number===args.pull_number).files;
  return method==='prs'?[input.pr,...input.peers]:[];
 }};
const context={repo:{owner:'kioconnor24-sketch',repo:'PokemonGame'},
 eventName:'pull_request_target',issue:{number:input.pr.number}};
const inertRequire=(name)=>{
 if(name!=='fs')throw Error('unexpected module '+name);
 return {writeFileSync:(path,text)=>{
  if(path!=='/tmp/averon-guard.json')throw Error(path);captured=JSON.parse(text);
 }};
};
(async()=>{
 await new Function('github','context','require','return (async()=>{'+input.script+'\n})()')
  (github,context,inertRequire);
 process.stdout.write(JSON.stringify({snapshot:captured,calls}));
})().catch(e=>{process.stderr.write(String(e));process.exit(1);});
'''
        own = dict(pr, head={"sha": "a" * 40})
        result = subprocess.run([node, "-e", harness],
            input=json.dumps(dict(script=script, pr=own, peers=list(peers),
                                  fresh=fresh or own)), capture_output=True, text=True,
            check=True, timeout=10)
        return json.loads(result.stdout)

    def main_checkout(self, root):
        for path in (STAGED + "SourceOnly/map.json", ENGINE + "OldTown/map.json"):
            p = root / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("{}")

    def test_required_path_rejects_unknown_partial_payload_and_source_to_engine_move(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.main_checkout(root)
            for status in ("added", "copied", "renamed"):
                with self.subTest(status=status):
                    pr = candidate(mode="repair", sources="main", files=[dict(
                        filename=ENGINE + "SourceOnly/map.bin", status=status,
                        previous_filename=STAGED + "SourceOnly/map.bin")], maps="SourceOnly")
                    raw = self.workflow_snapshot(pr)["snapshot"]
                    self.assertTrue(guard.validate(guard.guard_snapshot(raw, root)))

    def test_required_path_allows_existing_neighbour_and_inventories_actual_definitions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.main_checkout(root)
            pr = candidate(mode="integrate", sources="main", maps="NewRoute,OldTown", files=[
                dict(filename=ENGINE + "NewRoute/map.json", status="added"),
                dict(filename=ENGINE + "OldTown/map.json", status="modified")])
            raw = self.workflow_snapshot(pr)["snapshot"]
            snap = guard.guard_snapshot(raw, root)
            self.assertEqual(set(snap["main_maps"]), {"oldtown", "sourceonly"})
            self.assertEqual(snap["main_engine_maps"], ["oldtown"])
            self.assertEqual(guard.validate(snap), [])

    def test_required_collector_preserves_cited_peer_files_without_extra_api_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.main_checkout(root)
            pr = candidate(mode="repair", sources="#400", files=[
                dict(filename=ENGINE + "NewRoute/scripts.inc", status="added")])
            peer = candidate(number=400, mode="integrate", sources="main", files=[
                dict(filename=ENGINE + "NewRoute/map.json", status="renamed",
                     previous_filename=STAGED + "NewRoute/map.json"),
                dict(filename=ENGINE + "Retired/map.json", status="removed")])
            out = self.workflow_snapshot(pr, [peer])
            self.assertEqual(out["calls"].count(["files", 400]), 1)
            raw = out["snapshot"]
            self.assertEqual(raw["pull_request"]["body"], pr["body"])
            self.assertEqual(raw["identity_peers"][0]["files"], peer["files"])
            self.assertEqual(raw["other_open_prs"][0]["files"], [ENGINE + "NewRoute/map.json"])
            self.assertEqual(guard.validate(guard.guard_snapshot(raw, root)), [])

    def test_missing_or_malformed_required_metadata_fails_even_for_legacy_pr(self):
        good = self.workflow_snapshot(candidate(number=351))["snapshot"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.main_checkout(root)
            self.assertEqual(guard.validate(guard.guard_snapshot(good, root)), [])
        for missing in ("identity_peers", "other_open_prs"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as directory:
                raw = dict(good)
                del raw[missing]
                with self.assertRaises((ValueError, KeyError)):
                    guard.guard_snapshot(raw, Path(directory))
        for key in ("body", "head_sha", "files"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                raw = dict(good, pull_request=dict(good["pull_request"]))
                del raw["pull_request"][key]
                with self.assertRaises(ValueError):
                    guard.guard_snapshot(raw, Path(directory))
        for row in (dict(filename=ENGINE + "NewRoute/map.bin"),
                    dict(filename=ENGINE + "NewRoute/map.bin", status="renamed"),
                    dict(filename=ENGINE + "NewRoute/map.bin", status="unexpected")):
            with self.subTest(row=row):
                raw = dict(good, pull_request=dict(good["pull_request"], files=[row]))
                with self.assertRaises(ValueError):
                    guard.guard_snapshot(raw, Path("/unavailable-main"))
        raw = dict(good, identity_peers=[], other_open_prs=[dict(number=400, files=[])])
        with self.assertRaises(ValueError):
            guard.guard_snapshot(raw, Path("/unavailable-main"))

    def test_required_collector_rejects_moved_head_or_identity_claim(self):
        pr = candidate()
        for fresh in (dict(pr, head={"sha": "b" * 40}),
                      dict(pr, body="Sinnoh-Work: repair", head={"sha": "a" * 40})):
            with self.subTest(fresh=fresh):
                with self.assertRaises(subprocess.CalledProcessError):
                    self.workflow_snapshot(pr, fresh=fresh)

    def test_required_workflow_runs_same_validator_and_cli_failure_blocks(self):
        workflow = MODULE.parents[3] / ".github/workflows/averon-shared-file-guard.yml"
        step = workflow.read_text().split("      - name: Enforce unique map work inside the required check\n")[1]
        self.assertEqual(step.strip(), 'run: python3 "Pokemon Game/scripts/coordination/check_sinnoh_work_identity.py" --guard-snapshot /tmp/averon-guard.json')
        raw = self.workflow_snapshot(candidate(mode="repair", sources="main", files=[
            dict(filename=ENGINE + "PreviouslyUnknownMap/map.bin", status="added")],
            maps="PreviouslyUnknownMap"))["snapshot"]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "guard.json"
            source.write_text(json.dumps(raw))
            result = subprocess.run([sys.executable, str(MODULE), "--guard-snapshot", str(source)],
                                    capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn("requires integrate mode", result.stdout)


if __name__ == "__main__":
    unittest.main()

