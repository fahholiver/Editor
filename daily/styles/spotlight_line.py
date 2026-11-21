"""Visual style "spotlight_line" for the Motion engine: the mindset_explainer look (owner's references, 2026-11-21).

Pure black stage, white glowing line-art, one faceless white figure under a cone spotlight, ticking counters and
one literal visual metaphor per sentence; the camera glides from metaphor to metaphor on one continuous stage.
Our own drawings — only the technique of the references is reused.

Hooked into render.py by daily/bootstrap.py ("visual_style": "spotlight_line"); the file is copied into the story
folder as style.py, so the shots use it as a drawing kit:

    import style as K
    def s_hook(ctx, t, lt, d):
        K.glide(ctx, lt, [(0, 540, 900, 1.0), (d, 540, 940, 1.12)])
        K.stage(ctx)
        K.spotlight(ctx, 540, 1250)
        K.figure(ctx, 540, 1250, pose='arms_up', t=t)
        K.counter(ctx, 540, 520, 0, 1_000_000, K.prog(lt, 0, 2.2), label='NET WORTH')
    K.HOOK = ('FAIL MORE. EARN MORE.', 0.0, 3.0)    # big title in the first seconds (beats the originals)

Every primitive draws in the 1080x1920 scene space after cam()/glide(); `k` (0..1) is an appear/progress value.
Post-processing (post): soft bloom on everything bright, so lines and the figure glow.
"""
import math
import random

import cairo
import numpy as np

from gfx import clamp, ease_out, font, lerp, prog, rrect, smooth, text  # noqa: F401 (re-exported for shots)

BG = (0.02, 0.02, 0.022)
INK = (0.93, 0.93, 0.92)      # lines
FIG = (0.97, 0.97, 0.96)      # figure fill
DIM = (0.36, 0.36, 0.37)      # secondary lines / unlit things
KEY_COLOR = '#ffd54a'          # caption key words (the single accent; the scene stays black & white)
FLOOR_Y = 1250
HOOK = None                    # (title, t0, t1) drawn big at the top while t0 <= t < t1
BLOOM = 0.55                   # glow strength
THOUSANDS = ','                # ',' en / '.' pt, de, fr ...


def _rgb(ctx, c, a=1.0):
    ctx.set_source_rgba(c[0], c[1], c[2], a)


def _stroke(ctx, w=5, c=INK, a=1.0):
    _rgb(ctx, c, a)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def fmt(v, prefix='$'):
    return '%s%s' % (prefix, '{:,}'.format(int(round(v))).replace(',', THOUSANDS))


# ------------------------------------------------------------------ camera / stage

def glide(ctx, lt, keys):
    """camera through keyframes [(time, cx, cy, zoom), ...] with smooth easing (one continuous stage)"""
    if lt <= keys[0][0]:
        _, x, y, z = keys[0]
    elif lt >= keys[-1][0]:
        _, x, y, z = keys[-1]
    else:
        for a, b in zip(keys, keys[1:]):
            if a[0] <= lt <= b[0]:
                k = smooth((lt - a[0]) / max(1e-6, b[0] - a[0]))
                x, y, z = lerp(a[1], b[1], k), lerp(a[2], b[2], k), lerp(a[3], b[3], k)
                break
    ctx.translate(540, 960)
    ctx.scale(z, z)
    ctx.translate(-x, -y)


def stage(ctx, floor=FLOOR_Y, dashed=True, a=1.0):
    ctx.rectangle(-4000, -4000, 9000, 9000)
    _rgb(ctx, BG)
    ctx.fill()
    if floor is not None:
        ctx.move_to(-2000, floor)
        ctx.line_to(3000, floor)
        if dashed:
            ctx.set_dash([10, 14])
        _stroke(ctx, 3, DIM, 0.8 * a)
        ctx.set_dash([])


