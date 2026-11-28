"""Original score + sound effects synthesised in numpy, mixed under the voiceover with ducking.
Moods: epic (history: strings, choir pad, war drums, horn swells), noir (crime), heist, dark, mystery.
A real track (any MP3/WAV in the project's music/ folder) replaces the generated score; it is looped, levelled and ducked the same way. Music cuts out under black cards."""
import os, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, lfilter

SR = 48000
rng = np.random.default_rng(5)


def lp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), 'low'); return lfilter(b, a, x, axis=0)
def hp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), 'high'); return lfilter(b, a, x, axis=0)
def bp(x, f1, f2): b, a = butter(2, [f1 / (SR / 2), f2 / (SR / 2)], 'band'); return lfilter(b, a, x, axis=0)
hz = lambda n: 440 * 2 ** ((n - 69) / 12)


def place(buf, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0: return
    if x.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414; x = np.stack([x * l, x * r], 1)
    j = min(i + len(x), len(buf)); buf[max(i, 0):j] += x[max(0, -i):j - i] * gain


def env(n, a=.005, d=8.0):
    t = np.arange(n) / SR; return (1 - np.exp(-t / max(a, 1e-4))) * np.exp(-t * d)


# ---------------------------------------------------------------- instruments
def pluck(f, dur=.3, amp=.4, decay=10):
    n = int(dur * SR); t = np.arange(n) / SR
    return amp * env(n, .002, decay) * (np.sin(2 * np.pi * f * t) + .5 * np.sin(4 * np.pi * f * t) + .2 * np.sin(6 * np.pi * f * t))
def bass(f, dur=.3, amp=.5):
    n = int(dur * SR); t = np.arange(n) / SR
    return amp * env(n, .003, 7) * lp(np.sin(2 * np.pi * f * t) + .5 * np.sin(4 * np.pi * f * t) + .3 * np.sign(np.sin(2 * np.pi * f * t)) * .3, 700)
def pad(freqs, dur, amp=.05):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for f in freqs:
        for d in (-.6, 0, .7): out += np.sin(2 * np.pi * (f + d) * t + rng.uniform(0, 6)) + .3 * np.sin(4 * np.pi * (f + d) * t)
    e = np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.2)
    return amp * lp(out, 2200) * e / len(freqs)
def piano(f, dur=1.6, amp=.18):
    n = int(dur * SR); t = np.arange(n) / SR
    return amp * env(n, .002, 2.6) * (np.sin(2 * np.pi * f * t) + .45 * np.sin(4 * np.pi * f * t) * np.exp(-t * 4) + .2 * np.sin(6 * np.pi * f * t) * np.exp(-t * 7))
def hat(amp=.04): n = int(.05 * SR); return amp * hp(rng.standard_normal(n), 7000) * np.exp(-np.arange(n) / SR * 90)
def kick(amp=.35):
    n = int(.22 * SR); t = np.arange(n) / SR; return amp * np.sin(2 * np.pi * (46 + 70 * np.exp(-t * 34)) * t) * np.exp(-t * 15)
def heart(amp=.4): return np.concatenate([kick(amp), np.zeros(int(.12 * SR)), kick(amp * .7)])
def musicbox(f, amp=.12):
    n = int(1.2 * SR); t = np.arange(n) / SR; return amp * env(n, .001, 4) * (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 9))


