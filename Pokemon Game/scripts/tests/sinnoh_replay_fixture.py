"""Pinned inputs for historical source receipts; never a production/runtime profile.

Archived DEV receipts use post-C41. Installer regressions exercise current
producer code on exact accepted phase inputs, so later integrations/codec changes
do not alter their baseline. Actual production/native/runtime checks stay live.
"""
from functools import lru_cache
from pathlib import Path
import atexit
import shutil
import subprocess
import tempfile

POST_C_COMMIT = '05ecd230564983312f3868deb7a9afcbbb5610e2'
POST_C_ENGINE = 'b06114f532e98f331dcdf64481fd01e726073fdf'
POST_D_COMMIT = 'b94dd146a69857e301098dca954ed7e934ade0e8'
POST_D_ENGINE = 'fab47d0e978ce7c7a3addaa74405f3a249fc413d'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True,
                                   stderr=subprocess.PIPE).strip()


@lru_cache(maxsize=2)
def pinned_source_root(repo, commit, engine_tree):
    repo = Path(repo).resolve()
    if git(repo, 'rev-parse', 'HEAD:Pokemon Game/engine') == engine_tree:
        return repo
    # CI has a shallow checkout. Fetch only the exact accepted source revision;
    # never move its main/PR ref or relax the producers' hash guards.
    try:
        git(repo, 'cat-file', '-e', commit + '^{commit}')
    except subprocess.CalledProcessError:
        git(repo, 'fetch', '--no-tags', '--depth=1', 'origin', commit)
    if git(repo, 'rev-parse', commit + ':Pokemon Game/engine') != engine_tree:
        raise RuntimeError('Historical source replay engine identity differs')
    root = Path(tempfile.mkdtemp(prefix='sinnoh-pinned-source-'))
    try:
        git(repo, 'worktree', 'add', '--detach', str(root), commit)
    except BaseException:
        shutil.rmtree(root)
        raise
    def cleanup():
        subprocess.run(['git', '-C', str(repo), 'worktree', 'remove', '--force', str(root)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    atexit.register(cleanup)
    return root


def post_c_source_root(repo):
    return pinned_source_root(Path(repo).resolve(), POST_C_COMMIT, POST_C_ENGINE)


def post_d_source_root(repo):
    return pinned_source_root(Path(repo).resolve(), POST_D_COMMIT, POST_D_ENGINE)
