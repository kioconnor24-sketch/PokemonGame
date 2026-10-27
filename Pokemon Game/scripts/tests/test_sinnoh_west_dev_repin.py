"""All six DEV scenes preserve the exact narrowed west-packet production prefix."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SINNOH = ROOT / 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh'
FAMILIES = ('canalave-west', 'celestic-north', 'eastern-loop', 'eterna-cycle', 'forest-chateau', 'hearthome-solaceon')
ADDED = ['JubilifeCity_GlobalTerminal_1F', 'JubilifeCity_GlobalTerminal_2F', 'OreburghGate_B1F']


def load(name):
    spec = importlib.util.spec_from_file_location('west_repin_' + name.replace('-', '_'), SINNOH / name / 'prepare_runtime.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WestRepinTest(unittest.TestCase):
    def test_every_scene_keeps_all_production_slots_and_appends_after_21(self):
        prior = json.loads((ROOT / 'Pokemon Game/engine/data/maps/map_groups.json').read_text())
        self.assertEqual(len(prior['gMapGroup_Sinnoh']), 22)
        self.assertEqual(prior['gMapGroup_Sinnoh'][19:], ADDED)
        for family in FAMILIES:
            with self.subTest(family=family):
                module = load(family)
                files, receipt = module.assemble(ROOT)
                actual = json.loads(files['data/maps/map_groups.json'])
                for key, value in prior.items():
                    self.assertEqual(actual[key][:22] if key == 'gMapGroup_Sinnoh' else actual[key], value)
                self.assertEqual(list(receipt['temporary_map_slots'].values()), list(range(22, 22 + len(module.MAPS))))
                self.assertFalse(set(ADDED) & set(module.MAPS))
                pins = files['test/data/averon_map_registry_slots.inc'].decode()
                for slot, name in enumerate(ADDED, 19):
                    self.assertIn(f', {slot}, ', next(line for line in pins.splitlines() if line.endswith(', ' + name + ', 1)')))

    def test_changed_legacy_group_identity_still_fails_hash_guard(self):
        for family in FAMILIES:
            with self.subTest(family=family):
                module = load(family)
                original = module.base.verified_file
                def changed(repo, path, revision):
                    raw = original(repo, path, revision)
                    if str(path).endswith('data/maps/map_groups.json'):
                        data = json.loads(raw)
                        data['gMapGroup_Sinnoh'][0], data['gMapGroup_Sinnoh'][1] = data['gMapGroup_Sinnoh'][1], data['gMapGroup_Sinnoh'][0]
                        return json.dumps(data).encode()
                    return raw
                with mock.patch.object(module.base, 'verified_file', changed), self.assertRaisesRegex(ValueError, 'baseline inputs differ'):
                    module.assemble(ROOT)


if __name__ == '__main__':
    unittest.main()
