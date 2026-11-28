"""The finance documentary look: a dark market-terminal style built on real photos and numbers that move.

    from fin import *
    film = Film(__file__, vo='vo.wav', words='words.json', mood='money')
    T = film.cue
    fin = Fin(film)
    fin.photo(0, 'media/store.jpg', frm=(.5, .5, 1.0), to=(.55, .45, 1.15), credit='Photo: Jane Doe, CC BY-SA 2.0')
    fin.number(T('six billion'), 6_000_000_000, prefix='$', label='REVENUE, 2004')
    fin.chart(T('Then'), [(2000, 4.96), (2004, 6.05), (2010, 3.2)], title='REVENUE', unit='$B', crash_from=2004)
    fin.bars(T('stores'), [('Blockbuster', 9000, GREEN), ('Netflix', 0, BLUE)], title='STORES')
    fin.versus(T('offered'), ('NETFLIX', '$50M', 'the asking price'), ('BLOCKBUSTER', '$6B', 'yearly revenue'))
    fin.statement(T('They laughed'), 'THEY LAUGHED', sub='Blockbuster said no')
    fin.clipping(T('filed for'), 'media/clip_10k.png', mark=[(.08, .41, .93, .45)], at=T('six billion'), source='sec.gov', note='Form 10-K, 2004')
    @fin.screen
    def words(c, t):
        tag(c, t, T('Dallas'), T('By'), 'Dallas, Texas', '1985', 'THE FIRST STORE')
        stamp(c, t, T('bankrupt'), 'BANKRUPT')
    fin.render()
    film.main()

Shot kinds: photo (real photo full screen or on a floating card), footage (real archive film, cut by scripts/footage.py), clipping (a real article or filing screenshot on a tilted card,
the key line highlighted with a yellow marker as the narrator says it, with a Source label), chart (a line that draws itself, red after the crash),
number (a big counter), bars (comparison), versus (split screen), statement (one big line), scene (anything you draw).
Overlays (inside @fin.screen): tag, name_tag, year_badge, stamp, ticker, quote, credit_line, title_card.
Chapter cards come by themselves in the narrator's chapter pauses. See references/fin.md."""
import os, math, random, subprocess
import numpy as np, skia
from film import Film, W, H, FPS, C, K, ease, lerp, sfx, FFMPEG
from core import ease_out, pop as _pop
import doc as _doc
from doc import _art, _window, _blit, fade

_FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts') + os.sep
BEBAS = skia.Typeface.MakeFromFile(_FD + 'BebasNeue-Regular.ttf')
OSWALD = skia.Typeface.MakeFromFile(_FD + 'Oswald-Variable.ttf')
MONO = skia.Typeface.MakeFromFile(_FD + 'IBMPlexMono-Medium.ttf')
PLAYFAIR = skia.Typeface.MakeFromFile(_FD + 'PlayfairDisplay-Variable.ttf')   # recreated clippings: masthead and headline
BODY = skia.Typeface.MakeFromFile(_FD + 'CormorantGaramond-Variable.ttf')     # recreated clippings: article text
MARK = '#FFE14D'
V = H > W                       # vertical 9:16 (Shorts): set FDS_VERTICAL=1 before importing (see examples/blockbuster/short/)
CY = H * .40 if V else H / 2    # where centred shots sit (higher in vertical, so the captions and the app's buttons stay clear)                                                               # highlighter yellow
BG, PANEL, GRID, TXT, MUTED = '#0A0E13', '#111821', '#1A2430', '#ECF1F5', '#7F8C9B'
GREEN, RED, GOLD, BLUE, CYAN = '#2BD47D', '#FF4D4D', '#F2B544', '#4DA3FF', '#38D6E0'

col, fp, font, tw = _doc.col, _doc.fp, _doc.font, _doc.tw
def text(c, s, x, y, size, tf=OSWALD, h=TXT, align='left', a=255, track=0, wght=None, shadow=0):
    return _doc.text(c, s, x, y, size, tf, h, align, a, track, wght, shadow)
def line(w, h=TXT, a=255):
    p = skia.Paint(AntiAlias=True, Color=col(h, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join); return p
def glow(h, a, blur): return fp(h, a, blur)
def money(v, prefix='$', decimals=0):
    """6000000000 -> '$6,000,000,000'"""
    s = f'{abs(v):,.{decimals}f}'; return ('-' if v < 0 else '') + prefix + s
def short(v, prefix='$'):
    """6e9 -> '$6B', 5e7 -> '$50M'"""
    a = abs(v)
    for d, u in ((1e12, 'T'), (1e9, 'B'), (1e6, 'M'), (1e3, 'K')):
        if a >= d: s = f'{a / d:.1f}'.rstrip('0').rstrip('.'); return ('-' if v < 0 else '') + prefix + s + u
    return prefix + f'{a:g}'


# ================================================================ background: dark terminal with a slow grid
_rng = np.random.default_rng(5)
_g = (_rng.standard_normal((H, W)) * 14 + 128).clip(0, 255).astype(np.uint8)
_GRAIN = [skia.Image.fromarray(np.dstack([np.roll(_g, k * 97, 1), np.roll(_g, k * 97, 1), np.roll(_g, k * 97, 1), np.full((H, W), 14, np.uint8)]), colorType=skia.kRGBA_8888_ColorType) for k in range(4)]

def market_bg(c, t, glow_at=(W * .72, H * .28), tint=CYAN):
    c.drawRect(skia.Rect(0, 0, W, H), fp(BG))
    sh = skia.GradientShader.MakeRadial(glow_at, W * .7, [col(tint, 34), col(tint, 0)], [0, 1])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect(0, 0, W, H), p)
    off = (t * 9) % 80
    for x in range(-80, W + 80, 80): c.drawLine(x + off, 0, x + off, H, line(1, GRID, 120))
    for y in range(0, H + 80, 80): c.drawLine(0, y, W, y, line(1, GRID, 120))

def finish(c, t, vig=.55):
    c.drawImage(_GRAIN[int(t * 12) % 4], 0, 0)
    sh = skia.GradientShader.MakeRadial((W / 2, H / 2), W * .78, [col('#000000', 0), col('#000000', 0), col('#000000', 255 * vig)], [0, .55, 1])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect(0, 0, W, H), p)

# photo grade: a touch cooler and less saturated, so real photos sit inside the dark look
_GRADE = skia.ColorFilters.Matrix([.86, .12, .02, 0, 0,  .05, .89, .06, 0, 0,  .03, .12, .87, 0, .015,  0, 0, 0, 1, 0])


