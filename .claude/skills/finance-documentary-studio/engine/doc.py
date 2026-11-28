"""The documentary look (v2): light, full-screen, real art and real maps.

    from doc import *
    film = Film(__file__, vo='vo.wav', words='words.json', mood='epic')
    T = film.cue
    doc = Doc(film)
    doc.art(0, 'media/siege.jpg', frm=(.6, .45, 1.0), to=(.62, .42, 1.12))   # a painting, slow push (focus x, y, zoom)
    doc.map(T('a village'), MED, cam=[(T('a village'), 15, 41, .22), (T('roads'), 18, 40, .26)], layers=[...])
    doc.scene(T('huts'), palatine_huts)                                       # an ink-and-wash drawing fn(c, t, u)
    @doc.screen
    def words(c, t): caption(c, t, T('Romulus'), T('legend') + 2, 'Romulus and Remus, as Rubens imagined them', 'Peter Paul Rubens, c. 1615', 'The legend')
    doc.render()
    film.main()

Shots follow each other with soft crossfades. Chapter cards come by themselves in the narrator's chapter pauses.
See references/doc.md."""
import os, math, random, json
import numpy as np, skia
from PIL import Image
from film import Film, W, H, FPS, C, K, ease, lerp, sfx
from history import Atlas, border_file, _geo, fmt_year, BORDERS_CREDIT

_FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts') + os.sep
_GEO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'geo') + os.sep
CINZEL = skia.Typeface.MakeFromFile(_FD + 'Cinzel-Variable.ttf')
SERIF = skia.Typeface.MakeFromFile(_FD + 'CormorantGaramond-Variable.ttf')
ITALIC = skia.Typeface.MakeFromFile(_FD + 'CormorantGaramond-Italic-Variable.ttf')
INK, PAPER, GOLD, SEPIA, OXBLOOD, LAPIS, CREAM, SEA, LAND = '#2E2418', '#EFE6D2', '#A8823A', '#6B5638', '#8E2B22', '#2F5D74', '#F6EFDF', '#C9D3CC', '#ECE1C6'


# ================================================================ drawing basics
def col(h, a=255):
    if isinstance(h, tuple): return skia.Color(*h[:3], int(a))
    h = h.lstrip('#'); return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(max(0, min(255, a))))
