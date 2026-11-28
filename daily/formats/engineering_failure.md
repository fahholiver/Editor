# Format: engineering_failure — one real engineering disaster explained in 60–90 s, vertical

Owner's skill **Engineering Failures Studio** (2026-11-28), installed in `.claude/skills/engineering-failures-video`.
Plan.py forces **engine `engfail`**: the skill's 1920x1080 film (navy grid, white evidence boxes, handwritten
notes and arrows, archive footage, word-highlight captions) placed in a 9:16 frame with the title band on top.
Not horror: a calm, exact investigation. **Not assigned to an account (owner 2026-11-28: German uses finance_doc).** If used in German: German narration, German notes and title band; German/European cases (BFU, BAV, Bundesanstalt reports) or the big US/UK investigations, all retold in German.

## Story (read the skill's `reference/sourcing.md`, `production.md`, `scenes.md`)
- One completed investigation with a physical mechanism (NTSB, CSB, Coast Guard, HSE/AAIB for UK cases…).
  Never repeat a case of the log. Verify dates, numbers and findings in the primary report; findings as findings.
- Shape for a short: **the concrete detail that will be explained, in the first 3 s** ("Eine Schraube, so groß wie dein
  Daumen, hat eine Brücke zum Einsturz gebracht.") → normal operation (1 beat) → the initiating fault → the chain of
  failure, one link per 5–8 s with a number → what the investigation found → what changed → the last line loops
  to the hook → a comment question ("Hättest du es bemerkt? Ja oder nein.").
- Deaths and injuries factual and brief; no graphic images.

## Picture (`shots.py` in the project; studio.py setup writes vo/vo.mp3 + vo/vo.mp3.words.json and the toolchain)
- Copy `examples/bridge_shots.py`. Assets only from Wikimedia Commons (`scripts/commons.py`, `fetch.py`); the
  cloud cannot reach archive.org — use original diagrams (scenes.md) where footage is missing.
- `TITLE.txt` in the project = the band on top of the vertical frame (≤ 24 characters, German, e.g. "DIE DAUMENGROSSE SCHRAUBE").
