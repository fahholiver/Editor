"""Sets, props and on-screen graphics for heist and dark-history films.
Every set draws the full 1920x1080 frame (plus a margin for camera pushes) in world coordinates.
Lighting mode for sets: 'day', 'morning', 'dusk', 'night'. Call light(c, mode, pools) after drawing the set and characters."""
import math, random, os, json
import skia
from core import *

AMBIENT = {'day': '#E9ECF4', 'morning': '#C6CFE6', 'dusk': '#A99AC0', 'night': '#4C5CA0', 'inside': '#B9AFA0', 'dark': '#3A4170'}
SKY = {'day': ('#7FA6D8', '#CFE0F2'), 'morning': ('#6F86BE', '#D9C9C2'), 'dusk': ('#3B3F7A', '#D58C6A'), 'night': ('#0A1136', '#24338A')}
SFX_LOG = []                     # (kind, time) events collected while rendering, mixed by audio.py


def sfx(kind, t):
    SFX_LOG.append((kind, round(t, 3)))


def light(c, mode, pools=(), extra=()):
    """Multiply the mode's ambient tint over the frame and punch soft holes where light falls.
    pools: [(x, y, r, strength)]; extra: raw night() light tuples."""
    L = [('pool', x, y, r, a) for (x, y, r, a) in pools] + list(extra)
    night(c, L, ambient=AMBIENT.get(mode, mode))


# ------------------------------------------------------------------ outdoor
def sky(c, mode='day', h=900):
    a, b = SKY.get(mode, SKY['day'])
    c.drawRect(skia.Rect(-400, -300, W + 400, h), sp(linear(0, -300, 0, h, [hx(a), hx(b)])))
    if mode == 'night':
        r = random.Random(7)
        for i in range(90): c.drawCircle(r.uniform(-300, W + 300), r.uniform(-250, h * .55), r.uniform(1, 2.6), fp('#FFFFFF', r.uniform(90, 220)))
    elif mode in ('day', 'morning'):
        for (x, y, s) in ((300, 160, 1.0), (1300, 110, 1.3), (1750, 230, .8)):
            for dx, dy, rr in ((-60, 10, 50), (0, -10, 70), (70, 8, 52), (20, 25, 60)): c.drawCircle(x + dx * s, y + dy * s, rr * s, fp('#FFFFFF', 150))


