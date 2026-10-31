"""Pinned inputs for historical source receipts; never a production/runtime profile.

The old DEV producers certify post-C41 source. Production installers and their
new tests keep reading the actual checkout. Only archived replay tests opt in.
"""
from functools import lru_cache
from pathlib import Path
import atexit
import shutil
import subprocess
import tempfile

POST_C_COMMIT = '05ecd230564983312f3868deb7a9afcbbb5610e2'
POST_C_ENGINE = 'b06114f532e98f331dcdf64481fd01e726073fdf'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True,
                                   stderr=subprocess.PIPE).strip()


@lru_cache(maxsize=1)
def post_c_source_root(repo):
    repo = Path(repo).resolve()
    if git(repo, 'rev-parse', 'HEAD:Pokemon Game/engine') == POST_C_ENGINE:
        return repo
    # CI has a shallow checkout. Fetch only the exact accepted source revision;
    # never move its main/PR ref or relax the producers' hash guards.
    try:
        git(repo, 'cat-file', '-e', POST_C_COMMIT + '^{commit}')
    except subprocess.CalledProcessError:
        git(repo, 'fetch', '--no-tags', '--depth=1', 'origin', POST_C_COMMIT)
    if git(repo, 'rev-parse', POST_C_COMMIT + ':Pokemon Game/engine') != POST_C_ENGINE:
        raise RuntimeError('Historical source replay engine identity differs')
    root = Path(tempfile.mkdtemp(prefix='sinnoh-post-c-source-'))
    try:
        git(repo, 'worktree', 'add', '--detach', str(root), POST_C_COMMIT)
    except BaseException:
        shutil.rmtree(root)
        raise
    def cleanup():
        subprocess.run(['git', '-C', str(repo), 'worktree', 'remove', '--force', str(root)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    atexit.register(cleanup)
    return root
