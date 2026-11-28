"""Shot-list helpers for the Engineering Failures documentary style.
A video's shot list is a small Python file (see examples/bridge_shots.py) that does:
    from vidlib import *
    init('/path/to/project')
    sh(0.0, 'box', boxes=[V(...)], notes=[N(...)])   ... every shot, ABSOLUTE voiceover seconds
    finish(cuts=[...], names=[...], tags=[...], music=[...], sfx=[...], archive={...})
finish() writes <project>/shots.json and one HyperFrames project per chunk in <project>/chunks/."""
import json, os, re, shutil, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from toolkit import toolchain as _toolchain

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = None; WORDS = []; S = []; OV = []

def init(project):
    global P, WORDS
    P = os.path.abspath(project)
    WORDS = json.load(open(f'{P}/vo/vo.mp3.words.json', encoding='utf-8'))
    S.clear(); OV.clear()

def norm(s): return re.sub(r"[^a-z0-9$]", '', s.lower())
def w(word, after, tol=1.5):
    """Start time of the first spoken `word` at or after `after` seconds (from vo/vo.mp3.words.json)."""
    for x in WORDS:
        if x['s'] >= after - tol and norm(x['w']) == norm(word): return round(x['s'], 2)
    raise SystemExit(f'word not found: {word!r} after {after}  (check vo/sentences.txt for how whisper spelled it)')

def sh(t0, type, **k):
    k.update(t0=round(t0, 2), type=type); S.append(k); return k

# geometry presets (inner media rect; captions live under y=930, keep everything above that)
A43 = dict(x=170, y=165, w=880, h=660)          # 4:3 archive film
A169 = dict(x=150, y=200, w=1040, h=585)        # 16:9 stock / photo
NX = 1250                                       # x of the note column beside a box

def V(src, ss, geo=A169, cap='', at=None, nov=False, **k):
    """Video box. src = archive key (see finish(archive=...)) or a stock clip name in <project>/stock/<src>.mp4.
    ss = seconds into the clip. nov=True: no automatic overlay (add one by hand with OVL)."""
    b = dict(geo); b.update(vid=True, src=src, ss=ss, cap=cap, nov=nov); b.update(k)
    if at is not None: b['at'] = at
    return b
def I(img, geo, cap='', rot=0, at=None, **k):
    """Photo box. img = file name in <project>/media/. Extra keys: fit ('cover'|'contain'), pos, push (zoom), origin, pan, bg."""
    b = dict(geo); b.update(img=img, cap=cap, rot=rot); b.update(k)
    if at is not None: b['at'] = at
    return b
def N(text, x, y, at, color='white', size=None, sub=None, arrow=None, bend=None, w=None, subSize=None):
    """Handwritten note. color: white|yellow|red. arrow=[[x1,y1],[x2,y2]] draws a hand-drawn arrow (it may point INTO footage)."""
    n = dict(text=text, x=x, y=y, at=round(at, 2), color=color)
    for kk, vv in (('size', size), ('sub', sub), ('arrow', arrow), ('bend', bend), ('w', w), ('subSize', subSize)):
        if vv is not None: n[kk] = vv
    return n
def OVL(src, ss, geo, tin, tout, nofadein=False, grade=None):
    """Manual footage overlay (for clips that continue across shots, or two clips in one box)."""
    OV.append(dict(src=src, ss=ss, **geo, tin=round(tin, 2), tout=round(tout, 2), nofadein=nofadein, grade=grade))