def far_city(c, base, mode='day', seed=3):
    v = {'night': '#1A2560', 'dusk': '#5A4F86'}.get(mode, '#8E9CC0')
    r = random.Random(seed); x = -360
    while x < W + 360:
        w = r.uniform(90, 200); h = r.uniform(110, 240)
        c.drawRect(skia.Rect(x, base - h, x + w, base + 300), fp(v))
        if mode == 'night':
            for j in range(int(h // 50)):
                for i in range(int(w // 40)):
                    if r.random() < .3: c.drawRect(skia.Rect(x + 12 + i * 40, base - h + 16 + j * 50, x + 24 + i * 40, base - h + 36 + j * 50), fp('#E9CF86', 200))
        x += w + r.uniform(-6, 10)


def facade(c, kind='museum', lit=None, top=210, base=880, mode='day', seed=1, x0=-400, x1=None):
    """Long building front. kind: museum (stone + mansard roof), bank (columns), plain (apartment block).
    lit: (column, row) of one glowing window, counted from 0 at the left / top. Returns the window centres grid."""
    x1 = x1 or W + 400
    stone = {'museum': '#CDB98F', 'bank': '#D8D2C2', 'plain': '#B98E6E'}[kind]
    rect(c, x0, top, x1, base, stone, LW)
    if kind == 'museum':
        poly(c, [(x0 - 20, top), (x0 + 20, top - 110), (x1 - 20, top - 110), (x1 + 20, top)], '#5B6B8A', LW)
        for x in range(x0 + 40, x1, 160):
            rect(c, x + 40, top - 92, x + 92, top - 30, stone, LW * .8); rect(c, x + 52, top - 80, x + 80, top - 40, '#3B4767', LW * .5)
    elif kind == 'bank':
        poly(c, [(x0, top), ((x0 + x1) / 2, top - 150), (x1, top)], stone, LW)
    rect(c, x0, (top + base) / 2 - 30, x1, (top + base) / 2 - 6, '#B8A47A' if kind == 'museum' else '#BDB6A4', LW * .8)
    grid = {}
    rows = ((top + 50, (top + base) / 2 - 46), ((top + base) / 2 + 30, base - 50))
    for ci, x in enumerate(range(x0 + 20, x1, 160)):
        for ri, (y0, y1) in enumerate(rows):
            on = lit is not None and lit == (ci, ri)
            if kind == 'bank' and ri == 1 and ci % 3 == 1:
                rect(c, x + 20, y0, x + 130, base, '#5A4A3A', LW * .7)  # door
            else:
                rect(c, x + 30, y0, x + 120, y1, '#F2D88C' if on else ('#33405F' if mode != 'night' else '#22305A'), LW * .6)
                line(c, x + 75, y0, x + 75, y1, LW * .4); line(c, x + 30, (y0 + y1) / 2, x + 120, (y0 + y1) / 2, LW * .4)
                rect(c, x + 22, y0 - 16, x + 128, y0 - 4, '#B8A47A' if kind == 'museum' else '#BDB6A4', LW * .5)
            grid[(ci, ri)] = (x + 75, (y0 + y1) / 2)
        if kind == 'bank': rect(c, x - 8, top, x + 14, base, '#E6E0D0', LW * .6)
        else: rect(c, x - 6, top, x + 8, base, '#BCA77D', 0)
    return grid


def ground(c, kind='street', base=880, mode='day'):
    """kind: street (pavement + road), quay (stone quay + river), square (cobbles)."""
    if kind == 'quay':
        rect(c, -400, base, W + 400, base + 85, '#6F6E78', LW)
        for x in range(-400, W + 400, 90): line(c, x, base, x + 30, base + 85, LW * .3, v='#5B5A64')
        rect(c, -400, base + 85, W + 400, H + 400, '#2D4A78', LW)
        for i in range(18):
            y = base + 110 + (i % 4) * 22; x = (i * 173) % (W + 300) - 150
            line(c, x, y, x + 90, y, LW * .5, v='#5E7FB8')
    elif kind == 'square':
        c.drawRect(skia.Rect(-400, base, W + 400, H + 400), fp('#8B8478'))
        r = random.Random(4)
        for row in range(9):
            yy = base + 10 + row * 30 + row * row * 1.4; wd = 70 + row * 8
            for k in range(-6, 32):
                xx = k * (wd + 8) + (row % 2) * wd / 2 - 300
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(xx, yy, xx + wd, yy + 20 + row * 2), 8, 8), fp('#9A9284' if r.random() < .7 else '#A59D8E'))
    else:
        rect(c, -400, base, W + 400, base + 70, '#A7A39A', LW)
        rect(c, -400, base + 70, W + 400, H + 400, '#4A4D57', LW)
        for x in range(-400, W + 400, 220): c.drawRect(skia.Rect(x, base + 190, x + 120, base + 204), fp('#E8E4D8'))


def street_lamp(c, x, y_base, y_top):
    rect(c, x - 9, y_top, x + 9, y_base, '#2B2D3C', LW * .8)
    poly(c, [(x - 40, y_top), (x + 40, y_top), (x + 24, y_top - 50), (x - 24, y_top - 50)], '#2B2D3C', LW * .8)
    c.drawRect(skia.Rect(x - 22, y_top - 44, x + 22, y_top - 6), fp('#FFE9A8'))


# ------------------------------------------------------------------ indoor
def gallery(c, mode='inside', gold='#C9A227', wall='#5A4630', ceiling='#3D3550', floor='#6B4E2E', window=True):
    """Grand palace gallery (gilded hall). Back wall at y 180-760, floor below in perspective."""
    c.drawRect(skia.Rect(-400, -300, W + 400, 200), fp(ceiling))
    for i in range(-2, 14):  # painted ceiling panels
        x = i * 170
        rect(c, x + 10, -60, x + 150, 150, '#4B4366', LW * .5)
        c.drawOval(skia.Rect(x + 30, -30, x + 130, 120), fp('#6C5E7E'))
    rect(c, -400, 180, W + 400, 200, gold, LW * .7)
    c.drawRect(skia.Rect(-400, 200, W + 400, 760), fp(wall))
    for i in range(-2, 14):  # pilasters + paintings
        x = i * 170
        rect(c, x - 14, 200, x + 14, 760, gold, LW * .6)
        rect(c, x + 36, 270, x + 134, 420, '#7A5432', LW * .6); rect(c, x + 46, 280, x + 124, 410, '#A7744A' if i % 2 else '#6F7E5A', 0)
        rect(c, x + 46, 470, x + 124, 560, '#7A5432', LW * .5)
    if window:
        rect(c, 1560, 250, 1760, 640, '#BFD9F2', LW); line(c, 1660, 250, 1660, 640, LW * .6); line(c, 1560, 445, 1760, 445, LW * .6)
    rect(c, -400, 740, W + 400, 760, gold, LW * .6)
    c.drawRect(skia.Rect(-400, 760, W + 400, H + 400), fp(floor))
    for i in range(-20, 40):  # parquet converging lines
        x = i * 110; line(c, x, 760, (x - 960) * 2.2 + 960, H + 300, LW * .3, v='#4E3820')
    for y in (820, 900, 1000): line(c, -400, y, W + 400, y, LW * .3, v='#4E3820')


def display_case(c, x, y, w=300, items=(), broken=0.0, gone=False, t=0.0):
    """Glass case on a pedestal; x,y = centre of the pedestal base on the floor. items = jewel kinds.
    broken 0..1 shatters the glass; gone hides the jewels."""
    h_ped, h_gl = 170, 150
    rect(c, x - w / 2, y - h_ped, x + w / 2, y, '#2B2A35', LW)
    rect(c, x - w / 2 - 10, y - h_ped - 12, x + w / 2 + 10, y - h_ped, '#3A3946', LW * .8)
    gy0, gy1 = y - h_ped - 12 - h_gl, y - h_ped - 12
    rect(c, x - w / 2 + 14, gy1 - 20, x + w / 2 - 14, gy1, '#6B1F2A', LW * .6)  # velvet
    if not gone:
        n = max(1, len(items))
        for i, k in enumerate(items): jewel(c, k, x - w / 2 + (i + .5) * w / n, gy1 - 50, .55)
    if broken < 1:
        a = 1 - broken
        c.drawRect(skia.Rect(x - w / 2, gy0, x + w / 2, gy1), fp('#CFE8FF', 60 * a))
        c.drawRect(skia.Rect(x - w / 2, gy0, x + w / 2, gy1), ink(LW * .7, (220, 240, 255), 255 * a))
        c.drawLine(x - w / 2 + 30, gy0 + 20, x - w / 2 + 70, gy0 + 60, ink(4, (255, 255, 255), 160 * a))
    if broken > 0:
        r = random.Random(int(x))
        for i in range(16):  # shards on the floor
            sx = x + r.uniform(-w * .8, w * .8); sy = y + r.uniform(4, 40)
            poly(c, [(sx, sy), (sx + r.uniform(8, 22), sy - r.uniform(4, 14)), (sx + r.uniform(4, 18), sy + 6)], '#DDEEFF', 2)
        for i in range(7):  # jagged edges left on the frame
            ex = x - w / 2 + r.uniform(0, w); poly(c, [(ex, gy0), (ex + 18, gy0), (ex + 9, gy0 + r.uniform(20, 60))], '#DDEEFF', 2)


def control_room(c, mode='dark', screens=16, live=None, t=0.0, feed=None):
    """Security control room: wall of monitors + desk. live = index of the screen that matters (outlined red).
    feed(c, rect, i) can draw something inside screen i."""
    c.drawRect(skia.Rect(-400, -300, W + 400, H + 400), fp('#1B2033'))
    cols = 4; rows = (screens + cols - 1) // cols; sw, sh = 330, 190; x0 = W / 2 - cols * (sw + 20) / 2; y0 = 120
    rect(c, x0 - 30, y0 - 30, x0 + cols * (sw + 20) + 10, y0 + rows * (sh + 20) + 10, '#11141F', LW)
    for i in range(screens):
        cx = x0 + (i % cols) * (sw + 20); cy = y0 + (i // cols) * (sh + 20)
        r = skia.Rect(cx, cy, cx + sw, cy + sh)
        c.drawRect(r, fp('#2E3B4E' if i != live else '#3B4A60'))
        rr = random.Random(i * 7 + int(t * 2))
        for k in range(3): c.drawRect(skia.Rect(cx + rr.uniform(10, 200), cy + rr.uniform(40, 150), cx + rr.uniform(220, 320), cy + rr.uniform(150, 185)), fp('#405068'))
        if feed: c.save(); c.clipRect(r); feed(c, r, i); c.restore()
        c.drawRect(r, ink(LW * .6))
        label(c, f'CAM {i + 1:02d}', cx + 10, cy + 26, 22, '#C8D2E0', font=PATRICK, skew=0)
        if i == live: c.drawRect(skia.Rect(cx - 6, cy - 6, cx + sw + 6, cy + sh + 6), ink(8, RED))
    rect(c, -400, 860, W + 400, H + 400, '#2A2F45', LW)                 # desk
    rect(c, 300, 820, 760, 870, '#151826', LW * .7); rect(c, 1160, 820, 1620, 870, '#151826', LW * .7)
    for x in (360, 1220):
        for k in range(10): c.drawRect(skia.Rect(x + k * 38, 832, x + k * 38 + 30, 846), fp('#3A3F55'))


def office(c, mode='inside', wall='#55607A', window=True, night_city=False):
    c.drawRect(skia.Rect(-400, -300, W + 400, 760), fp(wall))
    for x in range(-400, W + 400, 64): c.drawRect(skia.Rect(x, -300, x + 26, 760), fp('#5D6984'))
    rect(c, -400, 640, W + 400, 760, '#4A3A2E', LW * .8)
    if window:
        rect(c, 150, 110, 760, 600, '#9DB9DE' if not night_city else '#16204E', LW)
        if night_city: far_city(c, 560, 'night')
        line(c, 455, 110, 455, 600, LW * .7); line(c, 150, 355, 760, 355, LW * .7)
    rect(c, 1260, 180, 1520, 380, '#7A5432', LW * .7); rect(c, 1276, 196, 1504, 364, '#B98B5A', 0)
    circ(c, 1700, 240, 70, '#F4EFE2', LW); line(c, 1700, 240, 1700, 195, LW * .7); line(c, 1700, 240, 1735, 252, LW * .7)
    c.drawRect(skia.Rect(-400, 760, W + 400, H + 400), fp('#6E5641'))
    rect(c, 820, 700, 1640, 760, '#6A4A30', LW); rect(c, 860, 760, 1600, 1000, '#5A3E28', LW)
    for y in (800, 880): rect(c, 1300, y, 1560, y + 60, '#6A4A30', LW * .6)


def airport(c, mode='day', board=None):
    """Terminal: tall windows with a plane outside, departures board. board = list of (time, city, gate, status)."""
    c.drawRect(skia.Rect(-400, -300, W + 400, H + 400), fp('#D9DCE2'))
    rect(c, -400, 80, W + 400, 640, '#A9C6E4', LW)
    for x in range(-400, W + 400, 240): rect(c, x - 8, 80, x + 8, 640, '#7C8494', LW * .6)
    # plane outside
    c.save(); c.translate(1250, 470)
    rect(c, -380, -40, 380, 40, '#F4F6FA', LW, r=40); poly(c, [(-60, 0), (120, 0), (40, 150), (-30, 150)], '#E2E6EE', LW)
    poly(c, [(300, -30), (380, -150), (420, -150), (370, -10)], '#C8242C', LW); c.restore()
    c.drawRect(skia.Rect(-400, 640, W + 400, H + 400), fp('#BFC3CA'))
    for i in range(-10, 30): line(c, i * 120, 640, (i * 120 - 960) * 2 + 960, H + 300, LW * .25, v='#A9AEB7')
    rows = board or [('09:55', 'LONDON', 'A12', 'BOARDING'), ('10:20', 'ALGIERS', 'B31', 'BOARDING'), ('10:45', 'NEW YORK', 'C04', 'ON TIME')]
    rect(c, 140, 140, 760, 180 + 64 * len(rows), '#14161E', LW)
    label(c, 'DEPARTURES', 170, 178, 34, '#F2C14E', font=PATRICK, skew=0)
    for i, (tm, city, gate, st) in enumerate(rows):
        y = 236 + i * 64
        for j, s in enumerate((tm, city, gate, st)): label(c, s, 170 + (0, 110, 390, 500)[j], y, 30, '#E8ECF2', font=PATRICK, skew=0)


def hearing(c, mode='inside', seal=True):
    """Wood-panelled hearing room / courtroom. Draw people standing at the bench, then hearing_bench(c) in front of them."""
    c.drawRect(skia.Rect(-400, -300, W + 400, H + 400), fp('#6B4A33'))
    for x in range(-400, W + 400, 140): rect(c, x + 10, 60, x + 130, 600, '#7A563C', LW * .5)
    if seal: circ(c, 960, 190, 90, '#C9A227', LW); circ(c, 960, 190, 60, '#7A563C', LW * .6)
    c.drawRect(skia.Rect(-400, 760, W + 400, H + 400), fp('#4A3424'))


def hearing_bench(c, mics=(560, 960, 1360)):
    rect(c, 240, 620, 1680, 860, '#5A3C27', LW); rect(c, 220, 600, 1700, 630, '#6E4A30', LW)
    for x in mics: line(c, x, 600, x + 30, 540, LW * .6); circ(c, x + 30, 536, 9, '#22222A', LW * .5)


def table(c, felt='#2F6B45'):
    """Top-down tabletop for documents, newspapers and evidence."""
    c.drawRect(skia.Rect(-900, -700, W + 900, H + 700), sp(radial(960, 520, 1300, [hx('#F6EED4'), hx('#E6DBB8'), hx('#CDBF98')], [0, .6, 1])))
    r = random.Random(9)
    for i in range(160): c.drawCircle(r.uniform(-300, W + 300), r.uniform(-200, H + 200), r.uniform(1, 3), fp('#9A8F6E', r.uniform(30, 90)))
    for (ya, yb) in ((-700, 64), (1016, H + 700)): c.drawRect(skia.Rect(-900, ya, W + 900, yb), fp(felt))
    for yy in (64, 1016): line(c, -900, yy, W + 900, yy, LW)


def map_city(c, t, pins=(), route=None, u=0.0, river=True, land='#22306E', title=None, vehicle='scooter'):
    """Stylised city map. pins: [(x, y, 'NAME', appear_time)]. route: [(x, y), ...] drawn up to fraction u with a vehicle."""
    c.drawRect(skia.Rect(-900, -700, W + 900, H + 700), fp('#0E1840'))
    for i in range(-8, 30): c.drawLine(i * 120, -700, i * 120, H + 700, ink(2, '#1A2658')); c.drawLine(-900, i * 120, W + 900, i * 120, ink(2, '#1A2658'))
    blk = random.Random(3)
    for i in range(70):
        x = blk.uniform(-200, W + 200); y = blk.uniform(-100, H + 100); w = blk.uniform(60, 180); h = blk.uniform(40, 120)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, y, x + w, y + h), 10, 10), fp(land))
    if river:
        rv = skia.Path(); rv.moveTo(-300, 380); rv.cubicTo(300, 300, 600, 640, 1000, 560); rv.cubicTo(1400, 480, 1700, 700, 2300, 620)
        p = ink(70, '#2D5A9A'); c.drawPath(rv, p); c.drawPath(rv, ink(4, '#5E7FB8'))
    pos = None
    if route:
        n = 60; pts = []
        for i in range(n + 1):
            f = i / n * (len(route) - 1); j = min(int(f), len(route) - 2); k = f - j
            pts.append((lerp(route[j][0], route[j + 1][0], k), lerp(route[j][1], route[j + 1][1], k)))
        for i, (x, y) in enumerate(pts):
            if i / n <= u:
                if i % 2 == 0: c.drawCircle(x, y, 8, fp(RED))
                pos = (x, y)
    for (x, y, name, t0) in pins:
        a = K(t, t0, .35)
        if a <= 0: continue
        for rr, aa in ((46, 30), (28, 60)): c.drawCircle(x, y, rr * a, fp('#FFD98A', aa))
        circ(c, x, y, 13 * pop(a), '#FFE9A0', LW * .7)
        label(c, name, x, y + 70, 48, CREAM, align='center', stroke=10, alpha=a)
    if pos and vehicle == 'scooter':
        c.save(); c.translate(pos[0], pos[1] - 30); scooter(c, 0, 26, .55, rider='#E8C21A'); c.restore()
    if title: label(c, title, 80, 120, 64, CREAM, stroke=12)


