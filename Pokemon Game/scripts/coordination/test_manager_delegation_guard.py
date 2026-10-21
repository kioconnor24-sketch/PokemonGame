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
    def workflow_snapshot(self, comments, *, head=HEAD, files=None):
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
                         listFiles:'files',list:'prs'},issues:{listComments:'comments'}},
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


if __name__ == "__main__":
    unittest.main()
