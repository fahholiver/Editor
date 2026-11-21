# Format: mindset_explainer — one counter-intuitive money/life truth, argued in 65–85 s

Owner's model (2026-11-21, 9 reference videos, see Drive `_state/inspiration.md`): calm, fast, convincing
"mindset" explainers on black, white glowing line-art. **Not horror.** One idea per video, argued like a
mini-essay so the viewer feels understood and convinced. Fiction-free: no claims about real people, no
financial advice, no promises of money.

## Script shape (in this order — the template is what convinces)
1. **Hook (0–2.5 s, ≤ 10 words):** a counter-intuitive claim that flatters the viewer or reveals a hidden rule.
   Patterns: *"If X, it's because Y."* / *"The one who X ends up Z."* / *"The first A is harder than the next B."*
   The same claim is on screen as a 2–4-word title + a big number/contrast **from frame 1**.
2. **Open loop (2.5–5 s), one line:** *"…and the reason explains almost everything about money."* / *"Here's why."*
3. **Escalate, don't explain (5–10 s):** a concrete number or two people side by side, same start, opposite end.
4. **"Most people believe…"** — the common belief, stated fairly (one or two lines).
5. **"Imagine someone who…"** — one anonymous figure, 3 small concrete facts with numbers (first product sells
   nothing, the second gets ignored, the third makes $40).
6. **"This happens because…"** — the mechanism in one plain sentence.
7. **"Of course, …"** — one honest concession (*"the thought alone won't put a single dollar in your account"*).
8. **Last line mirrors the hook** (reverse its words: *"In school failure was the price of being wrong. Out here,
   it's the price of finding out what's right."*). No CTA, no "follow" — the echo makes people rewatch.

## Voice and pacing
- "You" + one anonymous "someone" (he/she). Short sentences, 170–190 wpm, 190–240 words. No pauses longer
  than a line break; a soft continuous piano/ambient bed under the voice (low, never louder than the voice).
- One idea per sentence; every sentence must be drawable as one literal visual metaphor.
- Read the log: never repeat a hook claim or the same closing mirror.

## Look (9:16 vertical, beats the 16:9 originals) — visual style `spotlight_line`
Set `visual_style: spotlight_line` (sheet Modelo-skill `mindset_explainer/spotlight_line`). Shots use the style as a
kit: `import style as K` (see the docstring of `daily/styles/spotlight_line.py`). Set `K.HOOK = ("<2-4 WORD TITLE>", 0, 3)`
and `K.THOUSANDS = '.'` for pt/de/fr/es, `'cap_y': 1580` on every shot. One shot per sentence, each a
`K.glide()` between two camera keys (no cuts needed); all characters stand on `K.FLOOR_Y`.
Reference demo (pt-BR, 38 s): Drive `_inspiration/demo_spotlight_line.mp4`.
- Pure black, white glowing line-art with soft bloom, one faceless white figure under a cone spotlight.
- Literal metaphors per line: a counter ticking up ($0 → $1,000,000, MONTH 1 → MONTH 6), a thought cloud with a
  number, a boulder pushed up a curve, stairs labelled FAILS, a dial OUTCOME, a funnel INPUT → OUTCOME, a family
  tree of grey cards with one lit card, brain vs empty wallet.
- All-caps micro labels (1–3 words). Big number + figure in the middle third; nothing in the bottom 140 px.
- **Burned-in word captions** (white, bold, one accent word highlighted) — the originals have none, most
  viewers start muted.
- One continuous stage: the camera glides/zooms to the next metaphor; a visual change every 2–3 s in the first
  10 s, then every 4–6 s. No hard cuts needed.

## Title / caption
Title = the claim in 2–4 words (*Fail the Most*, *The First 10k*). Caption = the hook question + 3–5 hashtags,
e.g. *"Why the first $10k is the hardest 👇 #mindset #money #motivation #selfimprovement #animation"*.