def fp(h, a=255, blur=0):
    p = skia.Paint(AntiAlias=True, Color=col(h, a))
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p
def ink(w, h=INK, a=255):
    p = skia.Paint(AntiAlias=True, Color=col(h, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join); return p

_VF = {}
def font(tf, size, wght=None):
    if wght:
        key = (id(tf), wght)
        if key not in _VF:
            tag = (ord('w') << 24) | (ord('g') << 16) | (ord('h') << 8) | ord('t')
            fa = skia.FontArguments(); fa.setVariationDesignPosition(skia.FontArguments.VariationPosition(
                skia.FontArguments.VariationPosition.Coordinates([skia.FontArguments.VariationPosition.Coordinate(tag, wght)])))
            _VF[key] = tf.makeClone(fa)
        tf = _VF[key]
    return skia.Font(tf, size)
def tw(s, size, tf=SERIF, track=0, wght=None):
    f = font(tf, size, wght); return sum(f.measureText(ch) for ch in s) + track * max(0, len(s) - 1) if track else f.measureText(s)
def text(c, s, x, y, size, tf=SERIF, h=INK, align='left', a=255, track=0, wght=None, shadow=0):
    f = font(tf, size, wght); w = tw(s, size, tf, track, wght)
    x0 = x - (w if align == 'right' else w / 2 if align == 'center' else 0)
    if shadow:
        sp_ = fp('#000000', a * shadow, blur=size * .12)
        if track:
            xx = x0
            for ch in s: c.drawString(ch, xx + 2, y + 3, f, sp_); xx += f.measureText(ch) + track
        else: c.drawString(s, x0 + 2, y + 3, f, sp_)
    if track:
        for ch in s: c.drawString(ch, x0, y, f, fp(h, a)); x0 += f.measureText(ch) + track
    else: c.drawString(s, x0, y, f, fp(h, a))
    return w

def fade(t, t0, t1, d_in=.5, d_out=.5):
    if t0 is None or t < t0 or (t1 is not None and t > t1 + d_out): return 0.0
    a = K(t, t0, d_in)
    if t1 is not None: a *= 1 - K(t, t1, d_out)
    return a


# ================================================================ paper, grain, ink-and-wash
_rng = np.random.default_rng(3)
def _noise(w, h, scale):
    n = _rng.standard_normal((h // scale + 2, w // scale + 2))
    return np.array(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(float) / 255
_pn = _noise(W, H, 40) - .5; _pf = _rng.random((H, W)) - .5
_pa = np.clip(np.array([239, 230, 210], float)[None, None, :] * (1 + .06 * _pn[..., None] + .02 * _pf[..., None]), 0, 255).astype(np.uint8)
PAPER_IMG = skia.Image.fromarray(np.dstack([_pa, np.full((H, W), 255, np.uint8)]), colorType=skia.kRGBA_8888_ColorType)
_GRAINS = []
for _k in range(4):
    g = (_rng.standard_normal((H, W)) * 18 + 128).clip(0, 255).astype(np.uint8)
    _GRAINS.append(skia.Image.fromarray(np.dstack([g, g, g, np.full((H, W), 20, np.uint8)]), colorType=skia.kRGBA_8888_ColorType))
_tex = ((_pn * .5 + .5) * 255).astype(np.uint8)
TEXTURE = skia.Image.fromarray(np.dstack([_tex, _tex, _tex, np.full((H, W), 26, np.uint8)]), colorType=skia.kRGBA_8888_ColorType)

def paper(c): c.drawImage(PAPER_IMG, 0, 0)
def grain(c, t, vig=.28):
    c.drawImage(_GRAINS[int(t * 12) % 4], 0, 0)
    sh = skia.GradientShader.MakeRadial((W / 2, H / 2), W * .75, [col('#000000', 0), col('#000000', 0), col('#2A1A08', 255 * vig)], [0, .6, 1])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect(0, 0, W, H), p)

def wobble(pts, amp=1.4, seed=0):
    r = random.Random(seed); out = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]; n = max(2, int(math.dist(pts[i], pts[i + 1]) / 14))
        for k in range(n): u = k / n; out.append((x0 + (x1 - x0) * u + r.uniform(-amp, amp), y0 + (y1 - y0) * u + r.uniform(-amp, amp)))
    out.append(pts[-1]); return out
def sketch(c, pts, w=2.4, h=INK, a=230, passes=2, amp=1.4, seed=0, close=False, reveal=1.0):
    """a hand-inked line (two slightly different passes); reveal 0..1 draws it progressively"""
    if close: pts = list(pts) + [pts[0]]
    for k in range(passes):
        q = wobble(pts, amp, seed + k * 17)
        if reveal < 1: q = q[:max(2, int(len(q) * reveal))]
        p = skia.Path(); p.moveTo(*q[0])
        for pt in q[1:]: p.lineTo(*pt)
        c.drawPath(p, ink(w * (1 if k == 0 else .6), h, a * (1 if k == 0 else .6)))
def wash(c, pts, h, a=90, blur=10, seed=0):
    r = random.Random(seed); p = skia.Path(); p.moveTo(*pts[0])
    for pt in pts[1:]: p.lineTo(pt[0] + r.uniform(-6, 6), pt[1] + r.uniform(-6, 6))
    p.close(); c.drawPath(p, fp(h, a, blur)); c.drawPath(p, fp(h, a * .5, 2))
def hatch(c, x0, y0, x1, y1, n, h=SEPIA, a=120, seed=0, ang=(34, 26)):
    r = random.Random(seed)
    for k in range(n):
        x, y = r.uniform(x0, x1), r.uniform(y0, y1); sketch(c, [(x, y), (x + ang[0], y + ang[1])], 1.1, h, a, 1, .6, seed=seed * 100 + k)


# ================================================================ art (paintings, statues, photos) with a slow push and optional depth
_ART = {}
def _art(path, depth, build):
    key = (path, depth)
    if key in _ART: return _ART[key]
    im = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(path)); fg = bg = None
    if depth:
        os.makedirs(os.path.join(build, 'depth'), exist_ok=True)
        base = os.path.join(build, 'depth', os.path.splitext(os.path.basename(path))[0])
        if not os.path.exists(base + '_fg.png'):
            try:
                from rembg import remove, new_session
                import cv2
                pil = Image.open(path).convert('RGB'); m = remove(pil, session=new_session('u2net'), only_mask=True).convert('L')
                ma = np.array(m.resize(pil.size)).astype(np.float32) / 255
                ma = cv2.GaussianBlur(np.clip((ma - .25) / .5, 0, 1), (0, 0), 6)
                rgba = np.dstack([np.array(pil), (ma * 255).astype(np.uint8)]); Image.fromarray(rgba).save(base + '_fg.png')
                small = cv2.resize(np.array(pil)[..., ::-1], None, fx=.35, fy=.35)
                hole = (cv2.resize(ma, (small.shape[1], small.shape[0])) > .2).astype(np.uint8) * 255
                hole = cv2.dilate(hole, np.ones((9, 9), np.uint8))
                fill = cv2.inpaint(small, hole, 9, cv2.INPAINT_TELEA)
                fill = cv2.resize(cv2.GaussianBlur(fill, (0, 0), 3), (pil.width, pil.height))[..., ::-1]
                a3 = cv2.dilate(ma, np.ones((15, 15), np.uint8))[..., None]
                Image.fromarray((np.array(pil) * (1 - a3) + fill * a3).astype(np.uint8)).save(base + '_bg.jpg', quality=92)
            except Exception as e:
                print('depth layers not available (', e, '): using a flat push for', os.path.basename(path)); depth = False
        if depth and os.path.exists(base + '_fg.png'):
            fg = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(base + '_fg.png'))
            bg = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(base + '_bg.jpg'))
    _ART[key] = (im, fg, bg); return _ART[key]

def _window(im, fx, fy, z):
    iw, ih = im.width(), im.height(); s0 = max(W / iw, H / ih); ww, wh = W / (s0 * z), H / (s0 * z)
    cx = min(max(fx * iw, ww / 2), iw - ww / 2); cy = min(max(fy * ih, wh / 2), ih - wh / 2)
    return cx, cy, ww, wh
def _blit(c, im, cx, cy, ww, wh, a=255):
    p = skia.Paint(); p.setAlphaf(a / 255)
    c.drawImageRect(im, skia.Rect(cx - ww / 2, cy - wh / 2, cx + ww / 2, cy + wh / 2), skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p)