# ------------------------------------------------------------------ props
def jewel(c, kind, x, y, s=1.0, col_stone='#4F8FE0'):
    """Generic jewel icons (not replicas): tiara, necklace, earring, earrings, brooch, bow, crown, diamond, ring."""
    c.save(); c.translate(x, y); c.scale(s, s); g = '#E8C04A'
    if kind == 'tiara':
        poly(c, [(-70, 30), (-56, -10), (-30, 14), (0, -44), (30, 14), (56, -10), (70, 30)], g, LW); circ(c, 0, -10, 13, col_stone, LW * .7)
    elif kind == 'necklace':
        p = skia.Path(); p.moveTo(-60, -40); p.quadTo(0, 60, 60, -40); c.drawPath(p, ink(LW * 2, g)); c.drawPath(p, ink(3))
        poly(c, [(0, 22), (-16, 42), (0, 66), (16, 42)], col_stone, LW * .7)
    elif kind == 'earring':
        circ(c, 0, -40, 9, g, LW * .6); line(c, 0, -31, 0, -10, 5, v=g); poly(c, [(0, -10), (-16, 16), (0, 40), (16, 16)], col_stone, LW * .7)
    elif kind == 'earrings':
        for dx in (-26, 26): circ(c, dx, -36, 8, g, LW * .6); poly(c, [(dx, -24), (dx - 14, 0), (dx, 26), (dx + 14, 0)], col_stone, LW * .7)
    elif kind == 'brooch':
        circ(c, 0, 0, 40, g, LW); circ(c, 0, 0, 20, col_stone, LW * .7)
        for i in range(8): a = i * math.pi / 4; circ(c, 32 * math.cos(a), 32 * math.sin(a), 6, '#FFFFFF', 2)
    elif kind == 'bow':
        poly(c, [(0, 0), (-60, -34), (-60, 34)], g, LW); poly(c, [(0, 0), (60, -34), (60, 34)], g, LW); circ(c, 0, 0, 14, col_stone, LW * .7)
    elif kind == 'crown':
        poly(c, [(-56, 36), (-56, -14), (-30, 8), (0, -40), (30, 8), (56, -14), (56, 36)], g, LW); rect(c, -58, 24, 58, 40, g, LW * .8)
        circ(c, 0, -46, 9, col_stone, LW * .6)
    elif kind == 'diamond':
        poly(c, [(-40, -10), (-22, -34), (22, -34), (40, -10), (0, 40)], '#DFF2FF', LW); line(c, -40, -10, 40, -10, 3); line(c, -10, -34, 0, 40, 2); line(c, 10, -34, 0, 40, 2)
    elif kind == 'ring':
        c.drawCircle(0, 12, 30, ink(10, g)); c.drawCircle(0, 12, 30, ink(2)); poly(c, [(-14, -22), (0, -40), (14, -22), (0, -12)], '#DFF2FF', LW * .6)
    c.restore()


