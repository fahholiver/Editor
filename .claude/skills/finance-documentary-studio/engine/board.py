"""Documentary worlds with a camera that travels and never cuts.

A film is a Reel of Worlds. Each World is a big 2D place with its own surface (a dark desk, a blueprint,
a case board) and items placed on it: real footage and photos in white frames, animated noir scenes,
papers (newspaper, map, ledger, calendar...), and free drawing (big numbers, strings, stamps).
The camera glides between items and dives into them until they fill the screen.

Passing from one world to the next is seamless: the camera dives into an item in world A until it fills the
screen exactly, and world B starts dived into an item with the same content (same clip, same scene).
So "the blueprint fills into the room", "the footage becomes a photo on the FBI's board" and
"a suspect card opens into the interrogation room" are all one unbroken move.

    from board import *
    film = Film(__file__, vo='vo.wav', words='words.json', mood='noir')
    T = film.cue
    desk = World(film, 'desk'); plan = World(film, 'blueprint'); case = World(film, 'board')
    desk.item(0, 'clip', 'truck', 900, 900, 1280, 720, src='clips/truck.mp4', credit='FBI film / National Archives')
    desk.dive(0, 'truck')
    ...
    Reel(film, [(0, desk), (31.0, plan), (54.0, case), (63.7, desk)]).render_chunks(8)
    film.main()
See references/board.md.
"""
import os, math, subprocess, random
import numpy as np, skia
from film import *
from world import _once
import world

# ------------------------------------------------------------------ type: the documentary font set
_FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts') + os.sep
def _tf(n):
    p = _FD + n
    return skia.Typeface.MakeFromFile(p) if os.path.exists(p) else KALAM
BEBAS = _tf('BebasNeue-Regular.ttf')        # chapter cards, titles
OSWALD = _tf('Oswald-Variable.ttf')         # big numbers, name tags
ELITE = _tf('SpecialElite-Regular.ttf')     # typewritten documents
MONO = _tf('IBMPlexMono-Medium.ttf')        # place + time, labels, credits
STENCIL = _tf('StardosStencil-Bold.ttf')    # stamps (verdicts only)
PLAYFAIR = _tf('PlayfairDisplay-Variable.ttf')  # quotes, newspaper mastheads
COURIER = _tf('CourierPrime-Bold.ttf')      # official headings
BONE, AMBER, BLOOD, ASH = '#EDE8DC', '#E0B04A', '#B3242B', '#9A968C'


def txt(c, s, x, y, size, font=None, v=BONE, align='left', a=1.0, track=0):
    """Plain documentary text (no skew, no outline). Returns the width."""
    f = skia.Font(font or MONO, size); w = f.measureText(s) + track * max(len(s) - 1, 0)
    ox = -w / 2 if align == 'center' else -w if align == 'right' else 0
    if track:
        cx = x + ox
        for ch in s: c.drawString(ch, cx, y, f, fp(v, 255 * a)); cx += f.measureText(ch) + track
    else: c.drawString(s, x + ox, y, f, fp(v, 255 * a))
    return w


def tw(s, size, font=None): return skia.Font(font or MONO, size).measureText(s)


def type_on(c, t, t0, s, x, y, size, v=BONE, font=None, align='left', cps=24, a=1.0):
    """Typewriter reveal with a blinking block cursor (place + time lines, statements)."""
    if t0 is None or t < t0: return
    n = min(len(s), int((t - t0) * cps) + 1)
    if n < len(s): _once('type', t, t0)
    font = font or MONO; full = tw(s, size, font); ox = -full / 2 if align == 'center' else -full if align == 'right' else 0
    txt(c, s[:n], x + ox, y, size, font, v, a=a)
    if n < len(s) and int(t * 4) % 2 == 0:
        cx = x + ox + tw(s[:n], size, font) + 6; c.drawRect(skia.Rect(cx, y - size * .78, cx + size * .5, y + size * .12), fp(v, 200 * a))


