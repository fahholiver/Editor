# Music + SFX stems for "Why Airplane Windows Are Never Square" (60 s). Writes music.wav and sfx.wav (48 kHz stereo).
# Music: curious pizzicato (0-13.4) -> tense drone + pulse (13.4-30.7) -> hard stop on the crack -> hopeful resolve (34-60).
import numpy as np
from dsp import SR, TAU, ns, tt, rng, lp, bp, pan, place, fades, write_wav, read_wav, make_ir, convolve_st, smooth_noise
import instruments as I

V, _ = read_wav('voice48.wav')
N = V.shape[1]
DUR = N / SR
R = rng(5)
m2f = I.m2f

# =============================== MUSIC ===============================
mus = np.zeros((2, N))
B = 0.6  # 100 BPM

# A: curious. D minor plucked arpeggio, soft ticks, a sparse glock answer
A_CH = [[50, 57, 62, 65], [46, 53, 58, 62], [41, 48, 53, 57], [48, 55, 60, 64]]   # Dm Bb F C
t = 0.0; bar = 0
while t < 13.3:
    ch = A_CH[bar % 4]
    for k in range(8):
        tb = t + k * B / 2
        if tb >= 13.3: break
        n = ch[[0, 2, 1, 3, 2, 1, 3, 2][k]]
        place(mus, pan(I.pluck(m2f(n + 12), 0.42, R, dur=0.5, bright=0.6), (-0.3 if k % 2 else 0.3)), tb)
        place(mus, pan(I.pluck(m2f(n + 36), 0.05, R, dur=0.06, bright=1.0), 0.5), tb + B / 4)   # tick
    place(mus, pan(I.pluck(m2f(ch[0] - 12), 0.6, R, dur=1.4, bright=0.3), 0), t)
    place(mus, I.pad([m2f(x) for x in ch[:3]], 4 * B, 0.12, R, att=0.4, rel=0.6, warm=800), t)
    if bar % 2 == 1:
        for j, mm in enumerate([74, 77, 76]):
            place(mus, pan(I.glock(m2f(mm), 0.25, R, dur=1.2), 0.35), t + 2 * B + j * B / 2)
    t += 4 * B; bar += 1

# B: tense. Low drone, 8th-note pulse that tightens, timpani on the two crashes and the tank
place(mus, I.pad([m2f(38), m2f(45), m2f(50)], 30.68 - 13.3 + 0.3, 0.32, R, att=1.2, rel=0.2, warm=420), 13.3)
t = 13.4
while t < 30.65:
    prog = (t - 13.4) / 17.3
    vel = 0.28 + 0.25 * prog
    place(mus, pan(I.pluck(m2f(38 if int((t - 13.4) / (2 * B)) % 4 != 3 else 37), vel, R, dur=0.28, bright=0.35), -0.1), t)
    t += B / 2
for tt_ in (16.95, 21.5):
    place(mus, pan(I.timpani(m2f(38), 0.75, R, dur=2.2), 0), tt_)
for k in range(8):
    place(mus, I.pad([m2f(62 + k % 2), m2f(65 + k % 2)], 0.55, 0.06 + 0.012 * k, R, att=0.1, rel=0.3, warm=1500), 22.6 + k * 0.75)
mus[:, ns(30.68):] = 0                       # silence on "cracks"

# C: hopeful. F C Dm Bb, warm pad + plucked arpeggio + glock melody, resolves on "lesson"
C_CH = [[53, 57, 60], [48, 55, 60, 64], [50, 57, 62, 65], [46, 53, 58, 62]]
MEL = [(0, 72), (1, 74), (1.5, 76), (2, 77), (3, 76), (4, 74), (5, 72), (6, 69), (7, 72)]
t = 34.05; bar = 0
while t < 57.6:
    ch = C_CH[bar % 4]
    place(mus, I.pad([m2f(x) for x in ch[:3]], 4 * B + 0.1, 0.18 if t > 40 else 0.12, R, att=0.5, rel=0.6, warm=1100), t)
    place(mus, pan(I.pluck(m2f(ch[0] - 12), 0.5, R, dur=1.6, bright=0.3), 0), t)
    if t > 36.4:
        for k in range(8):
            tb = t + k * B / 2
            if tb >= 57.6: break
            place(mus, pan(I.pluck(m2f(ch[[0, 1, 2, 1, 0, 2, 1, 2][k] % len(ch)] + 12), 0.3, R, dur=0.45, bright=0.55), (-0.35 if k % 2 else 0.35)), tb)
    if t > 46.5:
        for ob, mm in MEL:
            if ob < 4 and bar % 2 == 0 or ob >= 4 and bar % 2 == 1:
                tn = t + (ob % 4) * B
                if tn < 57.6: place(mus, pan(I.glock(m2f(mm), 0.22, R, dur=1.3), 0.25), tn)
    t += 4 * B; bar += 1
