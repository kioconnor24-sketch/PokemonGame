"""static_scene: a batch's tileset declarations are validated and every write stays inside the engine tree."""
import importlib.util
import os
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1].parent
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("static_scene", ROOT / "scripts/claude_play/static_scene.py")
ss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ss)


def decl(**over):
    t = {"symbol": "ClaudeTestPrimary", "secondary": False, "graphics": "Building",
         "metatiles": "art/metatiles.bin", "attributes": "art/attributes.bin"}
    t.update(over)
    return t


class StaticSceneTilesetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.batch = pathlib.Path(self.tmp.name) / "batch"
        (self.batch / "art").mkdir(parents=True)
        (self.batch / "art/metatiles.bin").write_bytes(b"\1" * 16)
        (self.batch / "art/attributes.bin").write_bytes(b"\2" * 2)
        self.outside = pathlib.Path(self.tmp.name) / "outside.bin"
        self.outside.write_bytes(b"preserve outside work")

    def tearDown(self):
        self.tmp.cleanup()

    def refused(self, *decls):
        files = {}
        with self.assertRaises(SystemExit):
            ss.declare_tilesets(files, ENGINE, self.batch, list(decls))
        return files

    def test_a_valid_pair_is_declared_under_the_engine(self):
        files = {}
        ss.declare_tilesets(files, ENGINE, self.batch, [decl(), decl(symbol="ClaudeTestSecondary", secondary=True,
                                                                     graphics="Shop")])
        self.assertEqual(files["data/tilesets/primary/claudetestprimary/metatiles.bin"], b"\1" * 16)
        self.assertIn("data/tilesets/secondary/claudetestsecondary/metatile_attributes.bin", files)
        self.assertIn(b"gTileset_ClaudeTestSecondary = { .isCompressed=TRUE, .isSecondary=TRUE",
                      files["src/data/tilesets/headers.h"])

    def test_a_traversal_symbol_is_refused(self):
        files = self.refused(decl(symbol="../../../../outside"))
        self.assertFalse(any("outside" in k for k in files))
        self.assertEqual(self.outside.read_bytes(), b"preserve outside work")

    def test_non_identifier_graphics_and_bank_are_refused(self):
        self.refused(decl(graphics="Building|.*"))
        self.refused(decl(symbol="9Lives"))
        self.refused(decl(secondary="yes"))
        self.refused(decl(graphics="NoSuchTileset"))

    def test_an_existing_or_repeated_symbol_is_refused(self):
        self.refused(decl(symbol="General"))
        self.refused(decl(), decl())

    def test_sources_must_stay_inside_the_batch(self):
        self.refused(decl(metatiles="../outside.bin"))
        (self.batch / "art/link.bin").symlink_to(self.outside)
        self.refused(decl(attributes="art/link.bin"))

    def test_the_writer_refuses_an_escape_before_writing_anything(self):
        eng = pathlib.Path(self.tmp.name) / "engine"
        eng.mkdir()
        with self.assertRaises(SystemExit):
            ss.write_files(eng, {"data/ok.bin": b"x", "../outside.bin": b"\0" * 16})
        self.assertFalse((eng / "data/ok.bin").exists())
        self.assertEqual(self.outside.read_bytes(), b"preserve outside work")

    def test_the_writer_refuses_a_symlinked_directory_out_of_the_engine(self):
        eng = pathlib.Path(self.tmp.name) / "engine"
        (eng / "data").mkdir(parents=True)
        os.symlink(self.tmp.name, eng / "data/escape")
        with self.assertRaises(SystemExit):
            ss.write_files(eng, {"data/escape/outside.bin": b"\0"})
        self.assertEqual(self.outside.read_bytes(), b"preserve outside work")

    def test_the_writer_writes_inside_the_engine(self):
        eng = pathlib.Path(self.tmp.name) / "engine"
        eng.mkdir()
        ss.write_files(eng, {"data/maps/X/map.json": b"{}"})
        self.assertEqual((eng / "data/maps/X/map.json").read_bytes(), b"{}")


if __name__ == "__main__":
    unittest.main()