# ================================================================ overlays (call inside @fin.screen)
def tag(c, t, t0, t1, line_, sub=None, kind=None, x=None, y=None):
    """lower-left tag: a green mono kind, a big line, a small sub line"""
    a = fade(t, t0, t1, .45, .45)
    if a <= 0: return
    x = x if x is not None else (70 if V else 96); y = y if y is not None else (330 if V else H - 130)
    if V:      # Shorts: labels live at the top, the captions own the middle
        sh = skia.GradientShader.MakeLinear([(0, 0), (0, 520)], [col('#000000', 190 * a), col('#000000', 0)])
        p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect(0, 0, W, 520), p)
    else:
        sh = skia.GradientShader.MakeLinear([(0, H - 360), (0, H)], [col('#000000', 0), col('#000000', 190 * a)])
        p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect(0, H - 360, W, H), p)
    dx = 24 * (1 - ease_out(K(t, t0, .6)))
    if kind:
        kw = tw(kind.upper(), 24, MONO, 3) + 28
        c.drawRoundRect(skia.Rect(x + dx, y - 104, x + dx + kw, y - 66), 6, 6, fp(GREEN, 235 * a))
        text(c, kind.upper(), x + dx + 14, y - 77, 24, MONO, BG, a=255 * a, track=3)
    text(c, line_, x + dx, y, 64, OSWALD, TXT, a=255 * a, wght=600)
    if sub: text(c, sub, x + dx + 2, y + 48, 30, OSWALD, '#B8C3CF', a=230 * a, wght=400)

def name_tag(c, t, t0, t1, name, role, note=None, x=None, y=None):
    """a person's name beside their photo"""
    a = fade(t, t0, t1, .5, .5)
    if a <= 0: return
    x = x if x is not None else (90 if V else 1180); y = y if y is not None else (360 if V else 520)
    u = ease_out(K(t, t0, .7))
    c.drawRect(skia.Rect(x - 30, y - 120, x - 22, y + 110 * u), fp(GREEN, 255 * a))
    size = 100 if V else 140
    while tw(name.upper(), size, BEBAS, 2) > W - x - 60: size -= 6
    text(c, name.upper(), x, y, size, BEBAS, TXT, a=255 * a, track=2, shadow=.6)
    text(c, role, x + 4, y + 58, 40, OSWALD, '#C9D3DD', a=255 * a, wght=500, shadow=.5)
    if note: text(c, note, x + 4, y + 104, 24, MONO, MUTED, a=230 * a)

def year_badge(c, t, t0, t1, year, sub=None, x=96, y=None):
    """top-left mono year pill (year can be fn(t) -> number for a rolling year)"""
    a = fade(t, t0, t1, .45, .45)
    if a <= 0: return
    y = y if y is not None else (300 if V else 120)
    s = str(int(round(year(t)))) if callable(year) else str(year)
    w = tw(s, 54, MONO) + 50
    c.drawRoundRect(skia.Rect(x, y - 58, x + w, y + 18), 10, 10, fp(PANEL, 230 * a)); c.drawRoundRect(skia.Rect(x, y - 58, x + w, y + 18), 10, 10, line(2, GREEN, 200 * a))
    c.drawCircle(x + 20, y - 20, 6, fp(GREEN if int(t * 2) % 2 else '#1E7A4C', 255 * a))
    text(c, s, x + 36, y, 54, MONO, TXT, a=255 * a)
    if sub: text(c, sub.upper(), x + w + 22, y - 8, 30, OSWALD, '#C9D3DD', a=255 * a, track=3, wght=500, shadow=.6)

def stamp(c, t, t0, word, h=RED, x=W / 2, y=CY + 60, size=170, t1=None, rot=-6):
    """a word slammed onto the frame (BANKRUPT, SOLD, CLOSED). Logs a thud."""
    if t < t0 or (t1 is not None and t > t1 + .3): return
    if abs(t - t0) < 1 / FPS: sfx('thud', t0)
    u = K(t, t0, .22); a = min(1, u * 2) * (1 - (K(t, t1, .3) if t1 else 0)); s = 1.7 - .7 * ease_out(u)
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    w = tw(word, size, BEBAS, 6) + 70
    c.drawRect(skia.Rect(-w / 2, -size * .82, w / 2, size * .22), line(10, h, 235 * a))
    text(c, word, 0, 0, size, BEBAS, h, 'center', 235 * a, 6)
    c.restore()

def ticker(c, t, t0, t1, items, speed=120, y=None):
    """scrolling ticker tape along the bottom. items: [('BLOCKBUSTER STORES', '9,000', GREEN), ...]"""
    a = fade(t, t0, t1, .5, .5)
    if a <= 0: return
    y = y if y is not None else (250 if V else H - 46)
    c.drawRect(skia.Rect(0, y - 40, W, y + 22), fp('#05080B', 235 * a)); c.drawLine(0, y - 40, W, y - 40, line(1.5, GREEN, 160 * a))
    seg = []
    for k, v, h in items: seg.append((k + '  ', MUTED, None)); seg.append((v + '  ', h, 'up' if h == GREEN else 'down' if h == RED else None)); seg.append(('      ', GRID, None))
    total = sum(tw(s, 26, MONO) + (26 if arr else 0) for s, _, arr in seg); x = -((t - t0) * speed % total)
    while x < W:
        for s, h, arr in seg:
            text(c, s, x, y, 26, MONO, h, a=255 * a); x += tw(s, 26, MONO)
            if arr:
                p = skia.Path(); yy = y - 10
                if arr == 'up': p.moveTo(x - 6, yy + 7); p.lineTo(x + 6, yy + 7); p.lineTo(x, yy - 5)
                else: p.moveTo(x - 6, yy - 5); p.lineTo(x + 6, yy - 5); p.lineTo(x, yy + 7)
                p.close(); c.drawPath(p, fp(h, 255 * a)); x += 26

def quote(c, t, t0, t1, words, who, src=None):
    """a real quote, centred, with who said it and where (never invent quotes)"""
    a = fade(t, t0, t1, .5, .5)
    if a <= 0: return
    c.drawRect(skia.Rect(0, 0, W, H), fp('#000000', 150 * a))
    text(c, '“', W / 2, 360, 220, BEBAS, GREEN, 'center', 255 * a)
    lines = _wrap(words, 70, OSWALD, W - 360, 500)
    for i, ln in enumerate(lines): text(c, ln, W / 2, 470 + i * 88, 70, OSWALD, TXT, 'center', 255 * a, wght=500)
    yy = 470 + len(lines) * 88 + 30
    text(c, '— ' + who, W / 2, yy, 36, OSWALD, GREEN, 'center', 255 * a, wght=600)
    if src: text(c, src, W / 2, yy + 46, 24, MONO, MUTED, 'center', 230 * a)

def credit_line(c, t, t0, t1, s):
    """small photo credit bottom-right (every photo needs one)"""
    a = fade(t, t0, t1, .4, .4)
    if a <= 0: return
    if V: text(c, s, 70, H - 392, 20, MONO, '#AEB8C2', 'left', 210 * a, shadow=.8)
    else: text(c, s, W - 40, H - 30, 20, MONO, '#AEB8C2', 'right', 210 * a, shadow=.8)

