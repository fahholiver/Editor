---
name: cartoon-audio-short
description: Make a vertical animated cartoon short (flat bean-head cards in an inked, painted three.js world). Offers 10 ideas, writes the script, then turns the user's voiceover into a finished MP4 with music and SFX at half the voice level. Use for any cartoon short or animated story video request. Also the picture engine `cartoon` of the daily pipeline (daily/studio.py).
---

# Cartoon short: idea → script → voiceover → MP4

Look: flat 2D bean-head characters (canvas cards, plum outlines) in a colourful 3D world with black ink edges,
painted textures, depth of field and gliding cameras. 1080x1920, 30 fps, exactly as long as the voice.
Kit: `kit/` next to this file (read-only). Worked example: `kit/example/soldier/` ("The Soldier Who Never
Left", 19.7 s, 8 shots; `stills.jpg` shows the target look).

**Inside the daily pipeline** (engine `cartoon`): skip stages 1-3 and 4.1/4.7/4.8. `daily/studio.py setup`
makes voice + word times, `finish` renders, mixes (daily levels) and encodes. Follow only 4.2-4.6 here.

## Rules
- Original stories, characters and shots only. No real living people, no brand mascots or logos.
- No captions unless asked. Diegetic text (signs, carvings) must read correctly (not mirrored).
- Never edit or re-time the voice. Every visual reaction lands 0-3 frames before its word.
- Standalone audio: music at 50 % of the voice (−6 dB gated RMS), SFX ≤ that, peaks ≤ 0.7× voice peak.
  Always via `mix.py`; one linear gain only, no ducking.
- Keep a task list. Send a stills contact sheet before the long render.

## 1. Intake
Audio attached → stage 4 (with the script if given). Otherwise ask: voiceover ready / have a script / need
ideas. Ask the length if not given (default 20-30 s, max 60 s).

## 2. Ten ideas
Exactly 10, numbered: **title** (5-8 words), **hook line** (a paradox stated as fact), **twist** (one line),
**why it animates** (2-3 big visual moments), **true / disputed / legend**. One surprising story with physical
cause and effect, an everyman, escalating stakes, a set buildable from simple shapes. Mix eras and themes.
Verify "true" facts with a web search; nothing graphic or political.

## 3. Script
Narration only, ≈3.7 words/s (20 s ≈ 75 words, 30 s ≈ 110, 60 s ≈ 220): hook fact → setting (1-2 lines) →
2-4 escalating beats (one exaggeration joke) → "But…/You see," pivot with an everyday analogy → short ironic
payoff as the last words. Plain spoken English, contractions, numbers as words. Reply with the script (word
count, length), a one-paragraph shot plan, recording tips (one warm narrator, e.g. ElevenLabs speed 1.05-1.1,
stability 45-55 %, no music) and: **"Upload the voiceover when it's ready and I'll make the full video."**

## 4. Build (no stops unless the timing cannot be resolved)
**4.0 Kit.** `bash <skill>/kit/tools/setup.sh ~/shorts/<slug>` (vendored three.js r160 + toon.ts, no network).
Needs Node 22.6+, Python 3 + numpy + Pillow, ffmpeg, the pre-installed Playwright Chromium.

**4.1 Timing.** `python3 timing.py voice.mp3 script.txt --out work` (whisper if installed, else script phrases
aligned to silences). Pauses should fall at sentence ends. Total frames N = round(duration × 30).

**4.2 Plan** `work/PLAN.md`, one row per shot: frames, words, set, light, camera, cast/poses/faces, fx, SFX.
Frame 0 is the hook image. One shot per phrase. Illustrate each sentence literally; props carry the jokes.
Vary sizes: MCU hook → wide → two-shot → insert on the key object → reaction CU → environment move.
Light = beat: day normal, golden drama, night-blue explanation; time jump = 6-frame white flash. Twist line:
music stops, low hit, push-in with roll; the last physical payoff lands on the last word.

**4.3 World** (`web/main.js`, only between `// ---------- world ----------` and `// ---------- cards ----------`,
plus the story parts of `worldState()`). Primitives + `tbox` (constant texel density) + `paint.js` textures
(flat with dark seams). Background: half-buried sphere hills, cone mountains, cypress/pines, distant houses,
cloud billboards; fog = horizon colour. Set pieces = pivoted groups driven by 0..1 progress from `worldAt(f)`,
eased and staggered.

**4.4 Cast** (`web/roman.js` → `cat web/toonbase.js web/roman.js > web/toon.js` after every edit).
`romanFront(p, outfitKey, opts)`, design canvas 600x1000, soles y=975, card 2.25 m (1 unit = 0.00225 m).
New outfits in `OUTFITS`; arm poses hang/spear/point/up/wave/hip/belly/temple/lift/reach/cheek/shield/cross/thumb;
faces = toon FACE set + snore/stubborn/squint. Card keys from `q()`-rounded values. A detached part is its own
card at y = DECK + (partY − hc) × 0.00225. Render a character test still before using a new design.

**4.5 Motion** (`web/motion.js`). `camFromKeys(keys, f, {kicks})`: smootherstep glides 18-45 f, `easeOut`
reveals, `path` via-points for curves; holds always creep (nothing static ≥ 4 f); 3-5° roll on drama,
7-frame shake on impacts. Prefer continuous moves; hard cut only on place/time jumps (with flash).
Every card gets `idle(f, seed)` + `blinkAt` + head bobs on stressed words. Actions: anticipation → `back`
overshoot → `spring` settle. Something always moves (cloth, leaves, dust, water). DOF on CU/medium
(cInf 8-14 px, focus on eyes), wides sharp, racks ≈ 14 f.

**4.6 Look check.** `node render.mjs stills/a "5,40,…"` (each shot's middle + transitions) →
`python3 sheet.py stills/a stills/sheet_a.jpg` → look. Traps: narrow frame (half-width = d·tan(hfov/2),
hfov = 2·atan(tan(vfov/2)·0.5625); 4 m at fov 40 ≈ ±0.8 m → stage in depth), rails/posts across faces,
camera inside houses/bushes, props < 2 m from lens, hero behind a pillar, mirrored text, missing ink.
Send the sheet with a one-line shot summary, then render.

**4.7 Sound.** Lock picture first. Rewrite the cue table in `audio.py` (synths stay; it writes `music.wav` +
`sfx.wav`), then `python3 mix.py voice.mp3 music.wav sfx.wav` and confirm it prints music −6.0 dB, SFX ≤ −6 dB.

**4.8 Render + finish.** `node render.mjs frames "0-<N-1>"` in the background (`RESUME=1` continues;
≈3-10 s/frame on CPU; split the range over 2-3 processes on 4 cores). `bash finish.sh "Title"` → loudness
−14 LUFS, H.264 CRF 17, freeze/black QA, `out/qa_sheet.jpg` (frozen ≥ 0.4 s or black = fix). Deliver the MP4
with one line per shot; offer captions, tweaks or the next idea.

## Engine notes (keep if editing `main.js`)
Fog includes on their own lines; final pass writes `linearToOutputTexel` (linear HalfFloat targets). The
normal/depth pass swaps materials per mesh (cards → alpha mask, sky/blobs/clouds hidden, water flat); ink on
the near side of depth jumps, creases from normals, fades 140-520 m, radius ≈ 2.5 px. DOF 48 taps with
per-sample CoC. Sun from az/el per light preset; shadow camera centred on each shot's action.
Credits: three.js (MIT), `toon.ts` from github.com/mromidev/claude-animated-shorts (MIT, `kit/vendor/`).
