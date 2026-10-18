"""Scratch debugging only: load savestate slot N under the CLI debugger and
trace up to COUNT instructions; keep the tail before the crash."""
import collections, os, pty, select, subprocess, sys, time
rom, slot, logp, sym, count = sys.argv[1:6]
env = dict(os.environ, DISPLAY=':78', SDL_AUDIODRIVER='dummy')
xvfb = subprocess.Popen(['Xvfb', ':78', '-screen', '0', '800x600x24', '-nolisten', 'tcp'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
pid, fd = pty.fork()
if pid == 0:
    os.execvpe('mgba', ['mgba', '-d', '-2', rom], env)
ring = collections.deque(maxlen=20000)
partial = b''
alive = True
def pump(t):
    global partial, alive
    end = time.monotonic() + t
    while time.monotonic() < end and alive:
        r, _, _ = select.select([fd], [], [], 0.02)
        if not r:
            continue
        try:
            data = os.read(fd, 1 << 20)
        except OSError:
            alive = False; break
        if not data:
            alive = False; break
        lines = (partial + data).split(b'\n')
        partial = lines.pop()
        ring.extend(l.decode('utf-8', 'replace') for l in lines)
def send(c, t=2.0):
    ring.append(f'##> {c}')
    os.write(fd, (c + '\n').encode())
    pump(t)
pump(3)
send(f'load-symbols {sym}')
send(f'load {slot}', 3)
send('i', 2)
send(f'trace {count}', 1)
t_end = time.monotonic() + 1500
while alive and time.monotonic() < t_end:
    pump(1)
    if ring and ring[-1].startswith('Cycle:'):
        pass
with open(logp, 'w') as log:
    log.write(f'## alive={alive}\n' + '\n'.join(ring) + '\n' + partial.decode('utf-8', 'replace'))
try:
    os.kill(pid, 15)
except OSError:
    pass
xvfb.terminate()