def title_card(c, t, t0, t1, small, big, sub=None):
    a = fade(t, t0, t1, .6, .6)
    if a <= 0: return
    c.drawRect(skia.Rect(0, 0, W, H), fp(BG, 200 * a))
    u = ease_out(K(t, t0, .9))
    text(c, small.upper(), W / 2, 400, 40, MONO, GREEN, 'center', 255 * a, 10)
    size = 260
    while tw(big.upper(), size, BEBAS, 8) > W - 160: size -= 10
    text(c, big.upper(), W / 2, 400 + size * .95, size, BEBAS, TXT, 'center', 255 * a, 8)
    c.drawLine(W / 2 - 300 * u, 400 + size * 1.05, W / 2 + 300 * u, 400 + size * 1.05, line(4, GREEN, 255 * a))
    if sub: text(c, sub, W / 2, 400 + size * 1.05 + 70, 40, OSWALD, '#C9D3DD', 'center', 255 * a, wght=400)

def chapter_card(c, t, t0, dur, num, title, sub=None):
    """dark chapter card in the narrator's pause: CHAPTER 01 in mono, the title in Bebas, a little chart line under it"""
    a = min(1, K(t, t0, .35)) * (1 - K(t, t0 + dur - .3, .35))
    if a <= 0: return
    c.saveLayerAlpha(None, int(255 * a)); market_bg(c, t, (W / 2, H / 2), GREEN)
    u = ease_out(K(t, t0 + .05, .8))
    n = ''.join(ch for ch in num if ch.isdigit()) or num
    lab = f'CHAPTER {int(n):02d}' if n.isdigit() else num.upper()
    text(c, lab, W / 2, 400, 34, MONO, GREEN, 'center', track=10)
    size = 220
    while tw(title.upper(), size, BEBAS, 6) > W - 200: size -= 10
    text(c, title.upper(), W / 2, 420 + size * .92 - 16 * (1 - u), size, BEBAS, TXT, 'center', track=6)
    r = random.Random(len(title)); pts = []; v = .5
    for k in range(40): v = min(.95, max(.05, v + r.uniform(-.16, .16))); pts.append((W / 2 - 360 + k * 18.5, 700 + v * 60))
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:max(2, int(len(pts) * u))]: p.lineTo(*q)
    c.drawPath(p, line(3, GREEN, 230))
    if sub: text(c, sub, W / 2, 840, 40, OSWALD, '#C9D3DD', 'center', wght=400)
    finish(c, t); c.restore()


def title_slam(c, t, t0, dur, small, big):
    """the episode title at the end of a thriller cold open: black, a hard slam, a red rule, then it holds"""
    a = min(1, K(t, t0, .08)) * (1 - K(t, t0 + dur - .35, .4))
    if a <= 0: return
    c.saveLayerAlpha(None, int(255 * a)); c.drawRect(skia.Rect(0, 0, W, H), fp('#05070A'))
    sh = skia.GradientShader.MakeRadial((W / 2, H / 2), W * .6, [col(RED, 40), col(RED, 0)], [0, 1]); p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect(0, 0, W, H), p)
    u = K(t, t0, .25); sc = 1.25 - .25 * ease_out(u); shake = (1 - u) * 14 * math.sin(t * 90)
    c.save(); c.translate(W / 2 + shake, H / 2); c.scale(sc, sc)
    text(c, small.upper(), 0, -120, 46, MONO, '#C9D3DD', 'center', 255, 10)
    size = 230
    while tw(big.upper(), size, BEBAS, 6) > W - 180: size -= 10
    text(c, big.upper(), 0, -120 + 40 + size * .85, size, BEBAS, TXT, 'center', 255, 6)
    v = ease_out(K(t, t0 + .2, .7)); c.drawLine(-360 * v, size * .95, 360 * v, size * .95, line(7, RED))
    c.restore(); finish(c, t, .7); c.restore()

def datestamp(c, t, t0, t1, line1, line2=None, x=96, y=H - 150):
    """thriller date line typed out in mono with a blinking cursor (adds typing sounds)"""
    a = fade(t, t0, t1, .1, .4)
    if a <= 0: return
    full = line1 + ('\n' + line2 if line2 else ''); n = int(min(len(full), (t - t0) * 26))
    if n < len(full) and int((t - t0) * 26) != int((t - t0 - 1 / FPS) * 26) and int((t - t0) * 26) % 3 == 0: sfx('type', t)
    shown = full[:n].split('\n')
    for i, ln in enumerate(shown):
        text(c, ln, x, y + i * 56, 44 if i == 0 else 30, MONO, TXT if i == 0 else '#9FB0C0', a=255 * a, track=2, shadow=.8)
    if int(t * 2.5) % 2 == 0:
        last = shown[-1]; xx = x + tw(last, 44 if len(shown) == 1 else 30, MONO, 2) + 8
        c.drawRect(skia.Rect(xx, y + (len(shown) - 1) * 56 - 38, xx + 20, y + (len(shown) - 1) * 56 + 4), fp(RED, 230 * a))

def end_card(c, t, t0, t1, msg='FULL STORY ON THE CHANNEL', y=None):
    """a green pill for the last seconds of a Short (or an end screen): where to go next"""
    a = fade(t, t0, t1, .3, .3)
    if a <= 0: return
    y = y if y is not None else (H - 560 if V else H - 120); u = ease_out(K(t, t0, .4))
    w_ = tw(msg, 58, BEBAS, 4) + 70; c.save(); c.translate(W / 2, y); c.scale(.85 + .15 * u, .85 + .15 * u)
    c.drawRoundRect(skia.Rect(-w_ / 2, -64, w_ / 2, 22), 16, 16, fp(GREEN, 245 * a)); text(c, msg, 0, 0, 58, BEBAS, BG, 'center', 255 * a, 4)
    c.restore()

def _caption_groups(words, n=3):
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= n or w[2].endswith(('.', '?', '!', ',')): out.append(cur); cur = []
    if cur: out.append(cur)
    return out

def captions(c, t, groups, y=None, size=96):
    """big word-by-word captions (Shorts): up to 3 words at a time, the word being spoken in green"""
    g = next((g for g in groups if g[0][0] - .05 <= t <= g[-1][1] + .25), None)
    if not g: return
    y = y if y is not None else (H * .655 if V else H - 150)
    parts = [w[2].upper() for w in g]; full = ' '.join(parts)
    while tw(full, size, BEBAS, 2) > W - 120: size -= 4
    x = W / 2 - tw(full, size, BEBAS, 2) / 2; pop = 1 + .07 * (1 - K(t, g[0][0], .12))
    c.save(); c.translate(W / 2, y); c.scale(pop, pop); c.translate(-W / 2, -y)
    for w, s_ in zip(g, parts):
        on = w[0] - .02 <= t <= w[1] + .08
        text(c, s_, x + 5, y + 6, size, BEBAS, '#000000', a=210, track=2)
        text(c, s_, x, y, size, BEBAS, GREEN if on else TXT, track=2, shadow=.6)
        x += tw(s_ + ' ', size, BEBAS, 2)
    c.restore()

def _wrap(s, size, tf, maxw, wght=None):
    out, cur = [], ''
    for w in s.split():
        q = (cur + ' ' + w).strip()
        if tw(q, size, tf, 0, wght) > maxw and cur: out.append(cur); cur = w
        else: cur = q
    if cur: out.append(cur)
    return out


