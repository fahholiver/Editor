"""Scene-by-scene score: music written to fit each scene's mood, plus the SFX, from one cue sheet.

    python3 score.py <score.json> <voice48.wav>       # -> music.wav + sfx.wav (48 kHz stereo) next to the voice

score.json (times in seconds on the voice timeline):
{
  "key": "D",                       # tonic of the whole video (C, C#, D, ... B); moods choose major/minor
  "bpm": 96,
  "music": [                        # one cue per scene (or group of scenes with the same feeling)
    {"at": 0.0,  "to": 6.2,  "mood": "mystery"},
    {"at": 6.2,  "to": 21.0, "mood": "calm", "level": 0.8},
    {"at": 21.0, "to": 29.5, "mood": "tense", "build": true},
    {"at": 29.5, "to": 31.0, "mood": "silence"},          # a hard silence before the key line
    {"at": 31.0, "to": 62.0, "mood": "hopeful"}
  ],
  "sfx": [["paper", 0.1], ["slam", 3.68, {"amp": 0.6}, 0.2], ["whoosh", 6.3]]   # [name, time, {args}, pan]
}
Moods: calm, curious, mystery, tense, danger, sad, hopeful, storybook (3/4 waltz), mischief, triumph, silence.
`level` 0..1 scales one cue; `build` makes it grow from soft to full over the cue. Cues cross-fade (0.4 s);
a cue that starts right after "silence" enters on its first beat. The levels against the voice are set by
mix.py afterwards (voice first: music about 24 dB under the voice, effects about 18 dB under), so write the
cues for musical balance only.
SFX names: whoosh pop ting thud slam click scribble squeak paper hiss crack sting shimmer rumble flap wind step
hum twang rain lapping heartbeat tick page.
"""
import json
import os
import sys

import numpy as np
from dsp import SR, TAU, ns, tt, rng, lp, hp, bp, pan, place, fades, write_wav, read_wav, smooth_noise
import instruments as I

R = rng(7)
m2f = I.m2f
KEYS = {'C': 48, 'C#': 49, 'DB': 49, 'D': 50, 'D#': 51, 'EB': 51, 'E': 52, 'F': 53, 'F#': 54, 'GB': 54, 'G': 43,
        'G#': 44, 'AB': 44, 'A': 45, 'A#': 46, 'BB': 46, 'B': 47}
MAJ = [[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]]        # I V vi IV
MIN = [[0, 3, 7], [-4, 0, 3], [-9, -5, 0], [-2, 2, 5]]         # i VI iv VII
SAD = [[0, 3, 7], [-7, -4, 0], [-4, 0, 3], [-5, -1, 2]]        # i iv VI V
SCALE_MAJ = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16]
SCALE_MIN = [0, 2, 3, 5, 7, 8, 10, 12, 14, 15]


def _melody(scale, n, seed):
    r = rng(seed)
    i, out = 4, []
    for _ in range(n):
        i = int(np.clip(i + r.choice([-2, -1, -1, 1, 1, 2, 0]), 0, len(scale) - 1))
        out.append(scale[i])
    return out


