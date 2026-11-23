---
name: vox-style-animation
description: Use when the user wants a "Vox style animation", "Vox-style explainer", "paper collage", "cut-out explainer" or "documentary explainer" from a voiceover, a script, or an idea, e.g. "make a Vox style animation from this voiceover", "make a Vox-style video about why ships float". Builds a Remotion video on textured paper with cut-out art and photos, tape, film grain, hand-drawn arrows and circles, highlighter marks and slamming headlines timed to every word, plus music, SFX, two thumbnails and post text. 9:16 or 16:9.
---

# Vox Style Animation

The look: warm textured paper, cut-out pictures with a white border and drop shadow, masking tape, graph-paper panels, film grain, a slow camera drift, big Oswald headlines that slam in on their word with a yellow highlighter swipe, hand-drawn red arrows and circles that draw themselves on, small typewriter tags and labels, maps. No burned-in captions: the headlines carry the words.

The plugin root is two folders up from this skill's base directory. Call it `<plugin>`. The kit is `<plugin>/skills/vox-style-animation/kit` (read-only). The finishing rules are in `<plugin>/tools/STANDARDS.md`: **read it before step 2**.

Keep the user informed with a task list and work straight through.

## 0. Intake
- **Voiceover attached** → step 1. **Script only** → step 1 (the plugin makes the voice). **Idea only** → offer 10 explainer ideas ("Why ...?" questions with a surprising answer), then write a 45-75 s script: hook paradox → context with a date and place → the problem → the reveal of the real reason → what changed because of it → a short closing line.
- Format: 9:16 Short unless they ask for 16:9 / long-form.

## 1. Project
1. `python <plugin>/tools/new_project.py vox <project>` (folder named after the title).
2. Inside it: `npm install` (Remotion downloads its own headless Chrome on the first render). If Node, Python or ffmpeg are missing, run `animation-setup` first.
3. Put the voice at `<project>/voice.mp3`, the script (if any) at `<project>/script.txt`.

## 2. Voice + word timings
Follow STANDARDS "Voice and timing" → `voice.mp3` + `work/words.json`.

## 3. Study the example
The kit is a complete 60 s video, "Why Airplane Windows Are Never Square" (`example/script.txt`, `example/words.json`). Read:
- `src/window/ui.tsx`: the toolkit. `PaperBG` / `PaperOverlay` (paper, grain, vignette), `Defs` (SVG filters: `#cut` cut-out border, `#shadow`), `CutOut` (+ `tape`), `Tape`, `Grid` / `GridFull`, `Hi` (highlighter), `Slam` (headline that slams in at a time), `Tag`, `Draw` + `loopPath` + `Arrow` (self-drawing marks), `Scene` (slide in/out + push), `ramp`, `pop`, `useT(s)` (current time in seconds on the voice timeline). `LookCtx`: `rich: true` turns on the richer paper with creases, `dy` shifts the layout, `wide: true` is the 16:9 paper.
- `src/window/scenes.tsx`: 13 scenes. Each is a component `({ s })` that calls `const t = useT(s)` and times every element to absolute seconds taken from `words.json` (e.g. `<Slam t={t} at={0.86}>Square</Slam>` slams on the word "square" at 0.86 s).
- `src/window/art.tsx`: drawn SVG art (plane, windows). `src/window/map.ts`: world map with d3-geo.
- `src/window/WindowShort.tsx`: the `SCENES` table `[start, end, Component]`, the thumbnails, `DURATION`. `src/window/wide.tsx`: the 16:9 re-layout of the same scenes.

## 4. Build the new video
1. Copy `src/window` to `src/<slug>` (keep `ui.tsx` as is). Rewrite `scenes.tsx` (one scene per sentence or idea, 2-9 s each), `art.tsx` (new SVG drawings), the `SCENES` table, `DURATION` (= voice length rounded up) and the two thumbnails in `WindowShort.tsx`. Register the new composition and stills in `src/Root.tsx`. For a single narrator, drop the `lauren-map.json` remapping and use `BASE_LOOK` with `rich: true`.
2. Every sentence gets a visual idea, not just text: a cut-out object, a diagram that draws itself, a map with a highlighted place, a tally, a document with a highlighted line, a before/after.
3. **Photos:** when a real photo helps, use public-domain or CC images from Wikimedia Commons; save them in `public/<slug>/`, load them with `<Img src={staticFile("<slug>/x.jpg")} />` inside a `CutOut`, and list the credits (author, licence, link) in `out/credits.txt` and the video description. No logos or brand marks.
4. Layout rules for 9:16: keep the art between y 140 and 1330, headlines over about 100 px with 20+ characters overflow the 1080 width (split them), keep thumbnails' text in the top quarter.
5. Preview in the Remotion Studio (`npm run dev`) or render QA stills: `node qa.mjs <CompId> work/qa 1.5 4 9.2 ...` (one still per scene and at key words), then `python tools/sheet.py work/qa work/sheet.jpg`. Fix overlaps, overflow and anything off-frame. Send the sheet to the user before the full render.

## 5. Sound
Follow STANDARDS "Sound". The example `audio/audio.py` has the cue sheet for this style: curious pizzicato → tense drone and pulse → a hard stop on the reveal → hopeful resolve, with whooshes on scene changes, paper and tape sounds on cut-outs, pen scratches on drawn marks and a low hit on the twist. Rewrite the cues for the new scene times.

## 6. Render + finish
1. `npx remotion render <CompId> work/video_silent.mp4 --muted --crf=16` (foreground; keep the PC awake).
2. Mux with the mix (no captions for this style):
   `ffmpeg -y -i work/video_silent.mp4 -i audio/mix.wav -map 0:v -map 1:a -c:v libx264 -crf 21 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -shortest out/<Title>.mp4`
   (the film grain makes files big: crf 21-25 keeps a 60 s Short around 55-75 MB).
3. Thumbnails: `npx remotion still <ThumbId> out/thumbnail_A.jpg` and `..._B.jpg` (see STANDARDS for the text rules).
4. QA contact sheet of the final video, then post text (STANDARDS). Send the MP4 and both thumbnails with your pick.
5. 16:9 long-form: follow `wide.tsx` (split layout: headline column left, art right; or zoom windows), use `wide: true` paper, render at 1920x1080 and make 1280x720 thumbnails.
