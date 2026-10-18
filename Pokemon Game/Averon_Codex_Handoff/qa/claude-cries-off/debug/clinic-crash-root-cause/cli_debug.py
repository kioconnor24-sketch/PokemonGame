"""Scratch debugging only: load a savestate under mGBA's CLI debugger (-d) in a
pty, run setup commands, press keys in the window, and run commands after the
crash. Usage: cli_debug.py ROM STATE LOG 'cmd1;cmd2' 'key-plan' 'post1;post2'"""
import os, pty, select, subprocess, sys, time
rom, state, logp, pre, plan, post = sys.argv[1:7]
env = dict(os.environ, DISPLAY=':78', SDL_AUDIODRIVER='dummy')
xvfb = subprocess.Popen(['Xvfb', ':78', '-screen', '0', '800x600x24', '-nolisten', 'tcp'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
pid, fd = pty.fork()
if pid == 0:
    os.execvpe('mgba', ['mgba', '-d', '-2', '-t', state, rom], env)
log = open(logp, 'w')
def pump(t=0.5):
    end = time.monotonic() + t
    buf = b''
    while time.monotonic() < end:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try:
                data = os.read(fd, 65536)
            except OSError:
                return buf, False
            if not data:
                return buf, False
            buf += data
            log.write(data.decode('utf-8', 'replace')); log.flush()
    return buf, True
def cmd(c, t=1.0):
    log.write(f'\n##> {c}\n'); log.flush()
    os.write(fd, (c + '\n').encode())
    return pump(t)
pump(3)
window = None
for _ in range(40):
    out = subprocess.run(['xdotool', 'search', '--name', 'mGBA'], env=env, capture_output=True, text=True).stdout.split()
    if out:
        window = out[0]; break
    time.sleep(0.25)
log.write(f'\n## window {window}\n')
for c in pre.split(';'):
    if c.strip():
        cmd(c.strip(), 1.5)
alive = True
# Key plan: comma list of KEY:hold:after (KEY in x=A, z=B, Up, Down...)
for step in plan.split(','):
    if not step:
        continue
    k, hold, after = step.split(':')
    subprocess.run(['xdotool', 'keydown', '--window', window, k], env=env)
    _, alive = pump(float(hold))
    subprocess.run(['xdotool', 'keyup', '--window', window, k], env=env)
    _, alive = pump(float(after))
    if not alive:
        break
    if os.path.exists(logp) and 'crashed' in open(logp).read().lower() or 'Jumped' in open(logp).read():
        log.write('\n## crash text seen\n'); break
for c in post.split(';'):
    if c.strip():
        _, alive = cmd(c.strip(), 3)
        if not alive:
            log.write('\n## pty closed\n'); break
subprocess.run(['xdotool', 'search', '--name', 'mGBA'], env=env)
try:
    os.kill(pid, 15)
except OSError:
    pass
time.sleep(1)
xvfb.terminate()