def spotlight(ctx, x, floor=FLOOR_Y, top=None, w=260, a=1.0, lamp=True):
    """cone of light from a ceiling lamp onto the floor at x"""
    top = floor - 1050 if top is None else top
    g = cairo.LinearGradient(0, top, 0, floor)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.20 * a)
    g.add_color_stop_rgba(1, 1, 1, 1, 0.07 * a)
    ctx.move_to(x - 34, top)
    ctx.line_to(x + 34, top)
    ctx.line_to(x + w, floor)
    ctx.line_to(x - w, floor)
    ctx.close_path()
    ctx.set_source(g)
    ctx.fill()
    r = cairo.RadialGradient(x, floor, 10, x, floor, w * 1.1)
    r.add_color_stop_rgba(0, 1, 1, 1, 0.32 * a)
    r.add_color_stop_rgba(1, 1, 1, 1, 0)
    ctx.save()
    ctx.translate(x, floor)
    ctx.scale(1, 0.16)
    ctx.arc(0, 0, w * 1.1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source(r)
    ctx.fill()
    if lamp:
        ctx.move_to(x, top - 400)
        ctx.line_to(x, top - 30)
        _stroke(ctx, 3, DIM, a)
        ctx.move_to(x - 44, top)
        ctx.line_to(x - 26, top - 34)
        ctx.line_to(x + 26, top - 34)
        ctx.line_to(x + 44, top)
        ctx.close_path()
        _rgb(ctx, INK, a)
        ctx.fill()


# ------------------------------------------------------------------ the figure

def figure(ctx, x, y=FLOOR_Y, s=1.0, pose='stand', t=0.0, a=1.0, col=FIG, face_left=False):
    """faceless white bean figure standing on y. pose: stand, arms_up, point, push, sit, think, slump"""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(-s if face_left else s, s)
    bob = 3 * math.sin(t * 2.4)
    if pose == 'sit':
        ctx.translate(0, 40)
    if pose == 'slump':
        ctx.rotate(0.12)
    _rgb(ctx, col, a)
    # body: rounded trapezoid
    ctx.move_to(-46, 0)
    ctx.curve_to(-52, -80, -44, -150 + bob, 0, -158 + bob)
    ctx.curve_to(44, -150 + bob, 52, -80, 46, 0)
    ctx.close_path()
    ctx.fill()
    hy = -200 + bob + (14 if pose == 'slump' else 0)
    ctx.arc(0, hy, 36, 0, 2 * math.pi)
    ctx.fill()
    arms = {
        'stand': [((-34, -120), (-52, -40)), ((34, -120), (52, -40))],
        'arms_up': [((-34, -130), (-80, -250 + 8 * math.sin(t * 6))), ((34, -130), (80, -250 + 8 * math.sin(t * 6 + 1)))],
        'point': [((-34, -120), (-52, -40)), ((34, -125), (130, -150))],
        'push': [((30, -120), (110, -110)), ((30, -100), (112, -80))],
        'sit': [((30, -120), (120, -105 + 6 * math.sin(t * 9))), ((30, -110), (116, -90 + 6 * math.cos(t * 9)))],
        'think': [((-34, -120), (-52, -40)), ((30, -125), (24, -185))],
        'slump': [((-34, -110), (-44, -20)), ((34, -110), (44, -20))],
    }[pose]
    for (sx, sy), (ex, ey) in arms:
        ctx.move_to(sx, sy + bob)
        ctx.line_to(ex, ey + bob)
        _stroke(ctx, 26, col, a)
    ctx.restore()


def crowd(ctx, x0, x1, y=FLOOR_Y, n=6, s=0.6, lit=None, a=1.0, t=0.0):
    """a row of grey figures; index `lit` is the white one (the viewer)"""
    for i in range(n):
        x = lerp(x0, x1, i / max(1, n - 1))
        figure(ctx, x, y, s, t=t + i, a=a, col=FIG if i == lit else DIM)


# ------------------------------------------------------------------ numbers and labels

def counter(ctx, x, y, v0, v1, k, label=None, size=120, prefix='$', a=1.0, ease=True):
    """a number that ticks from v0 to v1 as k goes 0..1 (the odometer feel of the references)"""
    kk = smooth(k) if ease else clamp(k)
    v = v0 + (v1 - v0) * kk
    if 0 < kk < 1:   # last digits flicker while it runs
        v += random.Random(int(k * 997)).randint(0, 9)
    if label:
        text(ctx, label.upper(), x, y - size * 0.95, size * 0.24, '#9a9a9a', weight='x', a=a)
    text(ctx, fmt(v, prefix), x, y, size, '#ffffff', weight='b', a=a)


def label(ctx, s, x, y, size=30, a=1.0, box=True, inverted=False):
    """small ALL-CAPS tag (in a pill if box)"""
    s = s.upper()
    font(ctx, size, weight='x')
    w = ctx.text_extents(s).x_advance
    if box:
        rrect(ctx, x - w / 2 - 22, y - size * 0.95, w + 44, size * 1.45, size * 0.7)
        if inverted:
            _rgb(ctx, INK, a)
            ctx.fill()
        else:
            _rgb(ctx, BG, 0.9 * a)
            ctx.fill_preserve()
            _stroke(ctx, 3, INK, a)
    text(ctx, s, x, y, size, '#111111' if inverted else '#f2f2f2', weight='x', a=a)


def hook_title(ctx, t, title, t0, t1, y=230):
    """big hook title in the first seconds (on screen from frame 1: muted viewers get the hook too)"""
    if not (t0 <= t < t1):
        return
    k = ease_out((t - t0) / 0.18) * (1 - smooth((t - (t1 - 0.25)) / 0.25))
    words = title.upper().split()
    lines, cur = [], ''
    for w in words:
        if len(cur) + len(w) > 14 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    lines.append(cur)
    for i, ln in enumerate(lines):
        size = 104
        font(ctx, size, weight='b')
        wd = ctx.text_extents(ln).x_advance
        if wd > 960:
            size *= 960 / wd
        yy = y + i * size * 1.05
        font(ctx, size, weight='b')
        e = ctx.text_extents(ln)
        ctx.move_to(540 - e.x_advance / 2, yy)
        ctx.text_path(ln)
        ctx.set_source_rgba(0, 0, 0, 0.9 * k)
        ctx.set_line_width(14)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
        ctx.set_source_rgba(1, 1, 1, k)
        ctx.fill()


# ------------------------------------------------------------------ metaphors

def thought_cloud(ctx, x, y, w=420, h=230, k=1.0, content=None, from_xy=None):
    """thought cloud (bubbles rise from from_xy = the figure's head); content(ctx, x, y) draws inside"""
    if from_xy:
        for i, f in enumerate((0.25, 0.5, 0.75)):
            if k > f * 0.6:
                bx, by = lerp(from_xy[0], x, f), lerp(from_xy[1], y + h / 2, f)
                ctx.arc(bx, by, 8 + 8 * i, 0, 2 * math.pi)
                _rgb(ctx, BG)
                ctx.fill_preserve()
                _stroke(ctx, 4)
    kk = ease_out(k)
    if kk <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(kk, kk)
    def path():
        ctx.new_path()
        for i in range(9):
            an = 2 * math.pi * i / 9
            ctx.new_sub_path()
            ctx.arc(math.cos(an) * w * 0.36, math.sin(an) * h * 0.32, h * 0.3, 0, 2 * math.pi)
        ctx.save()
        ctx.scale(w * 0.42, h * 0.4)
        ctx.new_sub_path()
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
    path()
    _rgb(ctx, INK)
    ctx.set_line_width(10)
    ctx.stroke()
    path()
    _rgb(ctx, BG)
    ctx.fill()
    if content:
        content(ctx, 0, 0)
    ctx.restore()


def desk(ctx, x, y=FLOOR_Y, s=1.0, screen=None, a=1.0, t=0.0):
    """desk + chair + monitor; screen(ctx, cx, cy, w, h) draws the screen content"""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.rectangle(-220, -190, 440, 14)
    _rgb(ctx, INK, a)
    ctx.fill()
    for lx in (-200, 200):
        ctx.move_to(lx, -176)
        ctx.line_to(lx, 0)
        _stroke(ctx, 8, INK, a)
    rrect(ctx, -150, -470, 300, 200, 14)
    _rgb(ctx, BG)
    ctx.fill_preserve()
    _stroke(ctx, 7, INK, a)
    ctx.move_to(0, -270)
    ctx.line_to(0, -190)
    _stroke(ctx, 10, INK, a)
    if screen:
        screen(ctx, 0, -370, 280, 180)
    else:
        for i in range(4):
            ctx.move_to(-110, -430 + i * 34)
            ctx.line_to(-110 + (180 if i % 2 else 220) * (0.6 + 0.4 * math.sin(t * 2 + i) ** 2), -430 + i * 34)
            _stroke(ctx, 9, DIM, a)
    ctx.restore()


def bars(ctx, x, y, values, k=1.0, w=300, h=260, a=1.0, lit=None):
    """bar chart growing with k; `lit` index is white, the rest grey"""
    n = len(values)
    bw = w / n * 0.62
    mx = max(values) or 1
    for i, v in enumerate(values):
        hh = h * v / mx * ease_out(k * 1.4 - i * 0.4 / n)
        bx = x - w / 2 + (i + 0.5) * w / n - bw / 2
        rrect(ctx, bx, y - hh, bw, hh, 6)
        _rgb(ctx, FIG if (lit is None or i == lit) else DIM, a)
        ctx.fill()
    ctx.move_to(x - w / 2 - 20, y)
    ctx.line_to(x + w / 2 + 20, y)
    _stroke(ctx, 4, INK, a)


def hill(ctx, x0, y0, x1, y1, k=1.0, boulder=None, push_t=0.0):
    """S-curve from (x0,y0) up to (x1,y1); boulder = (pos 0..1, radius, text) pushed up by a figure"""
    def pt(u):
        return x0 + (x1 - x0) * u, y0 + (y1 - y0) * smooth(u)
    ctx.move_to(*pt(0))
    for i in range(1, 41):
        ctx.line_to(*pt(i / 40 * k))
    _stroke(ctx, 6)
    if boulder:
        u, r, s = boulder
        bx, by = pt(u)
        e = 0.01
        dx, dy = pt(u + e)[0] - pt(u - e)[0], pt(u + e)[1] - pt(u - e)[1]
        nl = math.hypot(dx, dy)
        nx, ny = dy / nl, -dx / nl
        cx, cy = bx + nx * r, by + ny * r
        ang = math.atan2(dy, dx)
        figure(ctx, bx - dx / nl * (r + 70), by - dy / nl * (r + 70), 0.8, pose='push', t=push_t)
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        _rgb(ctx, FIG)
        ctx.fill()
        if s:
            ctx.save()
            ctx.translate(cx, cy)
            text(ctx, s, 0, r * 0.12, r * 0.42, '#111111', weight='b')
            ctx.restore()
        _ = ang


def stairs(ctx, x, y, n, k=1.0, step_w=110, step_h=70, labels=None, a=1.0):
    """steps appearing one by one (k 0..1); returns the top of the last visible step (for the figure)"""
    vis = n * clamp(k)
    top = (x, y)
    for i in range(n):
        kk = clamp(vis - i)
        if kk <= 0:
            break
        sx, sy = x + i * step_w, y - (i + 1) * step_h
        ctx.rectangle(sx, sy + step_h * (1 - ease_out(kk)), step_w, step_h * ease_out(kk))
        _rgb(ctx, BG)
        ctx.fill_preserve()
        _stroke(ctx, 4, INK, a)
        if labels and i < len(labels) and kk > 0.5:
            text(ctx, labels[i].upper(), sx + step_w / 2, sy + step_h * 0.62, 22, '#d8d8d8', weight='x', a=a)
        top = (sx + step_w / 2, sy)
    return top


def dial(ctx, x, y, r, v, label_text=None, a=1.0):
    """half-circle gauge, needle at v (0..1)"""
    ctx.arc(x, y, r, math.pi, 2 * math.pi)
    _stroke(ctx, 8, INK, a)
    for i in range(11):
        an = math.pi + math.pi * i / 10
        ctx.move_to(x + math.cos(an) * r * 0.86, y + math.sin(an) * r * 0.86)
        ctx.line_to(x + math.cos(an) * r * 0.96, y + math.sin(an) * r * 0.96)
        _stroke(ctx, 4, INK, a)
    an = math.pi + math.pi * clamp(v)
    ctx.move_to(x, y)
    ctx.line_to(x + math.cos(an) * r * 0.8, y + math.sin(an) * r * 0.8)
    _stroke(ctx, 9, FIG, a)
    ctx.arc(x, y, 14, 0, 2 * math.pi)
    _rgb(ctx, FIG, a)
    ctx.fill()
    if label_text:
        text(ctx, label_text.upper(), x, y + 60, 30, '#cfcfcf', weight='x', a=a)


def funnel(ctx, x, y, k=1.0, top='INPUT', bottom='OUTCOME', a=1.0, t=0.0):
    """funnel/machine: things fall into the top, one result comes out (cause -> effect)"""
    ctx.move_to(x - 170, y - 260)
    ctx.line_to(x + 170, y - 260)
    ctx.line_to(x + 50, y - 120)
    ctx.line_to(x + 50, y)
    ctx.line_to(x - 50, y)
    ctx.line_to(x - 50, y - 120)
    ctx.close_path()
    _rgb(ctx, BG)
    ctx.fill_preserve()
    _stroke(ctx, 6, INK, a)
    label(ctx, top, x, y - 300, 26, a)
    for i in range(5):
        ph = (t * 0.9 + i / 5) % 1
        ctx.rectangle(x - 60 + 30 * math.sin(i * 2.3), y - 520 + ph * 260, 22, 22)
        _rgb(ctx, INK, a * (1 - ph) * clamp(k * 2))
        ctx.fill()
    if k > 0.5:
        kk = ease_out((k - 0.5) * 2)
        label(ctx, bottom, x + 260 * kk, y - 40, 26, a * kk, inverted=True)


def cards(ctx, rows, x=540, y=600, k=1.0, lit=None, cw=96, chh=120, gap=26, a=1.0):
    """family-tree / grid of grey person cards; `lit` = (row, col) is the white card with a '?' until k=1"""
    for r, n in enumerate(rows):
        for c in range(n):
            kk = ease_out(k * len(rows) - r)
            if kk <= 0:
                continue
            cx = x + (c - (n - 1) / 2) * (cw + gap)
            cy = y + r * (chh + gap * 2)
            on = lit == (r, c)
            rrect(ctx, cx - cw / 2, cy, cw, chh, 12)
            _rgb(ctx, BG)
            ctx.fill_preserve()
            _stroke(ctx, 4, FIG if on else DIM, a * kk)
            if on and k < 1:
                text(ctx, '?', cx, cy + chh * 0.66, 60, '#ffffff', weight='b', a=a * kk)
            else:
                figure(ctx, cx, cy + chh - 14, 0.36, a=a * kk, col=FIG if on else DIM)


def house(ctx, x, y=FLOOR_Y, s=1.0, a=1.0, big=False):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * (1.5 if big else 1), s * (1.3 if big else 1))
    ctx.move_to(-120, 0)
    ctx.line_to(-120, -150)
    ctx.line_to(0, -240)
    ctx.line_to(120, -150)
    ctx.line_to(120, 0)
    ctx.close_path()
    _rgb(ctx, BG)
    ctx.fill_preserve()
    _stroke(ctx, 6, INK, a)
    for wx in (-70, 30) if big else (-25,):
        rrect(ctx, wx, -120, 40, 40, 4)
        _rgb(ctx, INK, 0.8 * a)
        ctx.fill()
    ctx.restore()