def big(c, t, t0, s, x, y, size=200, v=BONE, font=None, align='center', rot=0, until=None):
    """Big number or key word that settles in (Oswald by default)."""
    if t0 is None or t < t0 or (until and t > until + .4): return
    _once('pop', t, t0)
    u = K(t, t0, .5); sc = 1.10 - .10 * ease_out(u); a = min(1, u * 2.5)
    if until: a *= 1 - K(t, until, .4)
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(sc, sc); txt(c, s, 0, 0, size, font or OSWALD, v, align, a); c.restore()


CHAPTER_STYLE = dict(font=None, size=190, rule=None, small=None, y=600, track=0)   # history.py switches this to Cinzel + gold


def chapter(c, t, t0, num, title, dur=2.6):
    """Screen-space chapter card: small mono line + big title + a rule, over a dark band."""
    if t0 is None or not (t0 <= t < t0 + dur): return
    st = CHAPTER_STYLE; a = min(1, (t - t0) * 3, (t0 + dur - t) * 3)
    c.drawRect(skia.Rect(0, 330, W, 750), fp((0, 0, 0), 150 * a, blur=40))
    txt(c, num, W / 2, 440, 40, MONO, st.get('small') or ASH, 'center', a, track=10)
    size = st['size']; f = st.get('font') or BEBAS
    while tw(title, size, f) + st.get('track', 0) * len(title) > W - 160: size -= 6
    txt(c, title, W / 2, st.get('y', 600), size, f, BONE, 'center', a, track=st.get('track', 0))
    u = ease_out(K(t, t0 + .2, .6)); c.drawLine(W / 2 - 200 * u, 650, W / 2 + 200 * u, 650, ink(5, st.get('rule') or BLOOD, 255 * a))


def place_tag(c, t, t0, l1, l2, until=None):
    """Bottom-left place + time, typed on (screen space)."""
    if t0 is None or t < t0 or (until and t > until + .3): return
    a = 1 - K(t, until, .3) if until else 1
    c.drawRect(skia.Rect(40, H - 230, 1150, H - 50), fp((0, 0, 0), 150 * a, blur=26))
    type_on(c, t, t0, l1, 90, H - 150, 48, BONE, a=a)
    type_on(c, t, t0 + len(l1) / 24 + .15, l2, 90, H - 88, 48, AMBER, a=a)


def name_tag(c, t, t0, name, role, x=90, y=900, until=None):
    """Name tag: red bar, Oswald name, mono role."""
    if t0 is None or t < t0 or (until and t > until + .3): return
    _once('paper', t, t0); u = ease_out(K(t, t0, .45)); a = u * (1 - (K(t, until, .3) if until else 0))
    c.drawRect(skia.Rect(x - 30, y - 100, x + 30 + max(tw(name, 78, OSWALD), tw(role, 32)) + 40, y + 70), fp((0, 0, 0), 140 * a, blur=20))
    c.drawRect(skia.Rect(x, y - 80, x + 10, y + 50), fp(BLOOD, 255 * a))
    txt(c, name, x + 34 - 30 * (1 - u), y, 78, OSWALD, BONE, a=a); txt(c, role, x + 36, y + 46, 32, MONO, ASH, a=a)


def stamp2(c, t, t0, s, x, y, rot=-9, size=120, v=BLOOD):
    """Rubber stamp in stencil type that slams in (verdicts only)."""
    if t0 is None or t < t0: return
    _once('thud', t, t0); u = (t - t0) / .7
    sc = 2.2 - 1.2 * ease_out(min(u * 4, 1)); a = min(u * 6, 1); w = tw(s, size, STENCIL)
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(sc, sc)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-w / 2 - 44, -size * .95, w / 2 + 44, size * .32), 14, 14), ink(size * .09, v, 255 * a))
    txt(c, s, 0, 0, size, STENCIL, v, 'center', a); c.restore()


def strike(c, t, t0, x0, y, x1, v=BLOOD, w=12):
    if t0 is None or t < t0: return
    _once('scratch', t, t0)
    u = ease_out(K(t, t0, .3)); c.drawLine(x0 - 10, y + 4, lerp(x0, x1 + 10, u), y - 6 * u, ink(w, v))


