"""Check the actual Make overrides and production default, without building ROMs."""
from pathlib import Path
import shutil
import subprocess
import unittest


@unittest.skipUnless(shutil.which('make') and shutil.which('cc'), 'make and C preprocessor required')
class CryDefault(unittest.TestCase):
    engine = Path(__file__).resolve().parents[2] / 'engine'

    def enabled(self, profile, release):
        flags = subprocess.run(
            ['make', '--no-print-directory', 'SETUP_PREREQS=0', 'NODEP=1',
             f'RELEASE={release}', f'CRIES={profile}', '--eval',
             'show-cry-flags: ; @echo $(CRY_CPPFLAGS)', 'show-cry-flags'],
            cwd=self.engine, capture_output=True, text=True, check=True).stdout.split()
        source = '#include "gba/defines.h"\n#include "config/pokemon.h"\nP_CRIES_ENABLED\n'
        result = subprocess.run(
            ['cc', '-E', '-P', '-x', 'c', '-I', 'include', *flags,
             *(['-DRELEASE'] if release else []), '-'],
            cwd=self.engine, input=source, capture_output=True, text=True, check=True)
        return int(result.stdout.splitlines()[-1])

    def test_default_is_off_in_normal_and_release(self):
        for release in (0, 1):
            with self.subTest(release=release):
                self.assertEqual(self.enabled('default', release), 0)

    def test_explicit_on_restores_cries_in_normal_and_release(self):
        for release in (0, 1):
            with self.subTest(release=release):
                self.assertEqual(self.enabled('on', release), 1)

    def test_explicit_off_remains_off_in_normal_and_release(self):
        for release in (0, 1):
            with self.subTest(release=release):
                self.assertEqual(self.enabled('off', release), 0)


if __name__ == '__main__':
    unittest.main()
