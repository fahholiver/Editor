#!/usr/bin/env python3
"""Final assembly: rendered chunks + real footage behind the magenta windows + word-highlight captions + music/SFX mix.
usage: python assemble.py <project_dir> [--preview <chunk_name>]
Needs <project>/shots.json (from the shot list), <project>/out/<chunk>.mp4 (from render.py),
<project>/vo/vo.mp3 + vo.mp3.words.json, footage in <project>/real and <project>/stock, audio in <project>/audio."""
import json, subprocess, re, sys, os
P = os.path.abspath(sys.argv[1]); O = f'{P}/out'
os.makedirs(O, exist_ok=True)
PV = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
D = json.load(open(f'{P}/shots.json', encoding='utf-8')); OV = D['overlays']; END = D['end']; SH = D['shots']; names = D['names']
if PV and PV != names[0]:
    sys.exit('--preview takes the first chunk name.')
if PV:
    names = [PV]
    END = D['cuts'][1]

# ---------------- captions: whisper timings, corrected words, current word in yellow ----------------
toks = []
for x in json.load(open(f'{P}/vo/vo.mp3.words.json', encoding='utf-8')):
    t = x['w'].strip()
    if toks and re.match(r'^[.,\-][0-9A-Za-z]', t): toks[-1]['w'] += t; toks[-1]['e'] = x['e']   # "$425" ",000" -> "$425,000"
    else: toks.append(dict(w=t, s=x['s'], e=x['e']))
for ins in D['caption_inserts']:   # {"text": "...", "start": s, "end": e, "drop": [[t0,t1,["It","still"]]]}
    for a, b, ws in ins.get('drop', []): toks = [t for t in toks if not (a <= t['s'] <= b and t['w'] in ws)]
    words = ins['text'].split(); step = (ins['end'] - ins['start']) / len(words)
    toks += [dict(w=wd, s=round(ins['start'] + i * step, 2), e=round(ins['start'] + (i + 1) * step, 2)) for i, wd in enumerate(words)]
toks.sort(key=lambda t: t['s'])
FIX = D['caption_fixes']
for t in toks:
    if t['w'] in FIX: t['w'] = FIX[t['w']]
for a, b, pairs in D['caption_title_case']:   # [t0, t1, [["unsafe","Unsafe"], ...]]
    for t in toks:
        if a <= t['s'] <= b:
            for low, up in pairs:
                core = t['w'].strip('.,?!')
                if core.lower() == low: t['w'] = t['w'].replace(core, up)
for a, b, new in D.get('caption_merges', []):
    for i in range(len(toks) - 1):
        if toks[i]['w'].lower() == a and toks[i + 1]['w'].lower().strip('.,') == b:
            toks[i]['w'] = new + toks[i + 1]['w'][len(b):]; toks[i]['e'] = toks[i + 1]['e']; toks[i + 1]['w'] = ''
toks = [t for t in toks if t['w']]
groups = []; cur = []
for t in toks:
    if cur and t['s'] - cur[-1]['e'] > 0.9: groups.append(cur); cur = []
    cur.append(t)
    if (re.search(r'[.?!,]$', t['w']) and len(cur) >= 3) or len(cur) >= 6 or re.search(r'[.?!]$', t['w']): groups.append(cur); cur = []
if cur: groups.append(cur)
def ts(x):
    ticks = round(max(0, x) * 100)
    return f'{ticks // 360000}:{ticks // 6000 % 60:02d}:{ticks // 100 % 60:02d}.{ticks % 100:02d}'
