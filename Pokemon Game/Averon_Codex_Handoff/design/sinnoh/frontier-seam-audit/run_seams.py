"""Observe retained split-campus walls with existing map_qa; never repair donor geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
SCRIPTS = ROOT / 'Pokemon Game/scripts/claude_play'
sys.path.insert(0, str(SCRIPTS))
import driver  # Pin the host driver before loading the engine's gameplay wrapper.
import map_qa as qa
import mapdata

MAPS = ('MAP_SINNOH_FRONTIER_CAMPUSWEST', 'MAP_SINNOH_FRONTIER_CAMPUSEAST')


def cell(m, tile):
    return dict(word=m.blocks[tile[1] * m.width + tile[0]], collision=m.collision(*tile),
                elevation=m.elevation(*tile), behavior=m.behavior(*tile))


def groups(world):
    """Keep every failed face; partition by mutual foot reachability, not proximity."""
    result = []
    for mid in MAPS:
        m = world.map(mid)
        pending = []
        for p in qa.map_points(m):
            if p['kind'] != 'connection':
                continue
            dest = world.map(p['dest'])
            target = qa.across(m, dest, p['direction'], p['offset'], p['tile'])
            if dest.inside(*target) and dest.walkable(*target) and mapdata.crossable(m, p['tile'], dest, target):
                continue
            if not dest.inside(*target):
                raise ValueError('out-of-bounds seam needs a separate diagnosis')
            pending.append(dict(map=mid, tile=list(p['tile']), direction=p['direction'],
                                dest=p['dest'], dest_tile=list(target), source=cell(m, p['tile']),
                                target=cell(dest, target)))
        while pending:
            entry = tuple(pending[0]['tile'])
            component = qa.reach(m, [entry]) & qa.reach(m, [entry], reverse=True)
            selected = [p for p in pending if tuple(p['tile']) in component]
            if not selected:
                raise ValueError('probe tile is not mutually foot reachable from itself')
            result.append(dict(map=mid, entry=list(entry), faces=selected))
            pending = [p for p in pending if p not in selected]
    return result


def validate(engine, receipt):
    engine = Path(engine).resolve()
    if not (engine / '.map_qa_throwaway').is_file():
        raise ValueError('marked disposable engine required')
    if len(receipt['existing_map_names_preserved']) != 30 or len(receipt['scene']) != 44 or len(receipt['files']) != 191:
        raise ValueError('exact accepted 30+44 source receipt required')
    for path, expected in receipt['files'].items():
        p = Path(path)
        target = engine / p
        if p.is_absolute() or '..' in p.parts or not target.resolve().is_relative_to(engine):
            raise ValueError('source path escapes engine')
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise ValueError('source differs: ' + path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('engine', 'receipt', 'scratch', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--group', type=int, required=True)
    p.add_argument('--profile', choices=('normal', 'release'), required=True)
    a = p.parse_args()
    engine, scratch, out = a.engine.resolve(), a.scratch.resolve(), a.out.resolve()
    receipt = json.loads(a.receipt.read_text())
    validate(engine, receipt)
    if out == scratch or out.is_relative_to(engine) or scratch.is_relative_to(engine):
        raise ValueError('external distinct evidence and scratch required')
    if not (scratch / 'game.sav').is_file():
        raise ValueError('source-qualified private Continue fixture required')
    plan = groups(mapdata.World(engine))
    if not 0 <= a.group < len(plan):
        raise ValueError('unknown component')
    selected = plan[a.group]

    class SeamRunner(qa.Runner):
        def run_map(self, mid):
            self.check('component starts at qualified entry', self.d.here() == (mid, tuple(selected['entry'])), at=self.d.here())
            for face in selected['faces']:
                # Validate wall semantics separately; do not mask a later changed source.
                if face['target']['collision'] != 3:
                    raise ValueError('expected collision-3 source wall changed')
                if not self.go(mid, face['tile']):
                    self.check('source wall probe reachable', False, face=face, at=self.d.here())
                    continue
                self.d.settle()
                before = self.d.here()
                self.press(face['direction'], hold=.35, after=.8)
                self.d.settle()
                self.d.shot('source-wall-' + '-'.join(map(str, face['tile'])))
                self.check('source collision-3 neighbor blocks seam push', self.d.here() == before,
                           face=face, before=before, after=self.d.here())

    qa.Runner = SeamRunner
    rom = engine / ('pokeemerald-cries-off' + ('-release' if a.profile == 'release' else '') + '.gba')
    config = argparse.Namespace(engine=str(engine), rom=str(rom), scratch=str(scratch), out=str(out),
        build=a.profile, map=[selected['map']], expect=None, save=None, blocked=None,
        region_ui=None, region_ui_map=None, whiteout=None, whiteout_npc=None)
    code = qa.cmd_run(config)
    (out / 'component.json').write_text(json.dumps(dict(group=a.group, plan=selected,
        source_sha=receipt['source_sha'], base=receipt['base'],
        probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Rendered negative wall checks only; static findings remain, no full-world or production acceptance'), indent=2) + '\n')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
