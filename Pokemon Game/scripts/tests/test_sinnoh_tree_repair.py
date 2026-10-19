"""Sinnoh tree repair tool: orphan detection on synthetic layouts, a --fix that touches only the
metatile id bits of orphan quarters, exit codes, mutant fixers the checks must reject, and the real
Sandgem layout (read-only; any --fix runs on a temporary copy)."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'sinnoh-tree-repair.py'
ENGINE = Path(__file__).resolve().parents[2] / 'engine'
SPEC = importlib.util.spec_from_file_location('sinnoh_tree_repair', SCRIPT)
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)

TREE_IDS = (468, 469, 470, 471, 476, 477, 484, 485)
GRASS, ROAD, BUSH = 1, 2, 22
# Ids next to the tree quarters that must never be mistaken for trees.
NEAR_MISSES = (467, 472, 473, 474, 475, 478, 479, 483, 486)
# Sandgem's committed map.bin (main) has this many orphans. Set it to 0 once the repaired map lands.
SANDGEM_ORPHANS = 0  # repaired in the Route 201 + Sandgem tree-repair PR (was 57)


def high_bits(x, y):
    """Collision (bits 10-11) and elevation (bits 12-15), never zero, varying per cell."""
    return ((1 + (x + y) % 3) << 10) | ((1 + (x * 5 + y * 3) % 15) << 12)


def grid(rows, high=high_bits):
    """'T' tree quarter, '.' grass, 'r' road, 'b' bush. Returns (width, height, blocks)."""
    width, height = len(rows[0]), len(rows)
    assert all(len(r) == width for r in rows)
    blocks = []
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            mt = TREE_IDS[(x + 2 * y) % len(TREE_IDS)] if c == 'T' else {'.': GRASS, 'r': ROAD, 'b': BUSH}[c]
            blocks.append(mt | high(x, y))
    return width, height, blocks


def pack(blocks):
    return struct.pack(f'<{len(blocks)}H', *blocks)


def unpack(raw):
    return list(struct.unpack(f'<{len(raw) // 2}H', raw))


def make_engine(root, layouts):
    """A fake engine: data/layouts/layouts.json plus one map.bin per layout id."""
    engine = Path(root) / 'engine'
    entries = []
    for lid, (width, height, blocks) in layouts.items():
        rel = f'data/layouts/{lid}/map.bin'
        (engine / rel).parent.mkdir(parents=True, exist_ok=True)
        (engine / rel).write_bytes(pack(blocks))
        entries.append({'id': lid, 'name': f'{lid}_Layout', 'width': width, 'height': height,
                        'primary_tileset': 'gTileset_General', 'secondary_tileset': 'gTileset_Petalburg',
                        'border_filepath': f'data/layouts/{lid}/border.bin', 'blockdata_filepath': rel,
                        'layout_version': 'emerald'})
    (engine / 'data/layouts/layouts.json').write_text(json.dumps({'layouts_table_label': 'gMapLayouts',
                                                                   'layouts': entries}))
    return engine


def run_main(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = tool.main(list(argv))
    return code, out.getvalue()


def fix_violations(before_raw, after_raw, width, found, bush=BUSH):
    """Every way after_raw differs from a correct --fix of before_raw (empty list = correct)."""
    if len(before_raw) != len(after_raw):
        return [f'length {len(before_raw)} -> {len(after_raw)}']
    found = set(found)
    problems = []
    before, after = unpack(before_raw), unpack(after_raw)
    for i, (b, a) in enumerate(zip(before, after)):
        x, y = i % width, i // width
        if (x, y) not in found:
            if before_raw[2 * i:2 * i + 2] != after_raw[2 * i:2 * i + 2]:
                problems.append(f'non-orphan ({x},{y}) changed {b:#06x} -> {a:#06x}')
            continue
        if a & 0xFC00 != b & 0xFC00:
            problems.append(f'orphan ({x},{y}) high bits {b & 0xFC00:#06x} -> {a & 0xFC00:#06x}')
        if a & 0x0C00 != b & 0x0C00:
            problems.append(f'orphan ({x},{y}) collision {(b >> 10) & 3} -> {(a >> 10) & 3}')
        if a >> 12 != b >> 12:
            problems.append(f'orphan ({x},{y}) elevation {b >> 12} -> {a >> 12}')
        if a & 0x3FF != bush:
            problems.append(f'orphan ({x},{y}) metatile {a & 0x3FF} != bush {bush}')
    return problems


# A layout mixing complete trees, a misaligned tree, a top-half tree, a lone quarter, edge trees
# (odd width/height, blocks running off the map) and non-tree cells. Width 9, height 7.
MIXED = [
    'TT.TT...T',  # (0,0)-(1,1) complete; (3..4,0..1) misaligned; (8,0..1) edge column, block off-map
    'TT.TT...T',
    '..TT.....',  # (2..3,2) top half only: block (2..3,2..3) has grass below
    '....rr.T.',  # (7,3) lone quarter
    'TT..TT...',  # (0..1,4..5) complete; (4..5,4..5) complete
    'TT..TTrrr',
    'TT.T....T',  # row 6 is the last (odd height): (0..1,6) edge pair; (3,6) partner (2,6) grass; (8,6) corner
]
MIXED_ORPHANS = {(3, 0), (3, 1), (4, 0), (4, 1), (2, 2), (3, 2), (7, 3), (3, 6)}


class DetectionTests(unittest.TestCase):
    def scan(self, rows):
        width, height, blocks = grid(rows)
        return set(tool.orphans(blocks, width, height))

    def test_complete_aligned_tree_has_no_orphans(self):
        self.assertEqual(self.scan(['TT..', 'TT..', '....', '....']), set())
        self.assertEqual(self.scan(['....', '....', '..TT', '..TT']), set())
        self.assertEqual(self.scan(['TTTT', 'TTTT', 'TTTT', 'TTTT']), set())

    def test_lone_quarter_is_an_orphan(self):
        for x, y in [(0, 0), (1, 0), (2, 3), (3, 3)]:
            rows = [''.join('T' if (cx, cy) == (x, y) else '.' for cx in range(4)) for cy in range(4)]
            self.assertEqual(self.scan(rows), {(x, y)}, rows)

    def test_half_tree_and_odd_boundary_are_orphans(self):
        # Top half of an aligned block.
        self.assertEqual(self.scan(['TT..', '....', '....', '....']), {(0, 0), (1, 0)})
        # Left half of an aligned block.
        self.assertEqual(self.scan(['....', '....', '..T.', '..T.']), {(2, 2), (2, 3)})
        # A 2x2 tree starting on an odd column straddles two blocks: every quarter is cut.
        self.assertEqual(self.scan(['.TT.', '.TT.', '....', '....']), {(1, 0), (2, 0), (1, 1), (2, 1)})
        # Starting on an odd row likewise.
        self.assertEqual(self.scan(['....', 'TT..', 'TT..', '....']), {(0, 1), (1, 1), (0, 2), (1, 2)})

    def test_edge_blocks_running_off_the_map_are_not_orphans(self):
        # Width 5 / height 5: column 4 and row 4 blocks extend outside, which counts as tree.
        rows = ['....T', '....T', '.....', '.....', 'TT..T']
        self.assertEqual(self.scan(rows), set())
        self.assertEqual(self.scan(['T']), set())
        self.assertEqual(self.scan(['TTT', 'TTT', 'TTT']), set())
        self.assertEqual(self.scan(['..TT.', '..TT.', '....T']), set())
        # ...but an in-map partner that is not a tree still makes the edge quarter an orphan.
        self.assertEqual(self.scan(['....T', '.....', '.....']), {(4, 0)})
        self.assertEqual(self.scan(['.....', '.....', 'T....']), {(0, 2)})

    def test_only_the_low_ten_bits_decide_tree_membership(self):
        # A tree id with collision/elevation set is still a tree; ids next to the tree ids are not.
        width, height = 2, 2
        blocks = [468 | 0xFC00, 469 | 0x0400, 476 | 0x3000, 477]
        self.assertEqual(tool.orphans(blocks, width, height), [])
        for near in NEAR_MISSES:
            self.assertNotIn(near, TREE_IDS)
            blocks = [468, 469, 476, near | 0x0C00]
            self.assertEqual(set(tool.orphans(blocks, width, height)), {(0, 0), (1, 0), (0, 1)}, near)
        # Collision/elevation bits never turn a non-tree id into a tree.
        self.assertEqual(tool.orphans([468, 469, 476, GRASS | 0xFC00], 2, 2), [(0, 0), (1, 0), (0, 1)])

    def test_mixed_layout_orphan_set(self):
        self.assertEqual(self.scan(MIXED), MIXED_ORPHANS)

    def test_orphans_are_reported_in_row_major_order(self):
        width, height, blocks = grid(MIXED)
        found = tool.orphans(blocks, width, height)
        self.assertEqual(found, sorted(found, key=lambda p: (p[1], p[0])))


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def engine_with(self, **layouts):
        return make_engine(self.tmp.name, {lid: grid(rows) for lid, rows in layouts.items()})

    def map_bin(self, engine, lid):
        return engine / f'data/layouts/{lid}/map.bin'

    def test_detect_only_exit_codes_and_no_writes(self):
        engine = self.engine_with(LAYOUT_CLEAN=['TT..', 'TT..'], LAYOUT_DIRTY=MIXED)
        clean_before = self.map_bin(engine, 'LAYOUT_CLEAN').read_bytes()
        dirty_before = self.map_bin(engine, 'LAYOUT_DIRTY').read_bytes()
        self.assertEqual(run_main('--engine', str(engine), 'LAYOUT_CLEAN'),
                         (0, 'LAYOUT_CLEAN: 0 orphan tree quarters\n'))
        self.assertEqual(run_main('--engine', str(engine), 'LAYOUT_DIRTY'),
                         (1, f'LAYOUT_DIRTY: {len(MIXED_ORPHANS)} orphan tree quarters\n'))
        code, out = run_main('--engine', str(engine), 'LAYOUT_CLEAN', 'LAYOUT_DIRTY')
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), ['LAYOUT_CLEAN: 0 orphan tree quarters',
                                            f'LAYOUT_DIRTY: {len(MIXED_ORPHANS)} orphan tree quarters'])
        self.assertEqual(self.map_bin(engine, 'LAYOUT_CLEAN').read_bytes(), clean_before)
        self.assertEqual(self.map_bin(engine, 'LAYOUT_DIRTY').read_bytes(), dirty_before)

    def test_process_exit_status(self):
        engine = self.engine_with(LAYOUT_DIRTY=MIXED)
        cmd = [sys.executable, '-B', str(SCRIPT), '--engine', str(engine), 'LAYOUT_DIRTY']
        self.assertEqual(subprocess.run(cmd, capture_output=True, text=True).returncode, 1)
        done = subprocess.run(cmd + ['--fix'], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('-> fixed', done.stdout)
        self.assertEqual(subprocess.run(cmd, capture_output=True, text=True).returncode, 0)

    def test_fix_touches_only_orphan_metatile_bits(self):
        engine = self.engine_with(LAYOUT_DIRTY=MIXED)
        path = self.map_bin(engine, 'LAYOUT_DIRTY')
        before = path.read_bytes()
        width = len(MIXED[0])
        self.assertEqual(run_main('--engine', str(engine), 'LAYOUT_DIRTY', '--fix'),
                         (0, f'LAYOUT_DIRTY: {len(MIXED_ORPHANS)} orphan tree quarters -> fixed\n'))
        after = path.read_bytes()
        self.assertEqual(fix_violations(before, after, width, MIXED_ORPHANS), [])
        b, a = unpack(before), unpack(after)
        for i in range(len(b)):
            self.assertEqual(a[i] >> 10, b[i] >> 10, f'high 6 bits of cell {i % width},{i // width}')
            if (i % width, i // width) not in MIXED_ORPHANS:
                self.assertEqual(after[2 * i:2 * i + 2], before[2 * i:2 * i + 2])
        # Non-tree cells are never modified; complete trees keep their quarters.
        for i in range(len(b)):
            if b[i] & 0x3FF not in TREE_IDS:
                self.assertEqual(a[i], b[i])
        self.assertEqual(sum(1 for v in a if v & 0x3FF in TREE_IDS),
                         sum(1 for v in b if v & 0x3FF in TREE_IDS) - len(MIXED_ORPHANS))

    def test_rescan_after_fix_is_clean_and_fix_is_idempotent(self):
        engine = self.engine_with(LAYOUT_DIRTY=MIXED)
        path = self.map_bin(engine, 'LAYOUT_DIRTY')
        run_main('--engine', str(engine), 'LAYOUT_DIRTY', '--fix')
        fixed = path.read_bytes()
        self.assertEqual(tool.orphans(unpack(fixed), len(MIXED[0]), len(MIXED)), [])
        self.assertEqual(run_main('--engine', str(engine), 'LAYOUT_DIRTY'),
                         (0, 'LAYOUT_DIRTY: 0 orphan tree quarters\n'))
        self.assertEqual(run_main('--engine', str(engine), 'LAYOUT_DIRTY', '--fix'),
                         (0, 'LAYOUT_DIRTY: 0 orphan tree quarters\n'))
        self.assertEqual(path.read_bytes(), fixed)

    def test_fix_on_clean_layout_leaves_file_untouched(self):
        engine = self.engine_with(LAYOUT_CLEAN=['TT..', 'TT..', '..rr'])
        path = self.map_bin(engine, 'LAYOUT_CLEAN')
        before, mtime = path.read_bytes(), path.stat().st_mtime_ns
        self.assertEqual(run_main('--engine', str(engine), 'LAYOUT_CLEAN', '--fix'),
                         (0, 'LAYOUT_CLEAN: 0 orphan tree quarters\n'))
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.stat().st_mtime_ns, mtime)

    def test_custom_bush_and_untouched_sibling_layout(self):
        engine = self.engine_with(LAYOUT_DIRTY=MIXED, LAYOUT_OTHER=['.T..', '....'])
        other_before = self.map_bin(engine, 'LAYOUT_OTHER').read_bytes()
        before = self.map_bin(engine, 'LAYOUT_DIRTY').read_bytes()
        self.assertEqual(run_main('--engine', str(engine), 'LAYOUT_DIRTY', '--fix', '--bush', '7')[0], 0)
        after = self.map_bin(engine, 'LAYOUT_DIRTY').read_bytes()
        self.assertEqual(fix_violations(before, after, len(MIXED[0]), MIXED_ORPHANS, bush=7), [])
        self.assertEqual(self.map_bin(engine, 'LAYOUT_OTHER').read_bytes(), other_before)

    def test_unknown_layout_id_fails_loudly(self):
        engine = self.engine_with(LAYOUT_CLEAN=['TT', 'TT'])
        with self.assertRaises(KeyError), contextlib.redirect_stdout(io.StringIO()):
            tool.main(['--engine', str(engine), 'LAYOUT_MISSING'])


class MutantFixerTests(unittest.TestCase):
    """The --fix checks must reject plausible wrong fixers, or they prove nothing."""

    def setUp(self):
        self.width, self.height, self.blocks = grid(MIXED)
        self.before = pack(self.blocks)
        self.found = tool.orphans(self.blocks, self.width, self.height)
        self.assertEqual(set(self.found), MIXED_ORPHANS)

    def apply(self, rewrite, cells=None):
        blocks = list(self.blocks)
        for x, y in (self.found if cells is None else cells):
            i = y * self.width + x
            blocks[i] = rewrite(blocks[i]) & 0xFFFF
        return pack(blocks)

    def assert_rejected(self, after):
        self.assertNotEqual(fix_violations(self.before, after, self.width, self.found), [])

    def test_correct_fixer_is_accepted(self):
        self.assertEqual(fix_violations(self.before, self.apply(lambda v: (v & ~0x3FF) | BUSH),
                                        self.width, self.found), [])

    def test_fixer_that_clears_collision_is_rejected(self):
        self.assert_rejected(self.apply(lambda v: (v & 0xF000) | BUSH))

    def test_fixer_that_clears_elevation_is_rejected(self):
        self.assert_rejected(self.apply(lambda v: (v & 0x0C00) | BUSH))

    def test_fixer_that_writes_a_bare_metatile_is_rejected(self):
        self.assert_rejected(self.apply(lambda v: BUSH))

    def test_fixer_that_masks_the_wrong_width_is_rejected(self):
        # Clearing 11 bits instead of 10 drops the low collision bit.
        self.assert_rejected(self.apply(lambda v: (v & ~0x7FF) | BUSH))

    def test_fixer_with_the_wrong_metatile_is_rejected(self):
        self.assert_rejected(self.apply(lambda v: (v & ~0x3FF) | (BUSH + 1)))

    def test_fixer_that_also_touches_a_non_orphan_is_rejected(self):
        good = self.apply(lambda v: (v & ~0x3FF) | BUSH)
        blocks = unpack(good)
        blocks[0] = (blocks[0] & ~0x3FF) | BUSH  # (0,0) belongs to a complete tree
        self.assert_rejected(pack(blocks))
        blocks = unpack(good)
        grass = next(i for i, v in enumerate(self.blocks) if v & 0x3FF == GRASS)
        blocks[grass] ^= 1 << 10  # a collision flip on a grass cell
        self.assert_rejected(pack(blocks))

    def test_fixer_that_misses_an_orphan_is_rejected(self):
        self.assert_rejected(self.apply(lambda v: (v & ~0x3FF) | BUSH, cells=self.found[1:]))

    def test_fixer_that_changes_the_file_length_is_rejected(self):
        self.assert_rejected(self.apply(lambda v: (v & ~0x3FF) | BUSH) + b'\0\0')


@unittest.skipUnless((ENGINE / 'data/layouts/SandgemTown/map.bin').is_file(), 'Sandgem layout not in this tree')
class RealSandgemTests(unittest.TestCase):
    LID = 'LAYOUT_SANDGEM_TOWN'

    def setUp(self):
        table = json.loads((ENGINE / 'data/layouts/layouts.json').read_text())['layouts']
        self.entry = next(l for l in table if l.get('id') == self.LID)
        self.path = ENGINE / self.entry['blockdata_filepath']
        self.raw = self.path.read_bytes()
        self.digest = hashlib.sha256(self.raw).hexdigest()
        self.addCleanup(self.assert_committed_map_untouched)

    def assert_committed_map_untouched(self):
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), self.digest)

    def test_detector_reports_the_known_orphan_count(self):
        width, height = self.entry['width'], self.entry['height']
        self.assertEqual(len(self.raw), 2 * width * height)
        self.assertEqual(len(tool.orphans(unpack(self.raw), width, height)), SANDGEM_ORPHANS)
        self.assertEqual(run_main('--engine', str(ENGINE), self.LID),
                         (1 if SANDGEM_ORPHANS else 0, f'{self.LID}: {SANDGEM_ORPHANS} orphan tree quarters\n'))

    def test_fix_on_a_temporary_copy(self):
        width, height = self.entry['width'], self.entry['height']
        found = tool.orphans(unpack(self.raw), width, height)
        with tempfile.TemporaryDirectory() as tmp:
            engine = Path(tmp) / 'engine'
            copy = engine / self.entry['blockdata_filepath']
            copy.parent.mkdir(parents=True)
            shutil.copyfile(self.path, copy)
            (engine / 'data/layouts/layouts.json').write_text(json.dumps({'layouts': [self.entry]}))
            code, out = run_main('--engine', str(engine), self.LID, '--fix')
            self.assertEqual(code, 0)
            self.assertEqual(out, f'{self.LID}: {SANDGEM_ORPHANS} orphan tree quarters'
                             + (' -> fixed' if SANDGEM_ORPHANS else '') + '\n')
            fixed = copy.read_bytes()
        self.assertEqual(tool.orphans(unpack(fixed), width, height), [])
        self.assertEqual(fix_violations(self.raw, fixed, width, found), [])
        original, repaired = unpack(self.raw), unpack(fixed)
        for i, (o, r) in enumerate(zip(original, repaired)):
            self.assertEqual((r >> 10) & 3, (o >> 10) & 3, f'collision at {i % width},{i // width}')
            self.assertEqual(r >> 12, o >> 12, f'elevation at {i % width},{i // width}')


if __name__ == '__main__':
    unittest.main()