# ================================================================ maps on parchment
class ParchmentMap:
    """A light old-atlas map of a region: soft sea with water-lining, paper land, little mountain symbols, desert stipple,
    rivers, ink coast. Geometry in world px (Atlas projection); everything else in screen px so type stays the same size."""
    def __init__(self, lon0, lat0, lon1, lat1, width=9000):
        self.at = Atlas(lon0, lat0, lon1, lat1, width=width)
        self._mtn = {}; self._des = None; self.keys = []

    def xy(self, lon, lat): return self.at.xy(lon, lat)

    def _regions(self, cla):
        out = []
        for f in _geo(_GEO + 'regions.geojson')['features']:
            if f['properties']['FEATURECLA'] != cla: continue
            g = f['geometry']; polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
            p = skia.Path(); ok = False
            for poly in polys:
                if self.at._in(poly[0], 6): self.at._ring(p, poly[0]); ok = True
            if ok: out.append(p)
        return out

    def mountains(self, step):
        """one combined path of mountain symbols every `step` world px"""
        if step in self._mtn: return self._mtn[step]
        r = random.Random(5); outline, shade = skia.Path(), skia.Path()
        for p in self._regions('Range/mtn'):
            b = p.computeTightBounds(); y = b.top()
            while y < b.bottom():
                x = b.left() + r.uniform(0, step)
                while x < b.right():
                    jx, jy = x + r.uniform(-step * .3, step * .3), y + r.uniform(-step * .3, step * .3)
                    if p.contains(jx, jy):
                        s = step * r.uniform(.34, .48)
                        outline.moveTo(jx - s, jy); outline.lineTo(jx - s * .1, jy - s * 1.15); outline.lineTo(jx + s, jy)
                        shade.moveTo(jx - s * .1, jy - s * 1.15); shade.lineTo(jx + s, jy); shade.lineTo(jx + s * .1, jy); shade.close()
                    x += step
                y += step * .8
        self._mtn[step] = (outline, shade, step); return self._mtn[step]

    def deserts(self):
        if self._des is None:
            r = random.Random(9); p_ = skia.Path()
            for p in self._regions('Desert'):
                b = p.computeTightBounds()
                for i in range(int(b.width() * b.height() / 9000)):
                    x, y = r.uniform(b.left(), b.right()), r.uniform(b.top(), b.bottom())
                    if p.contains(x, y): p_.addCircle(x, y, 7)
            self._des = p_
        return self._des

    def camera(self, cam, t):
        """cam: [(t, lon, lat, zoom), ...] eased between keys (zoom moves in log space). Returns (cx, cy, z) in world px."""
        if t <= cam[0][0]: k = cam[0]; x, y = self.xy(k[1], k[2]); return x, y, k[3]
        for a, b in zip(cam, cam[1:]):
            if t < b[0]:
                u = ease((t - a[0]) / (b[0] - a[0])); (xa, ya), (xb, yb) = self.xy(a[1], a[2]), self.xy(b[1], b[2])
                return lerp(xa, xb, u), lerp(ya, yb, u), math.exp(lerp(math.log(a[3]), math.log(b[3]), u))
        k = cam[-1]; x, y = self.xy(k[1], k[2]); return x, y, k[3]

    def draw_base(self, c, z):
        at = self.at
        c.drawRect(skia.Rect(-3000, -3000, at.width + 3000, at.height + 3000), fp(SEA))
        for w_, a in ((22, 70), (50, 45), (90, 25)): c.drawPath(at.land_path, ink(w_ / max(z, .2) * .22, '#9FB0A8', a))
        c.drawPath(at.land_path, fp(LAND))
        c.save(); c.clipPath(at.land_path, doAntiAlias=True)
        c.drawPath(self.deserts(), fp('#A88E62', 130))
        for step, a in ((150, 1 - K(z, .5, .3)), (60, K(z, .5, .3))):       # coarse symbols far out, finer ones close in
            if a <= 0: continue
            o, s, st = self.mountains(step); c.drawPath(s, fp('#8C7552', 120 * a)); c.drawPath(o, ink(st * .06, '#5E4A30', 200 * a))
        c.restore()

    def draw_top(self, c, z):
        c.drawPath(self.at.land_path, ink(2.6 / z, '#5A4A34', 220))
        if self.at.river_path is not None: c.drawPath(self.at.river_path, ink(2.2 / z, '#6E8A8E', 200))

    def empire(self, keys, color=OXBLOOD, fill=48, fade_s=1.4, clip=None):
        """the state's lands over time: keys [(t, year, ['Rome', ...]), ...]; each fades into the next like ink spreading.
        clip: (lon0, lat0, lon1, lat1) box to keep (e.g. to leave out land the snapshot gives too early)."""
        keys = sorted(keys, key=lambda k: k[0])
        def draw(c, t, z):
            for i, (t0, year, names) in enumerate(keys):
                t1 = keys[i + 1][0] if i + 1 < len(keys) else 1e9
                a = K(t, t0, fade_s) * (1 - K(t, t1, fade_s))
                if a <= 0: continue
                p = self.at.state(year, names)
                c.save(); c.clipPath(self.at.land_path, doAntiAlias=True)
                if clip:
                    (x0, y0), (x1, y1) = self.xy(clip[0], clip[3]), self.xy(clip[2], clip[1]); c.clipRect(skia.Rect(x0, y0, x1, y1))
                c.drawPath(p, fp(color, fill * a)); c.drawPath(p, ink(9 / z, color, 70 * a)); c.drawPath(p, ink(3.2 / z, color, 230 * a)); c.restore()
        draw.world = True; return draw

    def route(self, pts, t0, dur=2.0, color=LAPIS, width=12, until=None):
        """a campaign arrow along [(lon, lat), ...] drawn over dur seconds"""
        def draw(c, t, z):
            a = fade(t, t0, until, .2, .5)
            if a <= 0: return
            xy = [self.xy(*p) for p in pts]; path = skia.Path(); path.moveTo(*xy[0])
            for i in range(1, len(xy) - 1):
                mx, my = (xy[i][0] + xy[i + 1][0]) / 2, (xy[i][1] + xy[i + 1][1]) / 2; path.quadTo(xy[i][0], xy[i][1], mx, my)
            path.lineTo(*xy[-1])
            meas = skia.PathMeasure(path, False); L = meas.getLength(); u = ease(K(t, t0, dur)); seg = skia.Path(); meas.getSegment(0, L * u, seg, True)
            c.drawPath(seg, ink(width * 2.4 / z, color, 60 * a)); c.drawPath(seg, ink(width / z, color, 235 * a))
            pos, tan = meas.getPosTan(L * u)
            if u > .03 and pos is not None:
                ang = math.atan2(tan.y(), tan.x()); s = width * 3.4 / z; bx, by = pos.x(), pos.y()
                hd = skia.Path(); hd.moveTo(bx + math.cos(ang) * s, by + math.sin(ang) * s)
                hd.lineTo(bx + math.cos(ang + 2.5) * s, by + math.sin(ang + 2.5) * s); hd.lineTo(bx + math.cos(ang - 2.5) * s, by + math.sin(ang - 2.5) * s); hd.close()
                c.drawPath(hd, fp(color, 240 * a))
        draw.world = True; return draw

    # screen-space layers (they get a projection fn)
    def place(self, name, lon, lat, t0, until=None, size=34, dot=True, dx=14, dy=-10, tf=SERIF, h=INK, wght=600):
        def draw(c, t, proj):
            a = fade(t, t0, until)
            if a <= 0: return
            x, y = proj(lon, lat); s = size
            if dot:
                c.drawCircle(x, y, s * .2, fp('#F4ECD8', 255 * a)); c.drawCircle(x, y, s * .2, ink(s * .07, INK, 255 * a)); c.drawCircle(x, y, s * .07, fp(INK, 255 * a))
            text(c, name, x + dx, y + dy, s, tf, h, a=255 * a, wght=wght)
        return draw

    def label(self, name, lon, lat, t0, until=None, size=40, h=SEPIA, tf=CINZEL, track=None, rot=0, a_max=.85):
        def draw(c, t, proj):
            a = fade(t, t0, until, .8, .6) * a_max
            if a <= 0: return
            x, y = proj(lon, lat); c.save(); c.translate(x, y); c.rotate(rot)
            text(c, name, 0, 0, size, tf, h, 'center', 255 * a, size * .35 if track is None else track); c.restore()
        return draw

    def army(self, name, lon, lat, t0, until=None, color=LAPIS, n=3, size=1.0, move=None):
        """unit blocks with the army's name; move=(t1, lon1, lat1) slides them"""
        def draw(c, t, proj):
            a = fade(t, t0, until, .4, .4)
            if a <= 0: return
            lo, la = lon, lat
            if move: u = ease(K(t, move[0], move[3] if len(move) > 3 else 2.0)); lo, la = lerp(lon, move[1], u), lerp(lat, move[2], u)
            x, y = proj(lo, la); s = 26 * size
            for k in range(n):
                r = skia.Rect(x - n * s * .9 + k * s * 1.8, y - s, x - n * s * .9 + k * s * 1.8 + s * 1.5, y + s)
                c.drawRect(r, fp(color, 235 * a)); c.drawRect(r, ink(3, '#F4ECD8', 255 * a))
            text(c, name, x, y + s + 44 * size, 38 * size, CINZEL, color, 'center', 255 * a, 6)
        return draw


