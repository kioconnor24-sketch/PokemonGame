"""Tiny isolated fixtures for archived DEV identity and registry rejection."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('preflight', Path(__file__).parents[1] / 'sinnoh-runtime-preflight.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class RuntimePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.engine = self.root / 'engine'
        self.archive = self.root / 'archive'
        self.engine.mkdir(); self.archive.mkdir()
        (self.engine / '.map_qa_throwaway').touch()
        f = self.engine / 'data/maps/map_groups.json'
        f.parent.mkdir(parents=True)
        f.write_text(json.dumps({'gMapGroup_Sinnoh': ['Existing', 'New']}))
        self.recipe = dict(status='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE', base='base',
                           existing_map_names_preserved=['Existing'], temporary_map_slots={'New': 1},
                           files={'data/maps/map_groups.json': p.digest(f)})
        self.refresh()

    def refresh(self):
        (self.archive / 'recipe.json').write_text(json.dumps(self.recipe))
        identity = dict(base='base', files=self.recipe['files'], engine_tree='tree',
                        recipe_sha256=p.digest(self.archive / 'recipe.json'))
        (self.archive / 'identity.json').write_text(json.dumps(identity))
        for stem in ('pokeemerald', 'pokeemerald-release'):
            for suffix in ('gba', 'elf'):
                (self.archive / (stem + '.' + suffix)).write_bytes((stem + suffix).encode())
        self.seal()

    def seal(self):
        (self.archive / 'archive.json').write_text(json.dumps({f.name: dict(bytes=f.stat().st_size, sha256=p.digest(f))
            for f in self.archive.iterdir() if f.name != 'archive.json'}))

    def verify(self, profile='normal'):
        return p.verify(self.engine, self.archive, 'recipe.json', 'identity.json', profile)

    def test_both_profiles_return_actual_distinct_identities(self):
        a, b = self.verify(), self.verify('release')
        self.assertNotEqual(a['rom_sha256'], b['rom_sha256'])
        self.assertEqual(a['source_files'], 1)
        self.assertEqual(a['temporary_maps'], 1)

    def test_changed_rom_elf_recipe_identity_rejected(self):
        for name in ('pokeemerald.gba', 'pokeemerald.elf', 'recipe.json', 'identity.json'):
            with self.subTest(name=name):
                f = self.archive / name; old = f.read_bytes(); f.write_bytes(old + b'changed')
                with self.assertRaisesRegex(ValueError, 'archive identity'): self.verify()
                f.write_bytes(old)

    def test_changed_engine_rejected(self):
        (self.engine / 'data/maps/map_groups.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'engine source'): self.verify()

    def test_resealed_mismatched_identity_rejected(self):
        f = self.archive / 'identity.json'; d = json.loads(f.read_text()); d['base'] = 'other'; f.write_text(json.dumps(d)); self.seal()
        with self.assertRaisesRegex(ValueError, 'source identity'): self.verify()

    def test_reordered_duplicate_or_noncontiguous_registry_rejected(self):
        for names, slots in [(['New', 'Existing'], {'New': 1}), (['Existing', 'Existing'], {'Existing': 1}), (['Existing', 'New'], {'New': 4})]:
            with self.subTest(names=names, slots=slots):
                f = self.engine / 'data/maps/map_groups.json'; f.write_text(json.dumps({'gMapGroup_Sinnoh': names}))
                self.recipe['files'] = {'data/maps/map_groups.json': p.digest(f)}
                self.recipe['temporary_map_slots'] = slots; self.refresh()
                with self.assertRaisesRegex(ValueError, 'append-only'): self.verify()

    def test_engine_and_archive_path_escape_or_symlink_rejected(self):
        outside = self.root / 'outside'; outside.write_bytes(b'outside')
        (self.engine / 'escape').symlink_to(outside)
        for name in ('../outside', str(outside), 'escape'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'escapes'): p.inside(self.engine, name)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            p.verify(self.engine, self.archive, '../outside', 'identity.json', 'normal')

    def test_unmarked_scratch_and_unknown_profile_rejected(self):
        (self.engine / '.map_qa_throwaway').unlink()
        with self.assertRaisesRegex(ValueError, 'marked scratch'): self.verify()
        with self.assertRaisesRegex(ValueError, 'profile'): self.verify('other')


if __name__ == '__main__': unittest.main()