def bills(ctx, t, x, y, n=18, k=1.0, spread=420, seed=4):
    """banknotes flying up and floating down around (x, y)"""
    rng = random.Random(seed)
    for i in range(int(n * clamp(k))):
        ph = (t * (0.35 + rng.random() * 0.3) + rng.random()) % 1
        bx = x + (rng.random() - 0.5) * spread + 40 * math.sin(t * 2 + i)
        by = y - 420 + ph * 520
        ctx.save()
        ctx.translate(bx, by)
        ctx.rotate(math.sin(t * 3 + i) * 0.8)
        ctx.rectangle(-26, -12, 52, 24)
        _rgb(ctx, INK, 0.9 * (1 - ph * 0.6))
        ctx.fill()
        ctx.restore()


def pile(ctx, x, y=FLOOR_Y, k=1.0, w=360, h=260, a=1.0):
    """pyramid of coins/blocks that grows with k"""
    rows = int(10 * clamp(k)) + (1 if k > 0 else 0)
    for r in range(rows):
        n = 10 - r
        for c in range(n):
            bx = x + (c - (n - 1) / 2) * w / 10
            by = y - (r + 1) * h / 10
            rrect(ctx, bx - w / 22, by, w / 11, h / 11, 3)
            _rgb(ctx, INK, a)
            ctx.fill()


