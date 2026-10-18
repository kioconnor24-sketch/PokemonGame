"""Scratch debugging only. Phase 1: from a savestate, break at BP (pressing A in
real time), then frame-advance with a fixed A schedule, saving a savestate every
frame into alternating slots 2/3, until the emulator dies. Records the frame
number and which slot holds the state from the frame before the crash."""
import os, pty, select, subprocess, sys, time, json
rom, state, logp, sym, bp = sys.argv[1:6]
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
def send(c, t=2.0, until=b'\n> '):
    log.write(f'\n##> {c}\n')
    os.write(fd, (c + '\n').encode())
    return pump(t, until)
pump(3)
window = subprocess.run(['xdotool', 'search', '--name', 'mGBA'], env=env, capture_output=True, text=True).stdout.split()[0]
def key(down):
    subprocess.run(['xdotool', 'keydown' if down else 'keyup', '--window', window, 'x'], env=env)
    time.sleep(0.05)
send(f'load-symbols {sym}')
send(f'break {bp}')
os.write(fd, b'c\n')
hit = False
t_end = time.monotonic() + 120
while alive and time.monotonic() < t_end and not hit:
    key(True); out = pump(0.1); key(False); out += pump(0.4)
    hit = 'Hit breakpoint' in out
if not hit:
    log.write('\n## never hit\n'); sys.exit(1)
send('delete 1')
# Check that keys reach the core while paused: KEYINPUT bit 0 is A (0 = pressed).
key(True); k1 = send('r/2 0x04000130'); key(False); k2 = send('r/2 0x04000130')
log.write(f'\n## keyinput down/up: {k1.strip()[-30:]!r} / {k2.strip()[-30:]!r}\n')
frames = 0
schedule = []
while alive and frames < 3000:
    down = (frames % 8) < 3
    key(down)
    out = send('frame', 5.0)
    if not alive:
        break
    frames += 1
    schedule.append(down)
    slot = 2 + frames % 2
    send(f'save {slot}', 5.0)
    if not alive:
        break
key(False)
result = dict(frames_completed=frames, last_saved_slot=2 + frames % 2 if frames else None,
              slot_before_crash=2 + (frames - 1) % 2 if frames > 1 else None, alive=alive,
              schedule='A down for frames where (n % 8) < 3, counted from the HealPlayerParty break')
log.write('\n## RESULT ' + json.dumps(result) + '\n')
log.close()
print(json.dumps(result))
try:
    os.kill(pid, 15)
except OSError:
    pass
xvfb.terminate()