# ================================================================ captions and type
def caption(c, t, t0, t1, line, sub=None, kind=None):
    """lower-left documentary caption: small-caps kind, italic line, small source line"""
    a = fade(t, t0, t1, .6, .6)
    if a <= 0: return
    sh = skia.GradientShader.MakeLinear([(0, H - 380), (0, H)], [col('#000000', 0), col('#140C04', 165 * a)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect(0, H - 380, W, H), p)
    y = H - 118; dx = 18 * (1 - ease(K(t, t0, .8)))
    if kind: text(c, kind.upper(), 96 + dx, y - 76, 28, CINZEL, '#E3C27A', a=255 * a, track=6)
    text(c, line, 96 + dx, y, 58, ITALIC, CREAM, a=255 * a, wght=500)
    if sub: text(c, sub, 98 + dx, y + 50, 28, SERIF, '#D9CBB0', a=230 * a, wght=500)

def name_card(c, t, t0, t1, first, last, role, note=None, x=1240, y=470, dark=True):
    """a person's name beside their portrait or bust"""
    a = fade(t, t0, t1, .7, .6)
    if a <= 0: return
    if dark:
        sh = skia.GradientShader.MakeLinear([(x - 540, 0), (x + 60, 0)], [col('#140C04', 0), col('#140C04', 190 * a)])
        p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect(x - 540, 0, W, H), p)
    u = ease(K(t, t0, .9)); h1, h2 = ('#E3C27A', CREAM) if dark else (GOLD, INK)
    if first: text(c, first.upper(), x, y, 46, CINZEL, h1, a=255 * a, track=8)
    size = 150
    while tw(last, size, CINZEL, 4) > W - x - 60: size -= 8
    text(c, last, x, y + 130, size, CINZEL, h2, a=255 * a, track=4)
    c.drawLine(x, y + 170, x + 380 * u, y + 170, ink(2.4, GOLD, 255 * a))
    text(c, role, x, y + 230, 44, ITALIC, '#E9DFC9' if dark else SEPIA, a=255 * a, wght=500)
    if note: text(c, note, x, y + 290, 24, SERIF, '#BFB094' if dark else SEPIA, a=230 * a, wght=500)

