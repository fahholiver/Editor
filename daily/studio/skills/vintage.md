---
name: 2d-vintage-animation
description: Use when the user wants a "2D vintage animation", "vintage cartoon", "old cartoon style" or "cartoon short" from a voiceover, a script, or just an idea, e.g. "make a 2D vintage animation from this voiceover", "turn my script into a cartoon short", "give me cartoon video ideas". Builds flat 2D cartoon characters in a colourful hand-painted 3D world (three.js) with ink outlines, gliding cameras, music, SFX, captions, two thumbnails and post text. 9:16 by default, 16:9 on request.
---

# 2D Vintage Animation

The look: flat 2D bean-head cartoon characters drawn on canvas "cards" with thick-thin plum outlines, standing in a colourful 3D world built from simple shapes with painted textures, black ink edges, depth of field, light presets (day, golden, dusk, night, dawn) and smooth gliding cameras. 30 fps, exactly as long as the voice.

The plugin root is two folders up from this skill's base directory. Call it `<plugin>`. The kit is `<plugin>/skills/2d-vintage-animation/kit` (treat it as read-only). The finishing rules are in `<plugin>/tools/STANDARDS.md`: **read it before step 2**.

Keep the user informed with a task list. Work straight through. Only stop to ask when something can't be decided from what they gave you.

## 0. Intake
- **Voiceover attached** → go to step 1. If they also gave the script, keep it (it fixes Whisper's mistakes).
- **Script only** → go to step 1. The plugin makes the voice (STANDARDS: "Script only").
- **Only an idea or nothing** → offer 10 numbered ideas (title, hook line, twist, why it animates well, true/legend). After they pick, write the narration at about 3.7 words per second (30 s ≈ 110 words, 60 s ≈ 220): hook fact first → setting → 2-4 escalating beats → "But..." pivot that explains the real mechanism → short ironic payoff as the last words. Plain spoken English, numbers as words. Then continue as "script only" unless they want to record it themselves.
- Format: 9:16 Short unless they say long-form / YouTube / 16:9.

## 1. Project
1. Make a project folder named after the title (e.g. `<working dir>/why-cats-purr-short`):
   `python <plugin>/tools/new_project.py vintage <project>`
2. Inside the project: `npm install`, then `npx playwright install chromium`. If Node, Python or ffmpeg are missing, run the `animation-setup` skill first.
3. Put the voice at `<project>/voice.mp3` (convert other formats with ffmpeg) and the script, if any, at `<project>/script.txt`.

## 2. Voice + word timings
Follow STANDARDS "Voice and timing". Result: `voice.mp3` + `work/words.json`. Total frames N = round(duration × 30).

## 3. Study the example, then plan
The kit is a complete, working 65-second short ("Why Is It So Hard to Let Go?": Leo with a heart balloon on a lakeside bench, a pier, a glowing brain in the night sky). Before writing anything, read `web/story.js`, skim `web/main.js` and `web/cast.js`, and read `work/PLAN.md` to see how a plan maps onto code.

Write the new `work/PLAN.md`: one row per shot with frames, words, setting/light, camera move, characters (pose, expression), effects and the SFX cue.
- Usually one shot per sentence; merge tiny phrases. Frame 0 is already the hook image.
- Illustrate every sentence literally; props carry the jokes.
- Vary shot sizes: hook close-up → wide reveal → two-shot → insert on the key object → reaction close-up → a big environment move for the payoff.
- Use light for beats: day for normal, golden for drama, night-blue for explanations. A time jump gets a 6-frame white flash.
- Every visual reaction lands 0-3 frames before its word (use the times in `work/words.json`).

## 4. Build
Edit the copied project files, not the kit.
- **`web/story.js`** (all pure functions of the frame number f): set `N`; `SHOTS` [{name, a, b}]; `camAt(f)` with `camFromKeys([[f, pos, look, fov, roll?, ease?], ...])` per shot (smooth 18-45 frame glides, every hold creeps, 3-5° rolls on drama, `shake()` on impacts); `lightFor(f)` (presets can blend with `to` + `mix`); `flashAt`; `dofAt` (focus on the eyes for close-ups, sharp wides); `worldAt(f)` for props and set pieces (0..1 progress values); `actorsAt(f)` for characters (`ch(id, outfit, pos, spec)`: mode stand/march/bench, facing, look, expr, armL/armR poses or `[from, to, t]` blends, headTilt, scale pops) and `fxAt` for effect cards.
- **`web/main.js`**: keep the engine sections (materials, ink, sky, lights, cards, render targets, light presets, render). Replace the example world between `// ---------- world ----------` and `// ---------- cards ----------`, and the story parts of `applyWorld()`. Build from primitives + `tbox` with painted textures from `web/paint.js` (planks, stone, plaster, grass, roof tiles, water...). Add new painters in the same flat-with-dark-seams style. For 16:9 change `const W = 1080, H = 1920` to `1920, 1080` and the viewport in `render.mjs`, `work/probe.mjs` and `work/thumbframes.mjs`.
- **`web/cast.js`**: define the cast in `OUT` (jacket, pants, boots, hat/hair, hairCut, dress, skin from `SKINS`). Poses and faces come from `web/toonbase.js` (faces include smile, smile_closed, sad, sadlook, hope, soft, closed, shock...; grep `FACE` for the full list). Characters stand or walk; avoid sitting poses unless the story needs them. Check new designs with `web/chartest.html`.
- Debug in the page with `node work/probe.mjs "<js expression>"`.

## 5. Look check (before the long render)
Render stills at the middle of each shot plus the key actions: `node render.mjs stills/a "40,180,..."`, then `python tools/sheet.py stills/a stills/sheet_a.jpg`. Look at the sheet and fix:
- Characters cut off by the narrow 9:16 frame (stage them in depth instead of side by side).
- Posts or railings across faces, cameras inside walls or bushes, props too close to the lens.
- Mirrored text, missing ink outlines, frozen moments (something should always move).
Send the sheet to the user with a one-line summary of each shot, then render.

## 6. Sound
Follow STANDARDS "Sound". Rewrite the cue table in `audio/audio.py` for the new story (frames → seconds with `F(f)`); keep the instruments.

## 7. Render + finish
1. `node render.mjs frames "0-<N-1>"` in the foreground (`RESUME=1` continues after an interruption). It uses the GPU. If WebGL fails, set `SWIFTSHADER=1` (slow CPU fallback).
2. Captions for 9:16 (STANDARDS "Captions"), then encode from the project folder:
   `ffmpeg -y -framerate 30 -i frames/f%04d.jpg -i audio/mix.wav -vf "subtitles=work/captions.ass" -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -shortest out/<Title>.mp4`
   (16:9 long-form: drop the `-vf` part and make the `.srt` instead.)
3. QA contact sheet of the final video. Fix freezes or black frames.
4. Thumbnails: re-shoot story frames with a custom camera through `window.camOverride` using `node work/thumbframes.mjs` (edit its SHOTS: frame + camera with empty space for text), then two specs like `example/thumb_a.json` → `node tools/thumbnail.mjs thumb/thumb_a.json`.
5. Post text (STANDARDS). Send the MP4 and both thumbnails to the user, with your pick.
