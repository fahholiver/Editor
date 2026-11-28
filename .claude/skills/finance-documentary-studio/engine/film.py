"""Film engine: cue shots on the voiceover's words, render them in parallel, mix sound, join.

Usage inside an episode file (see examples/rome/episode.py for the house style, which uses board.py):

    from film import *
    film = Film(__file__, vo='vo.mp3', words='words.json', mood='heist')
    T = film.cue                                   # T('furniture lift') -> time the phrase starts

    @film.shot(T('At 9:38'), push=(1.0, 1.06), cctv=dict(cam='CAM 14', clock=lambda t: '09:37:58'))
    def opening(c, t, cam):
        gallery(c); display_case(c, 700, 900, broken=1, gone=True)
        light(c, 'inside', [(700, 600, 500, .9)])
        cam.over(lambda c: stamp(c, t, T('empty'), 'EMPTY', 960, 520))

    film.main()

Command line (run from the episode folder):
    python3 episode.py info                  shot list with times
    python3 episode.py stills [t ...]        test frames (default: the middle of every shot) + a contact sheet
    python3 episode.py render [jobs]         render every shot not yet rendered (jobs = parallel processes, default 2)
    python3 episode.py redo NAME [NAME ...]  re-render named shots
    python3 episode.py audio                 music + sound effects + voice -> build/mix.wav
    python3 episode.py final                 join shots + mix -> <episode>_final.mp4 at -14 LUFS
    python3 episode.py all [jobs]            render + audio + final
"""
import os, sys, re, json, math, subprocess, importlib, shutil, glob
import numpy as np, skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *
from world import *
import world

_BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bin')
FFMPEG = os.environ.get('FFMPEG') or shutil.which('ffmpeg') or next((os.path.join(_BIN, n) for n in ('ffmpeg', 'ffmpeg.exe') if os.path.exists(os.path.join(_BIN, n))), 'ffmpeg')


class Cam:
    def __init__(self): self._over = []
    def over(self, fn): self._over.append(fn)          # draw fn(c) in screen space after the grade


class Shot:
    def __init__(self, fn, t0, kw): self.fn, self.t0, self.kw, self.name = fn, t0, kw, fn.__name__; self.t1 = None


def _norm(s): return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


