# Format: finance_doc — a 60–85 s vertical finance documentary ("Aufstieg und Fall", how a company lost billions)

Owner's skill **Finance Documentary Studio** (2026-11-28), installed in `.claude/skills/finance-documentary-studio`.
Plan.py forces **engine `finance`** (9:16, the skill's own score, no channel track). Not horror: a true money story
told like a streaming-service business film, in the account's language. **Assigned language: German (de-DE).**

## Story (true, checkable — read the skill's `references/script.md`, `legal.md`, `research.md`)
- One real company / brand / fraud / bubble per video. Topics people search now (the viral lab's research +
  the skill's research.md). Never repeat a company of the log.
- **Every number from a real source** (annual report, SEC/EDGAR, Bundesanzeiger, press release, reputable press)
  — check it with a web search before writing; if unsure, say "etwa"/"about" or leave it out. Note the sources
  in `<slug>/sources.md`. No financial advice, no defamation: documented facts only, court findings as findings.
- Shape (the skill's Shorts rule): **the most shocking fact in the first second** with its number
  ("Diese Firma hätte Netflix für 50 Millionen Dollar kaufen können."), one idea, a new beat every 2–3 s:
  rise (one number) → the decision that doomed them → the fall (one number, the crash) → today (one image) →
  a last line that loops to the hook → a one-word comment question ("Hättest du gekauft? Ja oder nein.").
- Write numbers as they are spoken (words), so the voice says them right.

## Picture (the skill's engine, `episode.py` in the project — studio.py setup writes the starter)
- Copy the structure of `examples/blockbuster/short/blockbuster_short.py` (the skill's Shorts rule: **the captions
  are the only words on screen**, plus small photo credits): `fin.photo` with real free photos from
  `scripts/photos.py` (Wikimedia Commons; one download at a time; vertical crops via `frm`/`to`, never one photo
  > 3 s), one or two clean `fin.chart(t, pts, '', ...)` that show what the narrator says (the crash turns red).
  `T('word')` matches word prefixes ('zwei' also hits 'zweitausend'): use `after=` to pin the right one.
  Crop bystanders' faces out with the focus; no photos of private people.
- A new picture every 2–3 s; never two number shots in a row. No AI images, no logos as the main picture.
- `python3 daily/studio.py stills <slug> …` → one contact sheet; `finish` renders, mixes, -14 LUFS.
