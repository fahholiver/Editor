"""Check a recorded voiceover against the approved script:  python3 scripts/vocheck.py script.txt words.json
Run it after scripts/timestamps.py whenever the user brings their own recording (ElevenLabs etc.).
Lists every line that was skipped, added or changed, with the time in the recording, so no shot lands on words that
were never said. The recording is the source of truth for timing: either fix the cue/shot, or ask for that line again.
Numbers are compared loosely ("fifty million dollars" = "$50 million"), and small transcription slips are ignored."""
import sys, re, json, difflib

NUM = set('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen '
          'nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion trillion percent dollars '
          'dollar and point'.split())

def toks(text):
    out = []
    for w in re.findall(r"[A-Za-z$0-9][A-Za-z0-9'$.,%-]*", text):
        n = re.sub(r"[^a-z0-9]", '', w.lower())
        if not n: continue
        isnum = any(ch.isdigit() for ch in n) or n in NUM or w.startswith('$')
        if isnum and out and out[-1] == '#': continue          # a run of number words is one number
        out.append('#' if isnum else n)
    return out

script = open(sys.argv[1], encoding='utf-8').read()
script = re.sub(r'^\s*\[(TITLE|CHAPTER):.*?\]\s*$', ' ', script, flags=re.M)
script = re.sub(r'<[^>]+>', ' ', script)                        # ElevenLabs break tags
words = json.load(open(sys.argv[2]))
a = toks(script)
b, times = [], []
for s, e, w in words:
    t = toks(w)
    for x in t:
        if x == '#' and b and b[-1] == '#': continue
        b.append(x); times.append(s)
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
issues = []
def show(seq, i, j): return ' '.join('<number>' if x == '#' else x for x in seq[i:j])
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == 'equal': continue
    at = times[min(j1, len(times) - 1)] if times else 0
    n = max(i2 - i1, j2 - j1)
    if op == 'replace' and n == 1 and difflib.SequenceMatcher(None, a[i1], b[j1]).ratio() > .6: continue   # spelling slip
    if op == 'delete': issues.append((at, f'SKIPPED  "{show(a, i1, i2)}"'))
    elif op == 'insert': issues.append((at, f'ADDED    "{show(b, j1, j2)}"'))
    else: issues.append((at, f'CHANGED  script "{show(a, i1, i2)}"  ->  said "{show(b, j1, j2)}"'))
dur = words[-1][1] if words else 0
print(f'recording {int(dur // 60)}:{dur % 60:05.2f}, {len(words)} words; script {len(a)} words')
if not issues: print('voiceover matches the script.'); sys.exit(0)
print(f'{len(issues)} difference(s) (time in the recording):')
for at, msg in issues: print(f'  {int(at // 60)}:{at % 60:05.2f}  {msg}')
print('Small wording changes are fine (cue on the words actually said). For a skipped line, drop its shot or ask for that line again.')