class Film:
    def __init__(self, file, vo='vo.mp3', words='words.json', mood='heist', fps=FPS):
        self.dir = os.path.dirname(os.path.abspath(file)); self.name = os.path.splitext(os.path.basename(file))[0]
        self.vo = os.path.join(self.dir, vo); self.mood = mood; self.shots = []
        self.build = os.path.join(self.dir, 'build'); os.makedirs(self.build, exist_ok=True)
        wp = os.path.join(self.dir, words)
        self.words = json.load(open(wp)) if os.path.exists(wp) else []
        self.end_time = (self.words[-1][1] + 1.2) if self.words else 10.0
        self.chapters = self._load_chapters()
        # searchable text: normalised words joined by spaces, with a char -> word index map
        self._txt = ''; self._map = []
        for i, (a, b, w) in enumerate(self.words):
            n = _norm(w)
            if not n: continue
            if self._txt: self._txt += ' '; self._map.append(i)
            for ch in n: self._txt += ch; self._map.append(i)

    def _load_chapters(self):
        """[(time, 'PART ONE', 'THE PLAN', length)] from chapters.json (free voice), or, for the user's own recording,
        the long pauses (1.5 s or more) matched in order to the [CHAPTER: ... | ...] lines in script.txt."""
        cp = os.path.join(self.dir, 'chapters.json')
        if os.path.exists(cp): return [tuple(c) for c in json.load(open(cp))]
        sp = os.path.join(self.dir, 'script.txt')
        if not os.path.exists(sp) or not self.words: return []
        marks = [(m[1] if m[0] == 'CHAPTER' else 'TITLE:' + m[1], m[2]) for m in re.findall(r'^\s*\[(CHAPTER|TITLE):\s*(.+?)\s*\|\s*(.+?)\s*\]\s*$', open(sp, encoding='utf-8').read(), re.M)]
        gaps = [(self.words[i][1], self.words[i + 1][0] - self.words[i][1]) for i in range(len(self.words) - 1) if self.words[i + 1][0] - self.words[i][1] >= 1.5]
        return [(round(g[0] + .05, 2), m[0], m[1], round(g[1] - .1, 2)) for m, g in zip(marks, gaps)]

    def chapter_at(self, title):
        """Start time of the chapter pause whose title matches (e.g. film.chapter_at('THE PLAN'))."""
        for c in self.chapters:
            if c[2].lower() == title.lower(): return c[0]
        raise KeyError(f'no chapter "{title}" (add [CHAPTER: PART ONE | {title}] to script.txt and remake the voice)')

    # ---- cues -------------------------------------------------------------------------
    def _find(self, phrase, nth=1, after=0.0):
        q = _norm(phrase); start = 0; hits = 0
        if self._txt.find(q) < 0:          # transcription split or joined a word ("safecracker" / "safe cracker"): match without spaces
            ns = self._txt.replace(' ', ''); qq = q.replace(' ', ''); idx = [i for i, ch in enumerate(self._txt) if ch != ' ']; st = 0; h = 0
            while True:
                k = ns.find(qq, st)
                if k < 0: break
                i0 = self._map[idx[k]]; i1 = self._map[idx[k + len(qq) - 1]]
                if self.words[i0][0] >= after - 1e-6:
                    h += 1
                    if h == nth: return i0, i1
                st = k + 1
        while True:
            k = self._txt.find(q, start)
            if k < 0: raise KeyError(f'phrase not found in the voiceover: "{phrase}" (nth={nth}, after={after})')
            i0 = self._map[k]; i1 = self._map[k + len(q) - 1]
            if self.words[i0][0] >= after - 1e-6:
                hits += 1
                if hits == nth: return i0, i1
            start = k + 1

    def cue(self, phrase, nth=1, after=0.0, off=0.0):
        """Start time (s) of the nth occurrence of phrase in the voiceover, optionally only after a time."""
        i0, _ = self._find(phrase, nth, after); return self.words[i0][0] + off

    def end(self, phrase, nth=1, after=0.0, off=0.0):
        """Time the phrase finishes being spoken."""
        _, i1 = self._find(phrase, nth, after); return self.words[i1][1] + off

    # ---- shots ------------------------------------------------------------------------
    def shot(self, t0, **kw):
        """Register a shot starting at t0. Options: push=(z0, z1) camera push, focus=(x, y), rot=(r0, r1) degrees,
        camera=fn(t, u)->(zoom, fx, fy, rot), shake=[t...], whip=True, card=False, cctv=dict(cam, clock(t), zoom(t)),
        vig=.62, bloom=.4, end=time (default: next shot start)."""
        def deco(fn):
            self.shots.append(Shot(fn, t0, kw)); return fn
        return deco

    def _finalise(self):
        self.shots.sort(key=lambda s: s.t0)
        for i, s in enumerate(self.shots):
            s.t1 = s.kw.get('end') or (self.shots[i + 1].t0 if i + 1 < len(self.shots) else self.end_time)
        self.shots[0].t0 = 0.0

    # ---- drawing one frame ------------------------------------------------------------
    def frame(self, surf, s, f):
        c = surf.getCanvas(); kw = s.kw; t = f / FPS
        n0, n1 = round(s.t0 * FPS), round(s.t1 * FPS); u = (f - n0) / max(n1 - n0 - 1, 1); e = ease(u)
        z0, z1 = kw.get('push', (1.0, 1.0) if kw.get('card') else (1.0, 1.06)); fx, fy = kw.get('focus', (960, 540))
        r0, r1 = kw.get('rot', (0, 0)); zoom, rot = lerp(z0, z1, e), lerp(r0, r1, e)
        if 'camera' in kw: zoom, fx, fy, rot = kw['camera'](t, u)
        dx = sum(shake(t, ts) for ts in kw.get('shake', ()))
        whip = kw.get('whip', not kw.get('card')) and s is not self.shots[0]; sig = 0
        if whip and f - n0 < 4: dx += (4 - (f - n0)) ** 2 * 52; sig = (4 - (f - n0)) * 18
        cam = Cam(); B = kw.get('board')
        if B is not None:
            zoom, fx, fy, rot = B.camera_at(t); dx += sum(shake(t, ts) for ts in getattr(B, 'shakes', ()))
            hw = (W / 2) / zoom * 1.5; hh = (H / 2) / zoom * 1.5
            view = (fx - hw, fy - hh, fx + hw, fy + hh)
        c.clear(C((0, 0, 0))); c.save(); c.translate(W / 2 + dx, H / 2); c.scale(zoom, zoom); c.rotate(rot); c.translate(-fx, -fy)
        if B is not None: B.draw(c, t, f, view)
        else: s.fn(c, t, cam)
        c.restore()
        if B is not None:
            for o in B.over: cam.over(lambda c, o=o: o(c, t))
        if not kw.get('card') and not kw.get('raw'): finish(surf, bloom=kw.get('bloom', .40)); vignette(c, kw.get('vig', .62))
        if kw.get('cctv'): self._cctv(surf, t, kw['cctv'], f)
        for o in cam._over: o(c)
        if sig:
            img = surf.makeImageSnapshot(); c.clear(C((0, 0, 0)))
            bp = skia.Paint(); bp.setImageFilter(skia.ImageFilters.Blur(sig, 0.01, skia.TileMode.kClamp)); c.drawImage(img, 0, 0, skia.SamplingOptions(), bp)

    _GREY = skia.ColorFilters.Matrix([.3, .59, .11, 0, .02, .3, .59, .11, 0, .02, .3, .59, .11, 0, .02, 0, 0, 0, 1, 0])
    def _cctv(self, surf, t, o, f):
        c = surf.getCanvas(); img = surf.makeImageSnapshot(); c.clear(C((0, 0, 0)))
        p = skia.Paint(); p.setColorFilter(self._GREY); c.drawImage(img, 0, 0, skia.SamplingOptions(), p)
        r = np.random.default_rng(f); n = (r.random((270, 480)) * 255).astype(np.uint8)
        a = np.dstack([n, n, n, np.full_like(n, 40)]); nimg = skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType)
        c.drawImageRect(nimg, skia.Rect(0, 0, W, H), skia.SamplingOptions())
        for y in range(0, H, 4): c.drawRect(skia.Rect(0, y, W, y + 1), fp((0, 0, 0), 40))
        cctv_overlay(c, t, o.get('cam', 'CAM 01'), o['clock'](t) if callable(o.get('clock')) else o.get('clock', ''), o['zoom'](t) if callable(o.get('zoom')) else o.get('zoom'))

    # ---- commands ---------------------------------------------------------------------
    def check_cues(self):
        """Find every T('...') phrase in the episode file and make sure the voiceover says it (cues inside overlays only fail at render time otherwise)."""
        src = open(os.path.join(self.dir, self.name + '.py'), encoding='utf-8').read(); bad = []
        for m in re.finditer(r"""\bT\((["'])(.*?)\1""", src):
            try: self.cue(m.group(2))
            except KeyError: bad.append(m.group(2))
        for b in bad: print(f'CUE NOT FOUND in the voiceover: "{b}"  (look at the words.json printout and use the words as transcribed)')
        return not bad

    def info(self):
        for i, s in enumerate(self.shots): print(f'{i:3d} {s.name:24s} {s.t0:7.2f} -> {s.t1:7.2f}  ({s.t1 - s.t0:4.1f}s){"  card" if s.kw.get("card") else ""}')
        print(f'total {self.end_time:.1f}s, {len(self.shots)} shots')

    def stills(self, times=None):
        out = os.path.join(self.build, 'stills'); os.makedirs(out, exist_ok=True)
        for p in glob.glob(out + '/*.png'): os.remove(p)
        times = times or [round((s.t0 + s.t1) / 2, 2) for s in self.shots]
        surf = skia.Surface(W, H); paths = []
        for t in times:
            f = round(t * FPS); s = next(x for x in self.shots if x.t0 <= t < x.t1 or x is self.shots[-1])
            self.frame(surf, s, f); p = f'{out}/{t:07.2f}_{s.name}.png'; surf.makeImageSnapshot().save(p); paths.append(p)
        # contact sheet: 4 across
        try:
            from PIL import Image, ImageDraw
            cols = 4 if W > H else 6; tw, th = (480, 270) if W > H else (270, 480); rows = (len(paths) + cols - 1) // cols
            for k in range(0, rows, 4):
                sheet = Image.new('RGB', (cols * tw, min(4, rows - k) * th), 'black')
                for j, p in enumerate(paths[k * cols:(k + 4) * cols]):
                    im = Image.open(p).convert('RGB').resize((tw, th)); sheet.paste(im, ((j % cols) * tw, (j // cols) * th))
                    ImageDraw.Draw(sheet).text(((j % cols) * tw + 8, (j // cols) * th + 6), os.path.basename(p)[:-4], fill='yellow')
                sheet.save(f'{out}/sheet_{k // 4 + 1}.jpg', quality=82)
            print('contact sheets in', out)
        except ImportError: print('stills in', out)

    def render(self, jobs=2, only=None, force=False):
        todo = [i for i, s in enumerate(self.shots) if (only is None or s.name in only) and (force or only or not os.path.exists(self._mp4(i)))]
        if not todo: print('nothing to render'); return
        if jobs > 1 and len(todo) > 1:
            procs = [subprocess.Popen([sys.executable, sys.argv[0], '_part', str(k), str(jobs)] + [str(i) for i in todo]) for k in range(jobs)]
            if any(p.wait() for p in procs): sys.exit('a render process failed')
        else: self._part(todo)
        print('rendered', len(todo), 'shots')

    def _mp4(self, i): return os.path.join(self.build, 'shots', f'{i:03d}_{self.shots[i].name}.mp4')

    def _part(self, idx):
        os.makedirs(os.path.join(self.build, 'shots'), exist_ok=True); surf = skia.Surface(W, H)
        for i in idx:
            s = self.shots[i]; out = self._mp4(i); tmp = out + '.tmp.mp4'
            for old in glob.glob(os.path.join(self.build, 'shots', f'{i:03d}_*.mp4')): os.remove(old)
            p = subprocess.Popen([FFMPEG, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                  '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
            world.SFX_LOG.clear()
            if s is not self.shots[0] and not s.kw.get('card') and not s.kw.get('board'): sfx('whoosh', s.t0)
            if s.kw.get('board') is not None:       # camera glides become soft air moves in the mix
                B = s.kw['board']
                for k in B.keys:
                    if s.t0 <= k['t'] - k['move'] < s.t1 and k['move'] >= .8: sfx('glide', k['t'] - k['move'])
                    if s.t0 <= k['t'] < s.t1 and k.get('cut') and k['t'] > .05: sfx('cut', k['t'])
            if s.kw.get('card'): sfx('boom', s.t0)
            for f in range(round(s.t0 * FPS), round(s.t1 * FPS)):
                self.frame(surf, s, f); p.stdin.write(surf.makeImageSnapshot().toarray(colorType=skia.kBGRA_8888_ColorType).tobytes())
            p.stdin.close()
            if p.wait() == 0: os.replace(tmp, out)
            json.dump(sorted(set(world.SFX_LOG)), open(os.path.join(self.build, 'shots', f'{i:03d}.sfx.json'), 'w'))
            print(f'  shot {i} {s.name} done', flush=True)

    def audio(self):
        import audio
        events = []
        for p in sorted(glob.glob(os.path.join(self.build, 'shots', '*.sfx.json'))): events += [tuple(e) for e in json.load(open(p))]
        cards = [(s.t0, s.t1) for s in self.shots if s.kw.get('card')]
        cues = dict(getattr(self, 'music', None) or {})
        if getattr(self, '_tension', None) and 'tension' not in cues: cues['tension'] = self._tension     # thriller cold open (fin.py)
        key = 'horns' if self.mood == 'epic' else 'hits'
        cues[key] = list(cues.get(key, [])) + [c[0] + .15 for c in self.chapters]          # each chapter card gets a hit (noir) or a horn swell (epic)
        mdir = os.path.join(self.dir, 'music')                   # a real track dropped into music/ replaces the generated score
        tracks = sorted(glob.glob(os.path.join(mdir, '*.mp3')) + glob.glob(os.path.join(mdir, '*.wav')) + glob.glob(os.path.join(mdir, '*.m4a')))
        if tracks and not cues.get('track'): cues['track'] = tracks[0]
        audio.mix(self.vo, os.path.join(self.build, 'mix.wav'), self.end_time, events, cards, self.mood, FFMPEG, cues)

    def final(self):
        lst = os.path.join(self.build, 'list.txt')
        with open(lst, 'w') as fh:
            for i in range(len(self.shots)):
                if not os.path.exists(self._mp4(i)): sys.exit(f'missing shot {i} ({self.shots[i].name}); run render first')
                fh.write(f"file '{self._mp4(i)}'\n")
        vid = os.path.join(self.build, 'video.mp4')
        subprocess.run([FFMPEG, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', vid], check=True)
        out = os.path.join(self.dir, f'{self.name}_final.mp4')
        subprocess.run([FFMPEG, '-v', 'error', '-y', '-i', vid, '-i', os.path.join(self.build, 'mix.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                        '-af', 'loudnorm=I=-14:TP=-1.5:LRA=9', '-ar', '48000', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out], check=True)
        print('wrote', out)

    def main(self):
        self._finalise(); a = sys.argv[1:] or ['info']
        if a[0] == 'info': self.info(); self.check_cues()
        elif a[0] == 'stills': self.stills([float(x) for x in a[1:]] or None)
        elif a[0] == 'render': self.render(int(a[1]) if len(a) > 1 else 2)
        elif a[0] == 'redo': self.render(1, only=a[1:])
        elif a[0] == '_part':
            k, n = int(a[1]), int(a[2]); idx = [int(x) for x in a[3:]]; self._part(idx[k::n])
        elif a[0] == 'audio': self.audio()
        elif a[0] == 'final': self.final()
        elif a[0] == 'all':
            if not self.check_cues(): sys.exit('fix the cues above first')
            self.render(int(a[1]) if len(a) > 1 else 2); self.audio(); self.final()
        else: print(__doc__)
