"""Helpers for the cursed_object format (copied into the story folder as kit.py).
Use from SHOTS functions: import kit; ... (German labels by default)."""
import math

import cairo

LABELS = {'de': ('Gefällt mir', 'Folgen'), 'fr': ("J'aime", "S'abonner"), 'en': ('Like', 'Follow')}
LANG = 'de'


def hip_sway(ctx, t, hip_x, hip_y, phase=0.0, amp_deg=6.0, hz=1.0, bob=6.0):
    """The reference's constant idle 'hip' rock: the whole body above the hips tilts side to side around the
    hip point (~1 cycle/s, ±6°), with a small up-down bob on each side (twice per cycle).
    Call ctx.save(); kit.hip_sway(ctx, t, hx, hy, phase); <draw torso+head+arms>; ctx.restore().
    Give every character a different phase (0, 1.3, 2.1…) so they don't move in sync. Legs stay still.
    Bigger amp (10–12°) and hz 1.6 when happy/smug; amp 0 for the blank/frozen reversal shot."""
    w = 2 * math.pi * hz * t + phase
    ctx.translate(hip_x, hip_y - bob * abs(math.sin(w)))
    ctx.rotate(math.radians(amp_deg) * math.sin(w))
    ctx.translate(-hip_x, -hip_y)


def head_lag(t, phase=0.0, amp_deg=6.0, hz=1.0):
    """counter-tilt (radians) for the head, a beat behind the hips: rotate the head by this around the neck"""
    return -0.5 * math.radians(amp_deg) * math.sin(2 * math.pi * hz * t + phase - 0.6)


def flash(ctx, t, t0, w, h, dur=0.3):
    """white full-frame flash for each use of the object (screen coordinates)"""
    if not t0 <= t < t0 + dur:
        return
    ctx.save()
    ctx.identity_matrix()
    ctx.set_source_rgba(1, 1, 1, 0.9 * (1 - (t - t0) / dur))
    ctx.paint()
    ctx.restore()


def question_mark(ctx, x, y, t, t0, size=90):
    """blue '?' that pops above a confused character's head from t0 (scene coordinates)"""
    if t < t0:
        return
    k = min(1.0, (t - t0) / 0.2)
    ctx.save()
    ctx.select_font_face('Inter ExtraBold', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size * (0.6 + 0.4 * k) * (1 + 0.04 * math.sin(6 * (t - t0))))
    e = ctx.text_extents('?')
    ctx.move_to(x - e.width / 2, y)
    ctx.text_path('?')
    ctx.set_source_rgb(1, 1, 1)
    ctx.set_line_width(10)
    ctx.stroke_preserve()
    ctx.set_source_rgb(0.25, 0.45, 0.95)
    ctx.fill()
    ctx.restore()


def end_pills(ctx, t, t0, w, h):
    """Like / Follow pill buttons popping in for the last 4-5 s (screen coordinates)"""
    if t < t0:
        return
    ctx.save()
    ctx.identity_matrix()
    ctx.select_font_face('Inter ExtraBold', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(40)
    labels = LABELS[LANG]
    ws = [ctx.text_extents(s).x_advance + 60 for s in labels]
    x = (w - sum(ws) - 30) / 2
    for i, (s, bw) in enumerate(zip(labels, ws)):
        k = min(1.0, max(0.0, (t - t0 - 0.25 * i) / 0.25))
        if k <= 0:
            continue
        y = h * 0.62 + 40 * (1 - k)
        ctx.new_path()
        r = 36
        ctx.arc(x + r, y + r, r, math.pi / 2, 3 * math.pi / 2)
        ctx.arc(x + bw - r, y + r, r, -math.pi / 2, math.pi / 2)
        ctx.close_path()
        ctx.set_source_rgba(*((1.0, 0.8, 0.15) if i == 0 else (0.92, 0.2, 0.2)), k)
        ctx.fill()
        ctx.set_source_rgba(1, 1, 1, k) if i else ctx.set_source_rgba(0.1, 0.1, 0.1, k)
        ctx.move_to(x + 30, y + 50)
        ctx.show_text(s)
        x += bw + 30
    ctx.restore()
