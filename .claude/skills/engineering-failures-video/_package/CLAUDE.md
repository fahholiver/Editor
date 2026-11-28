# Engineering Failures Studio

This folder makes faceless, roughly ten-minute documentaries about engineering failures (bridges, ships, planes, dams, industrial accidents). Use the **engineering-failures-video** skill in `.claude/skills/` for all of it. The person using this folder may be a complete beginner: keep replies short, plain and friendly, ask before installing anything, and never ask them to create folders, edit files or sign up for accounts.

There are only three things the person will say. Map them like this:

## 1. "Follow SETUP.md"
Do what SETUP.md says. Stop when setup is OK.

## 2. "Make a documentary about <topic>"
Create `episodes/<short-topic-name>/` and use it as the project folder for this episode (run the skill's `scripts/setup.py` on it). Then run the skill's stages 2, 3 and 4 in one go, without stopping in between:
- research the official investigation report and plan the episode,
- find and download free footage, photos and figures yourself (Wikimedia Commons via `commons.py`, agency files, Internet Archive; no accounts), and write `CREDITS.md` and `inventory.md`,
- write the final ~10-minute narration around the files that actually arrived.

Finish with exactly this:
1. a one-paragraph summary of the episode and what footage you found,
2. the **voiceover text** in one clean block, ready to paste into ElevenLabs or to read aloud,
3. "When your voiceover is ready, drag the MP3 into this chat and say: Make the video."

If a fact needs the person's judgement (for example names of victims that are not in the official report), list it briefly after the voiceover text.

## 3. "Make the video" (with an MP3 attached or a file path)
Copy the MP3 to `episodes/<topic>/vo/vo.mp3`, then run the skill's stage 5 for that episode: word timing, shots, stills check (fix anything that looks wrong yourself), render and assemble the full 1080p video. Do not stop for a preview approval unless the person asks for one. Finish with the path to `out/final.mp4`, its length, and a ready-to-paste YouTube description with the credits from CREDITS.md.

If the person asks for changes after watching, edit that part and re-render only what changed.