# ================================================================ shot drawers
def _photo(c, s, t, e, build):
    im, fg, bg = _art(s['src'], s['depth'], build)
    fx, fy, z = [lerp(a, b, e) for a, b in zip(s['frm'], s['to'])]
    if s.get('card'):
        market_bg(c, t)
        iw, ih = im.width(), im.height(); maxw, maxh = (W * .86, H * .46) if V else (W * .62, H * .66); sc = min(maxw / iw, maxh / ih) * z
        ww, hh = iw * sc, ih * sc; x = W * s['card'] - ww / 2 + (fx - .5) * 30; y = CY - hh / 2 - 20
        c.drawRect(skia.Rect(x + 16, y + 22, x + ww + 16, y + hh + 22), fp('#000000', 150, 30))
        c.drawRect(skia.Rect(x - 10, y - 10, x + ww + 10, y + hh + 10), fp('#E9EEF2'))
        p = skia.Paint(); p.setColorFilter(_GRADE)
        c.drawImageRect(im, skia.Rect(x, y, x + ww, y + hh), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p)
        if s.get('label'): text(c, s['label'].upper(), x, y + hh + 56, 26, MONO, GREEN, track=3)
        return
    gp = skia.Paint(); gp.setColorFilter(_GRADE); c.saveLayer(None, gp)
    if fg is not None:
        cx, cy, ww, wh = _window(bg, fx, fy, z); _blit(c, bg, cx, cy, ww, wh)
        k = 1 + .045 * e; _blit(c, fg, cx + ww * .012 * e, cy, ww / k, wh / k)
    else:
        cx, cy, ww, wh = _window(im, fx, fy, z); _blit(c, im, cx, cy, ww, wh)
    c.restore()
    # cool shadows: draw a cool shadow tint and a soft top/bottom fade toward the background colour
    c.drawRect(skia.Rect(0, 0, W, H), fp('#0A1A22', 38))
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [col(BG, 120), col(BG, 0), col(BG, 0), col(BG, 150)], [0, .22, .7, 1])
    q = skia.Paint(); q.setShader(sh); c.drawRect(skia.Rect(0, 0, W, H), q)

class _Clip:
    """Reads frames of a prepared footage clip (scripts/footage.py) in order through ffmpeg, scaled to cover the frame.
    Frames are asked for in increasing order while rendering, so one ffmpeg process per clip is enough; a jump restarts it."""
    def __init__(self, path):
        self.path, self.proc, self.n, self.img, self.size = path, None, -1, None, W * H * 4
        try:
            out = subprocess.run([FFMPEG, '-i', path], capture_output=True, text=True).stderr
            import re as _re
            m = _re.search(r'Duration: (\d+):(\d+):([\d.]+)', out); self.frames = max(1, int((int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])) * FPS) - 1)
        except Exception: self.frames = 10 ** 9
    def _start(self, n):
        if self.proc: self.proc.kill(); self.proc.wait()
        vf = f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}'
        self.proc = subprocess.Popen([FFMPEG, '-v', 'error', '-ss', f'{n / FPS:.3f}', '-i', self.path, '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=self.size); self.n = n - 1
    def frame(self, n):
        n = max(0, min(int(n), self.frames - 1))
        if n == self.n and self.img is not None: return self.img
        if self.proc is None or n < self.n or n > self.n + 150: self._start(n)
        buf = None
        while self.n < n:
            b = self.proc.stdout.read(self.size)
            if len(b) < self.size: break                              # past the end: hold the last frame
            buf = b; self.n += 1
        if buf is not None: self.img = skia.Image.frombytes(buf, (W, H), skia.kRGBA_8888_ColorType)
        self.n = max(self.n, n); return self.img

_CLIPS = {}
def _footage(c, s, t, e):
    cl = _CLIPS.get(s['src']) or _CLIPS.setdefault(s['src'], _Clip(s['src']))
    im = cl.frame((s['start'] + max(0, t - s['t0']) * s['speed']) * FPS)
    if im is None: market_bg(c, t); return
    fx, fy, z = [lerp(a, b, e) for a, b in zip(s['frm'], s['to'])]
    gp = skia.Paint()
    if s.get('bw'):                                   # old-film look for stock clips standing in for an older era
        r = random.Random(int(t * FPS)); k = 1.12 * (1 + .05 * (r.random() - .5)); o = -.05 + .02 * (r.random() - .5)
        gp.setColorFilter(skia.ColorFilters.Matrix([.30 * k, .59 * k, .11 * k, 0, o + .012,  .30 * k, .59 * k, .11 * k, 0, o + .006,  .30 * k, .59 * k, .11 * k, 0, o,  0, 0, 0, 1, 0]))
    else: gp.setColorFilter(_GRADE)
    c.saveLayer(None, gp)
    cx, cy, ww, wh = _window(im, fx, fy, z); _blit(c, im, cx, cy, ww, wh); c.restore()
    if s.get('bw'):
        r = random.Random(int(t * FPS) * 7 + 1)
        for _ in range(900): c.drawPoint(r.uniform(0, W), r.uniform(0, H), fp('#FFFFFF' if r.random() < .5 else '#000000', r.randint(18, 60)))
        if r.random() < .35:
            x = r.uniform(0, W); c.drawRect(skia.Rect(x, 0, x + 1.5, H), fp('#FFFFFF', 40))
        sh = skia.GradientShader.MakeRadial((W / 2, H / 2), max(W, H) * .72, [col('#000000', 0), col('#000000', 0), col('#000000', 150)], [0, .6, 1])
        q = skia.Paint(); q.setShader(sh); c.drawRect(skia.Rect(0, 0, W, H), q); return
    c.drawRect(skia.Rect(0, 0, W, H), fp('#0A1A22', 38))
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [col(BG, 120), col(BG, 0), col(BG, 0), col(BG, 150)], [0, .22, .7, 1])
    q = skia.Paint(); q.setShader(sh); c.drawRect(skia.Rect(0, 0, W, H), q)

def _chart(c, s, t):
    market_bg(c, t)
    pts, t0, dur = s['pts'], s['t0'], s['dur']
    x0, x1, y0, y1 = (150, W - 90, 560, 1130) if V else (220, W - 200, 290, H - 200)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    xmin, xmax = min(xs), max(xs); ymin = s.get('ymin', 0 if min(ys) >= 0 else min(ys)); ymax = s.get('ymax', max(ys) * 1.15)
    X = lambda v: x0 + (x1 - x0) * (v - xmin) / max(xmax - xmin, 1e-9); Y = lambda v: y1 - (y1 - y0) * (v - ymin) / max(ymax - ymin, 1e-9)
    u = ease(K(t, t0 + .4, dur)); xh = xmin + (xmax - xmin) * u
    # axes and labels
    a0 = K(t, t0, .4)
    if V:
        if s['title']: text(c, s['title'].upper(), 70, 400, 84, BEBAS, TXT, a=255 * a0, track=3)
        if s.get('sub'): text(c, s['sub'], 72, 452, 34, OSWALD, MUTED, a=255 * a0, wght=400)
    else:
        text(c, s['title'].upper(), x0, 222, 64, BEBAS, TXT, a=255 * a0, track=3)
        if s.get('sub'): text(c, s['sub'], x0 + tw(s['title'].upper(), 64, BEBAS, 3) + 30, 218, 30, OSWALD, MUTED, a=255 * a0, wght=400)
    for k in range(5):
        v = ymin + (ymax - ymin) * k / 4; yy = Y(v)
        c.drawLine(x0, yy, x1, yy, line(1, '#253241', 200 * a0))
        text(c, s['fmt'](v), x0 - 24, yy + 10, 26, MONO, MUTED, 'right', 230 * a0)
    xt = s['xticks'][::2] if V and len(s['xticks']) > 4 else s['xticks']
    for v in xt: text(c, str(v), X(v), y1 + 52, 26, MONO, MUTED, 'center', 230 * a0)
    # the line up to the head, red after crash_from
    seg = []; prev = None
    for i in range(len(pts) - 1):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        if xa >= xh: break
        f = min(1, (xh - xa) / max(xb - xa, 1e-9)); seg.append(((xa, ya), (xa + (xb - xa) * f, ya + (yb - ya) * f)))
    cf = s.get('crash_from')
    if seg:
        area = skia.Path(); area.moveTo(X(seg[0][0][0]), y1)
        for (pa, pb) in seg: area.lineTo(X(pa[0]), Y(pa[1])); area.lineTo(X(pb[0]), Y(pb[1]))
        area.lineTo(X(seg[-1][1][0]), y1); area.close()
        hc = RED if cf is not None and xh > cf else s['color']
        sh = skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [col(hc, 70), col(hc, 0)]); pa_ = skia.Paint(AntiAlias=True); pa_.setShader(sh); c.drawPath(area, pa_)
        for (pa, pb) in seg:
            h = RED if cf is not None and pa[0] >= cf else s['color']
            c.drawLine(X(pa[0]), Y(pa[1]), X(pb[0]), Y(pb[1]), glow(h, 120, 10)); c.drawLine(X(pa[0]), Y(pa[1]), X(pb[0]), Y(pb[1]), line(6, h))
        hx_, hy_ = seg[-1][1]; hc = RED if cf is not None and hx_ > cf else s['color']
        c.drawCircle(X(hx_), Y(hy_), 18, fp(hc, 90, 8)); c.drawCircle(X(hx_), Y(hy_), 9, fp(TXT))
        lab = s['fmt'](hy_); lw = tw(lab, 40, MONO) + 30; lx = min(X(hx_) + 26, x1 - lw + 60)
        c.drawRoundRect(skia.Rect(lx, Y(hy_) - 68, lx + lw, Y(hy_) - 18), 8, 8, fp(hc, 235)); text(c, lab, lx + 15, Y(hy_) - 30, 40, MONO, BG)
    # event markers appear as the head passes them
    for i, (ev, lab) in enumerate(s.get('events', [])):
        if xh < ev: continue
        b = K(xh, ev, (xmax - xmin) * .04 + 1e-9); yv = next(pp[1] for pp in pts if pp[0] >= ev) if ev <= xmax else pts[-1][1]
        xx = X(ev); c.drawLine(xx, Y(yv) + 16, xx, y1, line(2, GOLD, 160 * b))
        ty = Y(yv) - 110 - (i % 2) * 70
        text(c, lab, xx, ty, 32, OSWALD, GOLD, 'center', 255 * b, wght=600, shadow=.7)

