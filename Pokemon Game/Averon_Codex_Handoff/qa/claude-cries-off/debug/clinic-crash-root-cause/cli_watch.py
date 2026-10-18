"""Scratch debugging only: from a savestate, set a write watchpoint on ADDR
under the CLI debugger, press A in real time (0.1 s down, 0.4 s up), and log
every hit (registers, backtrace) until the watched word gets a value that is
neither NULL nor an EWRAM pointer, or the emulator dies."""
import json, os, pty, re, select, subprocess, sys, time
rom, state, logp, sym, addr = sys.argv[1:6]
env = dict(os.environ, DISPLAY=':78', SDL_AUDIODRIVER='dummy')
xvfb = subprocess.Popen(['Xvfb', ':78', '-screen', '0', '800x600x24', '-nolisten', 'tcp'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
pid, fd = pty.fork()
if pid == 0:
    os.execvpe('mgba', ['mgba', '-d', '-2', '-t', state, rom], env)
log = open(logp, 'w')
alive = True
def pump(t, until=None):
    global alive
    end = time.monotonic() + t
    got = b''
    while time.monotonic() < end and alive:
        r, _, _ = select.select([fd], [], [], 0.02)
        if not r:
            if until and until in got:
                break
            continue
        try:
            data = os.read(fd, 1 << 16)
        except OSError:
            alive = False; break
        if not data:
            alive = False; break
        got += data
        if until and until in got:
            break
    text = got.decode('utf-8', 'replace')
    log.write(text); log.flush()
    return text
def send(c, t=3.0, until=b'\n> '):
    log.write(f'\n##> {c}\n')
    os.write(fd, (c + '\n').encode())
    return pump(t, until)
pump(3)
window = subprocess.run(['xdotool', 'search', '--name', 'mGBA'], env=env, capture_output=True, text=True).stdout.split()[0]
def key(down):
    subprocess.run(['xdotool', 'keydown' if down else 'keyup', '--window', window, 'x'], env=env)
send(f'load-symbols {sym}')
send('stack trace-only')
send(f'watch/w {addr}')
hits = []
HIT = re.compile(r'Hit watchpoint \d+ at (0x[0-9A-Fa-f]+): \(new value = (0x[0-9A-Fa-f]+), old value = (0x[0-9A-Fa-f]+)\)')
PC = re.compile(r'r15: ([0-9A-F]{8})')
LR = re.compile(r'r14: ([0-9A-F]{8})')
os.write(fd, b'c\n')
t_end = time.monotonic() + 300
bad = None
while alive and time.monotonic() < t_end and len(hits) < 400 and bad is None:
    key(True); out = pump(0.1); key(False); out += pump(0.4)
    for m in HIT.finditer(out):
        new = int(m.group(2), 16)
        pc = PC.search(out); lr = LR.search(out)
        hit = dict(addr=m.group(1), new=f'{new:08X}', old=m.group(3),
                   pc=pc.group(1) if pc else None, lr=lr.group(1) if lr else None)
        bt = send('bt', 5.0)
        hit['bt'] = [l.strip() for l in bt.splitlines() if l.strip().startswith('#')][:12]
        hits.append(hit)
        if new and not (0x02000000 <= new < 0x02040000):
            bad = hit
    if 'Hit watchpoint' in out and bad is None:
        os.write(fd, b'c\n')
result = dict(alive=alive, hits=len(hits), bad=bad, last=hits[-6:])
log.write('\n## RESULT ' + json.dumps(result) + '\n')
if bad is not None:
    for c in ('r/4 0x02000014', 'r/4 0x02000018', 'r/4 0x0200001c', 'r/4 0x02000020'):
        send(c)
log.close()
print(json.dumps(result, indent=1))
try:
    os.kill(pid, 15)
except OSError:
    pass
xvfb.terminate()
