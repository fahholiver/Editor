#!/usr/bin/env python3
"""Level-locked mix:  python3 mix.py voice.mp3 music.wav sfx.wav [--music-db -6] [--sfx-db -6] -> mix_raw.wav
Music gated RMS = voice gated RMS + music-db (default -6 dB = 50 %). SFX at sfx-db, peaks capped at 0.7 x voice peak.
No ducking or compression; the voice is untouched."""
import argparse, subprocess, wave
import numpy as np
SR = 48000

def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def grms(x, gate=-50):
    """RMS over 50 ms blocks louder than the gate (silence does not count)"""
    b = int(0.05 * SR); n = len(x) // b
    if n == 0: return 1e-9
    r = np.sqrt((x[:n * b].reshape(n, b) ** 2).mean(1))
    keep = r[r > 10 ** (gate / 20)]
    return float(np.sqrt((keep ** 2).mean())) if len(keep) else 1e-9

db = lambda x: 20 * np.log10(max(x, 1e-9))
ap = argparse.ArgumentParser(); ap.add_argument('voice'); ap.add_argument('music'); ap.add_argument('sfx')
ap.add_argument('--music-db', type=float, default=-6); ap.add_argument('--sfx-db', type=float, default=-6)
ap.add_argument('--out', default='mix_raw.wav'); a = ap.parse_args()
v = load(a.voice); n = len(v)
fit = lambda x: np.pad(x, (0, max(0, n - len(x))))[:n]
m, s = fit(load(a.music)), fit(load(a.sfx))
gv = grms(v)
if grms(m) > 1e-6: m *= gv * 10 ** (a.music_db / 20) / grms(m)
if grms(s) > 1e-6:
    s *= gv * 10 ** (a.sfx_db / 20) / grms(s)
    cap = 0.7 * np.abs(v).max()
    if np.abs(s).max() > cap: s *= cap / np.abs(s).max()
mix = v + m + s
pk = np.abs(mix).max()
if pk > 0.99: mix *= 0.99 / pk          # one linear gain only
f = int(0.04 * SR); mix[-f:] *= np.linspace(1, 0, f)
with wave.open(a.out, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('voice %.1f dB | music %.1f dB vs voice | sfx %.1f dB vs voice (peak %.2f x voice) -> %s' % (
    db(gv), db(grms(m)) - db(gv), db(grms(s)) - db(gv), np.abs(s).max() / (np.abs(v).max() + 1e-9), a.out))