def score(N, mood, cards):
    m = np.zeros((N + SR * 4, 2)); end = N / SR
    if mood == 'heist':     # D minor, 96 bpm: pulsing bass eighths, ticking hats, plucked motif, low pad
        beat = 60 / 96; bar = 4 * beat
        prog = [(38, [62, 65, 69]), (34, [58, 62, 65]), (36, [60, 64, 67]), (33, [57, 61, 64])]
        motif = [[74, None, 72, None, 69, None, None, 70], [None, 69, None, 67, None, 65, 67, None], [72, None, 70, 69, None, None, 67, None], [None, 64, None, 65, 67, None, 69, None]]
        t = 0.0; b = 0
        while t < end:
            root, ch = prog[b % 4]
            place(m, pad([hz(n) for n in ch], bar * 1.05, .045), t, 1, 0)
            for i in range(8): place(m, bass(hz(root), beat * .45, .42 if i % 2 == 0 else .3), t + i * beat / 2)
            for i in range(16): place(m, hat(.035 if i % 4 else .05), t + i * beat / 4, 1, .35)
            for i in (0, 2): place(m, kick(.25), t + i * beat)
            if b % 8 >= 4:
                for i, n in enumerate(motif[b % 4]):
                    if n: place(m, pluck(hz(n), .28, .14), t + i * beat / 2, 1, -.25)
            t += bar; b += 1
    elif mood == 'dark':    # A minor drone, slow piano, heartbeat
        t = 0.0; notes = [69, 72, 71, 64, 69, 76, 74, 71]; k = 0
        while t < end:
            place(m, pad([hz(45), hz(52), hz(57)], 8.4, .07), t)
            for i in range(4): place(m, piano(hz(notes[k % 8]), 2.2, .13), t + i * 2.0 + .3, 1, (-.2, .2)[i % 2]); k += 1
            for i in range(4): place(m, heart(.18), t + i * 2.0)
            t += 8.0
    else:                   # mystery: music box over a soft pad
        t = 0.0; mel = [76, 79, 83, 81, 79, 76, 74, 76, 71, 72, 74, 76]; k = 0
        while t < end:
            place(m, pad([hz(52), hz(59), hz(64)], 6.4, .05), t)
            for i in range(8): place(m, musicbox(hz(mel[k % 12])), t + i * .8, 1, (-.3, .3)[i % 2]); k += 1
            t += 6.4
    m = m[:N]; tt = np.arange(N) / SR; g = np.ones(N)
    for (a, b_) in cards: g[(tt > a - .05) & (tt < b_)] = 0.0
    g = lp(g, 8, 1); m *= g[:, None]; m *= np.minimum(1, tt / 1.5)[:, None]
    m *= np.clip((end - tt) / 2.0, 0, 1)[:, None]
    return m



def saw(f, n, phase=0.0):
    t = np.arange(n) / SR; x = (f * t + phase) % 1.0; return 2 * x - 1
def strings(freqs, dur, amp=.06, cutoff=900, attack=1.6):
    """Dark bowed-string pad: detuned saws, low-passed, slow attack and release."""
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for f in freqs:
        for d in (-.18, 0, .21): out += saw(f * 2 ** (d / 12), n, rng.uniform(0, 1))
    out = lp(out / (3 * len(freqs)), cutoff, 2)
    e = np.minimum(1, t / attack) * np.minimum(1, (dur - t) / 1.4); trem = 1 + .06 * np.sin(2 * np.pi * 4.6 * t)
    return amp * out * e * trem
def bowed(f, dur, amp=.08):
    n = int(dur * SR); t = np.arange(n) / SR
    x = lp(saw(f, n) + .5 * saw(f * 2.003, n), 520, 2)
    return amp * x * np.minimum(1, t / .035) * np.exp(-t * 3.2) * np.minimum(1, (dur - t) / .05)
def sub(f, dur, amp=.2):
    n = int(dur * SR); t = np.arange(n) / SR
    return amp * np.sin(2 * np.pi * f * t) * np.minimum(1, t / 2.5) * np.minimum(1, (dur - t) / 2.5)
def glass(f, dur=3.5, amp=.035):
    n = int(dur * SR); t = np.arange(n) / SR
    return amp * (np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3)) * np.minimum(1, t / .4) * np.exp(-t * .9)
def reverb(x, secs=2.6, wet=.35, seed=3):
    from scipy.signal import fftconvolve
    r = np.random.default_rng(seed); n = int(secs * SR); t = np.arange(n) / SR
    ir = r.standard_normal((n, 2)) * np.exp(-t * 6.9 / secs)[:, None]; ir = lp(ir, 4200); ir /= np.sqrt((ir ** 2).sum(0))
    if x.ndim == 1: x = np.stack([x, x], 1)
    y = np.stack([fftconvolve(x[:, i], ir[:, i])[:len(x)] for i in range(2)], 1)
    return x * (1 - wet) + y * wet * 2.2
def riser(dur=2.2, amp=.12):
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.standard_normal(n); out = np.zeros(n); seg = 800
    for i in range(0, n, seg):
        u = i / n; y = bp(x[i:i + seg], 200 + 2600 * u ** 2, 400 + 6000 * u ** 2); out[i:i + len(y)] = y
    return amp * out * (t / dur) ** 2.2
