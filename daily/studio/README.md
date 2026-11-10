# Studio engines (Lumenstick animation plugins) in the daily run

Three extra visual engines from the owner's Lumenstick Studio plugins (MIT, see `LICENSE` and
`THIRD-PARTY.md`). They make the **picture** only. Everything else stays the same as for a Motion video:
story (format + locale + brief), account voice (ElevenLabs/Edge, word times from the TTS), the channel's
background track, `publish.py`, the story log, insights, metrics.

An account picks one with `"engine"` in `daily/accounts.json`. You can date it with
`"changes_from": {"YYYY-MM-DD": {"engine": "vox"}}`. No `engine` (or `"motion"`) = the Motion engine with
`bootstrap.py`, exactly as before.

| engine | look | renderer | time for a 100 s video (cloud CPU) | captions |
|---|---|---|---|---|
| `vintage` | 2D Vintage: flat bean-head cartoon characters with plum ink outlines in a hand-painted 3D world (three.js), gliding cameras, light presets day/golden/dusk/night/dawn | Playwright + Chromium (SwiftShader) | **≈ 90 min** with 2 workers, so start it first and in the background | burned in, word-highlight (Archivo Black, spoken word yellow) |
| `vox` | Vox Style: paper collage, cut-outs with white border and tape, film grain, self-drawing red arrows and circles, yellow highlighter, slamming Oswald headlines | Remotion | ≈ 10 min | none: the headlines carry the words |
| `modern` | 2D Modern: cinematic stick figures | **not available**: it needs the separate aiTrends 2D Studio plugin (another creator, not bundled). `studio.py` refuses it. | — | — |

