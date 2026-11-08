"""Drawing helpers for the interactive_series format (copied into the story folder as kit.py).
Use from SHOTS functions: import kit; kit.part_tag(ctx, 2) ... (French labels by default)."""
import math

import cairo

LABELS = {'fr': ('Partie', 'Commente', 'ou', 'Partie %d bientôt'),
          'de': ('Teil', 'Kommentiere', 'oder', 'Teil %d bald'),
          'en': ('Part', 'Comment', 'or', 'Part %d soon')}
LANG = 'fr'


def _text(ctx, s, x, y, size, rgb, align='c', bold=True, a=1.0):
    ctx.select_font_face('Inter ExtraBold' if bold else 'Inter', cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    e = ctx.text_extents(s)
    ctx.move_to(x - (e.x_advance / 2 if align == 'c' else 0), y)
    ctx.set_source_rgba(*rgb, a)
    ctx.show_text(s)
    return e.x_advance


def part_tag(ctx, n):
    """small 'Partie N' label, top-left, on every shot (call after the scene, in screen coordinates)"""
    ctx.save()
    ctx.identity_matrix()
    _text(ctx, '%s %d' % (LABELS[LANG][0], n), 40, 70, 34, (0.62, 0.95, 0.55), align='l')
    ctx.restore()


def red_circle(ctx, x, y, r, t, t0, dur=0.35):
    """a hand-drawn red circle that draws itself around (x, y) from t0 (scene coordinates)"""
    if t < t0:
        return
    k = min(1.0, (t - t0) / dur)
    ctx.save()
    ctx.new_path()
    ctx.arc(x, y, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * k * 1.04)
    ctx.set_source_rgba(0.9, 0.16, 0.2, 0.95)
    ctx.set_line_width(max(6, r * 0.05))
    ctx.stroke()
    ctx.restore()


def choice_card(ctx, t, t0, question, a, b, n_next):
    """final cliffhanger card: question + the two options + 'comment A or B' + next part (screen coordinates)"""
    if t < t0:
        return
    k = min(1.0, (t - t0) / 0.4)
    ctx.save()
    ctx.identity_matrix()
    ctx.rectangle(0, 0, 1080, 1920)
    ctx.set_source_rgba(0.02, 0.03, 0.06, 0.72 * k)
    ctx.fill()
    # question wrapped to the screen width (max 3 lines), shrinking the size if a word is too long
    size = 92
    ctx.select_font_face('Inter ExtraBold', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    while True:
        ctx.set_font_size(size)
        lines, cur = [], ''
        for w in question.split():
            test = (cur + ' ' + w).strip()
            if ctx.text_extents(test).x_advance <= 940 or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        if (len(lines) <= 3 and max(ctx.text_extents(l).x_advance for l in lines) <= 940) or size <= 50:
            break
        size -= 6
    y0 = 860 - (len(lines) - 1) * size * 1.1
    for i, l in enumerate(lines):
        _text(ctx, l, 540, y0 + i * size * 1.1, size, (0.95, 0.2, 0.22), a=k)
    lab = LABELS[LANG]
    w1 = _text(ctx, a, 540, 1000, 110, (1, 1, 1), a=k)
    _text(ctx, lab[2], 540, 1090, 46, (0.75, 0.78, 0.85), a=k)
    _text(ctx, b, 540, 1210, 110, (1, 0.84, 0.25), a=k)
    _text(ctx, '%s %s %s %s' % (lab[1], a, lab[2], b), 540, 1320, 40, (0.85, 0.88, 0.95), bold=False, a=k)
    _text(ctx, lab[3] % n_next, 540, 1400, 34, (0.62, 0.95, 0.55), a=k)
    ctx.restore()