def year_title(c, t, t0, t1, year, sub=None, x=92, y=150, dark=False):
    """big year top-left with a gold rule; year is text, a number (negative = BC) or fn(t) -> number"""
    a = fade(t, t0, t1, .6, .5)
    if a <= 0: return
    yv = year(t) if callable(year) else year; s = fmt_year(yv) if not isinstance(yv, str) else yv
    h = CREAM if dark else INK; sh = .5 if dark else 0
    w = text(c, s, x, y, 104, CINZEL, h, a=255 * a, track=10, shadow=sh)
    c.drawLine(x + 4, y + 26, x + 4 + max(w, 340) * ease(K(t, t0, .8)), y + 26, ink(2.4, GOLD, 255 * a))
    if sub: text(c, sub, x + 4, y + 76, 44, ITALIC, '#E9DFC9' if dark else SEPIA, a=255 * a, wght=500, shadow=sh)

def statement(c, t, t0, t1, line, y=H / 2 + 40, size=110, dark=True, sub=None):
    """a centred line in Roman capitals for the key idea ('ONE MAN · SIX MONTHS')"""
    a = fade(t, t0, t1, .6, .6)
    if a <= 0: return
    if dark: c.drawRect(skia.Rect(0, y - size - 60, W, y + (110 if sub else 70)), fp('#120A04', 120 * a, blur=50))
    while tw(line, size, CINZEL, 8) > W - 200: size -= 6
    text(c, line, W / 2, y, size, CINZEL, CREAM if dark else INK, 'center', 255 * a, 8)
    if sub: text(c, sub, W / 2, y + 66, 44, ITALIC, '#E9DFC9' if dark else SEPIA, 'center', 255 * a, wght=500)

def note(c, t, t0, t1, s, x=96, y=110, dark=True):
    """a small italic note top-left, e.g. 'The legend' / 'What archaeologists found'"""
    a = fade(t, t0, t1)
    if a > 0: text(c, s.upper(), x, y, 28, CINZEL, '#E3C27A' if dark else GOLD, a=255 * a, track=6, shadow=.6 if dark else 0)

def timeline(c, t, t0, t1, eras, start, end, now=None, marks=()):
    """engraved timeline on a paper strip at the bottom. eras: [(y0, y1, 'Kings'), ...]; now: year or fn(t)"""
    a = fade(t, t0, t1, .6, .5)
    if a <= 0: return
    y = H - 88; x0, x1 = 160, W - 160; X = lambda yr: x0 + (x1 - x0) * (yr - start) / (end - start); u = ease(K(t, t0, 1.2))
    c.drawRect(skia.Rect(0, H - 170, W, H), fp(PAPER, 230 * a)); c.drawLine(0, H - 170, W, H - 170, ink(1.4, GOLD, 200 * a))
    c.drawLine(x0, y, x0 + (x1 - x0) * u, y, ink(2, INK, 255 * a))
    for i, (ea, eb, n) in enumerate(eras):
        b = a * K(t, t0 + .3 + i * .15, .4)
        c.drawLine(X(ea), y - 10, X(ea), y + 10, ink(2, INK, 255 * b)); text(c, n, (X(ea) + X(eb)) / 2, y + 44, 34, ITALIC, SEPIA, 'center', 255 * b, wght=600)
        if i == len(eras) - 1: c.drawLine(X(eb), y - 10, X(eb), y + 10, ink(2, INK, 255 * b))
    for (yr, lab) in marks:
        text(c, lab, X(yr), y - 30, 24, CINZEL, SEPIA, 'center', 230 * a, 3)
    if now is not None:
        yr = now(t) if callable(now) else now; xx = X(min(max(yr, start), end))
        c.drawCircle(xx, y, 11, fp(OXBLOOD, 255 * a)); text(c, fmt_year(yr), xx, y - 26, 26, CINZEL, OXBLOOD, 'center', 255 * a, 3)

def roll(keys):
    """fn(t) rolling a year between [(t, year), ...]"""
    keys = sorted(keys)
    def f(t):
        if t <= keys[0][0]: return keys[0][1]
        for (ta, ya), (tb, yb) in zip(keys, keys[1:]):
            if t < tb: return ya + (yb - ya) * ease((t - ta) / (tb - ta))
        return keys[-1][1]
    return f