# final resolve: F major, held to the end
place(mus, I.pad([m2f(41), m2f(53), m2f(57), m2f(60)], DUR - 57.85, 0.3, R, att=0.15, rel=1.2, warm=1300), 57.85)
for j, mm in enumerate([72, 77, 81, 84]):
    place(mus, pan(I.glock(m2f(mm), 0.3, R, dur=2.0), -0.3 + 0.2 * j), 57.88 + j * 0.09)
mus[:, ns(DUR - 0.9):] *= np.linspace(1, 0, N - ns(DUR - 0.9)) ** 1.5
ir = make_ir(1.4, 3)
mus = convolve_st(mus, ir)[:, :N] * 0.3 + mus * 0.85

# =============================== SFX ===============================
sfx = np.zeros((2, N))
def env_exp(n, k): return np.exp(-np.arange(n) / SR * k)
def noise(d): return R.standard_normal(ns(d))
def whoosh(d=0.45, lo=300, hi=2500, amp=0.6):
    x = noise(d); n = len(x); out = np.zeros(n); seg = 256
    for i in range(0, n, seg):
        p = i / n; fc = lo + (hi - lo) * np.sin(np.pi * p)
        out[i:i + seg] = bp(x[max(0, i - 512):i + seg], max(60, fc * 0.6), fc * 1.4)[-len(out[i:i + seg]):]
    return amp * out * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
def pop(f0=700, f1=180, d=0.12, amp=0.6):
    t = tt(d); f = f1 + (f0 - f1) * np.exp(-t * 40)
    return amp * np.sin(TAU * np.cumsum(f) / SR) * env_exp(len(t), 30)
def ting(f=2093, amp=0.45): return amp * I.glock(f, 0.8, R, dur=1.2)
def thud(amp=0.8, f=80):
    t = tt(0.35); return amp * (np.sin(TAU * f * t) * env_exp(len(t), 14) + 0.6 * lp(noise(0.35), 400) * env_exp(len(t), 25))
def slam(amp=0.9):
    x = thud(amp, 70); x[:ns(0.25)] += 0.5 * amp * bp(noise(0.25), 200, 1200) * env_exp(ns(0.25), 20); return x
def click(amp=0.35, f=None):
    t = tt(0.03); f = f or R.uniform(2500, 4500); return amp * np.sin(TAU * f * t) * env_exp(len(t), 160)
def scribble(d=0.3, amp=0.35):                       # marker / pen on paper
    x = bp(noise(d), 1800, 6500); am = 0.5 + 0.5 * np.abs(np.sin(np.linspace(0, d * 38, len(x)) + R.uniform(0, 3)))
    return amp * fades(x * am * (0.7 + 0.3 * smooth_noise(len(x), R, 30)), 0.01, 0.05)
def squeak(d=0.35, amp=0.3):                         # highlighter swipe
    t = tt(d); f = 2600 + 500 * t / d
    tone = np.sin(TAU * np.cumsum(f) / SR) * 0.25 + bp(noise(d), 2500, 6000)
    return amp * fades(tone * (0.6 + 0.4 * np.sin(TAU * 31 * t)), 0.02, 0.08)
def paper(d=0.4, amp=0.4):                           # paper slide
    x = bp(noise(d), 500, 5000) * (0.4 + 0.6 * smooth_noise(ns(d), R, 25)); return amp * x * np.sin(np.pi * np.linspace(0, 1, len(x))) ** 0.8
def hiss(d, amp=0.25, rise=True):
    x = bp(noise(d), 1500, 7000); e = np.linspace(0.2, 1, len(x)) if rise else np.linspace(1, 0.1, len(x))
    return amp * fades(x * e, 0.04, 0.1)
def slosh(d=1.6, amp=0.4):
    x = lp(noise(d), 700) * (0.3 + 0.7 * np.abs(smooth_noise(ns(d), R, 2.5))); return amp * fades(x, 0.3, 0.6)
def bubble(amp=0.2):
    t = tt(0.06); f = R.uniform(350, 800) * (1 + 3 * t / 0.06)
    return amp * np.sin(TAU * np.cumsum(f) / SR) * np.sin(np.pi * np.linspace(0, 1, len(t)))
def crack(amp=1.0):
    out = np.zeros(ns(1.2))
    out[:ns(0.02)] += amp * noise(0.02) * env_exp(ns(0.02), 60)
    for k in range(26):                               # splintering crackle
        s = ns(R.uniform(0, 0.35) ** 1.6); b = bp(noise(0.012), 1500, 9000) * R.uniform(0.3, 0.9) * amp
        out[s:s + len(b)] += b
    th = thud(0.9 * amp, 55); out[:len(th)] += th
    return out