def truck_lift(c, x, y, ext=1.0, target=None, s=1.0):
    """Small truck with a basket lift. x,y = ground under the rear wheel. ext 0..1 raises the basket toward target (x, y).
    Returns the basket floor position (left x, y) so characters can stand in it."""
    c.save(); c.translate(x, y); c.scale(s, s)
    rect(c, -60, -110, 190, -10, '#E6E3DA', LW, r=8); rect(c, 190, -160, 310, -10, '#F1EEE6', LW, r=12)
    rect(c, 215, -140, 295, -90, '#9FC3E8', LW * .7, r=6)
    for wx in (0, 250): circ(c, wx, -5, 34, '#26262D', LW); circ(c, wx, -5, 12, '#9A9AA5', LW * .6)
    c.restore()
    tx, ty = target or (x - 200, y - 450)
    bx, by = lerp(x - 40 * s, tx, ext), lerp(y - 120 * s, ty, ext)
    p = skia.Path(); p.moveTo(x, y - 110 * s); p.lineTo(bx + 60, by + 40)
    arm = skia.Paint(AntiAlias=True, Color=hx('#F2B01E')); arm.setStyle(skia.Paint.kStroke_Style); arm.setStrokeWidth(26 * s); arm.setStrokeCap(skia.Paint.kRound_Cap)
    c.drawPath(p, ink(38 * s)); c.drawPath(p, arm); circ(c, x, y - 110 * s, 20 * s, '#F2B01E', LW)
    return bx, by


def lift_basket_front(c, bx, by, w=190):
    rect(c, bx - 20, by - 8, bx - 20 + w, by + 64, '#F2B01E', LW, r=6)
    for i in range(1, 6): line(c, bx - 20 + i * w / 6, by - 8, bx - 20 + i * w / 6, by + 64, LW * .5)


def scooter(c, x, y, s=1.0, rider=None, face=1, t=0.0):
    """Motor scooter facing right. rider = vest colour to draw a helmeted rider, or None."""
    c.save(); c.translate(x, y); c.scale(s * face, s)
    for wx in (-80, 90): circ(c, wx, -30, 32, '#22222A', LW); circ(c, wx, -30, 10, '#9A9AA5', LW * .5)
    poly(c, [(-120, -60), (40, -60), (70, -130), (100, -130), (110, -50), (90, -40), (-110, -40)], '#3A3F55', LW)
    rect(c, -100, -80, 10, -60, '#1B1E2A', LW * .7)
    line(c, 95, -130, 80, -180, LW); line(c, 60, -185, 100, -180, LW)
    c.restore()
    if rider:
        spec = dict(skin='#C99F70', skin_d='#A57F55', suit='#2B2B33', suit_d='#1E1E25', shirt='#2B2B33', tie='#2B2B33', vest=rider, hat='helmet')
        draw_char3(c, x - 20 * s * face, y - 60 * s, .55 * s, spec, face=.6 * face, arms=('push', 'push'), legs=((-24, 30, 0), (24, 30, 0)), bob=2 * math.sin(t * 12))