def chapter_card(c, t, t0, dur, num, title, sub=None, bgmap=None):
    """light paper chapter card over a faint map (drawn in the narrator's pause)"""
    a = min(1, K(t, t0, .45)) * (1 - K(t, t0 + dur - .35, .45))
    if a <= 0: return
    c.saveLayerAlpha(None, int(255 * a))
    paper(c)
    if bgmap is not None:
        m, lon, lat, z = bgmap; cx, cy = m.xy(lon, lat)
        c.save(); c.translate(W / 2, H / 2); c.scale(z * (1 + .03 * K(t, t0, dur)), z * (1 + .03 * K(t, t0, dur))); c.translate(-cx, -cy)
        m.draw_base(c, z); m.draw_top(c, z); c.restore(); c.drawRect(skia.Rect(0, 0, W, H), fp(PAPER, 205))
    u = ease(K(t, t0 + .1, .9))
    text(c, num.upper(), W / 2, 420, 40, CINZEL, GOLD, 'center', track=16)
    size = 190
    while tw(title, size, CINZEL, 6) > W - 200: size -= 8
    text(c, title, W / 2, 600 - 10 * (1 - u), size, CINZEL, INK, 'center', track=6)
    c.drawLine(W / 2 - 230 * u, 650, W / 2 + 230 * u, 650, ink(2.4, GOLD))
    if sub: text(c, sub, W / 2, 720, 50, ITALIC, SEPIA, 'center', wght=500)
    grain(c, t, .25)
    c.restore()

def title_card(c, t, t0, t1, small, big):
    a = fade(t, t0, t1, .8, .7)
    if a <= 0: return
    c.drawRect(skia.Rect(0, 300, W, 780), fp(PAPER, 150 * a, blur=80))
    text(c, small.upper(), W / 2, 440, 44, CINZEL, GOLD, 'center', 255 * a, 16)
    text(c, big, W / 2, 660, 240, CINZEL, INK, 'center', 255 * a, 30)
    u = ease(K(t, t0 + .2, 1.0)); c.drawLine(W / 2 - 260 * u, 712, W / 2 + 260 * u, 712, ink(2.4, GOLD, 255 * a))


# ================================================================ the documentary timeline
class Doc:
    """Shots in time order with soft crossfades: art (paintings, photos), map (parchment atlas with a moving camera),
    scene (ink-and-wash drawings or anything drawn on the 1920x1080 frame)."""
    def __init__(self, film, xfade=.8, chapter_map=None, chapter_subs=None):
        self.film, self.xf, self.shots, self._screen = film, xfade, [], []
        self.chapter_map, self.chapter_subs = chapter_map, chapter_subs or {}

    def _add(self, t0, kind, **kw): self.shots.append(dict(t0=t0, kind=kind, **kw)); self.shots.sort(key=lambda s: s['t0'])

    def art(self, t0, src, frm=(.5, .5, 1.0), to=None, depth=False, portrait=None):
        """src: image path (relative to the episode). frm/to: (focus x 0..1, focus y 0..1, zoom >= 1). depth: layered parallax.
        portrait=x (0..1): show a tall picture whole, standing at that x over a soft blurred copy of itself (portraits, statues)."""
        to = to or (frm[0], frm[1], frm[2] * 1.08)
        self._add(t0, 'art', src=os.path.join(self.film.dir, src), frm=frm, to=to, depth=depth, portrait=portrait)

    def map(self, t0, m, cam, layers=()):
        """m: ParchmentMap; cam: [(t, lon, lat, zoom), ...]; layers: world layers (m.empire, m.route) and screen layers (m.place, m.label, m.army)."""
        self._add(t0, 'map', m=m, cam=cam, layers=layers)

    def scene(self, t0, fn, paper_bg=True):
        """fn(c, t, u): draw on the 1920x1080 frame (u = 0..1 through the shot)."""
        self._add(t0, 'scene', fn=fn, paper=paper_bg)

    def screen(self, fn): self._screen.append(fn); return fn

    def _end(self, i): return self.shots[i + 1]['t0'] if i + 1 < len(self.shots) else self.film.end_time

    def _draw_shot(self, c, i, t):
        s = self.shots[i]; t0, t1 = s['t0'], self._end(i) + self.xf; u = max(0, min(1, (t - t0) / max(t1 - t0, .01))); e = ease(u) * .85 + u * .15
        if s['kind'] == 'art':
            im, fg, bg = _art(s['src'], s['depth'], self.film.build)
            fx, fy, z = [lerp(a, b, e) for a, b in zip(s['frm'], s['to'])]
            if s.get('portrait') is not None:
                cx, cy, ww, wh = _window(im, .5, .5, 1.0)
                p = skia.Paint(); p.setImageFilter(skia.ImageFilters.Blur(40, 40, skia.TileMode.kClamp))
                p.setColorFilter(skia.ColorFilters.Matrix([.55, 0, 0, 0, 0, 0, .52, 0, 0, 0, 0, 0, .48, 0, 0, 0, 0, 0, 1, 0]))
                c.drawImageRect(im, skia.Rect(cx - ww / 2, cy - wh / 2, cx + ww / 2, cy + wh / 2), skia.Rect(-60, -60, W + 60, H + 60), skia.SamplingOptions(skia.FilterMode.kLinear), p)
                hh = H * .9 * z; ww2 = hh * im.width() / im.height(); x = W * s['portrait'] + (fx - .5) * 40; y = H / 2 + (fy - .5) * 40
                c.drawRect(skia.Rect(x - ww2 / 2 + 14, y - hh / 2 + 18, x + ww2 / 2 + 14, y + hh / 2 + 18), fp('#000000', 110, blur=26))
                c.drawImageRect(im, skia.Rect(x - ww2 / 2, y - hh / 2, x + ww2 / 2, y + hh / 2), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
                return
            if fg is not None:
                cx, cy, ww, wh = _window(bg, fx, fy, z); _blit(c, bg, cx, cy, ww, wh)
                k = 1 + .045 * e; _blit(c, fg, cx + ww * .012 * e, cy, ww / k, wh / k)
            else:
                cx, cy, ww, wh = _window(im, fx, fy, z); _blit(c, im, cx, cy, ww, wh)
        elif s['kind'] == 'map':
            m = s['m']; cx, cy, z = m.camera(s['cam'], t)
            c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-cx, -cy)
            m.draw_base(c, z)
            for L in s['layers']:
                if getattr(L, 'world', False): L(c, t, z)
            m.draw_top(c, z); c.restore()
            c.drawImage(TEXTURE, 0, 0)
            proj = lambda lon, lat: ((m.xy(lon, lat)[0] - cx) * z + W / 2, (m.xy(lon, lat)[1] - cy) * z + H / 2)
            for L in s['layers']:
                if not getattr(L, 'world', False): L(c, t, proj)
        else:
            if s.get('paper', True): paper(c)
            s['fn'](c, t, u)

    # interface used by film.py (same as a Reel)
    def camera_at(self, t): return (1.0, W / 2, H / 2, 0)
    @property
    def shakes(self): return []
    @property
    def keys(self): return [dict(t=s['t0'] + .5, move=.9) for s in self.shots[1:]]

    def draw(self, c, t, f, view):
        c.clear(col(PAPER)); i = max([k for k, s in enumerate(self.shots) if s['t0'] <= t] or [0])
        if i > 0 and t < self.shots[i]['t0'] + self.xf:
            self._draw_shot(c, i - 1, t)
            c.saveLayerAlpha(None, int(255 * ease(K(t, self.shots[i]['t0'], self.xf)))); self._draw_shot(c, i, t); c.restore()
        else: self._draw_shot(c, i, t)
        grain(c, t)

    @property
    def over(self):
        def chap(c, t):
            for ch in self.film.chapters:
                chapter_card(c, t, ch[0] + .05, ch[3] + .25, ch[1], ch[2], self.chapter_subs.get(ch[2]), self.chapter_map)
        return [lambda c, t: [o(c, t) for o in self._screen], chap]

    def render(self, n=6):
        end = self.film.end_time; edges = [end * i / n for i in range(n + 1)]
        for i in range(n):
            def fn(c, t, cam): pass
            fn.__name__ = f'doc_{i:02d}'
            self.film.shot(edges[i], board=self, whip=False, end=edges[i + 1], raw=True)(fn)


