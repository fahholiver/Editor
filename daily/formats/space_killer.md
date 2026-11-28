# Format: space_killer — "Qu'est-ce qui te tuerait en premier sur ___ ?" in 60–85 s, vertical

Owner's skill **Orbit** (2026-11-28), installed in `.claude/skills/orbit-space-videos`. Plan.py forces
**engine `orbit`** (9:16 scene 1080x1920, the skill's own synth score, no channel track). Not horror: a fast,
true space explainer in the second person. **Assigned language: French (fr-FR).**

## Story (read the skill's `references/script.md`; every number checked against NASA/ESA/JPL)
- One place per video (planet, moon, star, black hole, comet, space itself…); never repeat a place of the log.
- Shape, short version of the skill's formula: **the rule, then the break (0–3 s)** with a number
  ("Sur Vénus, tu ne mourrais pas de chaud. Pas en premier.") → the killers in order, each worse, each with
  a number + an everyday comparison ("quatre-vingt-dix fois la pression de la Terre : un kilomètre sous la mer")
  → one light joke after a scare → the twist → the last line loops to the rule → a comment question
  ("Tu tiendrais combien de secondes ? Écris un nombre.").
- "Tu" all the way, short spoken lines, numbers written as spoken words. Facts in `<slug>/sources.md`;
  a hypothesis is said as a hypothesis ("pourrait").

## Picture (`build_scene.py` in the project writes `scene.json`; studio.py setup writes the starter)
- Read `references/style.md` + `elements.md` and copy `examples/build_venus.py`. The tiny astronaut is **TOI**
  (the `you` arrow says the word: set its text in French). Each killer opens with a `chapter` card
  ("TUEUR N°2 / NUAGES D'ACIDE"), a number that counts up, a verdict stamp; one new element every 1.5–3 s,
  a gag prop for every joke. On-screen words in French.
- Vertical: world x/y are pixels of 1080x1920, overlay x/y fractions; keep text inside 0.08–0.92 width and
  out of the bottom 18 % (TikTok UI). NASA images: the cloud cannot reach images-api.nasa.gov — draw instead.
- `scene.json` may set `"mood"` (dread | tense | wonder) for `scripts/sound.py`.