def sting(amp=0.8):
    t = tt(2.4); return amp * (np.sin(TAU * 41 * t) + 0.5 * np.sin(TAU * 61.7 * t) + 0.3 * lp(noise(2.4), 200)) * env_exp(len(t), 2.0)
def shimmer(amp=0.35):
    out = np.zeros(ns(1.0))
    for i, m in enumerate([84, 88, 91, 96, 100]):
        b = I.glock(m2f(m), 0.5, R, dur=0.8); s = ns(i * 0.05); out[s:s + len(b)] += b[:len(out) - s]
    return amp * out
def rumble(amp=0.5, d=1.2):
    t = tt(d); return amp * np.sin(TAU * np.cumsum(60 + 20 * np.sin(TAU * 6 * t)) / SR) * np.sin(np.pi * np.linspace(0, 1, len(t)))
def P(x, t, p=0.0, g=1.0): place(sfx, pan(x, p), t, g)

# 1 hook
P(paper(0.35), 0.1); P(scribble(0.25, 0.4), 1.3, -0.2); P(scribble(0.25, 0.4), 1.55, 0.2); P(squeak(0.35), 1.0)
# 2
P(thud(0.6, 60), 3.05); P(slam(0.8), 3.68); P(scribble(0.35, 0.3), 4.1)
# 3
P(slam(0.8), 4.95); P(whoosh(0.8, 250, 1800, 0.5), 6.3, 0.4); P(paper(0.4, 0.35), 6.9); P(pop(), 6.42, -0.4); P(pop(), 7.35); P(squeak(0.45), 9.25)
# 4
P(whoosh(2.6, 150, 900, 0.35), 10.9, 0.0)
for tb in (11.05, 11.88, 12.55): P(thud(0.7, 75), tb)
# 5 map
P(whoosh(1.2, 200, 1500, 0.45), 13.45); P(pop(800, 200), 13.6)
P(thud(0.9, 50), 16.95); P(pop(500, 120, 0.2, 0.6), 16.97); P(pop(), 17.95, -0.3)
P(pop(800, 200), 19.6); P(thud(0.9, 50), 21.5); P(pop(), 21.62, 0.3)
# 6 tank
P(paper(0.4), 22.45); P(pop(600, 150), 22.55); P(pop(), 23.1)
P(whoosh(1.0, 150, 900, 0.45), 23.45); P(slosh(1.8, 0.45), 24.2)
for i in range(60): P(bubble(0.16), 25.0 + i * 0.06 + R.uniform(0, 0.05), R.uniform(-0.4, 0.4))
for k in range(4): P(hiss(0.5, 0.22), 26.45 + k * 0.69 - 0.1, 0.2)
# 7 tally
P(thud(0.6, 90), 28.72); P(squeak(0.35), 29.45)
n_marks, tot = 180, 0
for k in range(n_marks):
    u = np.sqrt((k + 0.5) / n_marks); tk = 28.7 + u * 1.5
    if k % 3 == 0: P(click(0.22, R.uniform(1500, 3000)), tk, R.uniform(-0.5, 0.5))
# 8 crack
P(whoosh(0.4, 300, 2500, 0.5), 30.32); P(crack(1.0), 30.68, 0.1); P(sting(0.7), 30.7)
P(scribble(0.45, 0.4), 32.15, 0.2); P(squeak(0.35), 32.25)
# 9 puff
P(whoosh(0.4, 400, 2000, 0.3), 34.15); P(pop(), 34.9); P(pop(), 35.1)
P(hiss(0.8, 0.3, True), 36.55); P(pop(), 36.62); P(hiss(0.8, 0.3, False), 38.45); P(pop(), 38.52)
# 10 stress
P(paper(0.4), 40.05); P(thud(0.5, 90), 40.2); P(ting(2349), 42.46, -0.3)
P(paper(0.4), 43.72); P(pop(400, 100, 0.18, 0.6), 43.75, -0.3); P(rumble(0.4, 1.4), 44.4); P(scribble(0.45, 0.4), 45.35, 0.3)
# 11 doc
P(paper(0.5, 0.45), 46.85)
for i in range(12): P(click(0.25, 2200 + 60 * i), 46.95 + i * 0.13, -0.4 + 0.07 * i)
P(squeak(0.6), 48.2); P(squeak(0.5), 50.3)
# 12-13 end
P(paper(0.4), 51.5); P(scribble(0.7, 0.25), 53.05); P(squeak(0.35), 53.15)
P(scribble(0.5, 0.35), 55.2, 0.4); P(whoosh(0.5, 400, 2000, 0.3), 56.3); P(thud(0.6, 70), 57.86); P(shimmer(0.35), 57.9)

write_wav('music.wav', mus)
write_wav('sfx.wav', sfx)
print('stems written', round(DUR, 2))