def _number(c, s, t):
    market_bg(c, t, (W / 2, CY), s['color'])
    u = ease_out(K(t, s['t0'] + .25, s['dur'])); v = s['v0'] + (s['value'] - s['v0']) * u
    a = K(t, s['t0'], .3)
    if s.get('label'):
        for i, ln in enumerate(_wrap(s['label'].upper(), 40, MONO, W - 120)): text(c, ln, W / 2, CY - 160 + i * 52 - (40 if V else 0), 40, MONO, s['color'], 'center', 255 * a, 8)
    txt = money(v, s['prefix'], s['decimals']) + s['suffix']
    size = 230
    while tw(txt, size, BEBAS, 4) > W - (90 if V else 160): size -= 8
    if u < 1 and int(t * FPS) % 2 == 0: sfx('tick', t)
    text(c, txt, W / 2, CY + 20 + size * .35, size, BEBAS, TXT, 'center', 255 * a, 4)
    if s.get('sub'):
        b = K(t, s['t0'] + .25 + s['dur'], .4)
        for i, ln in enumerate(_wrap(s['sub'], 46, OSWALD, W - 140, 400)): text(c, ln, W / 2, CY + 220 + i * 58, 46, OSWALD, '#C9D3DD', 'center', 255 * b, wght=400)

def _bars(c, s, t):
    market_bg(c, t)
    items = s['items']; vmax = max(v for _, v, _ in items) or 1; x0, x1 = (70, W - 230) if V else (560, W - 260)
    text(c, s['title'].upper(), 70 if V else 200, 420 if V else 220, 84 if V else 64, BEBAS, TXT, a=255 * K(t, s['t0'], .4), track=3)
    n = len(items); gap = min(190, 640 / n) if V else min(150, (H - 420) / n)
    for i, (name, v, h) in enumerate(items):
        b0 = s['t0'] + .3 + i * s['stagger']; u = ease_out(K(t, b0, 1.0)); a = K(t, b0, .3); y = (540 + i * gap) if V else (330 + i * gap)
        if V: text(c, name.upper(), x0, y - 14, 48, BEBAS, TXT, 'left', 255 * a, 2)
        else: text(c, name.upper(), x0 - 34, y + 44, 48, BEBAS, TXT, 'right', 255 * a, 2)
        c.drawRoundRect(skia.Rect(x0, y, x1, y + 64), 8, 8, fp(PANEL, 255 * a))
        ww = (x1 - x0) * (v / vmax) * u
        if ww > 2: c.drawRoundRect(skia.Rect(x0, y, x0 + ww, y + 64), 8, 8, fp(h, 255 * a)); c.drawRoundRect(skia.Rect(x0, y, x0 + ww, y + 64), 8, 8, glow(h, 60 * a, 14))
        text(c, s['fmt'](v * u), x0 + max(ww, 0) + 22, y + 46, 40, MONO, TXT, a=255 * a)