def clock_line(c, t, a, b, t_from, t_to, label_from='7:10 PM', label_to='7:30 PM', until=None):
    """Screen-space clock bar that runs from t_from to t_to (minutes after 7:00)."""
    if t < a or (until and t > until + .3): return
    al = min(1, (t - a) * 3) * (1 - (K(t, until, .3) if until else 0))
    x0, x1, y = 300, W - 300, H - 80; u = ease(K(t, a, b - a))
    c.drawRect(skia.Rect(240, y - 110, W - 240, y + 40), fp((0, 0, 0), 120 * al, blur=24))
    c.drawLine(x0, y, x1, y, ink(4, '#8A8678', 255 * al)); c.drawLine(x0, y, lerp(x0, x1, u), y, ink(8, AMBER, 255 * al))
    c.drawCircle(lerp(x0, x1, u), y, 12, fp(AMBER, 255 * al))
    txt(c, label_from, x0, y - 26, 34, MONO, BONE, a=al)
    if u < .62: txt(c, label_to, x1, y - 26, 34, MONO, BONE, 'right', al)
    m = int(round(lerp(t_from, t_to, u)))
    if u < .88: txt(c, f'7:{m:02d} PM', lerp(x0, x1, u), y - 34, 46, MONO, AMBER, 'center', al)
    else: txt(c, label_to, x1, y - 26, 34, MONO, AMBER, 'right', al)


