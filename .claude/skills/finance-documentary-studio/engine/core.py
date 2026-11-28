"""Core drawing kit: flat cel-shaded round-head characters with one thick ink line,
lighting (night or day), depth blur, bloom, grade. Everything is drawn with skia-python."""
import math, random, os
import numpy as np, skia, soundfile as sf

W, H, FPS = (1080, 1920, 30) if os.environ.get('FDS_VERTICAL') == '1' else (1920, 1080, 30)   # vertical 9:16 for Shorts (set before importing)
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts') + os.sep
FONT_HAND = skia.Typeface.MakeFromFile(F + "CaveatBrush-Regular.ttf")


def C(rgb, a=255): return skia.Color(int(rgb[0]), int(rgb[1]), int(rgb[2]), int(max(0, min(255, a))))
def hx(h, a=255):
    h = h.lstrip('#'); return C((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)), a)
def radial(cx, cy, r, colors, pos=None): return skia.GradientShader.MakeRadial(center=(cx, cy), radius=r, colors=colors, positions=pos)
def linear(x0, y0, x1, y1, colors, pos=None): return skia.GradientShader.MakeLinear(points=[(x0, y0), (x1, y1)], colors=colors, positions=pos)
def ease(u): u = min(max(u, 0), 1); return 0.5 - 0.5 * math.cos(math.pi * u)
def ease_out(u): u = min(max(u, 0), 1); return 1 - (1 - u) ** 3
def pop(u):
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 1.15 * ease_out(u / 0.6) if u < 0.6 else 1.15 - 0.15 * ease((u - 0.6) / 0.4)
def K(t, t0, d): return min(max((t - t0) / d, 0.0), 1.0)
def blink(t, period=2.7, phase=0.0): return ((t + phase) % period) < 0.1
def mouth_track(wav, hold=3):
    s, sr = sf.read(wav); s = s.mean(1) if s.ndim > 1 else s
    hop = sr // FPS; n = len(s) // hop + 1
    rms = np.array([np.sqrt(np.mean(s[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    m = rms.max(); out = []; cur = 'closed'; held = hold
    for v in rms:
        tgt = 'open' if v > .45 * m else 'mid' if v > .14 * m else 'closed'
        if tgt != cur and held >= hold: cur = tgt; held = 0
        held += 1; out.append(cur)
    out[-1] = 'closed'; return out

GOLD = '#F2C14E'; RED = '#C8242C'; LIME = '#B8F04A'; CREAM = '#FFF6DC'
KALAM = skia.Typeface.MakeFromFile(F + "Kalam-Bold.ttf")
PATRICK = skia.Typeface.MakeFromFile(F + "PatrickHand-Regular.ttf")
MARKER = skia.Typeface.MakeFromFile(F + "PermanentMarker-Regular.ttf")
INK = (24, 22, 27)
LW = 6.0


def col(v, a=255):
    return hx(v, a) if isinstance(v, str) else C(v, a)


def fp(v, a=255, blur=0, blend=None):
    p = skia.Paint(AntiAlias=True, Color=col(v, a))
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend: p.setBlendMode(blend)
    return p


def sp(shader, blend=None, blur=0):
    p = skia.Paint(AntiAlias=True); p.setShader(shader)
    if blend: p.setBlendMode(blend)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def ink(w=LW, v=INK, a=255):
    p = skia.Paint(AntiAlias=True, Color=col(v, a))
    p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w)
    p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def shape(c, path, fill, w=LW, v=INK):
    c.drawPath(path, fill if isinstance(fill, skia.Paint) else fp(fill))
    if w: c.drawPath(path, ink(w, v))


def rect(c, x0, y0, x1, y1, fill, w=LW, r=0, v=INK):
    p = skia.Path()
    if r: p.addRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), r, r))
    else: p.addRect(skia.Rect(x0, y0, x1, y1))
    shape(c, p, fill, w, v); return p


def circ(c, x, y, r, fill, w=LW, v=INK):
    p = skia.Path(); p.addCircle(x, y, r); shape(c, p, fill, w, v); return p


def oval(c, x0, y0, x1, y1, fill, w=LW, v=INK):
    p = skia.Path(); p.addOval(skia.Rect(x0, y0, x1, y1)); shape(c, p, fill, w, v); return p


def line(c, x0, y0, x1, y1, w=LW, v=INK, a=255):
    c.drawLine(x0, y0, x1, y1, ink(w, v, a))


def poly(c, pts, fill, w=LW, v=INK, close=True):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    if close: p.close()
    shape(c, p, fill, w, v); return p


def label(c, s, x, y, size, color, font=None, align='left', stroke=0, stroke_col=INK, skew=-0.16, alpha=1.0, rot=0.0):
    """Hand-lettered text. A trailing ' ✓' or ' ✗' is drawn as a green tick / red cross (the fonts have no such glyphs)."""
    mark = None
    if s.endswith((' ✓', ' ✗')): mark = s[-1]; s = s[:-2]
    s = s.replace('→', '>').replace('♥', '')
    f = skia.Font(font or KALAM, size); w = f.measureText(s); mw = size * .9 if mark else 0
    ox = -(w + mw) / 2 if align == 'center' else -(w + mw) if align == 'right' else 0
    c.save(); c.translate(x, y); c.rotate(rot); c.skew(skew, 0)
    if stroke:
        c.drawString(s, ox, 0, f, ink(stroke, stroke_col, 255 * alpha))
    c.drawString(s, ox, 0, f, fp(color, 255 * alpha))
    if mark:
        mx = ox + w + size * .25; p = skia.Path(); q = size * .55
        if mark == '✓': p.moveTo(mx, -q * .45); p.lineTo(mx + q * .35, -q * .05); p.lineTo(mx + q, -q * .95)
        else: p.moveTo(mx, -q * .9); p.lineTo(mx + q * .8, -q * .1); p.moveTo(mx + q * .8, -q * .9); p.lineTo(mx, -q * .1)
        c.drawPath(p, ink(size * .2, INK, 255 * alpha)); c.drawPath(p, ink(size * .11, '#7BD34A' if mark == '✓' else '#E5352F', 255 * alpha))
    c.restore(); return w + mw


def text_w(s, size, font=None):
    return skia.Font(font or KALAM, size).measureText(s)


def back(u, k=1.9):
    """ease-out with overshoot (snappy pose change)"""
    u = min(max(u, 0.0), 1.0); u -= 1
    return 1 + (k + 1) * u ** 3 + k * u ** 2


def lerp(a, b, k): return a + (b - a) * k


# ---------------------------------------------------------------- lighting
def night(c, lights, ambient='#4A5A9A'):
    """Multiply a navy darkness over everything drawn so far, with soft holes where lights are."""
    p = skia.Paint(); p.setBlendMode(skia.BlendMode.kMultiply)
    c.saveLayer(None, p)
    c.drawPaint(fp(ambient))
    for L in lights:
        if L[0] == 'pool':
            _, x, y, r, a = L
            c.drawCircle(x, y, r, sp(radial(x, y, r, [C((0, 0, 0), 255 * a), C((0, 0, 0), 255 * a * .75), C((0, 0, 0), 0)], [0, .5, 1]),
                                     blend=skia.BlendMode.kDstOut))
        elif L[0] == 'oval':
            _, x, y, rx, ry, a = L
            c.save(); c.translate(x, y); c.scale(1, ry / rx)
            c.drawCircle(0, 0, rx, sp(radial(0, 0, rx, [C((0, 0, 0), 255 * a), C((0, 0, 0), 255 * a * .7), C((0, 0, 0), 0)], [0, .55, 1]),
                                     blend=skia.BlendMode.kDstOut))
            c.restore()
        elif L[0] == 'path':
            _, path, a, blur = L
            c.drawPath(path, fp((0, 0, 0), 255 * a, blur=blur, blend=skia.BlendMode.kDstOut))
    c.restore()


def add_light(c, x, y, r, v, a):
    c.drawCircle(x, y, r, sp(radial(x, y, r, [col(v, a), col(v, a * .4), col(v, 0)], [0, .5, 1]), blend=skia.BlendMode.kPlus))


def cone_path(x, y, top_w, bot_w, length, lean=0):
    p = skia.Path(); p.moveTo(x - top_w / 2, y); p.lineTo(x + top_w / 2, y)
    p.lineTo(x + lean + bot_w / 2, y + length); p.lineTo(x + lean - bot_w / 2, y + length); p.close(); return p


def blur_begin(c, sigma):
    p = skia.Paint(); p.setImageFilter(skia.ImageFilters.Blur(sigma, sigma)); c.saveLayer(None, p)


def vignette(c, strength=0.65, inner=.42):
    c.drawRect(skia.Rect(0, 0, W, H), sp(radial(W / 2, H / 2, W * 0.74,
               [C((0, 0, 0), 0), C((0, 0, 0), 0), C((2, 3, 12), 255 * strength)], [0, inner, 1])))


def _sat(s, contrast, lift):
    lr, lg, lb = 0.2126, 0.7152, 0.0722
    m = [lr * (1 - s) + s, lg * (1 - s), lb * (1 - s), lr * (1 - s), lg * (1 - s) + s, lb * (1 - s), lr * (1 - s), lg * (1 - s), lb * (1 - s) + s]
    out = []
    for r in range(3): out += [m[r * 3 + i] * contrast for i in range(3)] + [0, lift]
    return out + [0, 0, 0, 1, 0]


GRADE_CF = skia.ColorFilters.Matrix(_sat(0.94, 0.97, 0.012))
THRESH_CF = skia.ColorFilters.Matrix([1.7, 0, 0, 0, -0.78, 0, 1.7, 0, 0, -0.78, 0, 0, 1.7, 0, -0.78, 0, 0, 0, 1, 0])


def finish(surf, bloom=0.42, sigma=20):
    c = surf.getCanvas(); img = surf.makeImageSnapshot()
    c.clear(C((0, 0, 0)))
    p = skia.Paint(); p.setColorFilter(GRADE_CF); c.drawImage(img, 0, 0, skia.SamplingOptions(), p)
    if bloom > 0:
        b = skia.Paint(); b.setImageFilter(skia.ImageFilters.Blur(sigma, sigma, skia.TileMode.kClamp, skia.ImageFilters.ColorFilter(THRESH_CF)))
        b.setBlendMode(skia.BlendMode.kScreen); b.setAlphaf(bloom); c.drawImage(img, 0, 0, skia.SamplingOptions(), b)


# ---------------------------------------------------------------- characters
BODY_TOP, BODY_BOT, HEAD_R = -345, -128, 100
HEAD_CY = BODY_TOP - 74
SHOULDER = (-56, BODY_TOP + 54)
ARM = {  # left arm: (elbow, hand, show_hand)
    'down': ((-90, -235), (-96, -168), True),
    'pocket': ((-96, -232), (-70, -176), False),
    'hip': ((-128, -238), (-84, -190), True),
    'present': ((-128, -306), (-208, -338), True),
    'gesture': ((-136, -262), (-152, -352), True),
    'chin': ((-128, -262), (-62, -322), True),
    'hat': ((-140, -400), (-104, -482), True),
    'hold': ((-96, -236), (-44, -214), True),
    'push': ((-120, -270), (-190, -262), True),
}


def _arm(spec):
    if isinstance(spec, str):
        e, h, s = ARM[spec]; return e, h, s
    a, b, k = spec; k = back(k, 1.6)
    ea, ha, sa = ARM[a]; eb, hb, sb = ARM[b]
    return (lerp(ea[0], eb[0], k), lerp(ea[1], eb[1], k)), (lerp(ha[0], hb[0], k), lerp(ha[1], hb[1], k)), (sb if k > .5 else sa)


def draw_char3(c, x, y, s, spec, face=0.0, eyes='dot', mouth='smile', brow=0.0, brow_tilt=0.0, arms=('down', 'down'),
               tilt=0.0, bob=0.0, squash=0.0, sweat=-1.0, light=-1, rim=None, hat=False, legs=None, pupil=0.0, sparkle=0.0):
    """x,y = feet. s=1 -> head radius 100px. light: -1 key from left, +1 from right. face: -1..1 (3/4 turn)."""
    lw = max(5.2, 4.0 / s)
    R = HEAD_R
    c.save(); c.translate(x, y); c.scale(s, s)
    # --- legs (plain ink lines, no feet)
    if legs is None: legs = ((-24, 0, 0), (24, 0, 0))
    for (hx0, fx, lift) in legs:
        c.drawLine(hx0, BODY_BOT - 8, hx0 + fx, -lift, ink(lw))
    c.translate(0, -bob); c.scale(1 + squash * .6, 1 - squash)
    # --- body (pill)
    body = skia.Path(); body.addRRect(skia.RRect.MakeRectXY(skia.Rect(-84, BODY_TOP, 84, BODY_BOT), 66, 72))
    c.drawPath(body, fp(spec['suit']))
    c.save(); c.clipPath(body, doAntiAlias=True)
    sh = skia.Path(body); sh.offset(light * 16, -5)
    c.drawPath(skia.Op(body, sh, skia.PathOp.kDifference_PathOp), fp(spec['suit_d']))
    if spec.get('pants'):
        c.drawRect(skia.Rect(-90, BODY_BOT - 40, 90, BODY_BOT + 4), fp(spec['pants']))
        c.drawLine(-90, BODY_BOT - 40, 90, BODY_BOT - 40, ink(lw * .8))
    # shirt V, collar, tie / bow tie
    v = skia.Path(); v.moveTo(-34, BODY_TOP - 4); v.lineTo(0, BODY_TOP + 96); v.lineTo(34, BODY_TOP - 4); v.close()
    c.drawPath(v, fp(spec['shirt']))
    if spec.get('bowtie'):
        by = BODY_TOP + 40
        bt = skia.Path(); bt.moveTo(0, by); bt.lineTo(-24, by - 14); bt.lineTo(-24, by + 14); bt.close()
        bt.moveTo(0, by); bt.lineTo(24, by - 14); bt.lineTo(24, by + 14); bt.close()
        shape(c, bt, spec['tie'], lw * .75); circ(c, 0, by, 5, spec['tie'], lw * .7)
    else:
        t = skia.Path(); t.moveTo(-9, BODY_TOP + 24); t.lineTo(9, BODY_TOP + 24); t.lineTo(13, BODY_TOP + 82); t.lineTo(0, BODY_TOP + 98); t.lineTo(-13, BODY_TOP + 82); t.close()
        shape(c, t, spec['tie'], lw * .75)
    for sx in (-1, 1):
        lp = skia.Path(); lp.moveTo(sx * 36, BODY_TOP - 2); lp.lineTo(sx * 2, BODY_TOP + 98); lp.lineTo(sx * 2, BODY_BOT)
        c.drawPath(lp, ink(lw * .75))
        c.drawLine(sx * 22, BODY_TOP + 58, sx * 40, BODY_TOP + 44, ink(lw * .6))  # lapel notch
    if spec.get('hanky'):
        poly(c, [(30, BODY_TOP + 96), (52, BODY_TOP + 92), (48, BODY_TOP + 76), (40, BODY_TOP + 86), (33, BODY_TOP + 76)], spec['hanky'], lw * .55)
    if spec.get('vest'):  # hi-vis or tactical vest over the suit
        vc = spec['vest']
        for sx in (-1, 1):
            vp = skia.Path(); vp.moveTo(sx * 30, BODY_TOP - 4); vp.lineTo(sx * 90, BODY_TOP + 20); vp.lineTo(sx * 90, BODY_BOT); vp.lineTo(sx * 6, BODY_BOT); vp.lineTo(sx * 6, BODY_TOP + 70); vp.close()
            c.drawPath(vp, fp(vc)); c.drawPath(vp, ink(lw * .6))
        if spec.get('stripes', True):
            for yy in (BODY_TOP + 120, BODY_TOP + 160):
                c.drawRect(skia.Rect(-90, yy, -10, yy + 14), fp('#DCE3EA')); c.drawRect(skia.Rect(10, yy, 90, yy + 14), fp('#DCE3EA'))
    if spec.get('badge'):
        st = skia.Path()
        for i in range(10):
            r_ = 18 if i % 2 == 0 else 8; a = -math.pi / 2 + i * math.pi / 5
            (st.moveTo if i == 0 else st.lineTo)(-46 + r_ * math.cos(a), BODY_TOP + 70 + r_ * math.sin(a))
        st.close(); shape(c, st, spec['badge'], lw * .5)
    if spec.get('lanyard'):
        c.drawLine(-30, BODY_TOP, 0, BODY_TOP + 90, ink(lw * .6, spec['lanyard'])); c.drawLine(30, BODY_TOP, 0, BODY_TOP + 90, ink(lw * .6, spec['lanyard']))
        rect(c, -18, BODY_TOP + 90, 18, BODY_TOP + 130, '#F4F4F0', lw * .5)
    if spec.get('toga'):  # ancient draped cloth over the left shoulder and across the body (with an optional purple border)
        tg = skia.Path(); tg.moveTo(-96, BODY_TOP - 6); tg.lineTo(-20, BODY_TOP - 10); tg.lineTo(96, BODY_BOT - 70); tg.lineTo(96, BODY_BOT); tg.lineTo(40, BODY_BOT); tg.lineTo(-96, BODY_TOP + 110); tg.close()
        c.drawPath(tg, fp(spec['toga'])); c.drawPath(tg, ink(lw * .6))
        for k_ in range(3): c.drawLine(-70 + k_ * 34, BODY_TOP + 20 + k_ * 26, 40 + k_ * 20, BODY_BOT - 40 - k_ * 6, ink(lw * .35, (0, 0, 0)))
        if spec.get('toga_stripe'): c.drawLine(-20, BODY_TOP - 10, 96, BODY_BOT - 70, ink(lw * 1.2, spec['toga_stripe']))
    if spec.get('armour'):  # bronze breastplate (soldiers)
        rect(c, -84, BODY_TOP + 10, 84, BODY_BOT - 50, spec['armour'], lw * .6)
        for yy in range(BODY_TOP + 40, BODY_BOT - 60, 34): c.drawLine(-84, yy, 84, yy, ink(lw * .4))
    c.restore()
    c.drawPath(body, ink(lw))
    # --- arms (ink lines drawn over the body) + small hands
    for side, a in ((-1, arms[0]), (1, arms[1])):
        e, h, show = _arm(a); m = 1 if side < 0 else -1
        sx, sy = SHOULDER[0] * m, SHOULDER[1]
        ex, ey, hx_, hy_ = e[0] * m, e[1], h[0] * m, h[1]
        cx_, cy_ = 1.35 * ex - 0.175 * (sx + hx_), 1.35 * ey - 0.175 * (sy + hy_)
        ap = skia.Path(); ap.moveTo(sx, sy); ap.quadTo(cx_, cy_, hx_, hy_)
        c.drawPath(ap, ink(lw))
        if show: circ(c, hx_, hy_, 13, spec['skin'], lw * .8)
    # --- head
    c.save(); c.translate(0, HEAD_CY); c.rotate(tilt)
    head = skia.Path(); head.addCircle(0, 0, R)
    hair = spec.get('hair')
    if hair == 'bald':  # side tufts sit behind the head
        for sx in (-1, 1):
            tf = skia.Path(); tf.moveTo(sx * 84, -44)
            for i, (px, py) in enumerate(((112, -34), (98, -18), (118, -4), (100, 10), (112, 26), (86, 34))): tf.lineTo(sx * px, py)
            tf.close(); shape(c, tf, spec.get('hair_col', '#8A8A92'), lw * .8)
    if hair in ('bob', 'long', 'bun', 'curly'):  # back hair sits behind the head
        hc = spec.get('hair_col', '#3A2A20')
        if hair == 'bob':
            bk = skia.Path(); bk.addRRect(skia.RRect.MakeRectXY(skia.Rect(-R - 16, -R - 10, R + 16, R * .75), R * .9, R * .9)); shape(c, bk, hc, lw)
        elif hair == 'long':
            bk = skia.Path(); bk.addRRect(skia.RRect.MakeRectXY(skia.Rect(-R - 18, -R - 10, R + 18, R * 1.6), R * .9, R * .9)); shape(c, bk, hc, lw)
        elif hair == 'bun': circ(c, 0, -R - 18, 40, hc, lw)
        else:
            for k_ in range(14): a_ = k_ / 14 * math.pi * 2; circ(c, (R + 6) * math.cos(a_), (R + 6) * math.sin(a_) - 6, 30, hc, lw * .7)
    c.drawPath(head, fp(spec['skin']))
    c.save(); c.clipPath(head, doAntiAlias=True)
    lit = skia.Path(head); lit.offset(light * 7, -17)
    c.drawPath(skia.Op(head, lit, skia.PathOp.kDifference_PathOp), fp(spec['skin_d']))
    if rim:
        rm = skia.Path(head); rm.offset(-light * 11, 4)
        c.drawPath(skia.Op(head, rm, skia.PathOp.kDifference_PathOp), fp(rim, 215))
    c.restore()
    if hair == 'slick':
        o = skia.Rect(-R - 4, -R - 5, R + 4, R + 3)
        hp = skia.Path(); hp.moveTo(-R - 4, -4); hp.arcTo(o, 181, 178, False)
        fs = face * 14
        hp.cubicTo(R - 6, -40, 56 + fs, -70, 4 + fs, -62); hp.cubicTo(-36 + fs, -58, -78, -44, -R - 4, -4); hp.close()
        shape(c, hp, spec.get('hair_col', '#1C1B22'), lw)
        shn = skia.Path(); shn.addArc(skia.Rect(-R + 20, -R + 14, R - 20, R - 14), 208 if light < 0 else 282, 50)
        c.drawPath(shn, ink(lw * 1.3, (92, 96, 122)))
        c.drawLine(-30 + fs, -98, -18 + fs, -62, ink(lw * .6, (70, 72, 92)))
    if hair in ('bob', 'long', 'bun', 'curly'):  # fringe over the forehead
        fr = skia.Path(); fr.moveTo(-R - 2, -10); fr.arcTo(skia.Rect(-R - 4, -R - 6, R + 4, R + 4), 186, 168, False)
        fs = face * 18; fr.cubicTo(R - 20, -58, 30 + fs, -62, 0 + fs, -50); fr.cubicTo(-30 + fs, -62, -R + 20, -58, -R - 2, -10); fr.close()
        shape(c, fr, spec.get('hair_col', '#3A2A20'), lw)
    c.drawPath(head, ink(lw))
    if spec.get('mask'):  # balaclava: dark knit over the head, eye slit shows skin
        c.save(); c.clipPath(head, doAntiAlias=True)
        c.drawPath(head, fp(spec['mask']))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-70 + face * 40, -34, 70 + face * 40, 22), 26, 26), fp(spec['skin']))
        for i in range(-4, 5): c.drawLine(i * 24, -R, i * 24 + 6, -40, ink(lw * .35, (60, 60, 70)))
        c.restore(); c.drawPath(head, ink(lw))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-70 + face * 40, -34, 70 + face * 40, 22), 26, 26), ink(lw * .6))
    hw = spec.get('hat') if not hat else 'top'
    if hw == 'cap':  # peaked cap (police, guard, security)
        cr = skia.Path(); cr.moveTo(-R + 2, -40); cr.cubicTo(-R - 6, -R - 40, R + 6, -R - 40, R - 2, -40); cr.close()
        shape(c, cr, spec.get('hat_col', '#1E2A4A'), lw)
        c.drawRect(skia.Rect(-R + 4, -58, R - 4, -40), fp(spec.get('hat_band', '#11182E'))); c.drawLine(-R + 4, -58, R - 4, -58, ink(lw * .6))
        vz = skia.Path(); vz.moveTo(-R + 6 + face * 30, -40); vz.quadTo(face * 60, -10, R - 6 + face * 30, -40); vz.close(); shape(c, vz, '#14141A', lw * .8)
        if spec.get('cap_badge'): circ(c, face * 30, -78, 12, spec['cap_badge'], lw * .5)
    elif hw == 'helmet':  # motorbike helmet with tinted visor
        hm = skia.Path(); hm.addCircle(0, -6, R + 16); shape(c, hm, spec.get('hat_col', '#222630'), lw)
        vz = skia.Path(); vz.addRRect(skia.RRect.MakeRectXY(skia.Rect(-78 + face * 40, -46, 78 + face * 40, 30), 34, 34)); shape(c, vz, '#3D5A80', lw * .7)
        c.drawLine(-50 + face * 40, -32, -10 + face * 40, -32, ink(lw * .9, (180, 210, 240)))
    elif hw == 'beanie':
        bn = skia.Path(); bn.moveTo(-R - 2, -30); bn.cubicTo(-R - 8, -R - 50, R + 8, -R - 50, R + 2, -30); bn.close()
        shape(c, bn, spec.get('hat_col', '#2B2B33'), lw); rect(c, -R - 4, -46, R + 4, -24, spec.get('hat_col', '#2B2B33'), lw * .8)
    elif hw == 'hardhat':
        hh = skia.Path(); hh.moveTo(-R + 4, -40); hh.cubicTo(-R + 4, -R - 30, R - 4, -R - 30, R - 4, -40); hh.close()
        shape(c, hh, spec.get('hat_col', '#F2B01E'), lw); rect(c, -R - 18, -46, R + 18, -32, spec.get('hat_col', '#F2B01E'), lw * .8)
    elif hw == 'laurel':  # laurel wreath (emperors, generals)
        for sx in (-1, 1):
            for k_ in range(6):
                a_ = math.radians(200 + k_ * 14) if sx < 0 else math.radians(-20 - k_ * 14)
                lx, ly = (R - 2) * math.cos(a_), -34 + (R - 2) * math.sin(a_) * .55
                lf = skia.Path(); lf.addOval(skia.Rect(lx - 14, ly - 7, lx + 14, ly + 7)); shape(c, lf, spec.get('hat_col', '#6E8B3D'), lw * .4)
    elif hw == 'galea':  # Roman soldier's helmet with a red crest
        cr_ = skia.Path(); cr_.moveTo(-64, -R + 2); cr_.cubicTo(-34, -R - 74, 34, -R - 74, 64, -R + 2); cr_.close(); shape(c, cr_, spec.get('crest', '#A3241F'), lw * .8)
        gl = skia.Path(); gl.moveTo(-R - 4, -24); gl.cubicTo(-R - 8, -R - 44, R + 8, -R - 44, R + 4, -24); gl.close(); shape(c, gl, spec.get('hat_col', '#B08A3E'), lw)
        for sx in (-1, 1): rect(c, sx * R - (14 if sx > 0 else -2), -30, sx * R + (2 if sx > 0 else 14), 40, spec.get('hat_col', '#B08A3E'), lw * .6)
    elif hw == 'crown':  # simple gold crown (kings)
        cw = skia.Path(); cw.moveTo(-70, -R + 8); cw.lineTo(-74, -R - 46); cw.lineTo(-38, -R - 14); cw.lineTo(0, -R - 58); cw.lineTo(38, -R - 14); cw.lineTo(74, -R - 46); cw.lineTo(70, -R + 8); cw.close()
        shape(c, cw, spec.get('hat_col', '#C9A227'), lw * .8)
        for xx in (-74, 0, 74): circ(c, xx, -R - 50 if xx else -R - 62, 9, '#A3241F', lw * .4)
    elif hw == 'veil':  # draped head cloth (priestesses, Roman matrons)
        vl = skia.Path(); vl.moveTo(-R - 14, 60); vl.cubicTo(-R - 30, -R - 50, R + 30, -R - 50, R + 14, 60); vl.lineTo(R - 8, 40); vl.cubicTo(R, -R + 10, -R, -R + 10, -R + 8, 40); vl.close()
        shape(c, vl, spec.get('hat_col', '#E8E0CC'), lw * .8)
    elif hw == 'judge':  # white wig
        for sx in (-1, 1):
            for k_ in range(3): circ(c, sx * (R - 6), -20 + k_ * 34, 22, '#F2F0EA', lw * .6)
        wg = skia.Path(); wg.moveTo(-R, -20); wg.cubicTo(-R - 10, -R - 30, R + 10, -R - 30, R, -20); wg.close(); shape(c, wg, '#F2F0EA', lw)
    if hw == 'helmet':  # face mostly hidden behind the visor: skip eyes/mouth
        c.restore(); c.restore(); return
    if hat:
        crown = skia.Path(); crown.moveTo(-R + 6, -56); crown.cubicTo(-R - 2, -R - 82, R + 2, -R - 82, R - 6, -56); crown.close()
        shape(c, crown, spec.get('hat_col', '#2E2E38'), lw)
        c.save(); c.clipPath(crown, doAntiAlias=True)
        c.drawRect(skia.Rect(-R, -86, R, -56), fp(spec.get('hat_band', '#7E1C24')))
        c.drawLine(-R, -86, R, -86, ink(lw * .7))
        hs = skia.Path(crown); hs.offset(light * 14, -6); c.drawPath(skia.Op(crown, hs, skia.PathOp.kDifference_PathOp), fp((0, 0, 0), 70))
        c.restore(); c.drawPath(crown, ink(lw))
        oval(c, -R - 40, -70, R + 40, -40, spec.get('hat_col', '#2E2E38'), lw)
    # --- face
    fx = face * 40
    eyy = -6
    for i, ex0 in enumerate((-30, 30)):
        ex = ex0 + fx
        far = (face > 0 and ex0 > 0) or (face < 0 and ex0 < 0)
        sq = 1 - 0.3 * abs(face) if far else 1.0
        if eyes == 'wide':
            oval(c, ex - 17 * sq, eyy - 17, ex + 17 * sq, eyy + 17, '#FBFBF7', lw * .7)
            c.drawOval(skia.Rect(ex - 5.5 * sq + pupil * 6, eyy - 5.5, ex + 5.5 * sq + pupil * 6, eyy + 5.5), fp(INK))
        elif eyes == 'closed':
            e = skia.Path(); e.moveTo(ex - 11 * sq, eyy); e.quadTo(ex, eyy + 9, ex + 11 * sq, eyy); c.drawPath(e, ink(lw * .8))
        elif eyes == 'half':
            c.save(); c.clipRect(skia.Rect(ex - 20, eyy - 3, ex + 20, eyy + 20))
            c.drawOval(skia.Rect(ex - 6.5 * sq, eyy - 9, ex + 6.5 * sq, eyy + 9), fp(INK)); c.restore()
            c.drawLine(ex - 13 * sq, eyy - 4, ex + 13 * sq, eyy - 4, ink(lw * .8))
        else:
            c.drawOval(skia.Rect(ex - 5.5 * sq, eyy - 8, ex + 5.5 * sq, eyy + 8), fp(INK))
            c.drawCircle(ex + 1.5, eyy - 3, 1.8, fp((255, 255, 255), 220))
        inner = 1 if ex0 < 0 else -1  # direction toward nose
        by = eyy - 29 - brow * 9
        c.drawLine(ex - 13 * sq, by + (brow_tilt * 7 if inner < 0 else -brow_tilt * 7) * 1.0,
                   ex + 13 * sq, by + (brow_tilt * 7 if inner > 0 else -brow_tilt * 7), ink(lw * .78))
    if spec.get('glasses'):
        for ex0 in (-30, 30):
            ex = ex0 + fx; far = (face > 0 and ex0 > 0) or (face < 0 and ex0 < 0); sq = 1 - 0.3 * abs(face) if far else 1.0
            g = skia.Path(); g.addOval(skia.Rect(ex - 24 * sq, eyy - 24, ex + 24 * sq, eyy + 24))
            c.drawPath(g, fp((225, 240, 255), 55)); c.drawPath(g, ink(lw * .7))
        c.drawLine(fx - 7, eyy - 3, fx + 7, eyy - 3, ink(lw * .7))
    mx, my = face * 34, 42
    if spec.get('moustache'):
        mu = skia.Path(); mu.moveTo(mx, my - 20)
        mu.cubicTo(mx - 12, my - 28, mx - 30, my - 22, mx - 40, my - 30); mu.cubicTo(mx - 30, my - 10, mx - 12, my - 12, mx, my - 15)
        mu.cubicTo(mx + 12, my - 12, mx + 30, my - 10, mx + 40, my - 30); mu.cubicTo(mx + 30, my - 22, mx + 12, my - 28, mx, my - 20); mu.close()
        c.drawPath(mu, fp(spec.get('hair_col', '#1C1B22')))
    if spec.get('mask'): mouth = 'none'
    if mouth == 'smile':
        m = skia.Path(); m.moveTo(mx - 17, my - 2); m.quadTo(mx, my + 13, mx + 17, my - 2); c.drawPath(m, ink(lw * .8))
    elif mouth == 'smirk':
        d = 1 if face >= 0 else -1
        m = skia.Path(); m.moveTo(mx - 15 * d, my + 3); m.quadTo(mx + 4 * d, my + 12, mx + 20 * d, my - 6); c.drawPath(m, ink(lw * .8))
    elif mouth == 'flat':
        c.drawLine(mx - 12, my + 2, mx + 12, my + 2, ink(lw * .8))
    elif mouth == 'o':
        oval(c, mx - 8, my - 9, mx + 8, my + 11, '#5A1A1E', lw * .7)
    elif mouth == 'mid':
        oval(c, mx - 12, my - 4, mx + 12, my + 10, '#5A1A1E', lw * .7)
    elif mouth == 'open':
        mp = skia.Path(); mp.moveTo(mx - 20, my - 5); mp.lineTo(mx + 20, my - 5); mp.cubicTo(mx + 19, my + 24, mx - 19, my + 24, mx - 20, my - 5); mp.close()
        c.drawPath(mp, fp('#5A1A1E'))
        c.save(); c.clipPath(mp, doAntiAlias=True)
        c.drawRect(skia.Rect(mx - 22, my - 6, mx + 22, my + 2), fp('#FAFAF4'))
        c.drawOval(skia.Rect(mx - 11, my + 9, mx + 11, my + 26), fp('#D05860')); c.restore()
        c.drawPath(mp, ink(lw * .7))
    if sparkle > 0:
        k = pop(sparkle) * (1 if sparkle < 1 else max(0, 2 - sparkle))
        sx_, sy_ = mx + 26 * (1 if face >= 0 else -1), my - 8
        st = skia.Path()
        for i in range(8):
            r_ = (20 if i % 2 == 0 else 5) * k; a = i * math.pi / 4
            (st.moveTo if i == 0 else st.lineTo)(sx_ + r_ * math.cos(a), sy_ + r_ * math.sin(a))
        st.close(); c.drawPath(st, fp('#FFFFFF')); c.drawCircle(sx_, sy_, 26 * k, fp((255, 255, 255), 70, blur=8))
    if sweat >= 0:
        sd = -1 if face > 0 else 1
        sx0, sy0 = sd * 62, -66 + 30 * (sweat % 1.0)
        d = skia.Path(); d.moveTo(sx0, sy0 - 19); d.cubicTo(sx0 + 12, sy0 - 3, sx0 + 11, sy0 + 10, sx0, sy0 + 10); d.cubicTo(sx0 - 11, sy0 + 10, sx0 - 12, sy0 - 3, sx0, sy0 - 19); d.close()
        shape(c, d, '#8FC8EE', lw * .7)
    c.restore()
    c.restore()


def walk_legs(phase, stride=46, lift=20):
    a = math.sin(phase); b = -a
    return ((-10, a * stride, max(0, math.cos(phase)) * lift), (10, b * stride, max(0, -math.cos(phase)) * lift))