def cue(mood, d, root, bpm, build=False, seed=1):
    """music for one scene, d seconds long, starting at 0"""
    B = 60.0 / bpm
    buf = np.zeros((2, ns(d) + ns(3)))
    r = rng(seed)
    t = 0.0
    bar = 0
    if mood == 'silence':
        return buf[:, :ns(d)]
    prog = {'calm': MAJ, 'hopeful': MAJ, 'triumph': MAJ, 'storybook': MAJ, 'curious': MIN, 'mischief': MIN,
            'mystery': MIN, 'tense': MIN, 'danger': MIN, 'sad': SAD}[mood]
    scale = SCALE_MAJ if prog is MAJ else SCALE_MIN
    beats = 3 if mood == 'storybook' else 4
    while t < d - 0.05:
        ch = [root + x for x in prog[bar % 4]]
        g = (0.45 + 0.55 * t / max(d, 1e-3)) if build else 1.0
        L = beats * B
        if mood in ('calm', 'hopeful', 'triumph', 'sad', 'mystery', 'tense', 'danger'):   # bed under everything
            warm = {'calm': 900, 'hopeful': 1100, 'triumph': 1300, 'sad': 700, 'mystery': 600, 'tense': 450,
                    'danger': 380}[mood]
            place(buf, I.pad([m2f(x) for x in ch], L + 0.1, 0.14 * g, r, att=0.5, rel=0.6, warm=warm), t)
        if mood == 'calm':
            place(buf, pan(I.pluck(m2f(ch[0] - 12), 0.45 * g, r, dur=1.6, bright=0.3), 0), t)
            for k in (1, 3):
                place(buf, pan(I.pluck(m2f(ch[k % 3] + 12), 0.22 * g, r, dur=0.9, bright=0.4), 0.3 - 0.2 * k), t + k * B)
        elif mood == 'curious':
            for k in range(8):
                n = ch[[0, 2, 1, 2, 0, 2, 1, 2][k]] + 12
                place(buf, pan(I.pluck(m2f(n), 0.38 * g, r, dur=0.45, bright=0.6), -0.3 if k % 2 else 0.3), t + k * B / 2)
            place(buf, pan(I.pluck(m2f(ch[0] - 12), 0.5 * g, r, dur=1.2, bright=0.3), 0), t)
            if bar % 2:
                for j, m in enumerate(_melody(scale, 3, seed + bar)):
                    place(buf, pan(I.glock(m2f(root + 24 + m), 0.2 * g, r, dur=1.0), 0.35), t + 2 * B + j * B / 2)
        elif mood == 'mystery':
            for k, m in enumerate(_melody(scale, 4, seed + bar)):
                place(buf, pan(I.vibes(m2f(root + 12 + m), 0.22 * g, r, dur=1.6), -0.4 + 0.25 * k), t + k * B)
        elif mood == 'tense':
            for k in range(8):
                place(buf, pan(I.pluck(m2f(root - 12 + (1 if bar % 4 == 3 and k > 5 else 0)),
                                       (0.3 + 0.2 * g) * (0.8 + 0.2 * (k % 2 == 0)), r, dur=0.25, bright=0.35), -0.1), t + k * B / 2)
        elif mood == 'danger':
            for k in range(beats):     # heartbeat
                place(buf, pan(I.timpani(m2f(root - 12), 0.45 * g, r, dur=0.9), 0), t + k * B)
                place(buf, pan(I.timpani(m2f(root - 12), 0.25 * g, r, dur=0.7), 0), t + k * B + 0.22)
            place(buf, I.pad([m2f(root + 13), m2f(root + 12)], L, 0.05 * g, r, att=0.8, rel=0.5, warm=2000), t)
        elif mood == 'sad':
            for k, m in enumerate(_melody(scale, 2, seed + bar)):
                place(buf, pan(I.musicbox(m2f(root + 24 + m), 0.28 * g, r, dur=2.0), 0.2), t + 2 * k * B)
        elif mood in ('hopeful', 'triumph'):
            for k in range(8):
                place(buf, pan(I.pluck(m2f(ch[k % 3] + 12), 0.3 * g, r, dur=0.5, bright=0.5), -0.25 if k % 2 else 0.25), t + k * B / 2)
            place(buf, pan(I.pluck(m2f(ch[0] - 12), 0.5 * g, r, dur=1.6, bright=0.3), 0), t)
            for j, m in enumerate(_melody(scale, 4, seed + bar)):
                place(buf, pan(I.glock(m2f(root + 24 + m), 0.22 * g, r, dur=1.2), 0.3), t + j * B)
            if mood == 'triumph' and bar % 2 == 0:
                place(buf, pan(I.timpani(m2f(root - 12), 0.4 * g, r, dur=1.6), 0), t)
        elif mood == 'storybook':   # 3/4 waltz: bass on 1, chord plucks on 2 and 3, music-box melody
            place(buf, pan(I.pluck(m2f(ch[0] - 12), 0.5 * g, r, dur=1.0, bright=0.3), 0), t)
            for k in (1, 2):
                for x in ch:
                    place(buf, pan(I.pluck(m2f(x + 12), 0.14 * g, r, dur=0.35, bright=0.5), 0.15 * k - 0.2), t + k * B)
            for j, m in enumerate(_melody(scale, 3, seed + bar)):
                place(buf, pan(I.musicbox(m2f(root + 24 + m), 0.3 * g, r, dur=1.4), 0.3), t + j * B)
        elif mood == 'mischief':    # sneaky staccato walking bass + vibes answers
            walk = [0, 3, 5, 6, 7, 5, 3, 2]
            for k in range(8):
                place(buf, pan(I.pluck(m2f(root - 12 + walk[k]), 0.42 * g, r, dur=0.18, bright=0.45), -0.15), t + k * B / 2)
            if bar % 2:
                place(buf, pan(I.vibes(m2f(root + 15), 0.25 * g, r, dur=0.8), 0.4), t + 3 * B)
        t += L
        bar += 1
    return buf


