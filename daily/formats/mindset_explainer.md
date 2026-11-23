# Format: mindset_explainer — one counter-intuitive money/life truth, argued in 65–85 s

Owner's model (2026-11-21, 9 reference videos, see Drive `_state/inspiration.md`): calm, fast, convincing
"mindset" explainers on black, white glowing line-art. **Not horror.** One idea per video, argued like a
mini-essay so the viewer feels understood and convinced. Fiction-free: no claims about real people, no
financial advice, no promises of money.

## Engine and overrides (forced by plan.py FORMAT_LOOK — 2026-11-22 run came out wrong: vintage 1:1, navy, text only)
- Always **Motion engine + `spotlight_line`, 9:16**, whatever the account used before. If plan.py prints another
  engine for this format, stop and fix plan.py — never fall back to vintage/vox/cartoon or to plain kinetic text.
- **Every shot has the stage**: black `K.stage`, at least one `K.spotlight`, the white `K.figure` (or 2 figures /
  `K.crowd`) and one metaphor object. A shot with only text and numbers is wrong. Text on screen = the counter +
  1–3 word labels, never whole sentences (the captions already carry the words).
- **Not the horror opening:** Motion CLAUDE.md's "first 7 s every shot 0.5–1.0 s / cut at frame 210" and
  STORY_BRIEF's double-meaning + 3–5 cuts do NOT apply. The hook is the counter-intuitive claim; the "shock
  visual" is the big number already moving in frame 1 + `K.HOOK` title; then one glide per sentence.
- **Music:** no channel track (`music_bed: false`). Write `score.json` (`"key": "D", "bpm": 84`): `curious` under
  hook + doubt, `calm` (level 0.8) under the story, `curious` with `build` under concept + proof + flip side,
  `calm` under "Claro…", `hopeful` with `build` for the last line.
  SFX only `tick` on counter jumps, `whoosh` on big glides, `ting` on the last line.
- **Never reuse the references' claims** (first 10k vs next 100k, the one who fails most earns most, the smartest
  is broke, six months away, nobody rich in your family, obsessed with something other than money, always do
  what you always did, everyone wants to win, your brain keeps thinking about getting rich) — not even
  translated or with other numbers (2026-11-22's "le premier client est dix fois plus dur que les cent
  suivants" was too close).

## Every video teaches ONE real thing (owner, 2026-11-23: "algo que traga conhecimento")
Pick one real, checkable concept from psychology, economics, learning or habits and name it on screen with
`K.concept_card` (*efeito composto, custo de oportunidade, viés de sobrevivência, regra dos 72, princípio de
Pareto, efeito Dunning-Kruger, aversão à perda, curva do esquecimento, efeito Zeigarnik, lei de Parkinson,
efeito de ancoragem, custo afundado, efeito Lindy, juros compostos, inflação de estilo de vida…*), plus **one
number the viewer can check** (1,01^365 = 37,8 · money doubles in 72 ÷ rate years · 80 % of results from 20 % of
causes · we forget ~70 % of new information in 24 h). Verify the fact with a web search before writing; if it's
shaky, pick another concept. Read the log: never repeat a concept. No financial advice, no real people.

## Script shape — the story model of the references (in this order, 65–85 s)
1. **Hook (0–3 s, ≤ 12 words):** the concept's surprising result as a claim, with its number:
   *"Melhorar 1 % por dia te deixa 37 vezes melhor em um ano."* (`K.HOOK` = the same claim in ≤ 6 words.)
2. **Doubt (1 line):** *"E quase ninguém acredita nessa conta."* — the crowd says no.
3. **The story: "Imagine alguém que…"** — ONE anonymous person, one concrete goal, followed **through time** with
   a time tag per beat (*No primeiro mês… No terceiro… No sexto… Cinco anos depois…*) — 3–4 beats, each a small
   visible fact with a number (*entende uma música inteira*, *R$ 40 na primeira venda*). Optional: a second person
   who does the opposite, same start, opposite end.
4. **The concept named:** *"Isso se chama ___."* + one plain sentence of how it works.
5. **The proof:** the checkable number, built on screen piece by piece (an equation, a chart, a counter).
6. **The flip side** (1–2 lines): the same rule working against you (*piorar 1 % por dia te deixa perto de zero*).
7. **"Claro, …"** — one honest concession.
8. **"Mas…" + the last line mirrors the hook** in fewer words (*"Um por cento parece nada. Em um ano, é tudo."*).
Same voice rules: "you" + one "alguém", short sentences, no pauses longer than a line break, 170–190 wpm.

## Dynamics — more elements, more motion (owner, 2026-11-23: "mais dinâmico")
- **A new visual event every 1.5–2.5 s**, synced to the word: something pops in (`K.popin`, `K.speech`, `K.tag`,
  `K.concept_card`), a counter jumps, a chart draws, the camera pushes. A sentence of 4 s = at least 2 events.
- **Every shot has 4+ elements**: stage + light (`K.stage`, `K.spotlight`, `K.dust` and/or `K.grid`), the figure(s),
  the main metaphor, and at least one label / number / icon (`K.book`, `K.clock`, `K.bulb`, `K.coin`, `K.phone`,
  `K.check`, `K.arrow`, `K.calendar`, `K.progress`).
- The story part keeps a **`K.timeline`** at the top (MÊS 1 … MÊS 6) whose dot moves on each time tag.
- Concepts and proofs use **`K.graph`** (white line = the concept, grey = the intuition: linear vs exponential,
  with vs without), equations built term by term, and `K.flash_number` for the key number.
- People argue in **speech bubbles** (`K.speech`): the doubters, the dialogue in the story.
- Reference demo (pt-BR, 52 s, efeito composto): Drive `_inspiration/demo_efeito_composto.mp4`.

## Look (9:16 vertical, beats the 16:9 originals) — visual style `spotlight_line`
Set `visual_style: spotlight_line` (sheet Modelo-skill `mindset_explainer/spotlight_line`). Shots use the style as a
kit: `import style as K` (see the docstring of `daily/styles/spotlight_line.py`). Set `K.HOOK = ("<2-4 WORD TITLE>", 0, 3)`
and `K.THOUSANDS = '.'` for pt/de/fr/es, `'cap_y': 1580` on every shot. One shot per sentence, each a
`K.glide()` between two camera keys (no cuts needed); all characters stand on `K.FLOOR_Y`.
Older demo (pt-BR, 38 s, fewer elements): Drive `_inspiration/demo_spotlight_line.mp4`.
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
