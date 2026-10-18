"""Scratch debugging only: from a savestate, set a write watchpoint on ADDR
under the CLI debugger, press A in real time (0.1 s down, 0.4 s up), and stop
at the FIRST hit: log registers, backtrace and a memory dump, then quit."""
import json, os, pty, re, select, subprocess, sys, time
rom, state, logp, sym, addr = sys.argv[1:6]
dumps = sys.argv[6:]
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
            alive = False
            break
        if not data:
            alive = False
            break
        got += data
        if until and until in got:
            break
    text = got.decode('utf-8', 'replace')
    log.write(text)
    log.flush()
    return text


def send(c, t=3.0, until=b'\n> '):
    log.write(f'\n##> {c}\n')
    os.write(fd, (c + '\n').encode())
    return pump(t, until)


pump(3)
window = subprocess.run(['xdotool', 'search', '--name', 'mGBA'], env=env,
                        capture_output=True, text=True).stdout.split()[0]


def key(down):
    subprocess.run(['xdotool', 'keydown' if down else 'keyup', '--window', window, 'x'], env=env)


send(f'load-symbols {sym}')
send('stack trace-only')
send(f'watch/w {addr}')
HIT = re.compile(r'Hit watchpoint \d+ at (0x[0-9A-Fa-f]+): \(new value = (0x[0-9A-Fa-f]+), old value = (0x[0-9A-Fa-f]+)\)')
os.write(fd, b'c\n')
t_end = time.monotonic() + 300
hit = None
out = ''
while alive and time.monotonic() < t_end and hit is None:
    key(True)
    out = pump(0.1)
    key(False)
    out += pump(0.4)
    m = HIT.search(out)
    if m:
        hit = dict(addr=m.group(1), new=m.group(2), old=m.group(3), status=out[m.start():][:900])
if hit is not None:
    hit['bt'] = send('bt', 5.0)
    hit['regs'] = send('i', 3.0)
    hit['dumps'] = {d: send(f'r/4 {d}', 2.0) for d in dumps}
result = dict(alive=alive, hit=hit)
log.write('\n## RESULT ' + json.dumps(result) + '\n')
log.close()
print(json.dumps(result, indent=1))
try:
    os.kill(pid, 15)
except OSError:
    pass
xvfb.terminate()