# ================================================================ ink-and-wash library (places and things; no drawn people)
def palatine_huts(c, t, u):
    """first settlement: thatched huts on a hill above the Tiber marsh, smoke rising, sheep in a pen"""
    s = 1 + .05 * ease(u); c.save(); c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-W / 2, -H / 2)
    wash(c, [(0, 0), (1920, 0), (1920, 420), (0, 520)], '#C9B48A', 40, 50, 4)
    far = [(0, 520), (260, 430), (520, 470), (760, 400), (1040, 450)]
    wash(c, far + [(1040, 700), (0, 700)], '#A9AE8E', 70, 16, 6); sketch(c, far, 1.8, SEPIA, 170, seed=7)
    hill = [(-20, 760), (240, 560), (520, 420), (860, 380), (1180, 410), (1480, 520), (1940, 700)]
    wash(c, hill + [(1940, 1080), (-20, 1080)], '#9AA27A', 95, 12, 1); sketch(c, hill, 3.4, seed=3)
    r = random.Random(11)
    for k in range(70):
        x = r.uniform(1150, 1800); y0 = 420 + (x - 1150) * .45 + r.uniform(20, 160); sketch(c, [(x, y0), (x + 34, y0 + 26)], 1.1, SEPIA, 120, 1, .6, seed=300 + k)
    for k in range(40):
        x = r.uniform(0, 500); y0 = 760 - x * .6 + r.uniform(30, 200); sketch(c, [(x, y0), (x + 30, y0 + 22)], 1.1, SEPIA, 110, 1, .6, seed=400 + k)
    for i, (x, y, h) in enumerate(((330, 600, 150), (420, 560, 120), (1420, 560, 170), (1530, 610, 140))):
        sway = 3 * math.sin(t * 1.3 + i)
        pts = [(x + sway, y - h), (x + h * .22, y - h * .3), (x, y), (x - h * .22, y - h * .3)]
        wash(c, pts, '#5E6E44', 140, 4, 60 + i); sketch(c, pts, 2, seed=70 + i, close=True); sketch(c, [(x, y), (x, y + 24)], 2, seed=80 + i)
    for i, (x, y, s_) in enumerate(((640, 470, 1.15), (800, 430, 1.25), (970, 440, 1.3), (1140, 465, 1.1), (900, 560, 1.5))):
        P = lambda px, py: (x + px * s_, y + py * s_)
        roof = [P(-70, -20), P(0, -125), P(70, -20)]; wall = [P(-56, -20), P(56, -20), P(56, 52), P(-56, 52)]
        wash(c, wall, '#A47C52', 150, 3, 20 + i); wash(c, roof, '#C29A5C', 170, 3, 10 + i)
        sketch(c, wall, 2.4, seed=50 + i, close=True); sketch(c, roof, 2.8, seed=30 + i)
        for k in range(7): sketch(c, [P(-62 + k * 19, -24), P(-8 + k * 3, -118)], 1.1, SEPIA, 160, 1, .8, seed=90 + i * 9 + k)
        door = [P(-14, 52), P(-14, 10), P(14, 10), P(14, 52)]; wash(c, door, '#3A2A1A', 170, 2, 75 + i); sketch(c, door, 2, seed=70 + i)
        for k in range(5):     # smoke drifting up
            v = (t * .18 + k / 5 + i * .13) % 1
            cx_, cy_ = P(6 + 30 * v + 8 * math.sin(t + k), -135 - 260 * v)
            c.drawCircle(cx_, cy_, (10 + 26 * v) * s_, fp('#8A8070', 70 * (1 - v) * min(1, v * 5), blur=8))
    sketch(c, [(1240, 700), (1500, 690), (1700, 710)], 1.8, seed=150)
    for k in range(9): xx = 1240 + k * 55; sketch(c, [(xx, 702 + k), (xx, 670 + k)], 1.6, seed=160 + k)
    for k in range(7):
        x, y = 1270 + k * 60 + r.uniform(-8, 8) + 4 * math.sin(t * .7 + k), 740 + r.uniform(-10, 10)
        c.drawOval(skia.Rect(x - 20, y - 13, x + 20, y + 13), fp('#F6EFDF'))
        sketch(c, [(x - 20, y), (x - 10, y - 13), (x + 12, y - 13), (x + 20, y), (x + 10, y + 13), (x - 12, y + 13)], 1.5, seed=170 + k, close=True)
        sketch(c, [(x - 10, y + 12), (x - 10, y + 26)], 1.3, seed=180 + k); sketch(c, [(x + 10, y + 12), (x + 10, y + 26)], 1.3, seed=190 + k)
    riv = [(-20, 960), (500, 925), (1100, 975), (1940, 935)]
    wash(c, riv + [(1940, 1010), (1100, 1050), (500, 1000), (-20, 1030)], '#7E9AA4', 150, 6, 3)
    sketch(c, riv, 2.4, '#3E5560', seed=5); sketch(c, [(-20, 1030), (500, 1000), (1100, 1050), (1940, 1010)], 2.4, '#3E5560', seed=6)
    for k in range(16):
        x = 100 + k * 115 + 20 * math.sin(t * .4 + k); sketch(c, [(x, 975 + k % 3 * 10), (x + 54, 972 + k % 3 * 10)], 1.3, '#3E5560', 150, 1, seed=40 + k)
    for k in range(40):
        x = r.uniform(1150, 1900); y0 = r.uniform(905, 945); sw = 4 * math.sin(t * 1.5 + k)
        sketch(c, [(x, y0), (x + r.uniform(-6, 6) + sw, y0 - r.uniform(30, 60))], 1.2, '#4E5A3A', 170, 1, .5, seed=500 + k)
    text(c, 'Tiberis', 1500, 1000, 44, ITALIC, '#2F4A54', 'center', 220, wght=500)
    text(c, 'Mons Palatinus', 330, 400, 46, ITALIC, SEPIA, 'center', 230, wght=500)
    c.restore()


