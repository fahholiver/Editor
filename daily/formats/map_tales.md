# Format: map_tales — a real place told as a talking map (the GeoGlobeTales-Shorts technique)

Reference: owner's GeoGlobeTales Short of 2026-11-08 ("Why Denmark owns Greenland", 81 s). Take only the
technique: never its topics in the same order, its characters' look, its jokes or its music. Not assigned to an
account yet — set `"format": "map_tales"` (+ copy `styles/map_kit.py` as `kit.py`) when the owner picks one.
Write natively in the account's language; the English below only shows the shape.

## Shape (60–90 s, ~160–230 words, third person, present tense, tiny lines)
1. **Hook 0–3 s = a paradox about a place**, said while the camera dives from a wide map into it:
   *"One of the smallest countries in Europe owns the biggest island on Earth."* Then the place itself
   answers in one line, in character (*"Yeah. I'm kinda wondering that too."*).
2. **"It all started…"** — history as 6–10 quick beats, one fact per line, each with a year.
   Every beat = one visual change on the same map (a colour spreads, a year pops, a border moves, a tiny
   chibi figure walks/sails in). Never two new things at once.
3. **One comic cutaway** (~2–4 s, around 20–25 % in): a full-frame illustrated gag (e.g. the settlers doing
   "marketing" with a word-art title), then straight back to the map.
4. **Turn** — the twist of the story (a union, a war, a trade) shown by the territories gaining faces and
   reacting to each other (angry ↔ smug, side-eye).
5. **Today** — back to the satellite look; the place's face goes sad/worried and other places' faces peek in
   from the frame edge = open tension, no conclusion. Last line short.

## Look (from the reference, measured)
- **Almost no cuts: 2 hard cuts in 81 s.** The camera is the edit — `kit.camera()` with a new keyframe every
  2–4 s (zoom in to a detail, pan to the next place, pull out to show scale). Never fully still.
- Map backgrounds: satellite-style for present day/hook/ending; flat "old map" (sand land #d9c9a3, sea
  #5f95a8, no labels) for history. One page-turn wipe (`kit.page_turn`) when the era jumps.
- The main place is a solid colour fill (pink-red) with a black outline and a big face (`kit.face`, stick
  arms optional). Other countries get a face only when they "act". Mood changes on the emotional word.
- Ownership = solid colour fills spreading (`kit.fill_grow`), crown on the capital (`kit.crown`), a flag
  inside small islands. Big white serif years over the territory (`kit.big_year`); dated status changes as
  yellow year + italic label + hand-drawn arrow (`kit.year_label`). Place names in small white boxes.
- Captions: small, white, bold sans, bottom-centre (~70 % height), 1–3 words at a time; lines spoken by a
  place in italics. Nothing fills the screen except the cutaway.
- Sound: one light background track under the voice, voice ~ -15 LUFS.

## Title / caption
Title = the question (*Why Denmark Owns Greenland*). Caption: the paradox as a question + 4–5 hashtags
(#geography #history #maps #didyouknow #animation).
