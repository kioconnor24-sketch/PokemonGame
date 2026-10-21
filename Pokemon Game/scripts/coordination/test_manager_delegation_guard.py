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
PINS = ROOT + "scripts/averon-mapsec-pins.json"
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

    def test_renamed_reserved_path_cannot_use_routine_manager_marker(self):
        data = snapshot([MAP, ROOT + "engine/src/retired_save.c"], signed_paths=[MAP])
        data["pull_request"]["files"][1].update(status="renamed", previous_filename=SAVE)
        self.assertTrue(any("Manager delegation excludes" in e and SAVE in e
                            for e in guard.validate(data)[0]))

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

# Exercise the actual trusted-workflow JavaScript with inert API/FS doubles.
# No GitHub credentials, network calls or files under /tmp are used here.
import json
import shutil
import subprocess
import textwrap


class WorkflowDelegationTest(unittest.TestCase):
    def workflow_snapshot(self, comments, *, head=HEAD, files=None, registry_files=None):
        workflow = Path(__file__).resolve().parents[3] / '.github/workflows/averon-shared-file-guard.yml'
        source = workflow.read_text()
        script = textwrap.dedent(source.split('          script: |\n', 1)[1]
                                 .split('      - name:', 1)[0])
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node is required to verify the actual workflow parser')
        harness = r'''
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
let captured;
const github={rest:{pulls:{get:async()=>({data:{head:{sha:input.head}}}),
                         listFiles:'files',list:'prs'},issues:{listComments:'comments'},
 repos:{getContent:async({path,ref})=>{
   const version=ref==='main'?'base':'head';
   if(!input.registryFiles[path])throw Error('missing test registry: '+path);
   return {data:{type:'file',encoding:'base64',
     content:Buffer.from(JSON.stringify(input.registryFiles[path][version])).toString('base64')}};
 }}},
 paginate:async(method)=>method==='files'?input.files:
                        method==='prs'?[]:input.comments};
const context={repo:{owner:'kioconnor24-sketch',repo:'PokemonGame'},
               eventName:'pull_request_target',issue:{number:203}};
const inertRequire=(name)=>{
 if(name!=='fs')throw Error('unexpected module '+name);
 return {writeFileSync:(path,text)=>{if(path!=='/tmp/averon-guard.json')throw Error(path);captured=text;}};
};
(async()=>{
 await new Function('github','context','require','return (async()=>{'+input.script+'\n})()')
       (github,context,inertRequire);
 process.stdout.write(captured);
})().catch(e=>{process.stderr.write(String(e));process.exit(1);});
'''
        result = subprocess.run([node, '-e', harness], input=json.dumps(dict(
            script=script, comments=comments, head=head,
            registryFiles=registry_files or {},
            files=files if files is not None else [{"filename": MAP, "status": "modified"}])), text=True,
            capture_output=True, check=True, timeout=10)
        return json.loads(result.stdout)

    @staticmethod
    def comment(body, *, ident=1, login='kioconnor24-sketch', association='OWNER'):
        return dict(id=ident, user=dict(login=login), author_association=association, body=body)

    def directive(self, **kw):
        return self.comment('OWNER DIRECTIVE — PROJECT-WIDE CHATGPT MANAGEMENT AUTHORIZATION',
                            ident=6322129730, **kw)

    def marker(self, **kw):
        return self.comment(f'MANAGER_HANDOFF_APPROVED PR=#203 HEAD={HEAD} PATHS={MAP}', **kw)

    def test_live_workflow_accepts_explicit_manager_marker(self):
        data = self.workflow_snapshot([self.directive(), self.marker()])
        self.assertTrue(data['manager_delegation_active'])
        self.assertEqual(data['handoffs'], [])  # Never relabel manager as owner.
        self.assertEqual(guard.validate(data)[0], [])

    def test_live_workflow_absent_or_untrusted_directive_fails_closed(self):
        for directive in (None, self.directive(login='outsider'),
                          self.directive(association='MEMBER'),
                          self.comment('OWNER DIRECTIVE — PROJECT-WIDE CHATGPT MANAGEMENT AUTHORIZATION', ident=9)):
            with self.subTest(directive=directive):
                data = self.workflow_snapshot(([directive] if directive else []) + [self.marker()])
                self.assertFalse(data['manager_delegation_active'])
                self.assertTrue(guard.validate(data)[0])

    def test_live_workflow_owner_revocation_is_fail_closed(self):
        data = self.workflow_snapshot([self.directive(), self.marker(),
            self.comment('MANAGER_DELEGATION_REVOKED')])
        self.assertFalse(data['manager_delegation_active'])
        self.assertTrue(guard.validate(data)[0])
        data = self.workflow_snapshot([self.directive(), self.marker(),
            self.comment('MANAGER_DELEGATION_REVOKED', login='outsider')])
        self.assertEqual(guard.validate(data)[0], [])

    def test_live_workflow_rejects_other_login_and_changed_head(self):
        data = self.workflow_snapshot([self.directive(), self.marker(login='outsider')])
        self.assertEqual(data['manager_handoffs'], [])
        self.assertTrue(guard.validate(data)[0])
        data = self.workflow_snapshot([self.directive(), self.marker()], head='b'*40)
        self.assertTrue(guard.validate(data)[0])

    def test_live_workflow_retains_previous_name_for_reserved_rename(self):
        files = [{"filename": MAP, "status": "modified"},
                 {"filename": ROOT + "engine/src/retired_save.c", "status": "renamed",
                  "previous_filename": SAVE}]
        data = self.workflow_snapshot([self.directive(), self.marker()], files=files)
        self.assertEqual(data['pull_request']['files'][1]['previous_filename'], SAVE)
        self.assertTrue(any("Manager delegation excludes" in e and SAVE in e
                            for e in guard.validate(data)[0]))

    def test_live_workflow_preserves_legacy_without_directive(self):
        data = self.workflow_snapshot([self.comment(f'HANDOFF_APPROVED PR=#203 PATHS={MAP}')])
        self.assertFalse(data['manager_delegation_active'])
        self.assertEqual(guard.validate(data)[0], [])