styles = ['[Script Info]', 'ScriptType: v4.00+', 'PlayResX: 1920', 'PlayResY: 1080', 'WrapStyle: 2', '', '[V4+ Styles]',
       'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
       'Style: Cap,Arial,50,&H00F8F1EE,&H00F8F1EE,&H26140D0B,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,2,80,80,56,1', '', '[Events]',
       'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
events = []
for gi, g in enumerate(groups):
    g_end = min(g[-1]['e'] + 0.35, groups[gi + 1][0]['s'] if gi + 1 < len(groups) else END)
    for k, t in enumerate(g):
        a = t['s'] if k else g[0]['s'] - 0.04; b = g[k + 1]['s'] if k + 1 < len(g) else g_end
        if b <= a: continue
        txt = ' '.join(('{\\c&H3FD2FF&}' + x['w'] + '{\\c&HF8F1EE&}') if j == k else x['w'] for j, x in enumerate(g))
        events.append((a, b, txt))

# ---------------- footage: built on a base layer, the rendered graphics are keyed on top (magenta = window) ----------------
ARCH = D['archive']   # {"key": {"file": "real/x.mp4", "crop": "crop=...," or "", "stretch": false}}
GRADE = {'warm': 'eq=saturation=0.55:contrast=1.05,colorbalance=rs=0.12:gs=0.03:bs=-0.12,', 'cool': 'eq=saturation=0.7,colorbalance=bs=0.08:rs=-0.04,', None: 'eq=saturation=0.9,'}
for i, name in enumerate(names):
    start, stop = D['cuts'][i:i + 2]
    duration = round(stop - start, 3)
    if not os.path.isfile(f'{O}/{name}.mp4'):
        sys.exit(f'Missing graphics for {name}. Run scripts/render.py first.')
    ass = list(styles)
    for a, b, txt in events:
        if a < stop and b > start:
            ass.append(f'Dialogue: 0,{ts(a - start)},{ts(min(b, stop) - start)},Cap,,0,0,0,,{txt}')
    with open(f'{O}/captions.ass', 'w', encoding='utf-8') as file:
        file.write('\n'.join(ass) + '\n')

    inputs = ['-i', f'{name}.mp4', '-f', 'lavfi', '-i', f'color=c=0x050608:s=1920x1080:r=30:d={duration}']
    filters = []
    last = '1:v'
    overlays = [o for o in OV if o['tin'] < stop and o['tout'] > start and o['tout'] > o['tin']]
    for n, o in enumerate(overlays):
        idx = n + 2
        a, b = max(o['tin'], start) - start, min(o['tout'], stop) - start
        duration_on_screen = b - a
        seek = o['ss'] + max(0, start - o['tin'])
        arch = ARCH.get(o['src'])
        path = f"{P}/{arch['file']}" if arch else f"{P}/stock/{o['src']}.mp4"
        inputs += ([] if arch else ['-stream_loop', '-1']) + ['-ss', f'{seek:.3f}', '-t', f'{duration_on_screen + 0.3:.3f}', '-i', path]
        w, h = o['w'], o['h']
        pre = (arch or {}).get('crop', '')
        sc = f'scale={w}:{h},' if (arch or {}).get('stretch') else f'scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},'
        gr = 'eq=contrast=1.04,' if arch else GRADE.get(o.get('grade'), GRADE[None])
        if o.get('full'):
            gr = 'eq=saturation=0.85:brightness=-0.04,'
        fade_in = '' if o.get('nofadein') or o['tin'] < start else f"fade=t=in:st=0:d={0.17 if o.get('enter') else 0.22}:alpha=1,"
        fade_out = '' if o['tout'] > stop else f'fade=t=out:st={max(0, duration_on_screen - 0.2):.2f}:d=0.2:alpha=1,'
        filters.append(f"[{idx}:v]{pre}{gr}{sc}setsar=1,fps=30,format=yuva420p,{fade_in}{fade_out}setpts=PTS-STARTPTS+{a:.3f}/TB[e{n}]")
        ox, oy = str(o['x']), str(o['y'])
        if o.get('enter') and o['tin'] >= start:  # follow the evidence box's slide-in (power3.out over 0.6 s)
            q = f"(1-pow(1-clip((t-{a:.3f})/0.35,0,1),3))"
            ox = f"{o['x']}+(1-{q})*({o['enter']['dx']})"
            oy = f"{o['y']}+(1-{q})*({o['enter']['dy']})"
        filters.append(f"[{last}][e{n}]overlay=x='{ox}':y='{oy}':eof_action=pass:enable='between(t,{a:.3f},{b:.3f})'[v{n}]")
        last = f'v{n}'
    filters.append("[0:v]colorkey=0xFF00FF:0.3:0.1[fg]")
    filters.append(f"[{last}][fg]overlay=0:0:shortest=1,format=yuv420p,ass=captions.ass[vout]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-filter_complex_threads', '2'] + inputs + [
        '-filter_complex', ';'.join(filters), '-map', '[vout]', '-c:v', 'libx264',
        '-preset', 'veryfast', '-crf', '19', '-t', str(duration), f'assembled_{name}.mp4',
    ], cwd=O, check=True)
    print(f'Assembled {name}', flush=True)

with open(f'{O}/list.txt', 'w', encoding='utf-8') as file:
    file.writelines(f"file 'assembled_{name}.mp4'\n" for name in names)
inputs = ['-f', 'concat', '-safe', '0', '-i', 'list.txt']
idx = 1
fc = []
# ---------------- audio: VO + music (ducked under the voice) + SFX, loudness -14 LUFS ----------------
def ain(path, extra=None):
    global idx
    inputs.extend((extra or []) + ['-i', path]); idx += 1; return idx - 1
vo = ain(f'{P}/vo/vo.mp3')
music = [m for m in D['music'] if m['start'] < END]
fc.append(f"[{vo}:a]asplit=2[vo][sc]" if music else f"[{vo}:a]anull[vo]")
ml = []
for i, m in enumerate(music):   # {"file": "audio/x.mp3", "start": s, "dur": d, "vol": 0.14, "ss": 0}
    dur = min(m['dur'], END - m['start'])
    j = ain(f"{P}/{m['file']}", ['-ss', str(m.get('ss', 0)), '-t', str(dur)])
    fc.append(f"[{j}:a]volume={m['vol']},afade=t=in:st=0:d=1.2,afade=t=out:st={max(0, dur - 1.8):.2f}:d=1.8,adelay={int(m['start'] * 1000)}|{int(m['start'] * 1000)}[m{i}]"); ml.append(f'[m{i}]')
mix = ['[vo]']
if ml:
    fc.append(''.join(ml) + f"amix=inputs={len(ml)}:duration=longest:normalize=0[mus]")
    fc.append("[mus][sc]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=400[musd]")
    mix.append('[musd]')
sl = []
for i, s in enumerate(s for s in D['sfx'] if s['t'] < END):     # {"file": "audio/x.mp3", "t": s, "vol": 0.4, "ss": 0, "dur": null}
    j = ain(f"{P}/{s['file']}", ['-ss', str(s.get('ss', 0))] + (['-t', str(s['dur'])] if s.get('dur') else []))
    fc.append(f"[{j}:a]volume={s['vol']},adelay={int(s['t'] * 1000)}|{int(s['t'] * 1000)}[s{i}]"); sl.append(f'[s{i}]')
if sl: fc.append(''.join(sl) + f"amix=inputs={len(sl)}:duration=longest:normalize=0[sfx]"); mix.append('[sfx]')
fc.append(''.join(mix) + f"amix=inputs={len(mix)}:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,apad[aout]")
out = f'{O}/' + (f'preview_{PV}' if PV else 'final') + '.mp4'
temp = out.removesuffix('.mp4') + '.tmp.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inputs + [
    '-filter_complex', ';'.join(fc), '-map', '0:v', '-map', '[aout]', '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', str(END), temp,
], cwd=O, check=True)
os.replace(temp, out)
print('Wrote', out, '|', len(groups), 'caption groups')