def impact(amp=.9):
    n = int(3.2 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (34 + 60 * np.exp(-t * 18)) * t) * np.exp(-t * 1.6)
    low = lp(rng.standard_normal(n), 140) * np.exp(-t * 2.2) * 2.0
    return amp * (body + low)


def noir(N, cues, cards):
    """Dark cinematic score: sub drone, low strings over a slow minor progression, a pulsing low ostinato,
    glassy high notes, clock ticks for the 'heist' stretch, risers into the big hits."""
    end = N / SR; m = np.zeros((N + SR * 6, 2))
    prog = [[38, 50, 53, 57], [34, 46, 50, 53], [31, 43, 46, 50], [33, 45, 49, 52]]     # Dm  Bb  Gm  A
    bar = 8.0; t = 0.0; b = 0
    while t < end:
        ch = prog[b % 4]
        place(m, strings([hz(n) for n in ch[1:]], bar + 1.6, .085, 760), t, 1, 0)
        place(m, sub(hz(ch[0]), bar + 1.6, .22), t)
        t += bar; b += 1
    pulse = cues.get('pulse', [(0, end)]); beat = 60 / 72
    for (a, e_) in pulse:
        t = a; k = 0
        while t < e_:
            root = prog[int(t // bar) % 4][0] + 12
            place(m, bowed(hz(root), beat * .5, .075 if k % 2 == 0 else .05), t, 1, -.15); t += beat / 2; k += 1
    gl = [74, 77, 81, 76, 74, 69]
    for i, t in enumerate(np.arange(3.0, end, 11.0)): place(m, glass(hz(gl[i % len(gl)])), t, 1, (-.4, .4)[i % 2])
    for (a, e_) in cues.get('ticks', []):
        t = a
        while t < e_: place(m, tick() * .5, t, .6, .25); t += 1.0
    for h in cues.get('hits', []):
        place(m, riser(2.0, .07), h - 2.0, 1, 0); place(m, impact(.40), h, 1, 0)
    m = reverb(m[:N + SR * 6], 3.0, .32)[:N]
    tt = np.arange(N) / SR; g = np.ones(N)
    for (a, b_) in cards: g[(tt > a - .05) & (tt < b_)] = 0.0
    for (a, b_) in cues.get('drops', []): g[(tt > a) & (tt < b_)] = .25          # music falls away for a line
    g = lp(g, 3, 1); m *= g[:, None]; m *= np.minimum(1, tt / 2.0)[:, None]; m *= np.clip((end - tt) / 2.5, 0, 1)[:, None]
    return m


def choir(freqs, dur, amp=.05, vowel='a'):
    """Wordless 'aah' pad: detuned saws through two vowel formants, slow swell."""
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for f in freqs:
        for d in (-.12, .0, .14, .27): out += saw(f * 2 ** (d / 12), n, rng.uniform(0, 1)) * (1 + .004 * np.sin(2 * np.pi * 5.1 * t))
    f1, f2 = (700, 1150) if vowel == 'a' else (400, 800)
    out = bp(out, f1 * .7, f1 * 1.3) + .6 * bp(out, f2 * .8, f2 * 1.2) + .3 * lp(out, 500)
    e = np.minimum(1, t / 2.2) * np.minimum(1, (dur - t) / 1.8)
    return amp * out / (4 * len(freqs)) * e
def taiko(amp=.5):
    n = int(1.4 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (52 + 40 * np.exp(-t * 20)) * t) * np.exp(-t * 4.5)
    skin = lp(rng.standard_normal(n), 900) * np.exp(-t * 26) * .6
    return amp * (body + skin)
def horn(f, dur=3.0, amp=.06):
    n = int(dur * SR); t = np.arange(n) / SR; sw = np.minimum(1, t / (dur * .45)) * np.minimum(1, (dur - t) / (dur * .4))
    x = saw(f, n) + .6 * saw(f * 2.001, n) + .3 * saw(f * 1.5, n)
    cut = 300 + 1500 * sw
    out = np.zeros(n); seg = 2400
    for i in range(0, n, seg): y = lp(x[i:i + seg], float(cut[i]), 2); out[i:i + len(y)] = y
    return amp * out * sw


def epic(N, cues, cards):
    """History score: a slow minor progression in low strings and a wordless choir, a sub drone, war drums for battles
    and marches ('drums' ranges), horn swells on big moments ('horns' times), risers into impacts ('hits'),
    quiet stretches where only the drone stays ('drops')."""
    end = N / SR; m = np.zeros((N + SR * 6, 2))
    prog = [[38, 50, 57, 62], [34, 46, 53, 58], [36, 48, 55, 60], [33, 45, 52, 57]]     # Dm  Bb  C  Am
    bar = 7.0; t = 0.0; b = 0
    calm = cues.get('calm', [])
    while t < end:
        ch = prog[b % 4]
        q = .55 if any(a <= t < e_ for a, e_ in calm) else 1.0
        place(m, strings([hz(n) for n in ch[1:3]], bar + 1.6, .08 * q, 820), t, 1, -.1)
        place(m, choir([hz(n + 12) for n in ch[2:]], bar + 1.6, .05 * q), t, 1, .15)
        place(m, sub(hz(ch[0]), bar + 1.6, .2), t)
        t += bar; b += 1
    beat = 60 / 84
    for (a, e_) in cues.get('drums', []):
        t = a; k = 0
        while t < e_:
            pat = (1.0, 0, .55, 0, .8, .45, .55, 0)[k % 8]
            if pat: place(m, taiko(.42 * pat), t, 1, (-.2, .2)[k % 2])
            t += beat / 2; k += 1
    for (a, e_) in cues.get('pulse', []):
        t = a; k = 0
        while t < e_:
            root = prog[int(t // bar) % 4][0] + 12
            place(m, bowed(hz(root), beat * .5, .07 if k % 2 == 0 else .045), t, 1, -.15); t += beat / 2; k += 1
    for h in cues.get('horns', []):
        root = prog[int(h // bar) % 4][0] + 24; place(m, horn(hz(root), 3.6, .07), h - .4, 1, -.1); place(m, horn(hz(root + 7), 3.6, .05), h - .2, 1, .1)
    for h in cues.get('hits', []):
        place(m, riser(2.0, .07), h - 2.0, 1, 0); place(m, impact(.42), h, 1, 0); place(m, taiko(.5), h, 1, 0)
    m = reverb(m[:N + SR * 6], 3.4, .36)[:N]
    tt = np.arange(N) / SR; g = np.ones(N)
    for (a, b_) in cards: g[(tt > a - .05) & (tt < b_)] = .45          # the score stays under chapter cards, softer
    for (a, b_) in cues.get('drops', []): g[(tt > a) & (tt < b_)] = .25
    g = lp(g, 3, 1); m *= g[:, None]; m *= np.minimum(1, tt / 2.0)[:, None]; m *= np.clip((end - tt) / 2.5, 0, 1)[:, None]
    return m * .78


def money(N, cues, cards):
    """Finance documentary score: a modern, tense investigative bed. A minor progression in soft synth pads, a filtered
    pulse in eighths (like a ticking market), a sub, light kick and clock-like hats once the story gets going ('pulse'
    ranges, default: all), a sparse piano motif, risers into impacts on 'hits', near silence on 'drops'."""
    end = N / SR; m = np.zeros((N + SR * 6, 2))
    prog = [[45, 57, 60, 64], [41, 53, 57, 60], [48, 55, 60, 64], [43, 55, 59, 62]]     # Am  F  C  G
    bpm = 92; beat = 60 / bpm; bar = 4 * beat
    pulse = cues.get('pulse') or [(bar * 2, end)]
    motif = [[76, None, 72, None, None, 69, None, None], [None, None, 72, None, 74, None, 72, None], [79, None, 76, None, None, 72, None, None], [None, 74, None, 71, None, None, 67, None]]
    tension = cues.get('tension', [])
    for (a, e_) in tension:          # thriller cold open: a low drone, a heartbeat, a ticking clock, a riser into the title
        place(m, strings([hz(33), hz(40)], e_ - a + 1.0, .07, 500, 1.0), a, 1, 0); place(m, sub(hz(21), e_ - a + 1.0, .2), a)
        k = a + .3
        while k < e_ - .4: place(m, heart(.42), k, 1, 0); k += 1.1
        k = a + .1
        while k < e_ - .3: place(m, tick() * 1.6, k, .9, (-.3, .3)[int(k * 2) % 2]); k += .55
        place(m, riser(2.4, .09), e_ - 2.4, 1, 0)
    t = 0.0; b = 0
    while t < end:
        if any(a - .5 <= t < e_ for a, e_ in tension): t += bar; b += 1; continue
        ch = prog[b % 4]; on = any(a <= t < e_ for a, e_ in pulse)
        place(m, strings([hz(n) for n in ch[1:]], bar + 1.2, .05, 1400, .8), t, 1, 0)
        place(m, sub(hz(ch[0] - 12), bar + 1.2, .16), t)
        if on:
            for i in range(8):
                n = int(beat / 2 * SR); x = lp(saw(hz(ch[1] + (12 if i % 4 == 3 else 0)), n) , 1100 + 500 * (i % 2), 2)
                x *= np.exp(-np.arange(n) / SR * 9) * .11
                place(m, x, t + i * beat / 2, 1, (-.3, .3)[i % 2])
            for i in (0, 2): place(m, kick(.22), t + i * beat)
            for i in range(8): place(m, hat(.022 if i % 2 else .03), t + i * beat / 2, 1, .3)
        if b % 2 == 1:
            for i, n in enumerate(motif[(b // 2) % 4]):
                if n: place(m, piano(hz(n), 1.8, .07), t + i * beat / 2, 1, -.15)
        t += bar; b += 1
    for h in cues.get('hits', []):
        place(m, riser(1.8, .06), h - 1.8, 1, 0); place(m, impact(.36), h, 1, 0)
    m = reverb(m[:N + SR * 6], 2.4, .3)[:N]
    tt = np.arange(N) / SR; g = np.ones(N)
    for (a, b_) in cards: g[(tt > a - .05) & (tt < b_)] = .5
    for (a, b_) in cues.get('drops', []): g[(tt > a) & (tt < b_)] = .22
    g = lp(g, 3, 1); m *= g[:, None]; m *= np.minimum(1, tt / 1.5)[:, None]; m *= np.clip((end - tt) / 2.5, 0, 1)[:, None]
    return m * .8


def track(path, N, cards, cues, ffmpeg='ffmpeg'):
    """A real music file: decoded, looped with a crossfade to the film's length, levelled to the generated score's loudness."""
    tmp = os.path.join(tempfile.gettempdir(), 'hds_track.wav')
    subprocess.run([ffmpeg, '-v', 'error', '-y', '-i', path, '-ar', str(SR), '-ac', '2', tmp], check=True)
    x, _ = sf.read(tmp)
    out = np.zeros((N, 2)); i = 0; xf = int(3 * SR)
    while i < N:
        seg = x.copy()
        if i > 0: seg[:xf] *= np.linspace(0, 1, xf)[:, None]; out[i - xf:i] *= np.linspace(1, 0, xf)[:, None]; i -= xf
        j = min(N, i + len(seg)); out[i:j] += seg[:j - i]; i = j
    out *= .17 / (np.sqrt(np.mean(out ** 2)) + 1e-9)      # about the same loudness as the generated score
    tt = np.arange(N) / SR; g = np.ones(N)
    for (a, b_) in cards: g[(tt > a - .05) & (tt < b_)] = .6
    for (a, b_) in cues.get('drops', []): g[(tt > a) & (tt < b_)] = .3
    g = lp(g, 3, 1); out *= g[:, None]; out *= np.clip((N / SR - tt) / 3.0, 0, 1)[:, None]
    return out


# subtle sound design for the case-board films (no cartoon pops)
def glide(dur=1.1):
    n = int(dur * SR); t = np.arange(n) / SR; x = lp(rng.standard_normal(n), 900)
    return x * np.sin(np.pi * t / dur) ** 2 * .6
def soft_tock():
    n = int(.25 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 180 * t) * np.exp(-t * 40) + lp(rng.standard_normal(n), 2500) * np.exp(-t * 90) * .4) * .5
def typer(k=5):
    out = np.zeros(int(.09 * SR * k + .1 * SR))
    for i in range(k):
        n = int(.02 * SR); c_ = bp(rng.standard_normal(n), 1500, 5000) * np.exp(-np.arange(n) / SR * 260)
        j = int(i * .085 * SR + rng.uniform(0, .02) * SR); out[j:j + n] += c_ * rng.uniform(.6, 1)
    return out * .5
def projector(dur=1.8):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for k in np.arange(0, dur, 1 / 24): j = int(k * SR); m_ = min(n - j, int(.008 * SR)); x[j:j + m_] += bp(rng.standard_normal(m_), 600, 3000) * .7
    x += lp(rng.standard_normal(n), 300) * .2
    return x * np.minimum(1, t / .2) * np.minimum(1, (dur - t) / .8) * .5
def stamp_thump():
    n = int(1.0 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (55 + 80 * np.exp(-t * 30)) * t) * np.exp(-t * 9) + lp(rng.standard_normal(n), 1200) * np.exp(-t * 40) * .5) * .8
def marker(dur=.35):
    n = int(dur * SR); t = np.arange(n) / SR; return bp(rng.standard_normal(n), 2000, 6000) * np.sin(np.pi * t / dur) * .18
def soft_paper():
    n = int(.4 * SR); t = np.arange(n) / SR; return lp(bp(rng.standard_normal(n), 500, 5000), 3000) * np.sin(np.pi * t / .4) ** 2 * .22



# ---------------------------------------------------------------- sound effects
def whoosh(dur=.5):
    n = int(dur * SR); x = rng.standard_normal(n); out = np.zeros(n); seg = 600
    for i in range(0, n, seg):
        u = i / n; fc = 350 + 5200 * np.sin(np.pi * u) ** 1.3; y = bp(x[i:i + seg], max(fc * .55, 120), min(fc * 1.6, 16000)); out[i:i + len(y)] = y
    return out * np.sin(np.pi * np.arange(n) / n) ** 2 * 1.2
def popfx(f0=340):
    n = int(.13 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * (f0 + 900 * np.exp(-t * 42)) * t) * np.exp(-t * 34) * .55
def thud():
    n = int(.7 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (42 + 95 * np.exp(-t * 26)) * t) * np.exp(-t * 8) + lp(rng.standard_normal(n), 2800) * np.exp(-t * 38) * .7 + hp(rng.standard_normal(n), 3500) * np.exp(-t * 7) * .15) * .9
def tick(): n = int(.016 * SR); return hp(rng.standard_normal(n), 2800) * np.exp(-np.arange(n) / SR * 280) * .5
def shutter():
    out = np.zeros(int(.45 * SR)); a = tick() * 2.2; out[:len(a)] += a; k = int(.07 * SR); out[k:k + len(a)] += a
    t = np.arange(len(out)) / SR; return out + hp(rng.standard_normal(len(out)), 6000) * np.exp(-t * 12) * .12
def scribble(dur=.42):
    n = int(dur * SR); t = np.arange(n) / SR; return bp(rng.standard_normal(n), 1400, 5200) * (.5 + .5 * np.sin(2 * np.pi * 13 * t)) * .24
def boom():
    n = int(1.6 * SR); t = np.arange(n) / SR; return np.sin(2 * np.pi * 36 * t) * np.exp(-t * 2.4) * .8 + lp(rng.standard_normal(n), 180) * np.exp(-t * 3) * .4
def paper():
    n = int(.35 * SR); t = np.arange(n) / SR; return bp(rng.standard_normal(n), 900, 7000) * np.sin(np.pi * t / .35) ** 2 * .32
def alarm(dur=1.6):
    n = int(dur * SR); t = np.arange(n) / SR; f = 880 + 220 * np.sign(np.sin(2 * np.pi * 2 * t)); return .12 * np.sign(np.sin(2 * np.pi * f * t)) * lp(np.ones(n), 50) * np.minimum(1, (dur - t) * 4)
def grind(dur=1.2):
    n = int(dur * SR); t = np.arange(n) / SR; return bp(rng.standard_normal(n), 1800, 6000) * (.6 + .4 * np.sin(2 * np.pi * 31 * t)) * .22 * np.minimum(1, t * 10) * np.minimum(1, (dur - t) * 6)
def static(dur=.4):
    n = int(dur * SR); return hp(rng.standard_normal(n), 1500) * .08 * np.minimum(1, (dur - np.arange(n) / SR) * 8)
def ding():
    n = int(.9 * SR); t = np.arange(n) / SR; return (np.sin(2 * np.pi * 2637 * t) + .5 * np.sin(2 * np.pi * 3951 * t)) * np.exp(-t * 7) * .22
def siren(dur=2.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = 700 + 250 * np.sin(2 * np.pi * .8 * t); ph = np.cumsum(2 * np.pi * f / SR)
    return .1 * np.sin(ph) * np.minimum(1, t * 2) * np.minimum(1, (dur - t) * 2)

FX = dict(whoosh=(whoosh, .45, -.3), pop=(popfx, .55, .15), thud=(thud, 1.0, 0), tick=(tick, .45, .2), shutter=(shutter, 1.0, 0),
          scribble=(scribble, .8, -.2), boom=(boom, .7, 0), paper=(paper, .8, -.3), alarm=(alarm, .7, .2), grind=(grind, .8, .1),
          static=(static, .7, 0), ding=(ding, .7, -.1), siren=(siren, .6, .3))


FX_NOIR = dict(cut=(lambda: impact(.35) * np.exp(-np.arange(int(3.2 * SR)) / SR * 1.5), .4, 0), glide=(glide, .32, 0), hit=(lambda: impact(.5), .55, 0), type=(typer, .35, .1), scratch=(marker, .5, -.1),
               paper=(soft_paper, .45, -.2), projector=(projector, .35, .2), thud=(stamp_thump, .7, 0), pop=(soft_tock, .35, .1),
               tick=(tick, .3, .2), whoosh=(glide, .3, 0), shutter=(shutter, .5, 0), boom=(lambda: impact(.6), .6, 0))


def mix(vo, out, end, events, cards, mood, ffmpeg='ffmpeg', cues=None):
    N = int(SR * end)
    # voice: clean-up chain in ffmpeg (fast), then loaded as stereo
    tmp = os.path.join(tempfile.gettempdir(), 'hds_voice.wav')
    subprocess.run([ffmpeg, '-v', 'error', '-y', '-i', vo, '-af', 'highpass=f=72,equalizer=f=3400:t=q:w=1:g=2,acompressor=threshold=-22dB:ratio=3:attack=4:release=120:makeup=3',
                    '-ar', str(SR), '-ac', '2', tmp], check=True)
    v, _ = sf.read(tmp); voice = np.zeros((N, 2)); place(voice, v[:N], 0.0)
    vm = np.abs(voice).mean(1); e = lp(vm, 5, 1); e /= e.max() + 1e-9
    duck = (1 - .62 * np.clip(e * 3.2, 0, 1))[:, None]
    cues = cues or {}
    if cues.get('track'): music = track(cues['track'], N, cards, cues, ffmpeg); print('music: your track', os.path.basename(cues['track']))
    else: music = noir(N, cues, cards) if mood == 'noir' else epic(N, cues, cards) if mood == 'epic' else money(N, cues, cards) if mood == 'money' else score(N, mood, cards)
    cine = mood in ('noir', 'epic', 'money')
    fxset = FX_NOIR if cine else FX
    fx = np.zeros((N, 2))
    seen = set()
    for kind, t in events:
        if kind not in fxset or (kind, round(t, 2)) in seen: continue
        seen.add((kind, round(t, 2))); fn, g, pan = fxset[kind]
        place(fx, fn(), t - (.25 if kind == 'whoosh' else 0), g, pan)
    if cine: fx = reverb(fx, 1.6, .22, 9)
    tone = lp(rng.standard_normal(N), 400) * .003; fx += tone[:, None]
    if cine:
        # balance: the voice always leads. Effects sit well under it and duck further while a word is spoken.
        fduck = (1 - .55 * np.clip(e * 3.2, 0, 1))[:, None]
        m = voice * 1.0 + music * .28 * duck + fx * .20 * fduck
        rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
        pk = lambda x: 20 * np.log10(np.abs(x).max() + 1e-9)
        print(f'levels  voice {rms(voice):.1f} dB  music {rms(music * .28 * duck):.1f} dB  fx {rms(fx * .20 * fduck):.1f} dB (fx peak {pk(fx * .20 * fduck):.1f}, voice peak {pk(voice):.1f})')
    else:
        m = voice * 1.0 + music * .30 * duck + fx * .5
    m = np.tanh(m * 1.1) / np.tanh(1.1)
    sf.write(out, m.astype(np.float32), SR); print('mix', out, f'{end:.1f}s', len(seen), 'sound effects')