def fasces(c, x, y, s=1.0, seed=0, reveal=1.0):
    """the fasces: a bundle of rods tied with red straps around an axe (the symbol carried before a consul)"""
    P = lambda px, py: (x + px * s, y + py * s)
    blade = [P(30, -330), P(118, -360), P(132, -300), P(118, -240), P(30, -270)]
    wash(c, blade, '#B9BEC0', 220 * reveal, 2, seed); sketch(c, blade, 2.6 * s, seed=seed, close=True, reveal=reveal)
    for k in range(-3, 4):
        rod = [P(k * 13 - 4, -380), P(k * 13 + 4, -380), P(k * 13 + 4, 120), P(k * 13 - 4, 120)]
        wash(c, rod, '#B8905A', 230 * reveal, 1.5, seed + k); sketch(c, [P(k * 13, -380), P(k * 13, 120)], 1.6 * s, seed=seed + 20 + k, reveal=reveal)
    sketch(c, [P(-48, -380), P(48, -380), P(48, 120), P(-48, 120)], 2.8 * s, seed=seed + 40, close=True, reveal=reveal)
    for yy in (-300, -140, 20):
        strap = [P(-52, yy), P(52, yy + 30), P(52, yy + 52), P(-52, yy + 22)]
        wash(c, strap, OXBLOOD, 220 * reveal, 1.5, seed + yy); sketch(c, strap, 2 * s, seed=seed + 60 + yy, close=True, reveal=reveal)

def two_consuls(c, t, u):
    """two fasces side by side on paper, with a year ring: the two consuls, elected every year"""
    wash(c, [(0, 0), (W, 0), (W, H), (0, H)], '#D8C7A2', 40, 60, 2)
    for i, x in enumerate((760, 1160)):
        rv = ease(K(u, .05 + i * .12, .35)); fasces(c, x, 720, 1.25, seed=10 + i * 50, reveal=max(.02, rv))
    k = ease(K(u, .45, .4)); c.drawArc(skia.Rect(560, 120, 1360, 1040), -90, 360 * k, False, ink(3, GOLD, 220))
    text(c, 'I', 960, 175, 40, CINZEL, GOLD, 'center', 255 * K(u, .8, .2))