def brain(ctx, x, y, s=1.0, a=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for sx in (-1, 1):
        ctx.save()
        ctx.scale(sx, 1)
        ctx.move_to(4, -80)
        ctx.curve_to(90, -110, 140, -30, 110, 20)
        ctx.curve_to(120, 70, 50, 100, 4, 80)
        _stroke(ctx, 8, INK, a)
        ctx.move_to(30, -40)
        ctx.curve_to(70, -50, 60, 0, 90, 10)
        ctx.move_to(24, 30)
        ctx.curve_to(60, 20, 70, 60, 40, 70)
        _stroke(ctx, 6, INK, a)
        ctx.restore()
    ctx.move_to(0, -80)
    ctx.line_to(0, 80)
    _stroke(ctx, 6, INK, a)
    ctx.restore()


def wallet(ctx, x, y, s=1.0, a=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rrect(ctx, -110, -70, 220, 140, 18)
    _stroke(ctx, 8, INK, a)
    rrect(ctx, 30, -26, 90, 52, 12)
    _stroke(ctx, 6, INK, a)
    ctx.arc(62, 0, 8, 0, 2 * math.pi)
    _rgb(ctx, INK, a)
    ctx.fill()
    ctx.restore()


def calendar(ctx, x, y, month, a=1.0, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rrect(ctx, -80, -80, 160, 170, 10)
    _rgb(ctx, BG)
    ctx.fill_preserve()
    _stroke(ctx, 5, INK, a)
    ctx.rectangle(-80, -80, 160, 44)
    _rgb(ctx, INK, a)
    ctx.fill()
    text(ctx, month.upper(), 0, 40, 50, '#ffffff', weight='b', a=a)
    ctx.restore()


def progress(ctx, x, y, w, k, label_text=None, a=1.0):
    rrect(ctx, x - w / 2, y - 16, w, 32, 16)
    _stroke(ctx, 4, INK, a)
    rrect(ctx, x - w / 2 + 6, y - 10, (w - 12) * clamp(k), 20, 10)
    _rgb(ctx, FIG, a)
    ctx.fill()
    if label_text:
        text(ctx, label_text.upper(), x - w / 2, y - 34, 26, '#cfcfcf', align='l', weight='x', a=a)
        text(ctx, '%d%%' % round(100 * clamp(k)), x + w / 2, y - 34, 26, '#ffffff', align='r', weight='x', a=a)


def equals(ctx, x, y, left, right, sign='=', a=1.0, size=64):
    """'$3,200 = $3,200' style comparison"""
    label(ctx, left, x - 200, y, size * 0.5, a)
    text(ctx, sign, x, y, size, '#ffffff', weight='b', a=a)
    label(ctx, right, x + 200, y, size * 0.5, a)


def ring(ctx, x, y, r, k, a=1.0):
    """attention circle drawn around something (dashed, rotating)"""
    ctx.save()
    ctx.set_dash([18, 12], k * 60)
    ctx.arc(x, y, r * (0.9 + 0.1 * ease_out(k)), -math.pi / 2, -math.pi / 2 + 2 * math.pi * ease_out(k))
    _stroke(ctx, 5, INK, a)
    ctx.restore()


# ------------------------------------------------------------------ engine hooks (bootstrap.apply_style)

def after_scene(surf, W, H):
    pass


def bezel(ctx, W, H):
    pass


def overlay(surf, W, H, draw):
    ctx = cairo.Context(surf)
    draw(ctx)


def game_hud(ctx, t, dur):
    """the hook title for the first seconds (HOOK set by the story's render.py)"""
    if HOOK:
        hook_title(ctx, t, *HOOK)


def _blur_small(x, r):
    for _ in range(3):   # 3 box passes ~ gaussian
        for ax in (0, 1):
            c = np.cumsum(np.pad(x, [(r + 1, r) if i == ax else (0, 0) for i in range(3)], mode='edge'), axis=ax)
            x = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return x


def _up(x, f, H, W):
    h, w, _ = x.shape
    ys = np.clip((np.arange(H) + 0.5) / f - 0.5, 0, h - 1)
    xs = np.clip((np.arange(W) + 0.5) / f - 0.5, 0, w - 1)
    y0, x0 = ys.astype(int), xs.astype(int)
    y1, x1 = np.minimum(y0 + 1, h - 1), np.minimum(x0 + 1, w - 1)
    fy, fx = (ys - y0)[:, None, None], (xs - x0)[None, :, None]
    a = x[y0][:, x0] * (1 - fx) + x[y0][:, x1] * fx
    b = x[y1][:, x0] * (1 - fx) + x[y1][:, x1] * fx
    return a * (1 - fy) + b * fy


def post(rgb):
    """bloom: bright parts glow softly (rgb float32 HxWx3, BGR, 0..255)"""
    H, W, _ = rgb.shape
    f = 8
    small = rgb[:H // f * f, :W // f * f].reshape(H // f, f, W // f, f, 3).mean((1, 3))
    bright = np.clip(small - 120, 0, None) * 1.6
    glow = _blur_small(bright, 3) * 0.6 + _blur_small(bright, 9) * 0.4
    return rgb + BLOOM * _up(glow, f, H, W)
