"""Limited source-contract integration checks. No game or toolchain required."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'coordination/check_integration_contract.py'
spec = importlib.util.spec_from_file_location('integration', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

QUEST = 'Averon_FieldNotes_Researcher::\nAveron_BerrySketch_Artist::\nAveron_BerrySketch_Tree::\n'
BATTLE = '.macro averon_scripted_battle\n.endm\n.macro averon_recover_in_place\n.endm\n.macro averon_respawn\n.endm\n'
NATIVES = '\n'.join('void ' + name + '(void)' for name in (
    'AveronScriptedBattle_Begin', 'AveronScriptedBattle_Finish',
    'AveronScriptedBattle_PrepareRespawn', 'AveronScriptedBattle_DoRespawnWarp'))
FLAGS = '#define FLAG_AVERON_NOTES_STARTED 0x2A\n#define FLAG_SPECIAL_FLAG_UNUSED_0x4003 (0x4000+3)\n'
CONFIG = '#define B_FLAG_NO_WHITEOUT FLAG_SPECIAL_FLAG_UNUSED_0x4003\n'


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def fixture(self, quest=True, battle=True):
        registry = []
        if battle:
            registry.append(f'\t.include "{mod.BATTLE}"')
            self.put(mod.BATTLE, BATTLE)
            self.put(mod.BATTLE_C, NATIVES)
            self.put(mod.FLAG, CONFIG)
        if quest:
            registry.append(f'\t.include "{mod.QUEST}"')
            self.put(mod.QUEST, QUEST)
        self.put(mod.EVENT, '\n'.join(registry) + '\n')
        self.put(mod.CONST_FLAGS, FLAGS)

    def test_no_features_explains_skip(self):
        self.fixture(False, False)
        errors, notes = mod.examine(self.root)
        self.assertEqual(errors, [])
        self.assertIn('SKIP:', notes[0])

    def test_combined_contract(self):
        self.fixture()
        errors, notes = mod.examine(self.root)
        self.assertEqual(errors, [])
        self.assertTrue(any('Both feature sources' in x for x in notes))

    def test_missing_quest_registration(self):
        self.fixture()
        self.put(mod.EVENT, f'\t.include "{mod.BATTLE}"\n')
        errors, _ = mod.examine(self.root)
        self.assertTrue(any('QUEST registry' in x for x in errors), errors)

    def test_duplicate_quest_registration(self):
        self.fixture()
        self.put(mod.EVENT, f'\t.include "{mod.BATTLE}"\n' + 2*f'\t.include "{mod.QUEST}"\n')
        errors, _ = mod.examine(self.root)
        self.assertTrue(any('got 2' in x for x in errors), errors)

    def test_missing_battle_native(self):
        self.fixture()
        self.put(mod.BATTLE_C, 'void AveronScriptedBattle_Begin(void)\n')
        errors, _ = mod.examine(self.root)
        self.assertTrue(any('Finish' in x for x in errors), errors)

    def test_wrong_flag_mapping(self):
        self.fixture()
        self.put(mod.FLAG, '#define B_FLAG_NO_WHITEOUT 0\n')
        errors, _ = mod.examine(self.root)
        self.assertTrue(any('not bound' in x for x in errors), errors)

    def test_missing_file(self):
        self.fixture()
        (self.root/mod.BATTLE).unlink()
        errors, _ = mod.examine(self.root)
        self.assertTrue(any('registered macro file absent' in x for x in errors), errors)

    def test_registry_order(self):
        self.fixture()
        self.put(mod.EVENT, f'\t.include "{mod.QUEST}"\n\t.include "{mod.BATTLE}"\n')
        errors, _ = mod.examine(self.root)
        self.assertTrue(any('follows QUEST' in x for x in errors), errors)

    def test_comment_not_a_real_registration(self):
        self.fixture()
        self.put(mod.EVENT, f'@ .include "{mod.QUEST}"\n\t.include "{mod.BATTLE}"\n')
        errors, _ = mod.examine(self.root)
        self.assertTrue(any('QUEST registry' in x for x in errors), errors)


if __name__ == '__main__':
    unittest.main()