def _versus(c, s, t):
    market_bg(c, t, (W / 2, CY), GOLD)
    u = ease_out(K(t, s['t0'], .7))
    if V:       # stacked: one card above the other
        for side, (name, big, sub, h) in ((0, s['left']), (1, s['right'])):
            cy = CY + (-225 if side == 0 else 225) + (1 - u) * (-80 if side == 0 else 80); a = K(t, s['t0'] + side * s['delay'], .4)
            c.drawRoundRect(skia.Rect(70, cy - 195, W - 70, cy + 195), 22, 22, fp(PANEL, 235 * a)); c.drawRoundRect(skia.Rect(70, cy - 195, W - 70, cy + 195), 22, 22, line(3, h, 220 * a))
            text(c, name.upper(), W / 2, cy - 105, 56, BEBAS, h, 'center', 255 * a, 6)
            size = 190
            while tw(big, size, BEBAS, 2) > W - 220: size -= 10
            text(c, big, W / 2, cy + 75, size, BEBAS, TXT, 'center', 255 * a, 2)
            text(c, sub, W / 2, cy + 150, 36, OSWALD, '#C9D3DD', 'center', 255 * a, wght=400)
        b = K(t, s['t0'] + .5, .4)
        c.drawCircle(W / 2, CY, 60, fp(BG, 255 * b)); c.drawCircle(W / 2, CY, 60, line(3, GOLD, 255 * b)); text(c, 'VS', W / 2, CY + 20, 54, BEBAS, GOLD, 'center', 255 * b, 2)
        return
    for side, (name, big, sub, h) in ((0, s['left']), (1, s['right'])):
        cx = W * (.27 if side == 0 else .73) + (1 - u) * (-80 if side == 0 else 80); a = K(t, s['t0'] + side * s['delay'], .4)
        c.drawRoundRect(skia.Rect(cx - 380, 270, cx + 380, 830), 22, 22, fp(PANEL, 235 * a)); c.drawRoundRect(skia.Rect(cx - 380, 270, cx + 380, 830), 22, 22, line(3, h, 220 * a))
        text(c, name.upper(), cx, 380, 58, BEBAS, h, 'center', 255 * a, 6)
        size = 220
        while tw(big, size, BEBAS, 2) > 680: size -= 10
        text(c, big, cx, 610, size, BEBAS, TXT, 'center', 255 * a, 2)
        text(c, sub, cx, 730, 38, OSWALD, '#C9D3DD', 'center', 255 * a, wght=400)
    b = K(t, s['t0'] + .5, .4)
    c.drawCircle(W / 2, 550, 60, fp(BG, 255 * b)); c.drawCircle(W / 2, 550, 60, line(3, GOLD, 255 * b)); text(c, 'VS', W / 2, 570, 54, BEBAS, GOLD, 'center', 255 * b, 2)

def _statement(c, s, t):
    market_bg(c, t, (W / 2, CY), s['color'])
    a = K(t, s['t0'], .35); u = ease_out(K(t, s['t0'], .6))
    lines = _wrap(s['line'].upper(), s['size'], BEBAS, W - (110 if V else 260))
    y = CY + 40 - (len(lines) - 1) * s['size'] * .5
    for i, ln in enumerate(lines): text(c, ln, W / 2, y + i * s['size'] * .98 + 20 * (1 - u), s['size'], BEBAS, TXT, 'center', 255 * a, 4)
    c.drawLine(W / 2 - 220 * u, y + (len(lines) - 1) * s['size'] * .98 + 50, W / 2 + 220 * u, y + (len(lines) - 1) * s['size'] * .98 + 50, line(5, s['color'], 255 * a))
    if s.get('sub'):
        for i, ln in enumerate(_wrap(s['sub'], 44, OSWALD, W - 140, 400)): text(c, ln, W / 2, y + (len(lines) - 1) * s['size'] * .98 + 130 + i * 56, 44, OSWALD, '#C9D3DD', 'center', 255 * a, wght=400)


def _clip_layout(s):
    """lay out a recreated clipping once: returns (card w, card h, draw ops, highlight boxes) in card pixels (origin top-left)"""
    if '_lay' in s: return s['_lay']
    cw = 820 if V else 1240; pad = 60 if V else 76; x = pad; y = pad; ops = []
    if s.get('outlet'):
        ops.append(('t', s['outlet'], x, y + 44, 46, PLAYFAIR, '#141414', 800)); y += 64
        if s.get('dateline'): ops.append(('t', s['dateline'].upper(), x, y + 26, 22, MONO, '#6B6B6B', None)); y += 40
        ops.append(('r', x, y + 8, cw - pad, y + 10)); y += 34
    if s.get('headline'):
        for ln in _wrap(s['headline'], 62, PLAYFAIR, cw - 2 * pad, 700): ops.append(('t', ln, x, y + 58, 62, PLAYFAIR, '#111111', 700)); y += 74
        y += 22
    size, lh = 42, 58; words = (s.get('body') or '').split(); hit = set()
    ph = [w.lower().strip('.,;:"\'()') for w in (s.get('phrase') or '').split()]
    low = [w.lower().strip('.,;:"\'()') for w in words]
    for i in range(len(words) - len(ph) + 1):
        if ph and low[i:i + len(ph)] == ph: hit = set(range(i, i + len(ph))); break
    if ph and not hit: raise ValueError(f'clipping: phrase "{s["phrase"]}" is not in the body text (it must be copied exactly)')
    boxes = []; cx = x; sp = tw(' ', size, BODY, 0, 500); line_box = None
    for i, w in enumerate(words):
        ww = tw(w, size, BODY, 0, 500)
        if cx + ww > cw - pad and cx > x:
            if line_box: boxes.append(line_box); line_box = None
            cx = x; y += lh
        ops.append(('t', w, cx, y + 44, size, BODY, '#1C1C1C', 500))
        if i in hit:
            b = (cx - 6, y + 4, cx + ww + 6, y + 56)
            line_box = b if line_box is None else (line_box[0], line_box[1], b[2], line_box[3])
        elif line_box: boxes.append(line_box); line_box = None
        cx += ww + sp
    if line_box: boxes.append(line_box)
    s['_lay'] = (cw, y + lh + pad - 10, ops, boxes); return s['_lay']

