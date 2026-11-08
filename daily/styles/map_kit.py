"""Helpers for the map_tales format (copied into the story folder as kit.py), plus face() for any account.
Reference: owner's GeoGlobeTales Short of 2026-11-08 (talking countries on a map). Technique only.

    import kit
    kit.camera(ctx, t, keys, W, H)            # one continuous camera: smooth zoom/pan between keyframes
    kit.face(ctx, x, y, size, 'worried', t)    # cartoon face on any shape (country, house, object)
    kit.year_label(ctx, x, y, '1948', 'Self-government', t, t0)   # serif year + italic label + hand arrow
    kit.crown(ctx, x, y, s)                   # capital / ruler marker
    kit.fill_grow(t, t0, dur)                 # 0..1 ease for a territory colour spreading in
"""
import math

import cairo

PALETTE = {'sea': '#5f95a8', 'land': '#d9c9a3', 'outline': '#1b1b1b',
           'red': '#e0403a', 'blue': '#2f5fd0', 'yellow': '#e3b52c', 'pink': '#e25a5a', 'year': '#ffe14d'}


def _rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def camera(ctx, t, keys, W, H):
    """keys = [(time, cx, cy, zoom), ...] in map coordinates. Interpolates smoothly (ease in/out) and sets the
    transform so (cx, cy) is at the frame centre. The reference has ~2 hard cuts in 80 s: the camera itself is
    the editing, always moving (slow drift even when 'holding')."""
    keys = sorted(keys)
    if t <= keys[0][0]:
        a = b = keys[0]; u = 0
    elif t >= keys[-1][0]:
        a = b = keys[-1]; u = 0
    else:
        i = max(j for j, k in enumerate(keys) if k[0] <= t)
        a, b = keys[i], keys[i + 1]
        u = ease((t - a[0]) / (b[0] - a[0]))
    cx, cy = a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u
    z = math.exp(math.log(a[3]) + (math.log(b[3]) - math.log(a[3])) * u)  # zoom interpolates in log space
    z *= 1 + 0.01 * math.sin(t * 0.7)                                       # never fully still
    ctx.translate(W / 2, H / 2)
    ctx.scale(z, z)
    ctx.translate(-cx, -cy)


MOODS = {  # brow tilt (+ = worried/inner up, - = angry), mouth curve (+ smile, - frown), lids 0..1 closed
    'neutral': (0.0, 0.0, 0.0), 'happy': (0.1, 0.9, 0.0), 'worried': (0.6, -0.5, 0.0),
    'angry': (-0.7, -0.4, 0.25), 'smug': (-0.3, 0.5, 0.45), 'sad': (0.8, -0.9, 0.2),
    'shocked': (0.4, 0.0, 0.0), 'side_eye': (-0.2, -0.2, 0.4),
}