def newspaper(c, x, y, rot, masthead, headline, sub='', circle_u=0.0, picture=None, s=1.0):
    """Folded newspaper on a table. picture(c) draws inside the photo box. circle_u 0..1 draws a red marker ring round the headline."""
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.drawRect(skia.Rect(-392, -288, 412, 312), fp((60, 40, 10), 70, blur=12)); rect(c, -400, -300, 400, 300, '#F1EAD6', LW)
    label(c, masthead, 0, -222, 80, INK, font=MARKER, align='center', skew=0)
    c.drawLine(-370, -196, 370, -196, ink(5)); c.drawLine(-370, -184, 370, -184, ink(2.5))
    f = 52 if len(headline) < 26 else 42
    label(c, headline, -360, -118, f, INK, skew=-0.06)
    if sub: label(c, sub, -360, -70, 30, '#4A4A50', skew=0, font=PATRICK)
    rect(c, -360, -40, -60, 262, '#E3DAC2', LW * .6)
    if picture: c.save(); c.clipRect(skia.Rect(-360, -40, -60, 262)); picture(c); c.restore()
    textlines(c, -20, -30, 360, 10)
    if circle_u > 0:
        ring = skia.Path(); ring.addArc(skia.Rect(-384, -176, 384, -82), -170, 356 * ease(circle_u)); c.drawPath(ring, ink(11, RED))
    c.restore()


def textlines(c, x0, y0, x1, n, gap=30, v='#8E8878'):
    r = random.Random(int(x0 + y0))
    for i in range(n): c.drawLine(x0, y0 + i * gap, x1 - r.uniform(0, (x1 - x0) * .3), y0 + i * gap, ink(6, v))


def document(c, x, y, rot, title, sub='', lines=9, stamp_txt=None, stamp_u=0.0, highlight=None, s=1.0, paper='#FBFAF2', title_col='#2A44A8'):
    """Official paper. highlight = (line_index, 'quoted text') draws a yellow highlighted quote line."""
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    c.drawRect(skia.Rect(-312, -348, 332, 372), fp((60, 40, 10), 70, blur=12)); rect(c, -320, -360, 320, 360, paper, LW)
    label(c, title, 0, -270, 44, title_col, align='center', skew=0)
    if sub: label(c, sub, 0, -226, 30, title_col, align='center', skew=0, font=PATRICK)
    c.drawLine(-270, -200, 270, -200, ink(3, title_col)); textlines(c, -260, -160, 270, lines, 38)
    if highlight:
        i, q = highlight; yy = -160 + i * 38
        c.drawRect(skia.Rect(-270, yy - 30, 280, yy + 10), fp('#FFE45C', 200)); label(c, q, -262, yy, 30, INK, skew=0, font=PATRICK)
    if stamp_txt and stamp_u > 0: stamp(c, None, None, stamp_txt, -60, 250, rot=-14, size=78, u=stamp_u)
    c.restore()


def evidence_tag(c, x, y, n, text, u=1.0):
    if u <= 0: return
    k = pop(u); c.save(); c.translate(x, y); c.scale(k, k)
    poly(c, [(-60, -40), (60, -40), (60, 40), (-60, 40), (-80, 0)], '#F2C14E', LW * .7); circ(c, -58, 0, 7, '#FFFFFF', LW * .4)
    label(c, str(n), 6, 16, 52, INK, align='center', font=MARKER, skew=0)
    label(c, text, 0, 90, 34, CREAM, align='center', stroke=9)
    c.restore()


def tool(c, kind, x, y, rot=0, s=1.0):
    """Generic props: cutter (disc cutter), torch (blowtorch), helmet, vest, walkie, gloves, phone, passport, cuffs, cash, bag."""
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    if kind == 'cutter':
        rect(c, -90, -24, 40, 24, '#E0602A', LW, r=10); rect(c, -150, -12, -90, 12, '#22222A', LW, r=6)
        circ(c, 80, 0, 56, '#B9BEC8', LW); circ(c, 80, 0, 12, '#55555F', LW * .6)
    elif kind == 'torch':
        rect(c, -100, -30, 20, 30, '#C8242C', LW, r=14); rect(c, 20, -10, 110, 10, '#8A8A95', LW * .8); poly(c, [(110, -8), (150, 0), (110, 8)], '#5EA8FF', LW * .5)
    elif kind == 'helmet':
        hm = skia.Path(); hm.addCircle(0, 0, 70); shape(c, hm, '#222630', LW)
        rect(c, -52, -20, 52, 30, '#3D5A80', LW * .7, r=20)
    elif kind == 'vest':
        poly(c, [(-80, -90), (-30, -90), (0, -40), (30, -90), (80, -90), (90, 100), (-90, 100)], '#E8C21A', LW)
        for yy in (20, 60): c.drawRect(skia.Rect(-88, yy, 88, yy + 14), fp('#DCE3EA'))
    elif kind == 'walkie':
        rect(c, -34, -70, 34, 80, '#26262D', LW, r=10); line(c, 20, -70, 20, -120, LW); rect(c, -20, -44, 20, 0, '#5E7F6A', LW * .5)
    elif kind == 'gloves':
        for dx in (-50, 50): rect(c, dx - 34, -50, dx + 34, 50, '#3A3A44', LW, r=26)
    elif kind == 'phone':
        rect(c, -40, -80, 40, 80, '#1E2230', LW, r=12); rect(c, -32, -64, 32, 58, '#5E7FB8', LW * .5, r=6)
    elif kind == 'passport':
        rect(c, -60, -84, 60, 84, '#2B3E70', LW, r=8); circ(c, 0, -10, 26, '#C9A227', LW * .5)
    elif kind == 'cuffs':
        for dx in (-40, 40): c.drawCircle(dx, 0, 34, ink(14, '#B9BEC8')); c.drawCircle(dx, 0, 34, ink(2))
        line(c, -8, 0, 8, 0, 10, v='#B9BEC8')
    elif kind == 'cash':
        for a_ in (-16, -4, 9):
            c.save(); c.rotate(a_); rect(c, -130, -70, 130, 70, '#6FA36A', LW); rect(c, -108, -50, 108, 50, '#84B67E', LW * .5); circ(c, 0, 0, 26, '#6FA36A', LW * .5); c.restore()
    elif kind == 'bag':
        poly(c, [(-90, -40), (90, -40), (110, 90), (-110, 90)], '#2B2B33', LW); p = skia.Path(); p.addArc(skia.Rect(-50, -100, 50, -20), 180, 180); c.drawPath(p, ink(LW * 1.4))
    c.restore()


