---
name: 2d-modern-animation
description: Use when the user wants a "2D modern animation", "modern stick figure video", "cinematic stick figure", "What If video" or "modern 2D style" from a voiceover or script, e.g. "make a 2D modern animation from this voiceover, 16:9". Runs the 2D Modern workflow (cinematic stick figures with rim light, moody 2.5D sets, face close-ups, data overlays) through the aiTrends 2D Studio engine with this plugin's finishing standards.
---

# 2D Modern Animation

The look: cinematic stick figures with rim light, moody 2.5D sets, giant face close-ups, freeze-frames, data overlays, blueprint diagrams and low-poly 3D shots, with five colour styles (dusk, midnight, golden, neon, storybook).

**This style runs on a separate plugin, the aiTrends 2D Studio, made by aiTrends.** It isn't bundled here because it belongs to its creator. This skill hands the work to it and adds this plugin's finishing standards.

The plugin root is two folders up from this skill's base directory. Call it `<plugin>`.

## 1. Is the engine installed?
Look at your available skills.
- If the `aitrends-2d-studio` skills are there (`aitrends-2d-studio:make-2d-video`, `:new-video`, `:render-video`, `:video-sound`, `:video-styles`) → step 2.
- If not, tell the user plainly:
  "2D Modern uses the aiTrends 2D Studio plugin, which is made by a different creator. Get it from the link in the tutorial video's description, install it, restart the Claude app, and ask me again. Meanwhile I can make this video in 2D Vintage or Vox style instead."
  Then stop (or switch style if they say so). Don't try to rebuild or download the engine yourself.

## 2. Make the video
Invoke the `aitrends-2d-studio:make-2d-video` skill with the user's voiceover or script and format, and follow it. Apply these standards on top (they win where the two differ). Read `<plugin>/tools/STANDARDS.md` first:
- **Style:** offer the five-style comparison grid (`video-styles`) and recommend **golden** for stories and what-ifs.
- **Script only:** make the voice with `python <plugin>/tools/tts.py script.txt voice.mp3 --words work/words.json` (STANDARDS "Voice and timing") and use those word timings instead of transcribing.
- **Sound:** voice first (music around -16 dB under the voice, ducked further while talking; STANDARDS "Sound"). If the studio's own mixer is louder than that, lower its music level or mix with `<plugin>/tools/mix.py`.
- **Captions:** 9:16 → burned-in word-highlight captions (`python <plugin>/tools/captions.py work/words.json work/captions.ass`, burned in at encode time). 16:9 long-form → no burned captions; make the `.srt` with `<plugin>/tools/srt.py`.
- **Finish:** two thumbnails (A/B) with your pick, and post text with no emojis (title, description with chapters for long-form, hashtags) in chat and `out/post_text.txt`.
- **Rendering:** foreground, PC kept awake. If renders time out while booting, use fewer workers (4).