# ------------------------------------------------------------ SFX (from the kits' cue sheets)
def env_exp(n, k): return np.exp(-np.arange(n) / SR * k)
def noise(d): return R.standard_normal(ns(d))


def whoosh(d=0.45, lo=300, hi=2500, amp=0.6):
    x = noise(d); n = len(x); out = np.zeros(n); sg = 256
    for i in range(0, n, sg):
        p = i / n; fc = lo + (hi - lo) * np.sin(np.pi * p)
        out[i:i + sg] = bp(x[max(0, i - 512):i + sg], max(60, fc * 0.6), fc * 1.4)[-len(out[i:i + sg]):]
    return amp * out * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
def pop(f0=700, f1=180, d=0.12, amp=0.6):
    t = tt(d); f = f1 + (f0 - f1) * np.exp(-t * 40)
    return amp * np.sin(TAU * np.cumsum(f) / SR) * env_exp(len(t), 30)
def ting(f=2093, amp=0.45): return amp * I.glock(f, 0.8, R, dur=1.2)
def thud(amp=0.8, f=80, d=0.35):
    t = tt(d); return amp * (np.sin(TAU * f * t) * env_exp(len(t), 14) + 0.6 * lp(noise(d), 400) * env_exp(len(t), 25))
def slam(amp=0.9):
    x = thud(amp, 70); x[:ns(0.25)] += 0.5 * amp * bp(noise(0.25), 200, 1200) * env_exp(ns(0.25), 20); return x
def click(amp=0.35, f=None):
    t = tt(0.03); f = f or R.uniform(2500, 4500); return amp * np.sin(TAU * f * t) * env_exp(len(t), 160)
def tick(amp=0.3): return click(amp, 3200)
def scribble(d=0.3, amp=0.35):
    x = bp(noise(d), 1800, 6500); am = 0.5 + 0.5 * np.abs(np.sin(np.linspace(0, d * 38, len(x)) + R.uniform(0, 3)))
    return amp * fades(x * am * (0.7 + 0.3 * smooth_noise(len(x), R, 30)), 0.01, 0.05)
def squeak(d=0.35, amp=0.3):
    t = tt(d); f = 2600 + 500 * t / d
    tone = np.sin(TAU * np.cumsum(f) / SR) * 0.25 + bp(noise(d), 2500, 6000)
    return amp * fades(tone * (0.6 + 0.4 * np.sin(TAU * 31 * t)), 0.02, 0.08)
