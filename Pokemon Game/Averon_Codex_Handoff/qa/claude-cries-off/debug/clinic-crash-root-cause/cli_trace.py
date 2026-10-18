"""Scratch debugging only: savestate under mGBA CLI debugger; break at BP, then
trace N instructions while pressing A; keep the last lines before the crash."""
import collections, os, pty, select, subprocess, sys, time
rom, state, logp, sym, bp, n = sys.argv[1:7]
env = dict(os.environ, DISPLAY=':78', SDL_AUDIODRIVER='dummy')
xvfb = subprocess.Popen(['Xvfb', ':78', '-screen', '0', '800x600x24', '-nolisten', 'tcp'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
pid, fd = pty.fork()
if pid == 0:
    os.execvpe('mgba', ['mgba', '-d', '-2', '-t', state, rom], env)
log = open(logp, 'w')
ring = collections.deque(maxlen=6000)
partial = b''
alive = True
def pump(t):
    global partial, alive
    end = time.monotonic() + t
    got = b''
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
        got += data
        lines = (partial + data).split(b'\n')
        partial = lines.pop()
        for l in lines:
            ring.append(l.decode('utf-8', 'replace'))
    return got
def send(c):
    ring.append(f'##> {c}')
    os.write(fd, (c + '\n').encode())
pump(3)
window = subprocess.run(['xdotool', 'search', '--name', 'mGBA'], env=env, capture_output=True, text=True).stdout.split()[0]
for c in (f'load-symbols {sym}', f'break {bp}', 'c'):
    send(c); pump(1.0)
hit = False
t_end = time.monotonic() + 120
next_key = 0
while alive and time.monotonic() < t_end:
    now = time.monotonic()
    if now >= next_key:
        subprocess.run(['xdotool', 'keydown', '--window', window, 'x'], env=env)
        time.sleep(0.1)
        subprocess.run(['xdotool', 'keyup', '--window', window, 'x'], env=env)
        next_key = now + 0.5
    pump(0.1)
    if not hit and any(l.startswith('Hit breakpoint') or 'Hit breakpoint' in l for l in list(ring)[-8:]):
        hit = True
        log.write('## breakpoint hit; tracing\n' + '\n'.join(list(ring)[-20:]) + '\n'); log.flush()
        send(f'delete 1'); pump(0.5)
        send(f'trace {n}')
        t_end = time.monotonic() + 1800
log.write(f'## alive={alive} hit={hit}\n')
log.write('\n'.join(ring) + '\n' + partial.decode('utf-8', 'replace'))
log.close()
try:
    os.kill(pid, 15)
except OSError:
    pass
xvfb.terminate()
