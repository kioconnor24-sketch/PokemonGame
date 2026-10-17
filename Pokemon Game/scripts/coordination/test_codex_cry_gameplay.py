import unittest
from codex_cry_gameplay import lto_aliases


class Symbols(unittest.TestCase):
    def test_exact_elf_alias_only_and_no_input_mutation(self):
        original = {'sLockFieldControls.lto_priv.0': 123, 'unrelated': 456}
        result = lto_aliases(original)
        self.assertEqual(result['sLockFieldControls'], 123)
        self.assertNotIn('sLockFieldControls', original)

    def test_ambiguous_static_names_fail_closed(self):
        result = lto_aliases({'same.lto_priv.0': 1, 'same.lto_priv.1': 2})
        self.assertNotIn('same', result)

    def test_preserve_real_symbol_and_ignore_other_suffixes(self):
        original = {'same': 3, 'same.lto_priv.0': 1, 'other.constprop.0': 5}
        result = lto_aliases(original)
        self.assertEqual(result['same'], 3)
        self.assertNotIn('other', result)


if __name__ == '__main__':
    unittest.main()