def sparks(c, x, y, t, n=26, spread=(-2.6, -.4), length=90, seed=0):
    r = random.Random(int(t * 30) + seed)
    for i in range(n):
        a = r.uniform(*spread); L = r.uniform(20, length)
        line(c, x, y, x + math.cos(a) * L, y + math.sin(a) * L * -1 + r.uniform(0, 30), 3, v='#FFD36A')
    add_light(c, x, y, 120, '#FFB347', 140)


# ------------------------------------------------------------------ screen graphics (draw after the camera restore)
def _once(kind, t, t0):
    """Log a sound effect the first frame an element appears."""
    if t0 is not None and t0 <= t < t0 + 1 / FPS + 1e-6: sfx(kind, t0)


def poplabel(c, t, t0, s, x, y, size=110, v=LIME, rot=-5, font=None, stroke=15, until=None):
    if t0 is None or t < t0 or (until and t > until): return
    _once('pop', t, t0)
    pu = pop(min((t - t0) / .3, 1)); c.save(); c.translate(x, y); c.rotate(rot); c.scale(pu, pu)
    label(c, s, 0, 0, size, v, font=font, align='center', stroke=stroke, skew=-0.14 if font is None else 0); c.restore()


def stamp(c, t, t0, txt, x, y, rot=-10, size=140, v=RED, u=None):
    """Rubber stamp that slams in. Pass t and t0 (seconds), or u (0..1) when drawing inside a prop."""
    if u is None:
        if t0 is None or t < t0: return
        _once('thud', t, t0); u = (t - t0) / .9
    if u <= 0: return
    sc = 2.6 - 1.6 * ease_out(min(u * 5, 1)); a = min(u * 8, 1); w = text_w(txt, size, MARKER)
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(sc, sc)
    for inset, wd in ((0, 13), (18, 5)):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-w / 2 - 50 + inset, -size * .98 + inset, w / 2 + 50 - inset, size * .36 - inset), 16, 16), ink(wd, v, 255 * a))
    label(c, txt, 0, 0, size, v, font=MARKER, align='center', skew=0, alpha=a); c.restore()


def shake(t, t0, amp=10, dur=.35):
    """Camera shake offset to add to a shot's camera when a stamp lands."""
    if t0 is None or not (t0 <= t < t0 + dur): return 0.0
    return amp * math.sin(t * 90) * (1 - (t - t0) / dur)


def tag(c, t, t0, s, x=70, y=H - 86):
    """Location / time tag, lower left."""
    if t0 is None or t < t0: return
    a = ease_out((t - t0) * 3); w = text_w(s, 44)
    c.save(); c.translate(-50 * (1 - a), 0)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, y - 52, x + w + 64, y + 18), 10, 10), fp((10, 12, 26), 205 * a))
    c.drawRect(skia.Rect(x, y - 52, x + 10, y + 18), fp(GOLD, 255 * a))
    label(c, s, x + 34, y, 44, CREAM, alpha=a, skew=-0.12); c.restore()


def lower_third(c, t, t0, name, sub, x=90, y=920):
    if t0 is None or t < t0: return
    _once('pop', t, t0); a = back(min((t - t0) * 2.6, 1), 1.4); w = max(text_w(name, 76), text_w(sub, 40), 380)
    c.save(); c.translate(x, y); c.scale(a, a)
    rect(c, 0, -74, w + 84, 74, (12, 14, 28), LW * .8); c.drawRect(skia.Rect(3, -71, 19, 71), fp(GOLD))
    label(c, name, 44, 4, 76, CREAM, skew=-0.12); label(c, sub, 46, 54, 40, GOLD, skew=-0.12); c.restore()


def hms(sec):
    sec = int(round(sec)); return f'{sec // 3600:02d}:{sec // 60 % 60:02d}:{sec % 60:02d}'


def clock_bar(c, now, a, b, marks=(), x0=200, x1=W - 200, y=H - 70):
    """Heist timeline along the bottom: a..b in seconds of the day (e.g. 9*3600+30*60), playhead at now."""
    p = min(max((now - a) / (b - a), 0), 1)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0 - 30, y - 56, x1 + 30, y + 30), 16, 16), fp((10, 12, 26), 170))
    c.drawRect(skia.Rect(x0, y - 4, x1, y + 4), fp('#3A4058')); c.drawRect(skia.Rect(x0, y - 4, x0 + (x1 - x0) * p, y + 4), fp(RED))
    for m in marks:
        mx = x0 + (x1 - x0) * (m - a) / (b - a); c.drawRect(skia.Rect(mx - 2, y - 14, mx + 2, y + 14), fp('#9AA3BA'))
        label(c, hms(m)[:5], mx, y + 26, 22, '#9AA3BA', align='center', font=PATRICK, skew=0)
    px = x0 + (x1 - x0) * p; s = hms(now); w = text_w(s, 34, PATRICK)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(px - w / 2 - 14, y - 58, px + w / 2 + 14, y - 16), 8, 8), fp(RED))
    label(c, s, px, y - 26, 34, '#FFFFFF', align='center', font=PATRICK, skew=0)


def cctv_overlay(c, t, cam, clock, zoom=None):
    """Security-camera chrome drawn over a frame that Film has already turned grey and grainy (shot option cctv=True)."""
    c.drawRect(skia.Rect(40, 40, W - 40, H - 40), ink(3, (255, 255, 255), 120))
    for (s, x, al) in ((cam, 70, 'left'), (clock, W - 70, 'right')):
        w = text_w(s, 34, PATRICK); x0 = x if al == 'left' else x - w
        c.drawRect(skia.Rect(x0 - 10, 58, x0 + w + 10, 104), fp((0, 0, 0), 150)); label(c, s, x0, 94, 34, '#FFFFFF', font=PATRICK, skew=0)
    if int(t * 2) % 2: c.drawCircle(84, H - 84, 13, fp('#FF2B2B'))
    label(c, 'REC', 108, H - 72, 34, '#FFFFFF', font=PATRICK, skew=0)
    if zoom: label(c, zoom, W - 70, H - 72, 34, '#FFFFFF', font=PATRICK, skew=0, align='right')


