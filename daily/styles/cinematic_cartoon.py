"""Visual style "cinematic_cartoon": desaturated cinematic 2D (reference: owner's gas-station "FINAL PART" video).

  * colour grade: ~25 % desaturated, cool teal shadows, gentle contrast; DAWN (0..1) warms it to pink/violet
    for relief/ending beats (set STYLE.DAWN from a shot: import style; style.DAWN = 0.8)
  * captions white with ONE yellow key word (KEY_COLOR), standard font, no pixelation, no frame/HUD
Shot language that goes with it (write it in SHOTS): many extreme close-ups of hands/objects (keys, plug, lever,
phone), long shots (~5 s) with slow push-ins (zoom 1.00 -> 1.08), distance markers ("30 FT"), a night-to-dawn
colour arc for the ending, and a final card "THE END — <question>?" or "FINAL PART".
"""
import numpy as np

KEY_COLOR = '#ffd23f'
DAWN = 0.0
_TEAL = np.array([0.11, 0.09, 0.06], np.float32) * 255     # BGR shadow tint (teal)
_PINK = np.array([0.62, 0.48, 0.86], np.float32) * 255     # BGR dawn tint (pink/violet)


def after_scene(surf, W, H):
    surf.flush()
    img = np.ndarray((H, W, 4), np.uint8, surf.get_data())
    x = img[..., :3].astype(np.float32)
    lum = x[..., 0:1] * 0.114 + x[..., 1:2] * 0.587 + x[..., 2:3] * 0.299
    x = lum + (x - lum) * 0.75                                  # desaturate 25 %
    shadow = np.clip(1 - lum / 140, 0, 1)
    x = x + shadow * _TEAL * 0.35                               # teal shadows
    x = (x - 128) * 1.06 + 124                                  # gentle contrast, slightly darker
    if DAWN > 0:
        x = x * (1 - 0.35 * DAWN) + _PINK * 0.35 * DAWN * (0.6 + lum / 255)
    img[..., :3] = np.clip(x, 0, 255).astype(np.uint8)
    surf.mark_dirty()


def bezel(ctx, W, H):
    pass


def game_hud(ctx, t, dur, coins=0):
    pass


def overlay(surf, W, H, draw):
    """captions/tags drawn normally at full resolution"""
    import cairo
    draw(cairo.Context(surf))


def post(rgb):
    return rgb