def _clipping(c, s, t, build):
    """a source clipping: a screenshot (or a recreated article) on a light card, tilted, pushing in on the marked line
    while a yellow marker sweeps across it"""
    market_bg(c, t)
    t0, at = s['t0'], s['at']
    if s.get('src'):
        im, _, _ = _art(s['src'], False, build); iw, ih = im.width(), im.height()
        sc = min(W * (.9 if V else .66) / iw, H * (.42 if V else .74) / ih); cw, ch = iw * sc, ih * sc; ops = None
        boxes = [(a * cw, b * ch, cc * cw, d * ch) for a, b, cc, d in s['mark']]
    else:
        lw, lh, ops, bx = _clip_layout(s); sc = min(W * (.9 if V else .66) / lw, H * (.42 if V else .78) / lh, 1.15 if V else 1.0); cw, ch = lw * sc, lh * sc
        boxes = [tuple(v * sc for v in b) for b in bx]
    # camera: card slides in, then pushes toward the marked line as the narrator reaches it
    a = K(t, t0, .4); ui = ease_out(K(t, t0, .55))
    k = ease(K(t, at - .35, 1.1)) if (boxes and s['zoom'] > 1) else 0
    if boxes:
        hx = (min(b[0] for b in boxes) + max(b[2] for b in boxes)) / 2 - cw / 2; hy = (min(b[1] for b in boxes) + max(b[3] for b in boxes)) / 2 - ch / 2
    else: hx = hy = 0
    span = (max(b[2] for b in boxes) - min(b[0] for b in boxes)) if boxes else cw
    zmax = min(s['zoom'], (W * (.92 if V else .86)) / max(span, 1))            # never push so far that the marked line leaves the frame
    Z = (1 + .035 * K(t, t0, 8)) * lerp(1, max(1, zmax), k)
    c.saveLayerAlpha(None, int(255 * a)); c.save()
    c.translate(W / 2, CY + 14 + 70 * (1 - ui)); c.scale(Z, Z); c.rotate(s['rot'] * (1 - .55 * k) - 3 * (1 - ui)); c.translate(-hx * k, -hy * k)
    x0, y0 = -cw / 2, -ch / 2
    c.drawRect(skia.Rect(x0 + 18, y0 + 26, x0 + cw + 18, y0 + ch + 26), fp('#000000', 160, 34))
    c.drawRect(skia.Rect(x0 - 14, y0 - 14, x0 + cw + 14, y0 + ch + 14), fp('#F3F0E8'))
    if ops is None:
        c.drawImageRect(im, skia.Rect(x0, y0, x0 + cw, y0 + ch), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    else:
        c.save(); c.translate(x0, y0); c.scale(sc, sc)
        for op in ops:
            if op[0] == 't': _doc.text(c, op[1], op[2], op[3], op[4], op[5], op[6], 'left', 255, 0, op[7])
            else: c.drawRect(skia.Rect(op[1], op[2], op[3], op[4]), fp('#222222'))
        c.restore()
    # the marker: sweeps line by line, a little uneven like a real highlighter, multiplied so the text stays dark
    total = sum(b[2] - b[0] for b in boxes) or 1; done = (t - at) / s['dur'] * total if t >= at else -1
    if 0 <= done and int((t - at) * FPS) == 0: sfx('scratch', at)
    acc = 0
    for i, (bx0, by0, bx1, by1) in enumerate(boxes):
        w = bx1 - bx0; f = max(0, min(1, (done - acc) / w)); acc += w
        if f <= 0: break
        p = skia.Paint(AntiAlias=True, Color=col(s['color'], 235)); p.setBlendMode(skia.BlendMode.kMultiply)
        r = random.Random(i * 7 + 3); j = (by1 - by0) * .08
        path = skia.Path(); path.moveTo(x0 + bx0, y0 + by0 + r.uniform(-j, j)); path.lineTo(x0 + bx0 + w * f, y0 + by0 + r.uniform(-j, j))
        path.lineTo(x0 + bx0 + w * f, y0 + by1 + r.uniform(-j, j)); path.lineTo(x0 + bx0, y0 + by1 + r.uniform(-j, j)); path.close()
        c.drawPath(path, p)
    c.restore(); c.restore()
    # source label, bottom left (recreated clippings say so)
    b = K(t, t0 + .3, .4)
    if s.get('source') and b > 0:
        lab = 'SOURCE'; val = s['source']; lw_ = tw(lab, 22, MONO, 3) + 24; vw = tw(val, 30, MONO) + 30; xx, yy = (70, H - 470) if V else (96, H - 78)
        c.drawRoundRect(skia.Rect(xx, yy - 42, xx + lw_, yy + 6), 6, 6, fp(GREEN, 240 * b)); text(c, lab, xx + 12, yy - 10, 22, MONO, BG, a=255 * b, track=3)
        c.drawRoundRect(skia.Rect(xx + lw_, yy - 42, xx + lw_ + vw, yy + 6), 6, 6, fp('#05080B', 225 * b)); text(c, val, xx + lw_ + 15, yy - 8, 30, MONO, TXT, a=255 * b)
        sub = s.get('note') or ''
        if ops is not None: sub = (sub + ' · ' if sub else '') + 'quoted text, layout recreated'
        if sub: text(c, sub, xx, yy + 40, 24, MONO, '#AEB8C2', a=230 * b, shadow=.8)


def _flash(c, s, t, build):
    """rapid thriller montage: a new photo every `every` seconds with a punch-in and a white flash"""
    k = int((t - s['t0']) / s['every']); src = s['srcs'][k % len(s['srcs'])]; lt = (t - s['t0']) - k * s['every']
    im, _, _ = _art(src, False, build); z = 1.12 + .1 * (lt / s['every'])
    cx, cy, ww, wh = _window(im, .5, .5, z)
    gp = skia.Paint(); gp.setColorFilter(_GRADE); c.saveLayer(None, gp); _blit(c, im, cx, cy, ww, wh); c.restore()
    c.drawRect(skia.Rect(0, 0, W, H), fp('#0A1A22', 60))
    if lt < 2 / FPS: c.drawRect(skia.Rect(0, 0, W, H), fp('#FFFFFF', 150)); sfx('pop', t)

# ================================================================ the timeline of shots
class Fin(_doc.Doc):
    """Shots in time order with quick crossfades. Same interface as Doc (film.py renders it in parallel chunks)."""
    def __init__(self, film, xfade=.45, chapter_subs=None, thriller=True, captions=None):
        super().__init__(film, xfade=xfade, chapter_subs=chapter_subs)
        # word-by-word captions: on by default in vertical (Shorts), off in the landscape film
        self.caps = _caption_groups(film.words) if (V if captions is None else captions) else None
        # thriller cold open: everything before the [TITLE: ...] pause gets hard cuts, glitches, letterbox bars and a red pulse
        tt = [ch for ch in film.chapters if str(ch[1]).startswith('TITLE:')]
        self.cold = (tt[0][0] if tt else 0.0) if thriller else 0.0
        if self.cold > 0: film._tension = [(0.0, self.cold)]

    def flash(self, t0, srcs, every=.32):
        """a fast photo montage (thriller opens): a new photo every `every` seconds"""
        self._add(t0, 'flash', srcs=[os.path.join(self.film.dir, x) for x in srcs], every=every)

    def photo(self, t0, src, frm=(.5, .5, 1.0), to=None, depth=False, card=None, label=None):
        """a real photo. Full screen with a slow push (frm/to = (focus x, focus y, zoom)), or card=x (0..1) to show it whole
        on a floating white card over the dark background (logos on signs, documents, screenshots of filings), with a label."""
        to = to or (frm[0], frm[1], frm[2] * 1.08)
        self._add(t0, 'photo', src=os.path.join(self.film.dir, src), frm=frm, to=to, depth=depth, card=card, label=label)

    def footage(self, t0, src, start=0.0, speed=1.0, frm=(.5, .5, 1.0), to=None, bw=False):
        """real archive footage, full screen (a clip cut by scripts/footage.py: media/shopping_1957.mp4). It plays from `start`
        seconds into the clip at `speed` (0.5 = slow motion, good for stretching a short clip); if the shot lasts longer than
        the clip, the last frame holds. frm/to = (focus x, focus y, zoom) for a slow push, like photo. Give it a credit_line
        like a photo, and a tag with the place and year so nobody mistakes era footage for the company itself.
        bw=True: black and white with grain and flicker, for a STOCK clip used in a part of the story set before about 1970, so it sits
        with the real archive film. Real archive footage keeps its own look. A stock clip never gets a date or place tag."""
        to = to or (frm[0], frm[1], frm[2] * 1.05)
        self._add(t0, 'footage', src=os.path.join(self.film.dir, src), start=start, speed=speed, frm=frm, to=to, bw=bw)

    def clipping(self, t0, src=None, mark=(), at=None, source=None, note=None, headline=None, body=None, phrase=None,
                 outlet=None, dateline=None, rot=-2.2, zoom=1.5, dur=.9, color=MARK):
        """A source clipping: proof on screen. Two ways:
        - a real screenshot (article, SEC filing, court record, tweet): src='media/clip_10k.png' and mark = the highlighted
          line(s) as boxes in fractions of the image [(x0, y0, x1, y1), ...], one box per line (read them off
          `python3 scripts/grid.py media/clip_10k.png`, which draws a labelled grid on a copy).
        - no screenshot: outlet, dateline, headline and body (the exact published text, never invented) and phrase
          (the words to highlight, copied exactly from body). It is labelled "layout recreated" on screen.
        at: when the marker starts (cue it on the narrator saying those words: T('six billion')); dur: how long it takes.
        source: 'sec.gov' / 'nytimes.com'; note: 'Form 10-K, 2004'. The card pushes in on the line (zoom) as it is marked."""
        if src is None and not body: raise ValueError('clipping needs a screenshot (src) or the exact published text (body)')
        self._add(t0, 'clipping', src=os.path.join(self.film.dir, src) if src else None, mark=list(mark), at=at if at is not None else t0 + .8,
                  source=source, note=note, headline=headline, body=body, phrase=phrase, outlet=outlet, dateline=dateline, rot=rot, zoom=zoom, dur=dur, color=color)

    def chart(self, t0, pts, title, fmt=lambda v: short(v * 1e9), xticks=None, events=(), crash_from=None, color=GREEN, dur=3.5, sub=None, ymin=None, ymax=None):
        """a line chart that draws itself over dur seconds. pts: [(year, value), ...]; fmt(value) -> label;
        events: [(year, 'Netflix launches')]; crash_from: year after which the line turns red."""
        kw = dict(pts=pts, title=title, fmt=fmt, xticks=xticks or [p[0] for p in pts], events=events, crash_from=crash_from, color=color, dur=dur, sub=sub)
        if ymin is not None: kw['ymin'] = ymin
        if ymax is not None: kw['ymax'] = ymax
        self._add(t0, 'chart', **kw)

    def number(self, t0, value, prefix='$', suffix='', label=None, sub=None, dur=1.6, v0=0, decimals=0, color=GREEN):
        """a big counter rolling up (or down, with v0 > value) to value"""
        self._add(t0, 'number', value=value, prefix=prefix, suffix=suffix, label=label, sub=sub, dur=dur, v0=v0, decimals=decimals, color=color)

    def bars(self, t0, items, title, fmt=lambda v: f'{v:,.0f}', stagger=.5):
        """horizontal bars growing one after another. items: [('Blockbuster', 9000, GREEN), ...]"""
        self._add(t0, 'bars', items=items, title=title, fmt=fmt, stagger=stagger)

    def versus(self, t0, left, right, delay=.6):
        """split screen: left/right = ('NETFLIX', '$50M', 'asking price', RED)"""
        self._add(t0, 'versus', left=left, right=right, delay=delay)

    def statement(self, t0, line_, sub=None, color=GREEN, size=180):
        """one big line in capitals (the key idea of a paragraph)"""
        self._add(t0, 'statement', line=line_, sub=sub, color=color, size=size)

    def scene(self, t0, fn):
        """fn(c, t, u): draw anything on the 1920x1080 frame over the dark background"""
        self._add(t0, 'scene', fn=fn, paper=False)

    def _draw_shot(self, c, i, t):
        s = self.shots[i]; t0, t1 = s['t0'], self._end(i) + self.xf; u = max(0, min(1, (t - t0) / max(t1 - t0, .01))); e = ease(u) * .85 + u * .15
        k = s['kind']
        if k == 'photo': _photo(c, s, t, e, self.film.build)
        elif k == 'footage': _footage(c, s, t, e)
        elif k == 'chart': _chart(c, s, t)
        elif k == 'number': _number(c, s, t)
        elif k == 'bars': _bars(c, s, t)
        elif k == 'versus': _versus(c, s, t)
        elif k == 'statement': _statement(c, s, t)
        elif k == 'flash': _flash(c, s, t, self.film.build)
        elif k == 'clipping': _clipping(c, s, t, self.film.build)
        else: market_bg(c, t); s['fn'](c, t, u)

    def draw(self, c, t, f, view):
        c.clear(col(BG)); i = max([k for k, s in enumerate(self.shots) if s['t0'] <= t] or [0])
        cold = t < self.cold; xf = .1 if cold else self.xf
        if i > 0 and t < self.shots[i]['t0'] + xf:
            self._draw_shot(c, i - 1, t)
            c.saveLayerAlpha(None, int(255 * ease(K(t, self.shots[i]['t0'], xf)))); self._draw_shot(c, i, t); c.restore()
        else: self._draw_shot(c, i, t)
        if cold: self._thriller(c, t, self.shots[i]['t0'] if i > 0 else -9)
        finish(c, t, .7 if cold else .55)

    def _thriller(self, c, t, cut):
        # red pulse on the heartbeat (every 1.1 s), a glitch for 0.15 s after every cut, letterbox bars
        hb = (t % 1.1) / 1.1; pulse = math.exp(-hb * 9) + .6 * math.exp(-max(0, hb - .16) * 9) * (hb > .16)
        sh = skia.GradientShader.MakeRadial((W / 2, H / 2), W * .72, [col(RED, 0), col(RED, 0), col(RED, 70 * pulse)], [0, .55, 1])
        p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect(0, 0, W, H), p)
        g = t - cut
        if 0 <= g < .15:
            sf_ = c.getSurface()
            if sf_ is not None:
                img = sf_.makeImageSnapshot(); amt = (1 - g / .15) * 18; r = random.Random(int(t * 100))
                for cf, dx in ((skia.ColorFilters.Matrix([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, .55, 0]), amt), (skia.ColorFilters.Matrix([0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, .55, 0]), -amt)):
                    q = skia.Paint(); q.setColorFilter(cf); q.setBlendMode(skia.BlendMode.kScreen); c.drawImage(img, dx, 0, skia.SamplingOptions(), q)
                for _ in range(5):
                    y0 = r.uniform(0, H); hh = r.uniform(8, 60); dx = r.uniform(-60, 60) * (1 - g / .15)
                    c.save(); c.clipRect(skia.Rect(0, y0, W, y0 + hh)); c.drawImage(img, dx, 0); c.restore()
        bar = (0 if V else 132) * (1 - K(t, self.cold - .1, .3))
        c.drawRect(skia.Rect(0, 0, W, bar), fp('#000000')); c.drawRect(skia.Rect(0, H - bar, W, H), fp('#000000'))

    @property
    def over(self):
        def chap(c, t):
            for ch in self.film.chapters:
                if str(ch[1]).startswith('TITLE:'): title_slam(c, t, ch[0] + .05, ch[3] + .3, ch[1][6:], ch[2])
                else: chapter_card(c, t, ch[0] + .05, ch[3] + .25, ch[1], ch[2], self.chapter_subs.get(ch[2]))
        lay = [lambda c, t: [o(c, t) for o in self._screen], chap]
        if self.caps: lay.append(lambda c, t: captions(c, t, self.caps))
        return lay