class ApprovedIdentityAppendTest(unittest.TestCase):
    """A trusted-main pinned prefix may extend only with already-owner-approved IDs."""

    def make_data(self):
        import copy
        baseline = {"map_sections": [
            {"id": "MAPSEC_LAKE_VERITY", "value": 220, "name": "LAKE VERITY",
             "region": "REGION_SINNOH"}]}
        pins = {"comment": "retained legacy policy", "pins": {"MAPSEC_LAKE_VERITY": 220}}
        added = [
            {"id": "MAPSEC_JUBILIFE_CITY", "value": 221, "name": "JUBILIFE CITY",
             "region": "REGION_SINNOH"},
            {"id": "MAPSEC_ROUTE_203", "value": 222, "name": "ROUTE 203",
             "region": "REGION_SINNOH"},
            {"id": "MAPSEC_OREBURGH_GATE", "value": 223, "name": "OREBURGH GATE",
             "region": "REGION_SINNOH"},
        ]
        after = copy.deepcopy(baseline)
        after["map_sections"].extend(added)
        after_pins = copy.deepcopy(pins)
        after_pins["pins"].update({row["id"]: row["value"] for row in added})
        data = snapshot([MAP, REGION_IDS, PINS], signed_paths=[MAP, REGION_IDS, PINS])
        data["identity_files"] = {
            REGION_IDS: {"base": baseline, "head": after},
            PINS: {"base": pins, "head": after_pins},
        }
        return data

    def assert_rejected(self, data):
        self.assertFalse(guard.approved_identity_append(data, {
            f["filename"] for f in data["pull_request"]["files"]}))
        errors, _ = guard.validate(data)
        self.assertTrue(any("Manager delegation excludes" in e for e in errors))

    def test_preapproved_three_code_pair_is_delegatable(self):
        data = self.make_data()
        self.assertEqual(guard.validate(data)[0], [])

    def test_no_actual_trusted_registry_data_fails_closed(self):
        data = self.make_data()
        del data["identity_files"]
        self.assert_rejected(data)

    def test_new_unapproved_227_cannot_be_added(self):
        data = self.make_data()
        data["identity_files"][REGION_IDS]["head"]["map_sections"].append(
            {"id": "MAPSEC_NEW", "value": 227, "name": "NEW",
             "region": "REGION_SINNOH"})
        data["identity_files"][PINS]["head"]["pins"]["MAPSEC_NEW"] = 227
        self.assert_rejected(data)

    def test_existing_identity_changed_or_reordered_fails(self):
        data = self.make_data()
        data["identity_files"][REGION_IDS]["head"]["map_sections"][0]["name"] = "RENAMED"
        self.assert_rejected(data)

    def test_wrong_existing_pin_or_deleted_pin_fails(self):
        data = self.make_data()
        data["identity_files"][PINS]["head"]["pins"]["MAPSEC_LAKE_VERITY"] = 221
        self.assert_rejected(data)
        data = self.make_data()
        del data["identity_files"][PINS]["head"]["pins"]["MAPSEC_LAKE_VERITY"]
        self.assert_rejected(data)

    def test_reserved_name_value_region_and_order_fail_closed(self):
        for field, value in (("id", "MAPSEC_OTHER"), ("name", "OTHER"),
                             ("value", 225), ("region", "REGION_AVERON")):
            with self.subTest(field=field):
                data = self.make_data()
                data["identity_files"][REGION_IDS]["head"]["map_sections"][1][field] = value
                self.assert_rejected(data)
        data = self.make_data()
        rows = data["identity_files"][REGION_IDS]["head"]["map_sections"]
        rows[1], rows[2] = rows[2], rows[1]
        self.assert_rejected(data)

    def test_unrelated_json_metadata_edits_fail(self):
        data = self.make_data()
        data["identity_files"][PINS]["head"]["comment"] = "Changed policy"
        self.assert_rejected(data)
        data = self.make_data()
        data["identity_files"][REGION_IDS]["head"]["unexpected"] = True
        self.assert_rejected(data)

    def test_partial_or_renamed_registry_pair_fails(self):
        data = self.make_data()
        data["pull_request"]["files"] = [
            f for f in data["pull_request"]["files"] if f["filename"] != PINS]
        self.assert_rejected(data)
        data = self.make_data()
        data["pull_request"]["files"][1]["status"] = "renamed"
        data["pull_request"]["files"][1]["previous_filename"] = "previous.json"
        self.assert_rejected(data)

    def test_next_approved_sections_after_223(self):
        data = self.make_data()
        import copy
        files = data["identity_files"]
        files[REGION_IDS]["base"] = copy.deepcopy(files[REGION_IDS]["head"])
        files[PINS]["base"] = copy.deepcopy(files[PINS]["head"])
        next_rows = [
            {"id": "MAPSEC_ROUTE_204", "value": 224, "name": "ROUTE 204",
             "region": "REGION_SINNOH"},
            {"id": "MAPSEC_FLOAROMA_TOWN", "value": 225, "name": "FLOAROMA TOWN",
             "region": "REGION_SINNOH"},
            {"id": "MAPSEC_ROUTE_205", "value": 226, "name": "ROUTE 205",
             "region": "REGION_SINNOH"},
        ]
        files[REGION_IDS]["head"]["map_sections"].extend(next_rows)
        files[PINS]["head"]["pins"].update({r["id"]: r["value"] for r in next_rows})
        self.assertEqual(guard.validate(data)[0], [])

    def test_owner_legacy_authorization_still_works(self):
        data = self.make_data()
        data.pop("identity_files")
        data["manager_handoffs"] = []
        data["handoffs"] = [{
            "pr": 203, "paths": [MAP, REGION_IDS, PINS], "association": "OWNER"}]
        self.assertEqual(guard.validate(data)[0], [])


class TrustedWorkflowRegistryReadTest(WorkflowDelegationTest):
    def test_workflow_reads_both_versions_without_executing_pr_code(self):
        data = ApprovedIdentityAppendTest().make_data()
        files = data["identity_files"]
        events = [
            {"filename": MAP, "status": "modified"},
            {"filename": REGION_IDS, "status": "modified"},
            {"filename": PINS, "status": "modified"},
        ]
        approvals = [self.directive(), self.comment(
            f"MANAGER_HANDOFF_APPROVED PR=#203 HEAD={HEAD} PATHS={MAP},{REGION_IDS},{PINS}")]
        snapshot_data = self.workflow_snapshot(
            approvals, files=events, registry_files=files)
        self.assertEqual(snapshot_data["identity_files"], files)
        self.assertEqual(guard.validate(snapshot_data)[0], [])



if __name__ == "__main__":
    unittest.main()
