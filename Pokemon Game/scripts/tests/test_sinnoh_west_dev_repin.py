"""All six DEV scenes preserve the exact production prefix: west packets A (19-21), B (22-29) and C (30-40)."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SINNOH = ROOT / 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh'
FAMILIES = ('canalave-west', 'celestic-north', 'eastern-loop', 'eterna-cycle', 'forest-chateau', 'hearthome-solaceon')
ADDED = ['JubilifeCity_GlobalTerminal_1F', 'JubilifeCity_GlobalTerminal_2F', 'OreburghGate_B1F']
ADDED_B = ['FloaromaTown_FlowerShop', 'FloaromaTown_House1', 'FloaromaTown_Mart', 'FloaromaTown_House2',
           'FloaromaMeadow_House', 'Route205_South_House', 'ValleyWindworks', 'ValleyWindworks_Inside']
ADDED_C = ['OreburghCity', 'OreburghCity_PokemonCenter_1F', 'OreburghCity_Mart', 'OreburghCity_Museum_1F',
           'OreburghCity_Museum_2F', 'OreburghCity_Condo', 'OreburghCity_House1', 'OreburghCity_House2',
           'OreburghCity_House3', 'OreburghCity_House4', 'OreburghCity_House5']


def load(name):
    spec = importlib.util.spec_from_file_location('west_repin_' + name.replace('-', '_'), SINNOH / name / 'prepare_runtime.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WestRepinTest(unittest.TestCase):
    def test_every_scene_keeps_all_production_slots_and_appends_after_40(self):
        prior = json.loads((ROOT / 'Pokemon Game/engine/data/maps/map_groups.json').read_text())
        self.assertEqual(len(prior['gMapGroup_Sinnoh']), 41)
        self.assertEqual(prior['gMapGroup_Sinnoh'][19:], ADDED + ADDED_B + ADDED_C)
        for family in FAMILIES:
            with self.subTest(family=family):
                module = load(family)
                files, receipt = module.assemble(ROOT)
                actual = json.loads(files['data/maps/map_groups.json'])
                for key, value in prior.items():
                    self.assertEqual(actual[key][:41] if key == 'gMapGroup_Sinnoh' else actual[key], value)
                self.assertEqual(list(receipt['temporary_map_slots'].values()), list(range(41, 41 + len(module.MAPS))))
                self.assertFalse(set(ADDED + ADDED_B + ADDED_C) & set(module.MAPS))
                pins = files['test/data/averon_map_registry_slots.inc'].decode()
                for slot, name in enumerate(ADDED + ADDED_B + ADDED_C, 19):
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
