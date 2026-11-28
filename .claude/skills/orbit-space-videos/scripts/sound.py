"""Score + sound design from the scene, mixed under the voice. Everything is synthesised (no samples, no licences).
usage: python3 scripts/sound.py scene.json vo.wav mix.wav [--mood dread|wonder|tense] [--music your_track.mp3]
Cuts get a whoosh, stamps/big numbers a low hit, chapters a riser, lightning a crack, counters and timers soft ticks.
With --music, your own track replaces the synthesised pad (it is looped, ducked under the voice)."""
import sys, json, os, subprocess, argparse, numpy as np
from scipy.signal import butter, sosfilt
HERE = os.path.dirname(os.path.abspath(__file__)); os.environ['PATH'] = os.path.join(HERE, '..', 'bin') + os.pathsep + os.environ['PATH']
ap = argparse.ArgumentParser(); ap.add_argument('scene'); ap.add_argument('vo'); ap.add_argument('out'); ap.add_argument('--mood', default='dread'); ap.add_argument('--music'); ap.add_argument('--music-gain', type=float, default=1.0); a = ap.parse_args()
S = json.load(open(a.scene)); D = S['shots'][-1]['end']; SR = 48000; N = int(D * SR); t = np.arange(N) / SR; R = np.random.default_rng(7)
lp = lambda x, f: sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
bp = lambda x, f1, f2: sosfilt(butter(2, [f1, f2], 'band', fs=SR, output='sos'), x)
def load(p):
    pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.float32).astype(float)
def put(buf, at, sig):
    i = int(at * SR); L = min(len(sig), N - i)
    if i < 0 or L <= 0: return
    buf[i:i + L] += sig[:L]
fx = np.zeros(N)
whoosh = lambda d=.7: bp(R.standard_normal(int(d * SR)), 250, 3200) * np.sin(np.linspace(0, np.pi, int(d * SR))) ** 2
hit = lambda: lp(R.standard_normal(int(1.4 * SR)), 140) * np.exp(-np.arange(int(1.4 * SR)) / SR * 3.5) * 3 + np.sin(2 * np.pi * 46 * np.arange(int(1.4 * SR)) / SR) * np.exp(-np.arange(int(1.4 * SR)) / SR * 5) * .8
tick = lambda: np.sin(2 * np.pi * 2400 * np.arange(500) / SR) * np.exp(-np.arange(500) / 70)
riser = lambda d=1.0: bp(R.standard_normal(int(d * SR)), 500, 6000) * np.linspace(0, 1, int(d * SR)) ** 2
crack = lambda: bp(R.standard_normal(int(2.2 * SR)), 900, 7000) * np.exp(-np.arange(int(2.2 * SR)) / SR * 9) + lp(R.standard_normal(int(2.2 * SR)), 120) * np.exp(-np.arange(int(2.2 * SR)) / SR * 1.8) * 3
for i, sh in enumerate(S['shots']):
    if i: put(fx, sh['start'] - .22, whoosh() * .22)
    for e in sh['els']:
        at = sh['start'] + e.get('t0', 0); ty = e['type']
        if ty in ('stamp', 'big'): put(fx, at, hit() * .32)
        elif ty == 'chapter': put(fx, at - 1.0, riser() * .12); put(fx, at, hit() * .25)
        elif ty in ('pill', 'tag', 'caption') and ty != 'caption': put(fx, at, tick() * .25)
        elif ty in ('counter', 'timer', 'gauge', 'thermo'):
            d = e.get('t1', 1.5)
            for k in np.arange(0, d, .09): put(fx, at + k, tick() * .07)
        elif ty == 'descent':
            put(fx, sh['start'], (bp(R.standard_normal(int((sh['end'] - sh['start']) * SR)), 120, 1400) * .07))
            for b in e.get('bolts', []): put(fx, sh['start'] + e.get('t0', 0) + b, crack() * .3)
        elif ty == 'evidence': put(fx, at, whoosh(.5) * .12)
        elif ty == 'radar':
            for k in np.arange(0, sh['end'] - at, TAU := 2 * np.pi / 1.6): put(fx, at + k, np.sin(2 * np.pi * 1100 * np.arange(6000) / SR) * np.exp(-np.arange(6000) / 1500) * .05)
vo = load(a.vo); vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
if a.music:
    m = load(a.music); m = np.tile(m, int(np.ceil(N / len(m))))[:N]; bed = m * .35
else:
    root = {'dread': 55.0, 'tense': 49.0, 'wonder': 65.4}[a.mood]
    chord = [1, 1.5, 2, 2.4 if a.mood == 'wonder' else 2.378, 3]
    bed = sum((.5 / (i + 1)) * np.sin(2 * np.pi * root * r * t + i) * (1 + .3 * np.sin(2 * np.pi * (.05 + i * .03) * t)) for i, r in enumerate(chord)) * .1
    shimmer = sum(np.sin(2 * np.pi * root * 8 * r * t) for r in (1, 1.5)) * .006 * (1 + np.sin(2 * np.pi * .07 * t))
    pulse = np.zeros(N)
    for k in np.arange(0, D, 60 / 70): put(pulse, k, np.sin(2 * np.pi * 50 * np.arange(int(.4 * SR)) / SR) * np.exp(-np.arange(int(.4 * SR)) / SR * 11))
    bed = bed + shimmer + pulse * .09 * np.clip((t - 4) / 6, 0, 1)
env = lp(np.abs(vo), 5); duck = 1 - .8 * np.clip(env / (np.percentile(env, 95) + 1e-9), 0, 1)
mix = vo * 1.0 + bed * duck * .4 * a.music_gain + fx * .9   # music sits about 8 dB lower than v2 and dips harder under speech
mix *= np.minimum(1, np.minimum(t / .3, (D - t) / .8).clip(0, 1))
mix = np.tanh(mix * 1.05)
tmp = a.out + '.tmp.wav'
import wave; w = wave.open(tmp, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix / max(1e-9, np.abs(mix).max()) * .9, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', tmp, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ac', '2', '-ar', '48000', a.out], check=True); os.remove(tmp); print('wrote', a.out)