def face(ctx, x, y, size, mood='neutral', t=0.0, look=(0.0, 0.0), arms=False, lid_color=PALETTE['pink']):
    """Big cartoon face: white eyes with black pupils + thick black brows + one-line mouth (open 'O' when
    shocked). Put it on the shape that is the character. Blinks every ~3.5 s; pupils follow `look` (-1..1).
    Change the mood on the word that carries the emotion. lid_color = the colour of the shape it sits on."""
    brow, mouth, lid = MOODS.get(mood, MOODS['neutral'])
    s = size
    blink = 1.0 if (t % 3.5) < 0.12 else lid
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for side in (-1, 1):
        ex, ey, r = x + side * 0.28 * s, y - 0.12 * s, 0.17 * s
        ctx.arc(ex, ey, r, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve()
        ctx.set_source_rgb(0, 0, 0); ctx.set_line_width(0.025 * s); ctx.stroke()
        pr = r * (0.35 if mood == 'shocked' else 0.5)
        ctx.arc(ex + look[0] * r * 0.4, ey + look[1] * r * 0.4, pr, 0, 2 * math.pi); ctx.fill()
        if blink > 0:  # upper lid
            ctx.save(); ctx.new_path(); ctx.arc(ex, ey, r * 0.99, 0, 2 * math.pi); ctx.clip()
            ctx.rectangle(ex - r, ey - r, 2 * r, 2 * r * blink)
            ctx.set_source_rgb(*_rgb(lid_color)); ctx.fill_preserve()
            ctx.set_source_rgb(0, 0, 0); ctx.set_line_width(0.025 * s); ctx.stroke(); ctx.restore()
            ctx.arc(ex, ey, r, 0, 2 * math.pi); ctx.set_line_width(0.025 * s); ctx.stroke()
        by = ey - r * 1.45  # brow: inner end up when worried/sad, down when angry
        ctx.move_to(ex - side * 0.16 * s, by - brow * 0.07 * s)
        ctx.line_to(ex + side * 0.16 * s, by + brow * 0.07 * s)
        ctx.set_line_width(0.06 * s); ctx.stroke()
    my = y + 0.28 * s
    if mood == 'shocked':
        ctx.save(); ctx.translate(x, my); ctx.scale(1, 1.3)
        ctx.arc(0, 0, 0.08 * s, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    else:
        w = 0.2 * s
        ctx.move_to(x - w, my - mouth * 0.06 * s)
        ctx.curve_to(x - w / 2, my + mouth * 0.1 * s, x + w / 2, my + mouth * 0.1 * s, x + w, my - mouth * 0.06 * s)
        ctx.set_line_width(0.035 * s); ctx.stroke()
    if arms:  # thin stick arms down the sides, as in the reference
        for side in (-1, 1):
            ctx.move_to(x + side * 0.55 * s, y + 0.1 * s)
            ctx.curve_to(x + side * 0.75 * s, y + 0.4 * s, x + side * 0.7 * s, y + 0.7 * s, x + side * 0.72 * s, y + 0.9 * s)
            ctx.set_line_width(0.03 * s); ctx.stroke()
    ctx.restore()


def _serif(ctx, size, italic=False):
    ctx.select_font_face('DejaVu Serif', cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def _shadow_text(ctx, x, y, text, rgb):
    ctx.set_source_rgba(0, 0, 0, 0.45); ctx.move_to(x + 3, y + 3); ctx.show_text(text)
    ctx.set_source_rgb(*rgb); ctx.move_to(x, y); ctx.show_text(text)


def year_label(ctx, x, y, year, label, t, t0, size=64, arrow_to=None):
    """'1948 - Self-government': year in yellow serif, label in italic white serif, slight upward slant,
    typed on in 0.4 s from t0; optional hand-drawn arrow to the place it refers to."""
    k = ease((t - t0) / 0.4)
    if k <= 0:
        return
    ctx.save(); ctx.translate(x, y); ctx.rotate(-0.12)
    _serif(ctx, size); _shadow_text(ctx, 0, 0, year, _rgb(PALETTE['year']))
    w = ctx.text_extents(year + ' ').x_advance
    _serif(ctx, size * 0.85, italic=True)
    txt = '- ' + label
    _shadow_text(ctx, w, 0, txt[:max(1, int(len(txt) * k))], (1, 1, 1))
    ctx.restore()
    if arrow_to and k >= 1:
        ax, ay = arrow_to
        ctx.save(); ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(3); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        sx, sy = x + size, y + size * 0.4
        ctx.move_to(sx, sy); ctx.curve_to(sx + 30, sy + 40, ax - 20, ay - 50, ax, ay - 12); ctx.stroke()
        ctx.move_to(ax - 10, ay - 26); ctx.line_to(ax, ay - 12); ctx.line_to(ax + 10, ay - 26); ctx.stroke()
        ctx.restore()


def big_year(ctx, x, y, year, t, t0, size=150):
    """large white serif year centred on the territory (1261, 1397), popping in with a small overshoot"""
    k = (t - t0) / 0.3
    if k <= 0:
        return
    sc = 1 + 0.15 * math.sin(min(k, 1) * math.pi)
    ctx.save(); _serif(ctx, size * sc)
    e = ctx.text_extents(year)
    _shadow_text(ctx, x - e.width / 2, y + e.height / 2, year, (1, 1, 1))
    ctx.restore()


def place_label(ctx, x, y, text, size=34):
    """small black-on-white label box (as the reference's 'Denmark' tag) for a place name"""
    ctx.save()
    ctx.select_font_face('DejaVu Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(size)
    e = ctx.text_extents(text)
    pad = size * 0.3
    ctx.rectangle(x - pad, y - e.height - pad, e.width + 2 * pad, e.height + 2 * pad)
    ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve(); ctx.set_source_rgb(0, 0, 0); ctx.set_line_width(2); ctx.stroke()
    ctx.move_to(x, y); ctx.show_text(text)
    ctx.restore()


def crown(ctx, x, y, s=40):
    """white crown with black outline: capital / who rules"""
    ctx.save(); ctx.translate(x, y)
    ctx.move_to(-s / 2, s / 3); ctx.line_to(-s / 2, -s / 4); ctx.line_to(-s / 4, 0); ctx.line_to(0, -s / 2.5)
    ctx.line_to(s / 4, 0); ctx.line_to(s / 2, -s / 4); ctx.line_to(s / 2, s / 3); ctx.close_path()
    ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve(); ctx.set_source_rgb(0, 0, 0); ctx.set_line_width(s * 0.07); ctx.stroke()
    ctx.restore()


def fill_grow(t, t0, dur=0.8):
    """0..1 for a territory colour spreading in (use as alpha or as a clip radius from its capital)"""
    return ease((t - t0) / dur)


def page_turn(ctx, t, t0, W, H, dur=0.5):
    """the reference's one chapter transition: a white page sweeping across right-to-left (call last)"""
    k = (t - t0) / dur
    if not 0 <= k <= 1:
        return
    x = W * (1 - ease(k) * 1.3)
    ctx.save(); ctx.set_source_rgb(1, 1, 1)
    ctx.move_to(x, 0); ctx.line_to(W * 1.3, 0); ctx.line_to(W * 1.3, H); ctx.line_to(x + 80, H)
    ctx.curve_to(x - 60, H * 0.6, x - 60, H * 0.4, x, 0); ctx.fill()
    ctx.restore()
