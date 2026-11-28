"""History kit: the look of "The ENTIRE History of X" films, on top of board.py.

    from board import *
    from history import *            # switches chapter cards to Cinzel + gold, scenes to a warm antique grade

What it adds:
- Atlas: a real map (Natural Earth coastlines) of any region as a World surface, so the camera can fly over it,
  with the borders of any state in any period (historical-basemaps, ~50 snapshots from 123000 BC to 2010)
  growing and shrinking over time, city dots and labels.
- timeline(): a bar of years (BC/AD) with a moving marker and the period you are in.
- year_tag(): a big year counter (753 BC ... AD 476 ...).
- label(): LEGEND / EVIDENCE / HISTORIANS DISAGREE tags.
- surfaces: 'parchment' (old paper table for timelines and documents), 'atlas' (dark sea, for maps).
- ancient sets: hills_village(), temple_row(), senate_hall(), city_walls(); puppet presets for Rome
  (SENATOR, EMPEROR, LEGIONARY, CITIZEN, MATRON, KING).
See references/history.md.
"""
import os, json, math, random, urllib.request
import numpy as np, skia
import board as _b
from board import *

_FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts') + os.sep
_GEO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'geo') + os.sep
CINZEL = skia.Typeface.MakeFromFile(_FD + 'Cinzel-Variable.ttf')
GOLD, PURPLE, LAPIS, OCHRE, PAPER, SEPIA = '#C9A44C', '#6A2E7A', '#2D4E7A', '#B5793A', '#E8DDC4', '#4A3A26'

# ---------------------------------------------------------------- house look
_b.CHAPTER_STYLE.update(font=CINZEL, size=150, rule=GOLD, small=GOLD, y=595, track=6)
# warm antique grade for animated scenes (fresco colours, lifted blacks, soft gold highlights)
ANTIQUE = skia.ColorFilters.Matrix([.78, .22, .04, 0, .02, .12, .78, .08, 0, .015, .06, .2, .62, 0, .01, 0, 0, 0, 1, 0])
_b.GRADE = ANTIQUE


def fmt_year(y, short=False):
    """-753 -> '753 BC', 476 -> 'AD 476' (or '476' with short=True after AD 1000)."""
    y = int(round(y))
    if y < 0: return f'{-y} BC'
    if y == 0: return '1 BC'
    return f'{y}' if (short or y >= 1000) else f'AD {y}'


# ---------------------------------------------------------------- surfaces
def surface_parchment(c, view):
    x0, y0, x1, y1 = view
    c.drawRect(skia.Rect(x0 - 50, y0 - 50, x1 + 50, y1 + 50), fp('#2A2018'))
    c.drawRect(skia.Rect(-200, -200, 9200, 6200), fp('#D9CBA8'))
    for (lx, ly, r, col, a) in ((1800, 1500, 2400, '#C7B48C', 150), (6400, 2200, 2800, '#CDBB93', 120), (3600, 4600, 2600, '#C2AE85', 140),
                                (8200, 5200, 1800, '#B49C70', 110), (400, 5400, 1500, '#B49C70', 120)):
        if lx + r > x0 and lx - r < x1 and ly + r > y0 and ly - r < y1:
            c.drawCircle(lx, ly, r, sp(radial(lx, ly, r, [hx(col, a), hx(col, 0)])))
    r = random.Random(7)
    for i in range(int(max(0, (x1 - x0) * (y1 - y0)) / 160000)):
        c.drawCircle(r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(1, 3.5), fp('#A8946C', 90))
    c.drawRect(skia.Rect(-200, -200, 9200, 6200), sp(radial(4500, 3000, 6400, [hx('#000000', 0), hx('#000000', 0), hx('#3A2A18', 150)], [0, .7, 1])))


def surface_atlas(c, view):
    x0, y0, x1, y1 = view
    c.drawRect(skia.Rect(x0 - 50, y0 - 50, x1 + 50, y1 + 50), fp('#16232B'))


