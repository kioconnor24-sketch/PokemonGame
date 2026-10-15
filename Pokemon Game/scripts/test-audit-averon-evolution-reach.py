"""Conservative evolutionary source-closure regression fixtures."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

source = Path(__file__).with_name('audit-averon-evolution-reach.py')
spec = importlib.util.spec_from_file_location('evo_audit', source)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class EvolutionReachTests(unittest.TestCase):
    def test_extracts_simple_levels_only(self):
        text = '''
[SPECIES_ABC] =
{
 .evolutions = EVOLUTION({EVO_LEVEL, 16, SPECIES_DEF}, {EVO_ITEM, ITEM_STONE, SPECIES_GHI}),
},
[SPECIES_DEF] =
{
 .evolutions = EVOLUTION({EVO_LEVEL, 36, SPECIES_JKL}),
},
'''
        edges, methods = audit.parse_species_evolutions(text)
        self.assertEqual(edges, {('SPECIES_ABC', 'SPECIES_DEF', 16), ('SPECIES_DEF', 'SPECIES_JKL', 36)})
        self.assertEqual(methods['EVO_ITEM'], 1)

    def test_reaches_two_stage_chain_and_skips_item(self):
        edges, _ = audit.parse_species_evolutions('''
[SPECIES_ABC] =
{
 .evolutions = EVOLUTION({EVO_LEVEL, 16, SPECIES_DEF}, {EVO_ITEM, ITEM_STONE, SPECIES_GHI}),
},
[SPECIES_DEF] =
{
 .evolutions = EVOLUTION({EVO_LEVEL, 36, SPECIES_JKL}),
},
''')
        all_species, evolved = audit.level_closure({'SPECIES_ABC'}, edges)
        self.assertEqual(all_species, {'SPECIES_ABC', 'SPECIES_DEF', 'SPECIES_JKL'})
        self.assertEqual(evolved['SPECIES_JKL'], {'from': 'SPECIES_DEF', 'level': 36})

    def test_cycle_safe(self):
        result, derived = audit.level_closure({'SPECIES_A'}, {('SPECIES_A','SPECIES_B', 15),('SPECIES_B','SPECIES_A', 20)})
        self.assertEqual(result, {'SPECIES_A', 'SPECIES_B'})
        self.assertEqual(len(derived), 1)

    def test_no_source_is_not_a_guaranteed_species(self):
        result, derived = audit.level_closure(set(), {('SPECIES_A','SPECIES_B', 16)})
        self.assertEqual((result,derived), (set(),{}))

    def test_find_ordinary_givemon_refs_only_in_selected_maps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'data/maps/CoastalMeadow/scripts.inc'
            path.parent.mkdir(parents=True)
            path.write_text('    givemon SPECIES_SNIVY, 5\n    @ givemon SPECIES_FAKE, 99\n')
            # Explicitly ignore unrelated maps and their sources.
            found = audit.gift_references(root, [{'map_id':'MAP_COASTALMEADOW','directory':'CoastalMeadow'}])
            self.assertEqual(found, {'MAP_COASTALMEADOW': ['SPECIES_SNIVY']})


if __name__ == '__main__':
    unittest.main()