# ------------------------------------------------------------------ media
_CLIPS = {}
def clip_frames(path, width=1280):
    if path in _CLIPS: return _CLIPS[path]
    probe = subprocess.run([FFMPEG, '-v', 'error', '-i', path, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
    im = skia.Image.MakeFromEncoded(probe); h = int(round(width * im.height() / im.width() / 2) * 2)
    raw = subprocess.run([FFMPEG, '-v', 'error', '-i', path, '-vf', f'fps={FPS},scale={width}:{h}', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], capture_output=True).stdout
    n = len(raw) // (width * h * 4); arr = np.frombuffer(raw, np.uint8)[:n * width * h * 4].reshape(n, h, width, 4)
    _CLIPS[path] = (arr, width, h); return _CLIPS[path]


def clip_image(path, k):
    arr, w, h = clip_frames(path); k = int(max(0, min(k, len(arr) - 1)))
    return skia.Image.fromarray(np.ascontiguousarray(arr[k]), colorType=skia.kRGBA_8888_ColorType)


_IMG = {}
def image(path):
    if path not in _IMG: _IMG[path] = skia.Image.open(path)
    return _IMG[path]


def _cover(c, img, w, h, zoom=1.0, fx=.5, fy=.5):
    iw, ih = img.width(), img.height(); s = max(w / iw, h / ih) * zoom; dw, dh = iw * s, ih * s
    ox, oy = (0.5 - fx) * (dw - w), (0.5 - fy) * (dh - h)
    c.drawImageRect(img, skia.Rect(-dw / 2 + ox, -dh / 2 + oy, dw / 2 + ox, dh / 2 + oy), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))


def grain(c, x0, y0, x1, y1, f, a=34):
    r = np.random.default_rng(f % 997); n = (r.random((90, 160)) * 255).astype(np.uint8)
    img = skia.Image.fromarray(np.dstack([n, n, n, np.full_like(n, a)]), colorType=skia.kRGBA_8888_ColorType)
    c.drawImageRect(img, skia.Rect(x0, y0, x1, y1), skia.SamplingOptions())


def archive_matrix(tone='warm'):
    s = .45; r, g, b = (1.06, 1.0, .9) if tone == 'warm' else (.92, 1.0, 1.08) if tone == 'cold' else (1, 1, 1)
    lum = (.3 * (1 - s), .59 * (1 - s), .11 * (1 - s)); m = []
    for i, k in enumerate((r, g, b)):
        row = [lum[0] * k, lum[1] * k, lum[2] * k, 0, .03]; row[i] += s * k; m += row
    return m + [0, 0, 0, 1, 0]
world_bw = archive_matrix

# noir grade for animated scenes: muted, cold, deeper blacks
NOIR = GRADE = skia.ColorFilters.Matrix([.55, .38, .07, 0, -.01, .2, .72, .08, 0, -.005, .2, .38, .5, 0, .01, 0, 0, 0, 1, 0])

# noir cast: muted coats; the gang stays faceless (caps + masks); only named people get faces
NOIR_GANG = dict(skin='#BDB3A2', skin_d='#9C927F', suit='#1B1E26', suit_d='#111318', shirt='#1B1E26', tie='#1B1E26',
                 hat='cap', hat_col='#0E0F14', hat_band='#08090C', mask='#CFC8B4')
NOIR_GANG2 = dict(NOIR_GANG, suit='#23252B', suit_d='#16171B', mask='#C2BBA6')


# ------------------------------------------------------------------ world surfaces
def surface_desk(c, view):
    x0, y0, x1, y1 = view
    c.drawRect(skia.Rect(x0 - 50, y0 - 50, x1 + 50, y1 + 50), fp('#231A13'))
    step = 220; k0 = int(y0 // step) - 1
    for k in range(k0, int(y1 // step) + 2):         # long wood planks with faint grain
        y = k * step; r = random.Random(k)
        c.drawRect(skia.Rect(x0 - 50, y, x1 + 50, y + step - 4), fp(r.choice(('#2A2018', '#271D15', '#2D2219'))))
        for g in range(5): yy = y + 20 + g * 40 + r.uniform(-8, 8); c.drawLine(x0 - 50, yy, x1 + 50, yy + r.uniform(-6, 6), ink(2, '#33271D'))
    for (lx, ly, r) in ((1500, 1200, 2600), (5200, 1600, 2800), (3000, 4000, 2600), (6800, 4200, 2600)):
        if lx + r > x0 and lx - r < x1 and ly + r > y0 and ly - r < y1:
            c.drawCircle(lx, ly, r, sp(radial(lx, ly, r, [hx('#6A4A2A', 70), hx('#6A4A2A', 0)])))


def surface_blueprint(c, view):
    x0, y0, x1, y1 = view
    c.drawRect(skia.Rect(x0 - 50, y0 - 50, x1 + 50, y1 + 50), fp('#0F2A4A'))
    for step, col_ in ((40, '#163558'), (200, '#1E4370')):
        gx = int(x0 // step) * step
        while gx < x1 + step: c.drawLine(gx, y0 - 50, gx, y1 + 50, ink(1.2, col_)); gx += step
        gy = int(y0 // step) * step
        while gy < y1 + step: c.drawLine(x0 - 50, gy, x1 + 50, gy, ink(1.2, col_)); gy += step


def _clutter_list(seed=11, n=70, wmax=9000, hmax=5800):
    r = random.Random(seed); out = []
    for i in range(n):
        out.append((r.uniform(200, wmax - 200), r.uniform(200, hmax), r.uniform(260, 620), r.uniform(200, 460), r.uniform(-9, 9),
                    r.choice(('#3A3F4C', '#454A55', '#3B3A36', '#2F3A48')), r.randint(3, 9), r.random() < .3))
    return out
_CLUTTER = _clutter_list()


def surface_board(c, view):
    x0, y0, x1, y1 = view
    c.drawRect(skia.Rect(x0 - 50, y0 - 50, x1 + 50, y1 + 50), fp('#2A2119'))
    r = random.Random(4)
    for i in range(int((x1 - x0) * (y1 - y0) / 90000)):
        c.drawCircle(r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(1, 3), fp('#382C21'))
    for (x, y, w, h, rot, v, nl, ph) in _CLUTTER:
        if x + w < x0 or x - w > x1 or y + h < y0 or y - h > y1: continue
        c.save(); c.translate(x, y); c.rotate(rot)
        c.drawRect(skia.Rect(-w / 2 + 8, -h / 2 + 12, w / 2 + 12, h / 2 + 16), fp((0, 0, 0), 80, blur=10))
        c.drawRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), fp('#4A4236' if not ph else '#3A3530'))
        if ph: c.drawRect(skia.Rect(-w / 2 + 24, -h / 2 + 24, w / 2 - 24, h / 2 - 50), fp('#24221F'))
        else:
            for k in range(nl): yy = -h / 2 + 40 + k * (h - 60) / max(nl, 1); c.drawLine(-w / 2 + 30, yy, w / 2 - 30 - (k % 3) * 40, yy, ink(5, '#625948'))
        c.drawCircle(0, -h / 2 + 14, 9, fp('#6A2A30')); c.restore()

SURFACES = dict(desk=surface_desk, blueprint=surface_blueprint, board=surface_board)


def pin(c, x, y, v='#B3242B'):
    c.drawCircle(x + 4, y + 6, 15, fp((0, 0, 0), 120, blur=4)); circ(c, x, y, 14, v, 3); c.drawCircle(x - 4, y - 4, 4, fp('#FFFFFF', 160))


def string(c, t, t0, x0, y0, x1, y1, dur=.6, v='#9E2028'):
    if t0 is None or t < t0: return
    u = ease_out(K(t, t0, dur)); p = skia.Path(); p.moveTo(x0, y0)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + 60
    p.quadTo(lerp(x0, mx, u), lerp(y0, my, u), lerp(x0, x1, u), lerp(y0, y1, u)); c.drawPath(p, ink(5, v)); pin(c, x0, y0)
    if u >= 1: pin(c, x1, y1)


# ------------------------------------------------------------------ worlds
class Item:
    def __init__(self, name, t0, kind, x, y, w, h, kw):
        self.name, self.t0, self.kind, self.x, self.y, self.w, self.h, self.kw = name, t0, kind, x, y, w, h, kw
    @property
    def rot(self): return self.kw.get('rot', 0)


class World:
    """One place the camera can travel through. surface: 'desk', 'blueprint', 'board' or fn(c, view)."""
    def __init__(self, film, surface='desk'):
        self.film = film; self.items = []; self.keys = []; self.layers = []; self.unders = []; self.over = []; self.shakes = []
        self.surface = SURFACES.get(surface, surface) if isinstance(surface, str) else surface

    def item(self, t0, kind, name, x, y, w, h=None, **kw):
        """kind: 'clip' (src, t_play, speed, skip), 'photo' (src, kb), 'scene' (draw=fn(c, t) in a 1920x1080 frame, noir=True),
        'paper' (draw=fn(c, t, w, h), bg). Options: frame (white border, default True for clip/photo), credit, title, rot, pop, until."""
        h = h or w * 9 / 16; it = Item(name, t0, kind, x, y, w, h, kw); self.items.append(it); return it

    def get(self, name): return next(i for i in self.items if i.name == name)
    def layer(self, fn): self.layers.append(fn); return fn          # world-space drawing fn(c, t), on top of items
    def under(self, fn): self.unders.append(fn); return fn          # world-space drawing under the items (plans, maps)
    def screen(self, fn): self.over.append(fn); return fn           # screen-space overlay fn(c, t)

    # camera
    def cam(self, t, x, y, zoom=1.0, rot=0.0, move=1.3, dip=0.10, drift=.010):
        self.keys.append(dict(t=t, x=x, y=y, z=zoom, r=rot, move=move, dip=dip, drift=drift))

    def dive(self, t, name, move=1.1, over=1.0, dip=0.0, drift=0.0):
        """Fill the screen with an item exactly (over=1.0), which is what a world change needs."""
        it = self.get(name); z = max(W / it.w, H / it.h) * over
        self.cam(t, it.x, it.y, z, -it.rot, move=move, dip=dip, drift=drift)

    def frame_box(self, t, name, move=1.2, pad=1.3, dx=0, dy=0, dip=.08, drift=.008):
        it = self.get(name); z = min(W / (it.w * pad), H / (it.h * pad))
        self.cam(t, it.x + dx, it.y + dy, z, 0, move=move, dip=dip, drift=drift)

    # hard cuts: the camera jumps; the strongest images then hold with only a slow push
    def cut(self, t, x, y, zoom=1.0, rot=0.0, drift=.006):
        self.keys.append(dict(t=t, x=x, y=y, z=zoom, r=rot, move=0.0, dip=0.0, drift=drift, cut=True))

    def cut_to(self, t, name, pad=1.25, dx=0, dy=0, drift=.006):
        it = self.get(name); z = min(W / (it.w * pad), H / (it.h * pad)); self.cut(t, it.x + dx, it.y + dy, z, 0, drift)

    def cut_dive(self, t, name, over=1.0, drift=.006):
        it = self.get(name); z = max(W / it.w, H / it.h) * over; self.cut(t, it.x, it.y, z, -it.rot, drift)

    def camera_at(self, t):
        ks = sorted(self.keys, key=lambda k: k['t'])
        if not ks: return 1.0, W / 2, H / 2, 0
        if t <= ks[0]['t']: k = ks[0]; return k['z'], k['x'], k['y'], k['r']
        prev = ks[0]
        for k in ks[1:]:
            s = k['t'] - k['move']
            if t < s:
                h = t - prev['t']; return prev['z'] * (1 + prev['drift'] * h), prev['x'], prev['y'], prev['r']
            if t < k['t']:
                hold = s - prev['t']; z0 = prev['z'] * (1 + prev['drift'] * max(hold, 0))
                u = (t - s) / k['move']; e = u * u * u * (u * (u * 6 - 15) + 10)
                zl = math.exp(lerp(math.log(z0), math.log(k['z']), e)) * (1 - k['dip'] * math.sin(math.pi * u))
                # pan in screen terms so long zooms feel even: weight position by zoom
                wgt = (1 / z0 - 1 / zl) / ((1 / z0 - 1 / k['z']) or 1e-9) if abs(z0 - k['z']) > 1e-6 and k['dip'] == 0 else e
                wgt = min(max(wgt, 0), 1)
                return zl, lerp(prev['x'], k['x'], wgt), lerp(prev['y'], k['y'], wgt), lerp(prev['r'], k['r'], e)
            prev = k
        h = t - prev['t']; return prev['z'] * (1 + prev['drift'] * h), prev['x'], prev['y'], prev['r']

    # drawing
    def _draw_item(self, c, t, it, f):
        if t < it.t0 or (it.kw.get('until') and t > it.kw['until']): return
        kw = it.kw; u = K(t, it.t0, .5); a = back(u, 1.2) if kw.get('pop', True) else 1
        w, h = it.w, it.h
        if kw.get('pop', True): _once('projector' if it.kind == 'clip' else 'paper', t, it.t0)
        c.save(); c.translate(it.x, it.y); c.rotate(it.rot); sc = .9 + .1 * a; c.scale(sc, sc)
        alpha = min(1, u * 2.5) if kw.get('pop', True) else 1
        frame = kw.get('frame', it.kind in ('clip', 'photo', 'scene')); bw = kw.get('border', 24)
        if frame:
            cap = 62 if kw.get('credit') else 0
            c.drawRect(skia.Rect(-w / 2 - bw + 16, -h / 2 - bw + 22, w / 2 + bw + 22, h / 2 + bw + cap + 28), fp((0, 0, 0), 160 * alpha, blur=22))
            c.drawRect(skia.Rect(-w / 2 - bw, -h / 2 - bw, w / 2 + bw, h / 2 + bw + cap), fp('#EFEBE0', 255 * alpha))
            if kw.get('credit'): txt(c, kw['credit'], -w / 2, h / 2 + bw + 34, 26, MONO, '#55524C', a=alpha)
        elif kw.get('shadow', True):
            c.drawRect(skia.Rect(-w / 2 + 14, -h / 2 + 20, w / 2 + 20, h / 2 + 26), fp((0, 0, 0), 150 * alpha, blur=20))
        if kw.get('title'): txt(c, kw['title'], -w / 2 - bw, -h / 2 - bw - 26, kw.get('title_size', 56), BEBAS, BONE, a=alpha)
        c.save(); c.clipRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2))
        if it.kind == 'clip':
            c.drawRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), fp('#000000'))
            tp = t - kw.get('t_play', it.t0); k = int(max(tp, 0) * FPS * kw.get('speed', 1.0)) + int(kw.get('skip', 0) * FPS)
            img = clip_image(kw['src'], k); zz = 1 + kw.get('kb', .04) * max(tp, 0) / 6
            p = skia.Paint(); p.setColorFilter(skia.ColorFilters.Matrix(archive_matrix(kw.get('tone', 'warm'))))
            c.saveLayer(None, p); _cover(c, img, w, h, zz, kw.get('fx', .5), kw.get('fy', .5)); c.restore()
            grain(c, -w / 2, -h / 2, w / 2, h / 2, f, 30)
        elif it.kind == 'photo':
            img = image(kw['src']); zz = 1 + kw.get('kb', .05) * min(max(t - it.t0, 0) / 8, 1.5)
            _cover(c, img, w, h, zz, kw.get('fx', .5), kw.get('fy', .5))
        elif it.kind == 'scene':
            p = skia.Paint()
            if kw.get('noir', True): p.setColorFilter(kw.get('grade') or GRADE)
            c.saveLayer(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), p)
            c.save(); c.translate(-w / 2, -h / 2); c.scale(w / W, h / H); kw['draw'](c, t); c.restore(); c.restore()
            if kw.get('vig', True):
                c.drawRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), sp(radial(0, 0, max(w, h) * .62, [hx('#000000', 0), hx('#000000', 0), hx('#000000', 170)], [0, .55, 1])))
        elif it.kind == 'paper':
            c.drawRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), fp(kw.get('bg', '#E6DECB')))
            kw['draw'](c, t, w, h)
        c.restore()
        if kw.get('pin', False): pin(c, 0, -h / 2 - (bw if frame else 0) + 10)
        c.restore()

    def draw(self, c, t, f, view):
        self.surface(c, view)
        for fn in self.unders: fn(c, t)
        x0, y0, x1, y1 = view
        for it in self.items:
            m = max(it.w, it.h)
            if it.x + m < x0 or it.x - m > x1 or it.y + m < y0 or it.y - m > y1: continue
            self._draw_item(c, t, it, f)
        for fn in self.layers: fn(c, t)