_b.SURFACES.update(parchment=surface_parchment, atlas=surface_atlas)


# ---------------------------------------------------------------- maps
_BYEARS = [-123000, -10000, -8000, -5000, -4000, -3000, -2000, -1500, -1000, -700, -500, -400, -323, -300, -200, -100, -1,
           100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1279, 1300, 1400, 1492, 1500, 1530, 1600, 1650, 1700,
           1715, 1783, 1800, 1815, 1878, 1880, 1900, 1914, 1920, 1930, 1938, 1945, 1960, 1994, 2000, 2010]
_BURL = 'https://raw.githubusercontent.com/aourednik/historical-basemaps/master/geojson/'
BORDERS_CREDIT = 'Borders: historical-basemaps (A. Ourednik, GPL-3.0) · Map: Natural Earth'


def border_file(year):
    """The snapshot at or before `year` (snapshots: 500 BC, 400 BC, 323 BC, 300 BC, 200 BC, 100 BC, 1 BC, AD 100, 200 ...).
    Downloaded once into ~/.hds/borders."""
    y = max([b for b in _BYEARS if b <= year] or [_BYEARS[0]])
    name = f'world_bc{-y}' if y < 0 else f'world_{y}'
    d = os.path.join(os.path.expanduser('~'), '.hds', 'borders'); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name + '.geojson')
    if not os.path.exists(p) or os.path.getsize(p) < 1000:
        print('downloading borders', name, flush=True); urllib.request.urlretrieve(_BURL + name + '.geojson', p + '.part'); os.replace(p + '.part', p)
    return p


_GJ = {}
def _geo(path):
    if path not in _GJ: _GJ[path] = json.load(open(path, encoding='utf-8'))
    return _GJ[path]


def border_names(year):
    return sorted({f['properties'].get('NAME') for f in _geo(border_file(year))['features'] if f['properties'].get('NAME')})