def card(c, t, t0, text, dur, size=140, y=None):
    """Black chapter / punchline card: white handwriting typed word by word across dur seconds. Use with shot card=True."""
    c.drawRect(skia.Rect(-W, -H, 2 * W, 2 * H), fp((0, 0, 0)))
    words = text.split(); tot = sum(len(w) + 1 for w in words); acc = 0; k = 0
    for w_ in words:
        if t >= t0 + dur * acc / tot - .04: k += 1
        acc += len(w_) + 1
    f = skia.Font(FONT_HAND, size); full = f.measureText(text)
    if full > W - 200: f = skia.Font(FONT_HAND, size * (W - 200) / full); full = f.measureText(text)
    if k: c.drawString(' '.join(words[:k]), W / 2 - full / 2, (y or H / 2 + 44), f, fp('#FFFFFF'))


def counter(c, t, t0, dur, value, x, y, prefix='', suffix='', size=150, v=CREAM, label_txt=None):
    """Number that counts up from 0 to value over dur seconds."""
    if t0 is None or t < t0: return
    k = ease_out((t - t0) / dur); n = value * k
    s = prefix + (f'{n:,.0f}' if value >= 100 else f'{n:.1f}'.rstrip('0').rstrip('.')) + suffix
    label(c, s, x, y, size, v, align='center', stroke=16, font=MARKER, skew=0)
    if label_txt: label(c, label_txt, x, y + size * .55, size * .3, CREAM, align='center', stroke=8)
    if k < 1 and int((t - t0) * 20) != int((t - t0 - 1 / FPS) * 20): sfx('tick', t)


def marker_circle(c, t, t0, x, y, rx, ry, dur=.45, v=RED):
    if t0 is None or t < t0: return
    _once('scribble', t, t0); u = ease((t - t0) / dur)
    p = skia.Path(); p.addArc(skia.Rect(x - rx, y - ry, x + rx, y + ry), -100, 350 * u); c.drawPath(p, ink(10, v))


def arrow(c, t, t0, x0, y0, x1, y1, dur=.35, v=LIME, w=10):
    if t0 is None or t < t0: return
    u = ease((t - t0) / dur); ex, ey = lerp(x0, x1, u), lerp(y0, y1, u)
    p = skia.Path(); p.moveTo(x0, y0); p.quadTo((x0 + ex) / 2, min(y0, ey) - 60, ex, ey); c.drawPath(p, ink(w + 6)); c.drawPath(p, ink(w, v))
    if u > .9:
        a = math.atan2(ey - y0, ex - x0)
        poly(c, [(ex + 26 * math.cos(a), ey + 26 * math.sin(a)), (ex + 22 * math.cos(a + 2.4), ey + 22 * math.sin(a + 2.4)), (ex + 22 * math.cos(a - 2.4), ey + 22 * math.sin(a - 2.4))], v, 4)


_IMG = {}
def photo(c, t, t0, path, x, y, w, credit='', caption=None, rot=-3, kb=0.06, dur=6.0):
    """Real photo in a white evidence frame with its credit line, slow Ken Burns zoom. path = local image file."""
    if t0 is None or t < t0: return
    if path not in _IMG: _IMG[path] = skia.Image.open(path)
    img = _IMG[path]; h = w * img.height() / img.width(); a = back(min((t - t0) * 3, 1), 1.3)
    _once('paper', t, t0)
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(a, a)
    c.drawRect(skia.Rect(-w / 2 - 14, -h / 2 - 6, w / 2 + 30, h / 2 + 70), fp((0, 0, 0), 90, blur=14))
    rect(c, -w / 2 - 22, -h / 2 - 22, w / 2 + 22, h / 2 + (70 if credit else 22), '#FAFAF4', LW * .7)
    z = 1 + kb * min((t - t0) / dur, 1); c.save(); c.clipRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2))
    c.drawImageRect(img, skia.Rect(-w / 2 * z, -h / 2 * z, w / 2 * z, h / 2 * z), skia.SamplingOptions(skia.FilterMode.kLinear)); c.restore()
    c.drawRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), ink(3))
    if credit: label(c, credit, -w / 2, h / 2 + 46, 24, '#55555F', font=PATRICK, skew=0)
    c.restore()
    if caption: poplabel(c, t, t0 + .3, caption, x, y - h / 2 - 60, size=72, v=CREAM, rot=-3)


_SNAP = {}
def polaroid(c, t, t0, draw_fn, line_txt, ring=None, key='end'):
    """Ending: draw_fn(canvas) paints a frame once; it freezes into a tilted polaroid with a red ring (x, y, r) and a handwritten line."""
    if key not in _SNAP:
        s_ = skia.Surface(W, H); draw_fn(s_.getCanvas()); finish(s_); vignette(s_.getCanvas(), .5); _SNAP[key] = s_.makeImageSnapshot()
    frame_img = _SNAP[key]; u = K(t, t0, .5); _once('shutter', t, t0)
    c.drawRect(skia.Rect(-W, -H, 2 * W, 2 * H), fp('#1B1D2A'))
    s = lerp(1, .67, ease(u)); c.save(); c.translate(W / 2, H / 2 - 30); c.rotate(-4 * ease(u)); c.scale(s, s)
    rect(c, -W / 2 - 40, -H / 2 - 40, W / 2 + 40, H / 2 + 200, '#FAF6EA', LW)
    c.drawImageRect(frame_img, skia.Rect(-W / 2, -H / 2, W / 2, H / 2), skia.SamplingOptions(skia.FilterMode.kLinear))
    if ring and t > t0 + .5:
        rx, ry, rr = ring; p = skia.Path(); p.addArc(skia.Rect(rx - W / 2 - rr, ry - H / 2 - rr, rx - W / 2 + rr, ry - H / 2 + rr), -90, 360 * ease(K(t, t0 + .5, .5))); c.drawPath(p, ink(14, RED))
    if t > t0 + .9: label(c, line_txt, 0, H / 2 + 130, 90, INK, align='center', font=FONT_HAND, skew=0)
    c.restore()
    if t0 <= t < t0 + .22: c.drawRect(skia.Rect(-W, -H, 2 * W, 2 * H), fp('#FFFFFF', 255 * (1 - (t - t0) / .22)))


def icon_row(c, t, t0, items, y=300, step=.12, title=None, size=1.0):
    """Row of cards that pop in one by one: items = [(jewel_kind_or_tool, 'LABEL')]. Shows a running count."""
    n = len(items); cw = min(190, (W - 200) / n - 16) * size; x0 = W / 2 - n * (cw + 16) / 2
    shown = sum(1 for i in range(n) if t >= t0 + i * step) if t0 is not None and t >= t0 else 0
    if title:
        label(c, f'{shown}', x0, y - 150, 120, '#F2C14E', font=MARKER, skew=0); label(c, title, x0 + 110, y - 170, 48, CREAM, stroke=10)
    for i, (k, lab) in enumerate(items):
        if t0 is None or t < t0 + i * step: continue
        if t < t0 + i * step + 1 / FPS: sfx('pop', t0 + i * step)
        a = pop(min((t - t0 - i * step) / .3, 1)); cx = x0 + i * (cw + 16) + cw / 2
        c.save(); c.translate(cx, y); c.scale(a, a)
        rect(c, -cw / 2, -cw * .62, cw / 2, cw * .62, '#141824', LW * .7, r=16)
        if k in ('tiara', 'necklace', 'earring', 'earrings', 'brooch', 'bow', 'crown', 'diamond', 'ring'): jewel(c, k, 0, -cw * .12, .7 * cw / 190)
        else: tool(c, k, 0, -cw * .12, 0, .5 * cw / 190)
        label(c, lab, 0, cw * .45, 22 * cw / 190, CREAM, align='center', font=PATRICK, skew=0)
        c.restore()


