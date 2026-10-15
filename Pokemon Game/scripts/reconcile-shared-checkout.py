"""Copy only changed tracked source into the isolated GitHub checkout.

No deletion, generated ROM, save, cache, or unrelated personal files are copied.
"""
from pathlib import Path
import subprocess, shutil

root = Path(__file__).resolve().parents[1]
shared = root / 'shared-repo'
target = shared / 'Pokemon Game'
paths = subprocess.check_output(['git', '-C', str(shared), 'ls-files', '-z']).decode().split('\0')
# The migration uploaded the complete existing engine. Compare source changed
# since the pinned upstream commit, rather than re-reading every sprite asset.
upstream = '73b3fbeb574327cd9420c89e56bef5aa3c08fead'
modified = set(subprocess.check_output([
    'wsl', '-d', 'Ubuntu', '-u', 'root', '--exec', 'bash', '-lc',
    f'cd /root/averon/engine; git -c core.safecrlf=false diff --name-only {upstream}; git ls-files --others --exclude-standard'
]).decode().splitlines())
changed = []
for name in paths:
    if not name.startswith('Pokemon Game/'):
        continue
    rel = name.removeprefix('Pokemon Game/')
    if rel.startswith('engine/') and rel.removeprefix('engine/') not in modified:
        continue
    if rel.startswith('evidence/'):
        continue
    src, dst = root / rel, shared / name
    if src.is_file() and src.read_bytes().replace(b'\r\n', b'\n') != dst.read_bytes().replace(b'\r\n', b'\n'):
        shutil.copy2(src, dst)
        changed.append(rel)
# New authoring, QA and coordination files are explicit, never a whole-tree copy.
new = ['scripts/averon-first-gym.inc', 'scripts/build-averon-first-gym.py',
       'scripts/install-averon-debug-tests.py', 'scripts/send-mgba-input.ps1',
       'scripts/reconcile-shared-checkout.py',
       'scripts/test-averon-caps.py', 'engine/test/battle/averon_exp.c',
       'engine/test/battle/averon_rules.c', 'engine/test/battle/averon_trainers.c',
       'engine/test/averon_scripts.c',
       'engine/test/averon_fair.c',
       'engine/test/averon_healing.c',
       'engine/test/averon_respawn.c',
       'engine/test/averon_candy.c',
       'engine/test/averon_gym_reward.c',
       'scripts/check-averon-dialogue.py', 'scripts/check-averon-authoring.py',
       'Averon_Codex_Handoff/development/FIRST_GYM_IMPLEMENTATION.md',
       'Averon_Codex_Handoff/development/TASKS.md',
       'Averon_Codex_Handoff/qa/OPENING_TEST_RESULTS.md']
for rel in new:
    src, dst = root / rel, target / rel
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
print('\n'.join(changed))
print(f'Compared {len(paths)-1} tracked files; copied {len(changed)} differing files plus explicit new files.')