class Atlas:
    """A real map of a region laid out in world coordinates (equirectangular, ~9000 px wide by default).
    atlas = Atlas(lon0=-12, lat0=24, lon1=46, lat1=56)      # the Mediterranean
    world = World(film, atlas.surface)                       # fly over it like any other world
    atlas.xy(12.48, 41.89) -> world x, y of Rome"""
    def __init__(self, lon0, lat0, lon1, lat1, width=9000, sea='#1B2C36', land='#C9B993', coast='#6E5F45', rivers=True):
        self.lon0, self.lat0, self.lon1, self.lat1 = lon0, lat0, lon1, lat1
        self.kx = math.cos(math.radians((lat0 + lat1) / 2)); self.k = width / ((lon1 - lon0) * self.kx)
        self.width, self.height = width, (lat1 - lat0) * self.k
        self.sea, self.land, self.coast = sea, land, coast
        self.land_path = self._paths(_geo(_GEO + 'land.geojson'), pad=4)
        self.river_path = self._lines(_geo(_GEO + 'rivers.geojson'), pad=2) if rivers else None
        self._st = {}

    def xy(self, lon, lat): return (lon - self.lon0) * self.kx * self.k, (self.lat1 - lat) * self.k

    def _in(self, coords, pad):
        for lon, lat in coords[::max(1, len(coords) // 40)]:
            if self.lon0 - pad < lon < self.lon1 + pad and self.lat0 - pad < lat < self.lat1 + pad: return True
        return False

    def _ring(self, path, ring):
        for i, (lon, lat) in enumerate(ring):
            x, y = self.xy(lon, lat)
            path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
        path.close()

    def _paths(self, gj, pad=4, match=None):
        p = skia.Path(); p.setFillType(skia.PathFillType.kWinding)
        for f in gj['features']:
            if match and not match(f['properties'].get('NAME') or ''): continue
            g = f.get('geometry') or {}
            polys = [g['coordinates']] if g.get('type') == 'Polygon' else g.get('coordinates', []) if g.get('type') == 'MultiPolygon' else []
            for poly in polys:
                if not poly or not self._in(poly[0], pad): continue
                for ring in poly: self._ring(p, ring)
        return p

    def _lines(self, gj, pad=2):
        p = skia.Path()
        for f in gj['features']:
            g = f.get('geometry') or {}
            lines = [g['coordinates']] if g.get('type') == 'LineString' else g.get('coordinates', []) if g.get('type') == 'MultiLineString' else []
            for ln in lines:
                if not ln or not self._in(ln, pad): continue
                for i, (lon, lat) in enumerate(ln):
                    x, y = self.xy(lon, lat); p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
        return p

    def state(self, year, names):
        """Path of the states whose NAME matches any of `names` (substring, case-insensitive) in the snapshot for `year`."""
        key = (year, tuple(names))
        if key not in self._st:
            ns = [n.lower() for n in names]
            self._st[key] = self._paths(_geo(border_file(year)), pad=30, match=lambda n: any(k in n.lower() for k in ns))
        return self._st[key]

    def others(self, year):
        key = (year, '*')
        if key not in self._st: self._st[key] = self._paths(_geo(border_file(year)), pad=10, match=lambda n: bool(n))
        return self._st[key]

    # world surface: sea, a soft graticule, land, coast, rivers
    def surface(self, c, view):
        x0, y0, x1, y1 = view
        c.drawRect(skia.Rect(x0 - 50, y0 - 50, x1 + 50, y1 + 50), fp(self.sea))
        for lon in range(int(self.lon0 // 5) * 5, int(self.lon1) + 6, 5):
            x, _ = self.xy(lon, 0); c.drawLine(x, -400, x, self.height + 400, ink(2, '#22394A'))
        for lat in range(int(self.lat0 // 5) * 5, int(self.lat1) + 6, 5):
            _, y = self.xy(0, lat); c.drawLine(-400, y, self.width + 400, y, ink(2, '#22394A'))
        c.drawPath(self.land_path, fp('#000000', 90, blur=30))
        c.drawPath(self.land_path, fp(self.land))
        c.drawPath(self.land_path, ink(3, self.coast))
        if self.river_path is not None: c.drawPath(self.river_path, ink(3, '#5E7F8C', 200))

    def empire(self, keys, color=BLOOD, alpha=150, edge=None, fade=1.4, label=None, others=False):
        """World-space layer: the state's territory changing over time.
        keys: [(t, year, ['Rome', 'Roman Republic', 'Roman Empire'])...]; each key fades into the next over `fade` s.
        Use as  world.under(atlas.empire(keys))  so it sits on the land, under items and labels."""
        keys = sorted(keys, key=lambda k: k[0])
        def draw(c, t):
            if not keys or t < keys[0][0]: return
            if others:
                k = [k for k in keys if k[0] <= t][-1]; c.drawPath(self.others(k[1]), ink(2, '#8C7B5C', 160))
            for i, (t0, year, names) in enumerate(keys):
                t1 = keys[i + 1][0] if i + 1 < len(keys) else 1e9
                a = K(t, t0, fade) * (1 - K(t, t1, fade))
                if a <= 0: continue
                if i == 0: a = K(t, t0, .6) * (1 - K(t, t1, fade))
                p = self.state(year, names)
                c.save(); c.clipPath(self.land_path, doAntiAlias=True)      # borders stop at the coast
                c.drawPath(p, fp(color, alpha * a)); c.drawPath(p, ink(5, edge or color, 255 * a)); c.restore()
        return draw

    def city(self, c, t, t0, name, lon, lat, size=70, v=BONE, dx=26, dy=-22, dot=GOLD, font=None, until=None):
        """A city dot with its name (world space), fading in at t0."""
        if t0 is None or t < t0 or (until and t > until + .4): return
        a = K(t, t0, .5) * (1 - K(t, until, .4) if until else 1)
        x, y = self.xy(lon, lat); r = size * .18 * (.6 + .4 * back(K(t, t0, .5)))
        c.drawCircle(x, y, r * 1.8, fp('#000000', 120 * a, blur=10)); c.drawCircle(x, y, r, fp(dot, 255 * a)); c.drawCircle(x, y, r, ink(4, '#1A1410', 255 * a))
        f = font or CINZEL
        c.drawString(name, x + dx + 3, y + dy + 4, skia.Font(f, size), fp('#000000', 160 * a, blur=6))
        txt(c, name, x + dx, y + dy, size, f, v, a=a)

    def region_label(self, c, t, t0, s, lon, lat, size=120, v=PAPER, a_max=.85, until=None, track=12):
        if t0 is None or t < t0 or (until and t > until + .6): return
        a = a_max * K(t, t0, .8) * (1 - K(t, until, .6) if until else 1); x, y = self.xy(lon, lat)
        txt(c, s, x, y, size, CINZEL, v, 'center', a, track)

    def route(self, c, t, t0, pts, dur=2.0, v=BLOOD, w=12, dash=True, until=None):
        """An arrow drawn along [(lon, lat), ...] over dur seconds (armies, roads, trade)."""
        if t0 is None or t < t0 or (until and t > until + .4): return
        a = 1 - K(t, until, .4) if until else 1; u = ease_out(K(t, t0, dur))
        xy = [self.xy(*p) for p in pts]; seg = [math.dist(xy[i], xy[i + 1]) for i in range(len(xy) - 1)]; L = sum(seg) * u
        p = skia.Path(); p.moveTo(*xy[0]); acc = 0; last = xy[0]; ang = 0
        for i, d in enumerate(seg):
            if acc + d >= L:
                k = (L - acc) / d if d else 0; last = (lerp(xy[i][0], xy[i + 1][0], k), lerp(xy[i][1], xy[i + 1][1], k)); p.lineTo(*last)
                ang = math.atan2(xy[i + 1][1] - xy[i][1], xy[i + 1][0] - xy[i][0]); break
            p.lineTo(*xy[i + 1]); acc += d; last = xy[i + 1]; ang = math.atan2(xy[i + 1][1] - xy[i][1], xy[i + 1][0] - xy[i][0])
        pt = ink(w, v, 255 * a); pt.setStrokeCap(skia.Paint.kRound_Cap)
        if dash: pt.setPathEffect(skia.DashPathEffect.Make([w * 3, w * 2], 0))
        c.drawPath(p, pt)
        if u > .02:
            hd = skia.Path(); s_ = w * 3.2
            hd.moveTo(last[0] + math.cos(ang) * s_, last[1] + math.sin(ang) * s_)
            hd.lineTo(last[0] + math.cos(ang + 2.4) * s_, last[1] + math.sin(ang + 2.4) * s_)
            hd.lineTo(last[0] + math.cos(ang - 2.4) * s_, last[1] + math.sin(ang - 2.4) * s_); hd.close()
            c.drawPath(hd, fp(v, 255 * a))


# ---------------------------------------------------------------- type for history
def year_tag(c, t, t0, year, x=W - 90, y=150, size=110, until=None, sub=None):
    """Big year in the top right (screen space). year: a number (negative = BC) or a fn(t) -> number for a counter."""
    if t0 is None or t < t0 or (until and t > until + .4): return
    a = K(t, t0, .4) * (1 - K(t, until, .4) if until else 1)
    yv = year(t) if callable(year) else year; s = fmt_year(yv)
    w = tw(s, size, CINZEL) + 8 * len(s); wb = max(w, tw(sub, 32, MONO) + 4 * len(sub) if sub else 0)
    c.drawRect(skia.Rect(x - wb - 50, y - size - 30, x + 40, y + (90 if sub else 40)), fp((0, 0, 0), 130 * a, blur=30))
    txt(c, s, x, y, size, CINZEL, BONE, 'right', a, track=8)
    c.drawLine(x - w, y + 22, x, y + 22, ink(4, GOLD, 255 * a))
    if sub: txt(c, sub, x, y + 64, 32, MONO, GOLD, 'right', a, track=4)


def year_counter(keys):
    """fn(t) for year_tag that rolls between [(t, year), ...] (eased), for 'centuries pass' moments."""
    keys = sorted(keys)
    def f(t):
        if t <= keys[0][0]: return keys[0][1]
        for (ta, ya), (tb, yb) in zip(keys, keys[1:]):
            if t < tb: return ya + (yb - ya) * ease_out((t - ta) / (tb - ta))
        return keys[-1][1]
    return f


def timeline(c, t, t0, start, end, marks=(), now=None, x0=170, x1=W - 170, y=H - 110, until=None, eras=()):
    """Screen-space timeline bar. start/end: years (negative = BC). marks: [(year, 'label'), ...] ticks that appear
    in order. now: year or fn(t) for the moving marker. eras: [(y0, y1, 'KINGS', colour), ...] coloured spans."""
    if t0 is None or t < t0 or (until and t > until + .4): return
    a = K(t, t0, .5) * (1 - K(t, until, .4) if until else 1); u = ease_out(K(t, t0, 1.0))
    X = lambda yr: x0 + (x1 - x0) * (yr - start) / (end - start)
    c.drawRect(skia.Rect(x0 - 70, y - 150, x1 + 70, y + 70), fp((0, 0, 0), 140 * a, blur=30))
    for (ea, eb, name, col) in eras:
        c.drawRect(skia.Rect(X(ea), y - 9, X(eb), y + 9), fp(col, 200 * a))
        if X(eb) - X(ea) > tw(name, 24, MONO) + 20: txt(c, name, (X(ea) + X(eb)) / 2, y + 48, 24, MONO, BONE, 'center', a * .9, track=3)
    c.drawLine(x0, y, x0 + (x1 - x0) * u, y, ink(4, BONE, 220 * a))
    prev_right, lift = -1e9, 0
    for i, (yr, lab) in enumerate(marks):
        b = K(t, t0 + .5 + i * .25, .35) * a; xx = X(yr)
        half = max(tw(lab or '', 28, CINZEL), tw(fmt_year(yr), 26, MONO)) / 2 + 14
        lift = 64 if (xx - half < prev_right and lift == 0) else 0          # stagger labels that would touch
        prev_right = xx + half if lift == 0 else max(prev_right, xx + half)
        c.drawLine(xx, y - 18 - lift, xx, y + 18, ink(4 if not lift else 2, GOLD, 255 * b))
        txt(c, fmt_year(yr), xx, y - 32 - lift, 26, MONO, GOLD, 'center', b)
        if lab: txt(c, lab, xx, y - 62 - lift, 28, CINZEL, BONE, 'center', b)
    if now is not None:
        yr = now(t) if callable(now) else now; xx = X(min(max(yr, start), end))
        c.drawCircle(xx, y, 15, fp(BLOOD, 255 * a)); c.drawCircle(xx, y, 15, ink(4, BONE, 255 * a))


def label(c, t, t0, kind, x, y, size=46, until=None, rot=-4):
    """A small tag on a picture: 'LEGEND' (myth, told by the Romans), 'EVIDENCE' (archaeology, documents),
    'HISTORIANS DISAGREE', 'RECONSTRUCTION', or any text. Screen or world space."""
    if t0 is None or t < t0 or (until and t > until + .3): return
    a = K(t, t0, .25) * (1 - K(t, until, .3) if until else 1)
    col = {'LEGEND': '#8E6BB0', 'EVIDENCE': '#4E8A5A', 'HISTORIANS DISAGREE': OCHRE, 'RECONSTRUCTION': '#5C7E9E'}.get(kind.upper(), BLOOD)
    w = tw(kind.upper(), size, MONO) + 4 * len(kind) + 50; s = .8 + .2 * back(K(t, t0, .3))
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.drawRect(skia.Rect(-w / 2 + 6, -size * .9 + 8, w / 2 + 6, size * .55 + 8), fp((0, 0, 0), 120 * a, blur=8))
    c.drawRect(skia.Rect(-w / 2, -size * .9, w / 2, size * .55), fp(col, 235 * a))
    txt(c, kind.upper(), 0, size * .18, size, MONO, '#F6F1E6', 'center', a, track=4)
    c.restore()
    _b._once('thud', t, t0)


def quote(c, t, t0, text, who, x=W / 2, y=H / 2 - 40, size=64, width=1400, until=None):
    """A primary-source quote, set in Playfair italic-ish with the author and source under it (screen space)."""
    if t0 is None or t < t0 or (until and t > until + .4): return
    a = K(t, t0, .6) * (1 - K(t, until, .4) if until else 1)
    words = text.split(); lines = []; cur = ''
    for wd in words:
        if tw(cur + ' ' + wd, size, PLAYFAIR) > width and cur: lines.append(cur); cur = wd
        else: cur = (cur + ' ' + wd).strip()
    lines.append(cur); h = len(lines) * size * 1.3
    c.drawRect(skia.Rect(x - width / 2 - 90, y - h / 2 - 90, x + width / 2 + 90, y + h / 2 + 110), fp((0, 0, 0), 160 * a, blur=40))
    txt(c, '“', x - width / 2 - 40, y - h / 2 + 40, 160, PLAYFAIR, GOLD, a=a)
    for i, ln in enumerate(lines): txt(c, ln, x, y - h / 2 + size + i * size * 1.3, size, PLAYFAIR, BONE, 'center', a)
    txt(c, '— ' + who, x, y + h / 2 + 60, 32, MONO, GOLD, 'center', a, track=3)


# ---------------------------------------------------------------- ancient sets (draw on the 1920x1080 scene frame)
def _sky(c, top='#3D3A52', bottom='#C79A6A', h=760):
    c.drawRect(skia.Rect(0, 0, W, h), sp(skia.GradientShader.MakeLinear([(0, 0), (0, h)], [hx(top), hx(bottom)])))


def hills_village(c, t=0.0, river=True, huts=((640, 640), (760, 610), (880, 650), (1020, 620), (1160, 660)), mode='dusk', smoke=True):
    """The first village: seven soft hills, shepherd huts with thatched roofs, the river in front."""
    _sky(c, '#2F3550' if mode == 'dusk' else '#6F8FB8', '#D79A62' if mode == 'dusk' else '#D9E0D6')
    for (cx, cy, rx, col) in ((300, 760, 520, '#4E5A3A'), (900, 700, 560, '#57653F'), (1500, 750, 520, '#4A5636'), (1150, 800, 700, '#5E6B44')):
        c.drawOval(skia.Rect(cx - rx, cy - rx * .45, cx + rx, cy + rx * .9), fp(col))
    c.drawRect(skia.Rect(0, 860, W, H), fp('#3E4A2E'))
    if river:
        rp = skia.Path(); rp.moveTo(0, 940); rp.cubicTo(500, 880, 1200, 1010, W, 920); rp.lineTo(W, 990); rp.cubicTo(1200, 1080, 500, 950, 0, 1010); rp.close()
        c.drawPath(rp, fp('#5F7C86')); c.drawPath(rp, ink(4, '#2C3A3E'))
    for (x, y) in huts:
        c.drawRect(skia.Rect(x - 46, y - 40, x + 46, y + 30), fp('#7A5A3A')); c.drawRect(skia.Rect(x - 46, y - 40, x + 46, y + 30), ink(4))
        rf = skia.Path(); rf.moveTo(x - 66, y - 34); rf.lineTo(x, y - 110); rf.lineTo(x + 66, y - 34); rf.close(); shape(c, rf, '#A88A50', 4)
        c.drawRect(skia.Rect(x - 12, y - 6, x + 12, y + 30), fp('#2A1E14'))
        if smoke:
            for k in range(4):
                u = ((t * .25 + k * .25 + x * .001) % 1); c.drawCircle(x + 10 + 20 * u + 8 * math.sin(t + k), y - 120 - 140 * u, 10 + 18 * u, fp('#C8C0B0', 90 * (1 - u)))


def temple_row(c, cols=8, x0=360, x1=1560, base=820, top=360, marble='#E6DCC6', shade='#BDAF92', ruin=0.0, mode='day'):
    """A classical temple front: steps, columns, architrave, pediment. ruin 0..1 breaks it (fallen columns, no roof)."""
    _sky(c, '#6E86A8' if mode == 'day' else '#2A2E48', '#E6D5B4' if mode == 'day' else '#B3805A', 900)
    c.drawRect(skia.Rect(0, base + 60, W, H), fp('#8A7A5A'))
    for k in range(3): c.drawRect(skia.Rect(x0 - 60 + k * 20, base + k * 20, x1 + 60 - k * 20, base + 20 + k * 20), fp(marble)); c.drawLine(x0 - 60 + k * 20, base + 20 + k * 20, x1 + 60 - k * 20, base + 20 + k * 20, ink(3, shade))
    step = (x1 - x0) / (cols - 1); r = random.Random(3)
    for i in range(cols):
        x = x0 + i * step; broken = ruin > 0 and r.random() < ruin
        ht = top + (r.uniform(.3, .7) * (base - top) if broken else 0)
        c.drawRect(skia.Rect(x - 34, ht, x + 34, base), fp(marble)); c.drawRect(skia.Rect(x + 8, ht, x + 34, base), fp(shade))
        for f in (-18, 0, 18): c.drawLine(x + f, ht + 10, x + f, base - 10, ink(2, shade))
        c.drawRect(skia.Rect(x - 34, ht, x + 34, base), ink(4))
        if not broken: c.drawRect(skia.Rect(x - 46, top - 24, x + 46, top), fp(marble)); c.drawRect(skia.Rect(x - 46, top - 24, x + 46, top), ink(3))
    if ruin < .5:
        c.drawRect(skia.Rect(x0 - 70, top - 90, x1 + 70, top - 24), fp(marble)); c.drawRect(skia.Rect(x0 - 70, top - 90, x1 + 70, top - 24), ink(4))
        pd = skia.Path(); pd.moveTo(x0 - 90, top - 90); pd.lineTo((x0 + x1) / 2, top - 250); pd.lineTo(x1 + 90, top - 90); pd.close(); shape(c, pd, marble, 4)
    else:
        for k in range(3): c.drawRoundRect(skia.Rect(400 + k * 420, base + 70, 640 + k * 420, base + 130), 30, 30, fp(marble)); c.drawRoundRect(skia.Rect(400 + k * 420, base + 70, 640 + k * 420, base + 130), 30, 30, ink(3))


def senate_hall(c, mode='inside'):
    """The Curia: tiered benches either side, a marble floor, light from high windows."""
    c.drawRect(skia.Rect(0, 0, W, H), fp('#6E5A44'))
    for x in (380, 960, 1540): c.drawRect(skia.Rect(x - 70, 90, x + 70, 300), fp('#E9D9AE')); c.drawRect(skia.Rect(x - 70, 90, x + 70, 300), ink(4))
    c.drawRect(skia.Rect(0, 640, W, H), fp('#B8A888'))
    for k in range(6): c.drawLine(0, 680 + k * 70, W, 680 + k * 70, ink(2, '#9C8C6C'))
    for side in (-1, 1):
        for k in range(3):
            y = 560 + k * 90; xa, xb = (0, 620 - k * 60) if side < 0 else (1300 + k * 60, W)
            c.drawRect(skia.Rect(xa, y, xb, y + 50), fp('#8A6A44')); c.drawRect(skia.Rect(xa, y, xb, y + 50), ink(3))
    for (x, a) in ((380, 1), (960, 1), (1540, 1)):
        bm = skia.Path(); bm.moveTo(x - 70, 300); bm.lineTo(x + 70, 300); bm.lineTo(x + 260, H); bm.lineTo(x - 260, H); bm.close()
        c.drawPath(bm, fp('#FFF2C8', 28))


def city_walls(c, t=0.0, fire=0.0, mode='dusk', towers=(260, 760, 1260, 1700)):
    """Stone city walls with towers; fire 0..1 adds smoke and a red sky (sieges, sacks, the fall)."""
    _sky(c, '#2A2238' if fire > 0 else '#3A4262', '#C2502E' if fire > .3 else '#C98E5E', 820)
    if fire > 0:
        for k in range(10):
            u = (t * .08 + k * .1) % 1; x = 200 + k * 170
            c.drawCircle(x + 60 * math.sin(k + t * .3), 640 - 520 * u, 80 + 140 * u, fp('#2A2420', 150 * fire * (1 - u), blur=40))
    c.drawRect(skia.Rect(0, 560, W, 900), fp('#7E705C'));
    for k in range(0, W, 120):
        c.drawRect(skia.Rect(k, 520, k + 70, 560), fp('#7E705C')); c.drawRect(skia.Rect(k, 520, k + 70, 560), ink(3))
    for x in towers:
        c.drawRect(skia.Rect(x - 90, 400, x + 90, 900), fp('#8A7C66')); c.drawRect(skia.Rect(x - 90, 400, x + 90, 900), ink(4))
        for k in range(3): c.drawRect(skia.Rect(x - 90 + k * 70, 370, x - 50 + k * 70, 400), fp('#8A7C66')); c.drawRect(skia.Rect(x - 90 + k * 70, 370, x - 50 + k * 70, 400), ink(3))
    for yy in range(600, 900, 50):
        off = 0 if (yy // 50) % 2 else 60
        for xx in range(-60 + off, W, 120): c.drawRect(skia.Rect(xx, yy, xx + 120, yy + 50), ink(1.5, '#5E5242'))
    c.drawRect(skia.Rect(0, 560, W, 900), ink(4)); c.drawRect(skia.Rect(0, 900, W, H), fp('#4A4030'))
    if fire > 0:
        for k in range(14):
            x = 60 + k * 140 + 30 * math.sin(k * 7); fl = 30 + 25 * math.sin(t * 9 + k)
            c.drawOval(skia.Rect(x - 26, 560 - fl - 40, x + 26, 560), fp('#F0A030', 220 * fire)); c.drawOval(skia.Rect(x - 12, 560 - fl * .6 - 20, x + 12, 560), fp('#FFE08A', 220 * fire))


# ---------------------------------------------------------------- puppets (ancient Rome; adapt the colours for other eras)
_SK = dict(skin='#D9B48C', skin_d='#B89370')
def _cloth(col, dark=None):
    d = dark or '#' + ''.join(f'{max(0, int(col[i:i + 2], 16) - 32):02x}' for i in (1, 3, 5))
    return dict(suit=col, suit_d=d, shirt=col, tie=col)
CITIZEN = dict(_SK, **_cloth('#C8BBA0'), toga='#ECE6D6', hair='slick', hair_col='#3A2A1E')
SENATOR = dict(_SK, **_cloth('#ECE6D6'), toga='#F0EBDD', toga_stripe=PURPLE, hair='bald', hair_col='#8A8A92')
EMPEROR = dict(_SK, **_cloth('#ECE6D6'), toga='#5E2A78', toga_stripe=GOLD, hat='laurel')
LEGIONARY = dict(_SK, **_cloth('#8A2A25'), armour='#B08A3E', hat='galea')
KING = dict(_SK, **_cloth('#7A2E2A'), toga='#8E3A30', toga_stripe=GOLD, hat='crown', hair='slick', hair_col='#2A1E14')
MATRON = dict(_SK, **_cloth('#8A6A8E'), toga='#A585A8', hat='veil')
BARBARIAN = dict(skin='#E2C09A', skin_d='#C29E78', **_cloth('#6A5A3A'), hair='long', hair_col='#B58A4A', pants='#4A3A2A')