def finish(cuts, names, tags, music, sfx, archive, end, caption_fixes=None, caption_title_case=None, caption_inserts=None, caption_merges=None, only=None):
    gsap = Path(os.environ.get('ENGINEERING_GSAP', _toolchain(P) / 'node_modules/gsap/dist/gsap.min.js'))
    if not gsap.is_file():
        raise SystemExit('GSAP is missing. Run scripts/setup.py with the project directory first.')
    if len(cuts) != len(names) + 1 or cuts[0] != 0 or cuts[-1] != end or any(a >= b for a, b in zip(cuts, cuts[1:])):
        raise SystemExit('Cuts must start at 0, end at the episode duration, and define one positive duration per chunk.')
    if not names or len(set(names)) != len(names) or any(not re.fullmatch(r'[a-zA-Z0-9_-]+', name) for name in names):
        raise SystemExit('Chunk names must be unique and use letters, numbers, underscores or hyphens.')
    # House rule: moving footage plays FULL SCREEN like a normal documentary. Evidence boxes, notes and
    # arrows are only for photos, documents and figures. A box shot that holds a video is turned into a
    # full-screen shot automatically, unless the shot was built with boxed=True on purpose.
    for s in S:
        if s['type'] == 'box' and not s.get('boxed'):
            vids = [b for b in s.get('boxes', []) if b.get('vid') and not b.get('nov')]
            if vids:
                c = vids[0]
                keep = dict(t0=s['t0'])
                s.clear(); s.update(keep, type='full', clip=dict(src=c['src'], ss=c['ss']), label=c.get('cap', ''))
    S.sort(key=lambda s: s['t0'])
    if not S or S[0]['t0'] != 0 or S[-1]['t0'] >= end or any(a['t0'] >= b['t0'] for a, b in zip(S, S[1:])):
        raise SystemExit('Shots must have distinct start times from 0 up to the episode duration.')
    for i, s in enumerate(S):
        nxt = S[i + 1]['t0'] if i + 1 < len(S) else end
        full_next = i + 1 < len(S) and S[i + 1]['type'] == 'full'
        s['t1'] = round(nxt + (0.0 if s['type'] == 'full' or full_next else 0.35), 2)
    ov = list(OV)
    for s in S:
        if s['type'] == 'box':
            for b in s['boxes']:
                if b.get('vid') and not b.get('nov'):
                    at = b.get('at', s['t0'])
                    ov.append(dict(src=b['src'], ss=b['ss'], x=b['x'], y=b['y'], w=b['w'], h=b['h'], tin=round(at, 2), tout=round(s["t1"] - 0.35, 2), grade=b.get('grade'), enter=dict(dx=b.get('dx') or 0, dy=-50 if b.get('dy') is None else b['dy'])))
        if s['type'] == 'full':
            c = s['clip']; ov.append(dict(src=c['src'], ss=c['ss'], x=0, y=0, w=1920, h=1080, tin=s['t0'], tout=s['t1'], full=True))
    ov.sort(key=lambda o: o['tin'])
    hide = [[s['t0'], s['t1']] for s in S if s['type'] in ('title', 'section', 'full', 'blueprint')]
    json.dump(dict(shots=S, overlays=ov, cuts=cuts, names=names, end=end, music=music, sfx=sfx, archive=archive,
                   caption_fixes=caption_fixes or {}, caption_title_case=caption_title_case or [], caption_inserts=caption_inserts or [], caption_merges=caption_merges or []),
              open(f'{P}/shots.json', 'w', encoding='utf-8'), indent=1)
    TPL = open(f'{SKILL}/engine/template.html', encoding='utf-8').read(); ENG = open(f'{SKILL}/engine/engine.js', encoding='utf-8').read()
    for ci, name in enumerate(names):
        a, b = cuts[ci], cuts[ci + 1]
        if only and name not in only: continue
        loc = [s for s in S if s['t1'] > a and s['t0'] < b]
        D = f'{P}/chunks/{name}'; os.makedirs(D, exist_ok=True)
        for f in ('studio.js', 'hyperframes.json', 'meta.json'):
            shutil.copy(f'{SKILL}/runtime/{f}', D)
        shutil.copy(gsap, f'{D}/gsap.min.js')
        media = Path(D) / 'media'
        if media.exists():
            shutil.rmtree(media)
        media.mkdir()
        images = {s['img'] for s in loc if s.get('img')}
        images.update(box['img'] for s in loc for box in s.get('boxes', []) if box.get('img'))
        for img in images:
            target = media / img
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(Path(P) / 'media' / img, target)
        chap = dict(tags=tags, hideTag=hide)
        html = TPL.replace('__DUR__', str(round(b - a, 3))).replace('/*SHOTS*/', 'window.OFF=' + str(a) + ';window.SHOTS=' + json.dumps(loc) + ';window.CHAP=' + json.dumps(chap) + ';').replace('/*ENGINE*/', ENG)
        open(f'{D}/index.html', 'w', encoding='utf-8').write(html)
        print(name, round(b - a, 2), 's,', len(loc), 'shots')
    gaps = sorted([(round(S[i + 1]['t0'] - S[i]['t0'], 1), S[i]['type'], S[i]['t0']) for i in range(len(S) - 1)], reverse=True)
    print('shots', len(S), 'overlays', len(ov), '| longest holds (aim for under ~10 s):', gaps[:6])

def tag(no, name):
    return '<span style="color:#FF4D5E">' + no + '</span>&nbsp;&nbsp;' + name.upper()
