# Editor — notes for Claude

This repo holds the owner's daily horror-shorts pipeline in `daily/` (see `daily/README.md`; the daily run is the skill `.claude/skills/daily-shorts/SKILL.md`).
The owner (fahholiver) writes in Portuguese; answer in Portuguese.

## When the owner sends a video (or several) as inspiration
Recognise it whenever the owner uploads a video file or says "inspiração", "referência", "modelo", "quero
nesse estilo" etc. Then, without asking first:
1. `python3 daily/inspire.py <video> --account <account|all> --note "<what they said>"` — measured facts
   (length, cut rhythm, cuts in the first 7 s, hook timing, loudness) + a 1-frame/s contact sheet.
2. Look at the contact sheet (one image) and, if there is speech, the words on screen / captions.
3. Write a short reference card (markdown) — `## <date> · <file> · for <account|all>`, then: what makes it
   work (hook in the first 3 s, story shape, pacing in numbers, framing/camera, character design, captions,
   colours, sound/music, ending) and **concrete rules to apply** in our 2D engine. Never copy its story,
   characters, art or music — only techniques.
4. `python3 daily/inspire.py <video> --save-card card.md` — archives the video in Drive `TikTok Daily/_inspiration/`
   and appends the card to Drive `_state/inspiration.md`, which every daily run reads.
5. If it changes a format or the rules, also update `daily/formats/*.md` / `daily/STORY_BRIEF.md` on the
   pipeline branch `claude/buffer-tiktok-video-generation-lrudue` and push.
Tell the owner in 3–5 lines what you learned and what changes from the next video on.