def paper(d=0.4, amp=0.4):
    x = bp(noise(d), 500, 5000) * (0.4 + 0.6 * smooth_noise(ns(d), R, 25)); return amp * x * np.sin(np.pi * np.linspace(0, 1, len(x))) ** 0.8
def hiss(d=1.0, amp=0.25, rise=True):
    x = bp(noise(d), 1500, 7000); e = np.linspace(0.2, 1, len(x)) if rise else np.linspace(1, 0.1, len(x))
    return amp * fades(x * e, 0.04, 0.1)
def crack(amp=0.8):
    x = hp(noise(0.25), 1500) * (R.random(ns(0.25)) > 0.55) * env_exp(ns(0.25), 18)
    return amp * x + thud(0.6 * amp, 60, 0.25)[:ns(0.25)]
def sting(amp=0.8):
    t = tt(2.4); return amp * (np.sin(TAU * 41 * t) + 0.5 * np.sin(TAU * 61.7 * t) + 0.3 * lp(noise(2.4), 200)) * env_exp(len(t), 2.0)
def shimmer(amp=0.35, up=True):
    out = np.zeros(ns(1.4)); seq = (84, 88, 91, 96, 100) if up else (100, 96, 91, 88, 84)
    for i, m in enumerate(seq):
        b = I.glock(m2f(m), 0.5, R, dur=0.9); s = ns(i * 0.06); out[s:s + len(b)] += b[:len(out) - s]
    return amp * out
def rumble(amp=0.4, d=2.4):
    t = tt(d); return amp * lp(noise(d), 160) * (0.4 + 0.6 * np.sin(np.pi * t / d)) * (0.6 + 0.4 * smooth_noise(ns(d), R, 3))
def flap(amp=0.35, d=0.18):
    x = bp(noise(d), 600, 4000); return amp * x * np.abs(np.sin(np.linspace(0, 6 * np.pi, len(x)))) * np.sin(np.pi * np.linspace(0, 1, len(x)))
def wind(d=3.0, amp=0.25):
    x = lp(noise(d), 600) * (0.5 + 0.5 * smooth_noise(ns(d), R, 0.8)); return amp * fades(x, 0.8, 0.8)
def step(amp=0.25, f=180, wood=False):
    t = tt(0.12); x = lp(noise(0.12), 1800 if wood else 900) * env_exp(len(t), 45)
    return amp * (x + (0.7 if wood else 0.3) * np.sin(TAU * f * t) * env_exp(len(t), 40))
def hum(d=1.0, f0=300, f1=600, amp=0.25):
    t = tt(d); f = f0 + (f1 - f0) * (t / d); y = sum(np.sin(TAU * np.cumsum(f * k) / SR) / k for k in (1, 2, 3))
    return amp * fades(y, 0.05, 0.03)
def twang(amp=0.6):
    t = tt(0.9); f = 520 * (1 - 0.35 * (1 - np.exp(-t * 8)))
    return amp * (np.sin(TAU * np.cumsum(f) / SR) * env_exp(len(t), 5) + 0.5 * hp(noise(0.9), 3000) * env_exp(len(t), 60))
def rain(d=4.0, amp=0.2):
    x = bp(noise(d), 1200, 7500) * (0.7 + 0.3 * smooth_noise(ns(d), R, 6))
    drops = (R.random(ns(d)) > 0.9993) * R.uniform(0.5, 1.5, ns(d)); drops = np.convolve(drops, np.exp(-np.arange(200) / 30), 'same')
    return amp * fades(x + 2.5 * hp(drops, 2000), 1.2, 1.2)
def lapping(d=4.0, amp=0.18):
    x = lp(noise(d), 500) * (0.35 + 0.65 * (0.5 + 0.5 * np.sin(TAU * 0.35 * tt(d)))) ** 2
    return amp * fades(x, 1.5, 1.0)
