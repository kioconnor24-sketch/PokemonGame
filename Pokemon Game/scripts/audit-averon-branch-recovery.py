#!/usr/bin/env python3
"""Read-only branch preservation audit. Never deletes, fetches, pushes or merges.

Squash receipts must match the exact branch head, be reachable from main, and
preserve every feature-path blob/mode at the integration commit. Ambiguous
combination/conflict/supersession cases remain UNKNOWN, not deletion candidates.
"""
import argparse
import csv
import json
from pathlib import Path
import re
import subprocess


class Git:
    def __init__(self, repo):
        self.repo = repo

    def run(self, *args, allowed=(0,)):
        p = subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True)
        if p.returncode not in allowed:
            raise ValueError(f"git {args[0]} failed: {p.stderr.decode(errors='replace').strip()}")
        return p

    def exists(self, sha):
        return bool(re.fullmatch(r'[0-9a-f]{40}', sha or '')) and self.run(
            'cat-file', '-e', sha + '^{commit}', allowed=(0, 128)).returncode == 0

    def ancestor(self, old, new):
        return self.run('merge-base', '--is-ancestor', old, new, allowed=(0, 1)).returncode == 0

    def changed(self, old, new, paths=None):
        args = ['diff', '--name-only', '--no-renames', '-z', old, new]
        if paths is not None:
            args += ['--'] + [':(literal)' + path for path in paths]
        return [p.decode('utf-8') for p in self.run(*args).stdout.split(b'\0') if p]

    def squash_scope(self, head, merge):
        parent = self.run('rev-parse', merge + '^1').stdout.decode().strip()
        base = self.run('merge-base', head, parent).stdout.decode().strip()
        paths = self.changed(base, head)
        missing = []
        for start in range(0, len(paths), 128):
            missing += self.changed(head, merge, paths[start:start + 128])
        return paths, sorted(set(missing))


def classify(git, branch, main, prs, active=(), retained=()):
    name, head = branch['name'], branch['sha']
    matches = [p for p in prs if p['head']['ref'] == name or p['head']['sha'] == head]
    row = dict(branch=name, head_sha=head, main_sha=main,
               classification='UNKNOWN', deletion_candidate=False,
               prs=','.join(str(p['number']) for p in matches), proof_sha='',
               feature_paths=0, unaccounted_paths='[]', reason='No verified integration receipt')

    def finish(kind, reason, proof=''):
        row.update(classification=kind, reason=reason, proof_sha=proof,
                   deletion_candidate=kind == 'INTEGRATED_WITH_NO_UNIQUE_WORK')
        return row

    if name == 'main' or branch.get('protected') or name in active or any(p['state'] == 'open' for p in matches):
        return finish('ACTIVE', 'Protected/default branch, explicit live claim, or open PR; retain')
    if name in retained:
        return finish('HISTORICAL_CHECKPOINT', 'Explicit preserved proof/checkpoint or attached worktree; retain')
    if not git.exists(head) or not git.exists(main):
        return finish('UNKNOWN', 'Commit object unavailable; retain and fetch evidence separately')
    try:
        if git.ancestor(head, main):
            return finish('INTEGRATED_WITH_NO_UNIQUE_WORK', 'Entire tip is reachable in main history', main)
        merged = [p for p in matches if p.get('merged_at')]
        for pr in merged:
            receipt = pr.get('merge_commit_sha')
            if pr['head']['sha'] != head or not git.exists(receipt) or not git.ancestor(receipt, main):
                continue
            paths, missing = git.squash_scope(head, receipt)
            row.update(feature_paths=len(paths), unaccounted_paths=json.dumps(missing))
            if paths and not missing:
                return finish('INTEGRATED_WITH_NO_UNIQUE_WORK',
                              f"PR#{pr['number']} exact-head receipt preserves every feature blob/mode", receipt)
            return finish('UNKNOWN', f"PR#{pr['number']} merged, but combined/conflicted/empty feature scope needs review", receipt)
        for pr in merged:
            old = pr['head']['sha']
            if git.exists(old) and git.ancestor(old, head) and git.changed(old, head):
                return finish('UNIQUE_UNMERGED_WORK',
                              'Nonempty commits after the recorded merged PR head; preserve, may be superseded', old)
        base = git.run('merge-base', head, main).stdout.decode().strip()
        paths = git.changed(base, head)
        missing = []
        for start in range(0, len(paths), 128):
            missing += git.changed(head, main, paths[start:start + 128])
        row.update(feature_paths=len(paths), unaccounted_paths=json.dumps(sorted(set(missing))))
        if matches and not merged and missing:
            return finish('UNIQUE_UNMERGED_WORK',
                          'Unmerged PR has literal feature-path differences; preserve, may be superseded')
        row['reason'] = 'No verified receipt; literal feature-path differences recorded; retain history'
        return row
    except (ValueError, UnicodeError) as error:
        return finish('UNKNOWN', str(error) + '; retain')


def audit(repo, inputs):
    branches = inputs['branches']
    if len({b['name'] for b in branches}) != len(branches):
        raise ValueError('Duplicate branch names in frozen snapshot')
    if not re.fullmatch(r'[0-9a-f]{40}', inputs['main']):
        raise ValueError('main must be a full commit SHA')
    git = Git(repo)
    return [classify(git, b, inputs['main'], inputs['prs'], inputs.get('active', ()),
                     inputs.get('retained', ())) for b in sorted(branches, key=lambda b: b['name'])]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--csv', type=Path, required=True)
    args = parser.parse_args()
    rows = audit(args.repo, json.loads(args.inputs.read_text()))
    if not rows:
        parser.error('Empty branch inventory')
    with args.csv.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({kind: sum(r['classification'] == kind for r in rows)
                      for kind in sorted({r['classification'] for r in rows})}, sort_keys=True))
    print(f"{len(rows)} branches; {sum(r['deletion_candidate'] for r in rows)} verified candidates; none deleted")


if __name__ == '__main__':
    main()