Board = World   # older name


class Reel:
    """Worlds in time order: [(start_time, world), ...]. The film shows one world at a time."""
    def __init__(self, film, segments):
        self.film = film; self.seg = sorted(segments, key=lambda s: s[0])

    def at(self, t):
        w = self.seg[0][1]
        for t0, ww in self.seg:
            if t >= t0: w = ww
        return w

    def camera_at(self, t): return self.at(t).camera_at(t)
    def draw(self, c, t, f, view): self.at(t).draw(c, t, f, view)

    @property
    def shakes(self): return []

    @property
    def keys(self):
        out = []
        for i, (t0, w) in enumerate(self.seg):
            t1 = self.seg[i + 1][0] if i + 1 < len(self.seg) else 1e9
            out += [k for k in w.keys if t0 <= k['t'] - k['move'] < t1]
        return out

    @property
    def over(self):
        film = self
        class _O(list): pass
        chap = lambda c, t: [chapter(c, t, ch[0] + .1, ch[1], ch[2], max(ch[3] - .1, 1.2)) for ch in self.film.chapters]
        return [lambda c, t: [o(c, t) for o in film.at(t).over]] + [o for o in getattr(self, '_over', [])] + [chap]

    def screen(self, fn):
        self.__dict__.setdefault('_over', []).append(fn); return fn

    def render_chunks(self, n=8, end=None):
        end = end or self.film.end_time; edges = [end * i / n for i in range(n + 1)]
        for i in range(n):
            def fn(c, t, cam): pass
            fn.__name__ = f'reel_{i:02d}'
            self.film.shot(edges[i], board=self, whip=False, end=edges[i + 1], vig=.5, bloom=.22)(fn)


def portal(world):
    """Draw fn for a 'scene' item that shows another world live, exactly as that world's camera sees it.
    Dive into the item (over=1.0) and switch the Reel to that world at the same moment: no visible cut."""
    def draw(c, t):
        z, fx, fy, r = world.camera_at(t); hw, hh = W / 2 / z * 1.5, H / 2 / z * 1.5
        c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.rotate(r); c.translate(-fx, -fy)
        world.draw(c, t, 0, (fx - hw, fy - hh, fx + hw, fy + hh)); c.restore()
    return draw


def single(film, world, n=8):
    """A film that stays in one world."""
    Reel(film, [(0, world)]).render_chunks(n)
