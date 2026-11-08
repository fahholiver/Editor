"""Visual style "pixel_arcade" for the Motion engine: 16-bit horror game look.

The story's shots are drawn as usual (vector), then:
  * the scene is pixelated: 6x6 pixel blocks (180x320 game resolution) and a limited 32-colour palette
  * captions, tags and HUD are drawn at 1/3 resolution without antialiasing and scaled up -> pixel font
  * game HUD: heart + health bar that drains over the video, stage label, coin counter
  * a retro handheld/monitor bezel around a rounded screen, with scanlines
Hooked into render.py by daily/bootstrap.py when the account's "visual_style" is "pixel_arcade".
"""
import math

import cairo
import numpy as np

PIX = 6                      # one game pixel = 6x6 video pixels
OVER = 4                     # overlay (captions/HUD) drawn at 1/4 resolution -> chunky pixel text
BEZEL = 44                   # frame width (video pixels)
STAGE = 'LEVEL 1-1'

# dark horror palette (32 colours): night blues, sick greens, bone, blood, warm lamp light
PALETTE = np.array([
    (8, 8, 16), (18, 16, 32), (28, 28, 52), (40, 44, 74), (56, 64, 100), (78, 92, 130), (110, 128, 160),
    (150, 166, 190), (200, 208, 214), (240, 236, 220), (22, 36, 34), (34, 60, 52), (52, 92, 72), (88, 132, 92),
    (140, 172, 110), (44, 26, 22), (74, 42, 32), (110, 66, 44), (150, 96, 60), (196, 140, 90), (232, 196, 140),
    (255, 236, 178), (96, 16, 22), (150, 22, 30), (210, 36, 42), (240, 90, 70), (60, 36, 70), (98, 60, 110),
    (240, 200, 60), (255, 240, 120), (180, 120, 150), (230, 170, 150)], np.float32)[:, ::-1]   # stored BGR
_PAL_SQ = (PALETTE ** 2).sum(1)


def _quantize(small):
    """nearest palette colour with a light 2x2 ordered dither (keeps gradients readable)"""
    h, w, _ = small.shape
    bayer = np.array([[0, 2], [3, 1]], np.float32) / 4 - 0.375
    dith = np.tile(bayer, (h // 2 + 1, w // 2 + 1))[:h, :w, None] * 10
    x = (small + dith).reshape(-1, 3)
    d = _PAL_SQ[None, :] - 2 * x @ PALETTE.T
    return PALETTE[d.argmin(1)].reshape(h, w, 3)


def after_scene(surf, W, H):
    """pixelate the scene that is on the surface (in place)"""
    surf.flush()
    img = np.ndarray((H, W, 4), np.uint8, surf.get_data())
    small = img[..., :3].astype(np.float32).reshape(H // PIX, PIX, W // PIX, PIX, 3).mean((1, 3))
    q = _quantize(small)
    img[..., :3] = np.repeat(np.repeat(q, PIX, 0), PIX, 1).astype(np.uint8)
    surf.mark_dirty()


def overlay(surf, W, H, draw):
    """run draw(ctx) on a 1/3-size transparent layer without antialiasing, scale it up with hard pixels and
    composite it onto surf"""
    w, h = W // OVER, H // OVER
    lay = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(lay)
    c.set_antialias(cairo.ANTIALIAS_NONE)
    fo = cairo.FontOptions()
    fo.set_antialias(cairo.ANTIALIAS_NONE)
    fo.set_hint_style(cairo.HINT_STYLE_FULL)
    c.set_font_options(fo)
    c.scale(1 / OVER, 1 / OVER)
    draw(c)
    lay.flush()
    a = np.ndarray((h, w, 4), np.uint8, lay.get_data())
    a = np.repeat(np.repeat(a, OVER, 0), OVER, 1)
    surf.flush()
    img = np.ndarray((H, W, 4), np.uint8, surf.get_data())
    al = a[..., 3:4].astype(np.float32) / 255
    img[..., :3] = (a[..., :3].astype(np.float32) + img[..., :3] * (1 - al)).astype(np.uint8)  # premultiplied
    surf.mark_dirty()


def _px_rect(ctx, x, y, w, h, col):
    ctx.rectangle(x, y, w, h)
    ctx.set_source_rgb(*col)
    ctx.fill()


def game_hud(ctx, t, dur, coins=0):
    """heart + draining health bar (top left), stage label (top right), coin counter; drawn in the overlay"""
    x, y = BEZEL + 24, BEZEL + 24
    # heart (pixel shape)
    heart = ['.XX.XX.', 'XXXXXXX', 'XXXXXXX', '.XXXXX.', '..XXX..', '...X...']
    for r, row in enumerate(heart):
        for cidx, ch in enumerate(row):
            if ch == 'X':
                _px_rect(ctx, x + cidx * 9, y + r * 9, 9, 9, (0.86, 0.14, 0.17))
    life = max(0.08, 1 - t / max(dur, 1) * 0.92)
    bx, by, bw, bh = x + 80, y + 6, 300, 42
    _px_rect(ctx, bx - 6, by - 6, bw + 12, bh + 12, (0.06, 0.06, 0.08))
    segs = 10
    for i in range(segs):
        on = i < round(life * segs) and not (life < 0.25 and int(t * 4) % 2 and i == round(life * segs) - 1)
        _px_rect(ctx, bx + i * (bw / segs) + 3, by + 3, bw / segs - 6, bh - 6,
                 (0.92, 0.22, 0.2) if on else (0.25, 0.1, 0.12))
    ctx.select_font_face('DejaVu Sans Mono', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(42)
    ext = ctx.text_extents(STAGE)
    _px_rect(ctx, 1080 - BEZEL - 40 - ext.x_advance, y - 4, ext.x_advance + 24, 58, (0.06, 0.06, 0.08))
    ctx.move_to(1080 - BEZEL - 28 - ext.x_advance, y + 40)
    ctx.set_source_rgb(0.96, 0.84, 0.3)
    ctx.show_text(STAGE)


def bezel(ctx, W, H):
    """retro handheld frame around a rounded screen (drawn last, full resolution)"""
    ctx.save()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.rectangle(0, 0, W, H)
    r, x0, y0, x1, y1 = 46, BEZEL, BEZEL, W - BEZEL, H - BEZEL
    ctx.new_sub_path()
    ctx.arc(x1 - r, y0 + r, r, -math.pi / 2, 0)
    ctx.arc(x1 - r, y1 - r, r, 0, math.pi / 2)
    ctx.arc(x0 + r, y1 - r, r, math.pi / 2, math.pi)
    ctx.arc(x0 + r, y0 + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()
    ctx.set_source_rgb(0.78, 0.74, 0.62)
    ctx.fill()
    ctx.restore()
    # inner shadow line
    ctx.set_line_width(6)
    ctx.set_source_rgba(0, 0, 0, 0.45)
    ctx.rectangle(BEZEL - 3, BEZEL - 3, W - 2 * BEZEL + 6, H - 2 * BEZEL + 6)
    ctx.stroke()


def post(rgb):
    """scanlines (every game-pixel row has a darker last line) on the final BGR float frame"""
    rgb[PIX - 1::PIX] *= 0.82
    return rgb


def font(ctx, size, mono=False, weight='x'):
    """all text in a blocky monospace bold (replaces the engine's font() for this style)"""
    ctx.select_font_face('DejaVu Sans Mono', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size * 0.92)