Files: `kits/vintage`, `kits/vox` (read-only templates, the example video of each plugin), `tools/` (shared
tools: words/tts/captions/srt/sheet/thumbnail + audio engine dsp/instruments/mix), `skills/*.md` (the
plugins' original instructions, the reference for the code), `fonts/` (caption font, OFL).
Changes against the plugins, all for the headless cloud run: Vox fonts are bundled in
`kits/vox/public/fonts` (the session cannot reach Google Fonts), `qa.mjs` and the vintage scripts use the
machine's Chromium (`/opt/pw-browsers`) instead of downloading one, and captions use the bundled Archivo Black
(it has all German/French accents).

## Workflow (replaces "Voiceover + engine folder" and "Animation" in DAILY_RUN.md for these accounts)
```bash
cd /home/user/motion   # same root as the Motion stories, so output/ and save-story work unchanged
python3 /home/user/Editor/daily/studio.py setup . <slug> "<Title>" _story_<account>.txt --account <account>
#   voice + word times (printed), work/words.json, voice.mp3, audio/voice48.wav, background track, npm install
#   LENGTH ... OUTSIDE -> rewrite the story, delete <slug>/ and run setup again
# build the video in <slug>/ (below), then:
python3 /home/user/Editor/daily/studio.py stills <slug> 1.5 4 9 ...   # -> <slug>/work/sheet.jpg (look at it)
python3 /home/user/Editor/daily/studio.py finish <slug>              # -> output/<slug>_1080x1920.mp4 (or _1080x1080) + QC
#   prints the length check and black/freeze check, writes <slug>/work/final_sheet.jpg (12 frames) to look at
```
Then `publish.py` and `engine.py save-story /home/user/motion <slug>` exactly as for Motion videos.
`finish` keeps finished frames (vintage `RESUME`), so after a crash run it again. A re-run keeps the old MP4 as
`*_v1.mp4`.

### vintage: what to write
Follow `skills/vintage.md` steps 3–6 (study `web/story.js`, `web/main.js`, `web/cast.js`, `work/PLAN.md` of
the example first). In short:
`work/PLAN.md` (one row per shot) → `web/story.js` (`N` = the frames that setup printed, `SHOTS`, `camAt`,
`lightFor`, `flashAt`, `dofAt`, `worldAt`, `actorsAt`, `fxAt`) → the world in `web/main.js` (between
`// ---------- world ----------` and `// ---------- cards ----------`, plus `applyWorld()`) → the cast in
`web/cast.js` → the music per scene + SFX in `work/score.json` (`audio/audio.py` runs `score.py` on it; the kit's
own cue sheet stays as `audio/audio_example.py` for reference).
Debug: `node work/probe.mjs "<js>"` (set `CHROMIUM_PATH=$(ls /opt/pw-browsers/chromium-*/chrome-linux*/chrome)` and
`SWIFTSHADER=1` when you run the node scripts yourself). On-screen signs (`paint.sign`) are in the account's language.

### vox: what to write
Follow `skills/vox.md` steps 3–5. `setup` already copied the example to `src/story/` and registered it as
the composition `Story` (+ stills `StoryThumbA/B`) in `src/Root.tsx`. Rewrite `src/story/scenes.tsx` (one scene
per sentence, 2–9 s, every element timed to absolute seconds from `work/words.json`), `src/story/art.tsx`
(new SVG drawings), the `SCENES` table and `DURATION` (= the voice length rounded up) in
`src/story/WindowShort.tsx`. Drop the `lauren-map.json` look and use `BASE_LOOK` with `rich: true`. Delete
the example scenes you no longer import. Headlines are in the account's language. Split them so each one is
20 characters or less, because German words are long.

## Square (1:1) and own music
`"aspect": "1:1"` → `setup` makes everything 1080×1080: vox registers `Story` at 1080×1080 and switches
`src/story/WindowShort.tsx` to `SQUARE_LOOK` (rich paper, square overlay and grid); vintage sets the three.js
canvas and every Playwright viewport to 1080×1080 (cameras: the frame is wider than 9:16, so two characters fit
side by side); captions move to the lower part of the square. Lay out every scene for 1080×1080 with a 60 px
margin and keep the bottom 140 px free.
`"music_bed": false` → no channel background track; only the music you compose in `work/score.json`.

## Accounts (from 2026-11-11)
- **thai.1382** → `vox`, 1:1, format `survival_guide` (German blackout / cyberattack guide, not horror).
- **kaelusuxkzx** → `vintage`, 1:1, format `parable` (French La Fontaine-style fables with a trending angle).
Both: no fast-cut opening and no channel music; the format files give their own pacing (3–6 s scenes).

## Horror rules for these looks (on top of STORY_BRIEF.md and the format file)
(only for horror formats; `survival_guide` and `parable` follow their own format files instead)
Both plugins were made for explainers. For our horror shorts:
- **Hook in the first frame**, cuts every 0.5–1.0 s in the first 7 s (same as Motion), the twist line gets
  silence + one hard hit (sfx), not music.
- **vintage = "cosy turns wrong".** Start in a warm, friendly light (day/golden), then move to dusk → night
  as the story turns, with a 6-frame white flash on the reveal. Characters use the toonbase faces
  (`smile` → `soft` → `shock`/`sad`). Show the threat through **depth and staging**: a second figure far
  back in the fog, a door ajar behind the character, a shape in a window, never gore. Slow creeping cameras on
  the build-up, a 3–5° roll and `shake()` on the scare. Local sets (German/French flats, stairwells,
  allotments, village streets) built from `tbox` + `paint.js` textures.
- **vox = "case file".** Use the rich paper and a darker vignette. Cut-out police reports, newspaper
  clippings, polaroids, a hand-drawn floor plan or street map with a red circle, a timeline with timestamps,
  redacted lines (black bars), red string between clues. Use the Slam headlines for the key words (the time,
  the floor number, the wrong detail). **No photos**: draw everything as SVG cut-outs. Wikimedia photos need
  credits and checks the daily run cannot do, and real places of tragedy are forbidden anyway.
  Fits `map_tales`, `cursed_object` and true-story-style `confession` formats best.
- Every on-screen word (headlines, tags, signs, labels) is in the account's language. No brands, no real people.
- Captions: vintage burns them in (like Motion); vox has none, so make sure the headlines carry the story.