def heartbeat(amp=0.6, n=4, bpm=70):
    out = np.zeros(ns(n * 60 / bpm + 0.5))
    for k in range(n):
        for dt, a in ((0, 1.0), (0.22, 0.6)):
            th = thud(amp * a, 55, 0.3); s = ns(k * 60 / bpm + dt); out[s:s + len(th)] += th[:len(out) - s]
    return out


def page(amp=0.4):   # page turn: a paper slide with a soft whoosh
    a = paper(0.55, amp); b = whoosh(0.55, 600, 3000, 0.5 * amp)
    return a[:len(b)] + b[:len(a)]


SFX = {k: v for k, v in globals().items() if k in (
    'whoosh pop ting thud slam click tick scribble squeak paper page hiss crack sting shimmer rumble flap wind '
    'step hum twang rain lapping heartbeat').split()}


def build(spec, N):
    key = KEYS[str(spec.get('key', 'D')).upper()]
    bpm = float(spec.get('bpm', 96))
    mus = np.zeros((2, N))
    cues = sorted(spec.get('music', []), key=lambda c: c['at'])
    for i, c in enumerate(cues):
        a, b = float(c['at']), min(float(c['to']), N / SR)
        if b <= a or c['mood'] == 'silence':
            continue
        after_silence = i > 0 and cues[i - 1]['mood'] == 'silence'
        x = cue(c['mood'], b - a, key + int(c.get('transpose', 0)), float(c.get('bpm', bpm)), c.get('build', False),
                seed=11 + i) * float(c.get('level', 1.0))
        x = x[:, :ns(b - a) + ns(0.4)]
        fin = 0.02 if after_silence else 0.4
        nxt_silent = i + 1 < len(cues) and cues[i + 1]['mood'] == 'silence'
        fout = 0.04 if nxt_silent else 0.4
        n = x.shape[1]
        e = np.ones(n)
        e[:ns(fin)] = np.linspace(0, 1, ns(fin))
        k = min(ns(b - a), n)
        if nxt_silent or i + 1 == len(cues):          # stop on time (hard before a silence)
            j = max(0, k - ns(fout))
            e[j:k] *= np.linspace(1, 0, k - j)
            e[k:] = 0
        else:                                          # cross-fade: the tail overlaps the next cue's fade-in
            m = min(n, k + ns(0.4))
            e[k:m] *= np.linspace(1, 0, m - k)
            e[m:] = 0
        place(mus, x * e[None, :], a)
    end = ns(min(N / SR, max([float(c['to']) for c in cues] + [0])))
    mus[:, end:] = 0
    tail = ns(1.2)
    if end > tail:
        mus[:, end - tail:end] *= np.linspace(1, 0, tail) ** 1.5
    sfx = np.zeros((2, N))
    for ent in spec.get('sfx', []):
        name, t = ent[0], float(ent[1])
        kw = ent[2] if len(ent) > 2 and isinstance(ent[2], dict) else {}
        p = float(ent[3]) if len(ent) > 3 else 0.0
        x = SFX[name](**kw)
        x = x[0] if x.ndim == 2 else x
        place(sfx, pan(x, p), t)
    for x in (mus, sfx):   # stems are levelled against the voice by mix.py; here only keep them unclipped
        pk = float(np.abs(x).max())
        if pk > 0.9:
            x *= 0.9 / pk
    return mus, sfx


def main():
    spec = json.load(open(sys.argv[1], encoding='utf-8'))
    v, _ = read_wav(sys.argv[2])
    mus, sfx = build(spec, v.shape[1])
    d = os.path.dirname(os.path.abspath(sys.argv[2]))
    write_wav(os.path.join(d, 'music.wav'), mus)
    write_wav(os.path.join(d, 'sfx.wav'), sfx)
    print('score: %d music cues (%s), %d sfx -> music.wav, sfx.wav' % (
        len(spec.get('music', [])), ', '.join(sorted({c['mood'] for c in spec.get('music', [])})), len(spec.get('sfx', []))))


if __name__ == '__main__':
    main()