# ------------------------------------------------------------------ extra sets / props
SKINS = [('#F1CFA8', '#D6AF84'), ('#E6BE8E', '#C99F70'), ('#C99266', '#A8734A'), ('#8E5B3E', '#6E4329'), ('#5E3B28', '#472A1A')]
CLOTH = ['#3B4660', '#7A5A3C', '#5A6B4A', '#6A4A6A', '#3F5F72', '#8A3A3A', '#4A4A58', '#2F6B4E', '#B5653A']


def civilian(seed, **over):
    """A random everyday character (tourist, passer-by, staff). Override any key, e.g. civilian(3, hat='cap')."""
    r = random.Random(seed); sk, skd = r.choice(SKINS); su = r.choice(CLOTH)
    d = dict(skin=sk, skin_d=skd, suit=su, suit_d=su, shirt=r.choice(['#F4EFE2', '#DCE6F0', '#F2E2C4']), tie=r.choice(CLOTH),
             hair=r.choice(['slick', 'bald', 'bob', 'long', 'bun', 'curly']), hair_col=r.choice(['#1C1B22', '#3A2A20', '#6B4A2A', '#A08060', '#C9A27A']),
             glasses=r.random() < .25)
    d['suit_d'] = '#' + ''.join(f'{max(0, int(d["suit"][i:i + 2], 16) - 30):02x}' for i in (1, 3, 5))
    d.update(over); return d


def sofa(c, x, y, s=1.0, col='#B5653A'):
    c.save(); c.translate(x, y); c.scale(s, s)
    rect(c, -150, -120, 150, -40, col, LW, r=24); rect(c, -170, -70, 170, 0, col, LW, r=20)
    rect(c, -190, -100, -140, 0, col, LW, r=18); rect(c, 140, -100, 190, 0, col, LW, r=18)
    for lx in (-150, 150): rect(c, lx - 8, 0, lx + 8, 22, '#3A2A20', LW * .6)
    c.restore()


def barrier(c, x, y, w=220, s=1.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    for lx in (-w / 2 + 20, w / 2 - 20): rect(c, lx - 6, -90, lx + 6, 0, '#55555F', LW * .6)
    rect(c, -w / 2, -90, w / 2, -50, '#F4F4F0', LW * .8)
    for i in range(int(w // 40)): poly(c, [(-w / 2 + i * 40, -90), (-w / 2 + i * 40 + 22, -90), (-w / 2 + i * 40 + 2, -50), (-w / 2 + i * 40 - 18, -50)], RED, 0)
    c.drawRect(skia.Rect(-w / 2, -90, w / 2, -50), ink(LW * .8)); c.restore()


def garage(c, open_u=0.0, mode='dark'):
    """Underground lock-up: concrete walls, a roller shutter (open_u 0 closed .. 1 open), strip light."""
    c.drawRect(skia.Rect(-400, -300, W + 400, H + 400), fp('#5B5F68'))
    for x in range(-400, W + 400, 300): rect(c, x, -300, x + 296, 760, '#666A73', LW * .4)
    rect(c, 560, 200, 1360, 760, '#2A2D35', LW)
    sh = 560 * (1 - open_u)
    for i in range(int(sh // 28) + 1): c.drawRect(skia.Rect(570, 200 + i * 28, 1350, min(200 + sh, 200 + i * 28 + 24)), fp('#8D929C'))
    rect(c, 820, 60, 1100, 84, '#F4F4E8', LW * .6)
    c.drawRect(skia.Rect(-400, 760, W + 400, H + 400), fp('#4A4D55'))
    for x in range(-400, W + 400, 260): c.drawRect(skia.Rect(x, 900, x + 140, 914), fp('#E8D24A'))


def vault_door(c, x, y, r=260, u=0.0):
    """Round vault door, u = how far it has swung shut (decorative spin)."""
    circ(c, x, y, r + 40, '#3A3F4A', LW); circ(c, x, y, r, '#8C929E', LW); circ(c, x, y, r * .55, '#A7ADB8', LW * .8)
    for i in range(8):
        a = i * math.pi / 4 + u * 3; line(c, x + math.cos(a) * r * .2, y + math.sin(a) * r * .2, x + math.cos(a) * r * .5, y + math.sin(a) * r * .5, LW * 1.4, v='#55555F')
    circ(c, x, y, r * .16, '#55555F', LW * .8)


def screen_post(c, x, y, w, h, title, body, rot=0, s=1.0):
    """A phone showing a social-media style post (generic, no real platform branding)."""
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    rect(c, -w / 2 - 20, -h / 2 - 50, w / 2 + 20, h / 2 + 50, '#1E2230', LW, r=40)
    rect(c, -w / 2, -h / 2, w / 2, h / 2, '#F4F6FA', LW * .5, r=14)
    circ(c, -w / 2 + 50, -h / 2 + 54, 26, '#3B4660', LW * .5); label(c, title, -w / 2 + 92, -h / 2 + 66, 30, INK, font=PATRICK, skew=0)
    yy = -h / 2 + 130
    for ln in body.split('\n'): label(c, ln, -w / 2 + 30, yy, 34, INK, font=PATRICK, skew=0); yy += 46
    c.restore()


def timer_bars(c, t, t0, rows, x=360, y=380, w=1200):
    """Horizontal bars that grow to their values: rows = [('LABEL', value, max, 'shown text', colour)]."""
    for i, (lab, v, mx, txt, col) in enumerate(rows):
        a = t0 + i * .5
        if t < a: continue
        u = ease_out((t - a) / .8); yy = y + i * 200
        label(c, lab, x, yy - 24, 50, CREAM, stroke=10)
        rect(c, x, yy, x + w, yy + 70, '#141824', LW * .7, r=14)
        rect(c, x, yy, x + w * v / mx * u, yy + 70, col, LW * .7, r=14)
        label(c, txt, x + w * v / mx * u + 30, yy + 56, 64, col, font=MARKER, skew=0)
