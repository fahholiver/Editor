---
name: engineering-failures-video
description: Make a roughly ten-minute documentary about an engineering failure using U.S. archives, original diagrams, narration, and captions. Use for bridge, transport, or industrial investigations.
---

# Engineering Failures Video

Build a 1920×1080 documentary around a real case and its documented chain of failure. The visual style uses a navy grid, white evidence boxes, handwritten notes and arrows, neon diagrams, and word-highlight captions. The renderer is HyperFrames with FFmpeg. Every script is Python and runs the same on Windows (PowerShell, no WSL), macOS and Linux. Treat this folder as the skill root in every command, and use `python` on Windows and `python3` elsewhere.

Work only inside the creator's project folder (for example `~/Documents/key-bridge-doc`). If the session was opened somewhere else, ask for the project folder or use the one created in Stage 1, and save every file there.

**Style rule:** video footage always plays full screen; evidence boxes, notes and arrows are for photos, documents and figures only (see scenes.md).

## The five stages (do one at a time, then stop for the creator)

1. **Set up** → Run `scripts/check.py` with the project folder. Install what it reports missing, asking before each install, and run the check again until everything except word timing is OK. Stop there. Do not render the 16-second demo unless the creator asks for it or a later render fails and you need to isolate the problem. If the creator says not to use Homebrew, use the official installers or static builds instead.
2. **Tentative script** → Open [sourcing.md](reference/sourcing.md) (for Baltimore, the [case starter](reference/baltimore.md)). Read the primary report and deliver a ten-minute outline and a draft narration marked TENTATIVE, plus a shot wish-list: the footage, stills and figures each beat needs. The video is faceless and fully automated, so the wish-list may only contain free archive footage and stills (Wikimedia Commons, U.S. agencies, Internet Archive), report photos and figures, and original diagrams or animations this skill draws (see scenes.md). Never plan original filming, macro inserts, interviews, re-enactments or news footage. Save the plan inside the project folder.
3. **Gather the assets (no accounts needed)** → Source everything yourself from places that allow free download without a login, in this order: (a) Wikimedia Commons, searched with `scripts/commons.py "<case> " --video` and `--image` (it shows only public-domain, CC0 and CC BY/BY-SA files and can add them to `assets.json` with `--add PROJECT`). Commons mirrors most U.S. Coast Guard, Army and Navy footage from DVIDS as direct downloads. (b) Direct agency files: NTSB/CSB report PDFs and figures, USGS, NASA, NOAA. (c) Internet Archive public-domain films. Prune `assets.json` to items that really show the case, then run `scripts/fetch.py PROJECT`. It downloads everything into `real/` and `media/` and writes `CREDITS.md` and `inventory.md`. Never ask the creator to register anywhere; only if an essential item exists nowhere else, mark it `manual` and explain it is optional. Extract a few frames from each clip and note what it really shows and its usable in/out points.
4. **Final script** → Rewrite the narration around `inventory.md`: every beat must point to a file that exists, a report figure, or an original diagram. Cut or redraw beats whose footage did not arrive. Deliver the final narration, a plain voiceover copy for the voice tool, and claim-to-source notes. Then stop while the creator records or generates `vo/vo.mp3`.
5. **Build the video** → Open [production.md](reference/production.md) and [scenes.md](reference/scenes.md). Time the voiceover, write `shots.py`, check stills, render and assemble the opening chapter as a preview, and only after the creator approves it render the full MP4. Deliver the MP4 path, duration, CREDITS.md and a short YouTube description.

## Research and story

1. Prefer a completed U.S. investigation with an identifiable physical mechanism. Start with NTSB, CSB, NHTSA, Coast Guard, or another agency with firsthand evidence. Find at least two distinct usable moving sequences, a still or figure, and a primary report before treating a case as ready to script. Open the report and verify dates, quantities, technical claims, and findings against exact sections or pages.
2. Classify every visual as incident footage, aftermath, test, official reconstruction, illustration, or original diagram. Caption footage with what it actually depicts. Keep documented findings, disputed accounts, and our interpretation distinct. If event footage is unavailable, use verified scene footage with a labeled schematic.
3. Target about ten minutes. Draft roughly 1,350–1,550 spoken words, then time the actual narration. Suggested beats are a short visual cold open, normal operation, initiating fault, chain of failure, investigation, and what changed. Build the hook around a concrete detail the video will explain. Use original narration and diagrams that fit this case. Treat injuries and deaths factually. Keep graphic images out of the video.
4. Record or supply an MP3 and align the edit to its word timings. Source footage is silent by default. Music and sound effects are optional. For a first render, a recorded voice with cleared assets is enough.
5. Deliver the MP4 only after assembly and review. Include source credits, a short YouTube description, and the final duration. Report unresolved asset rights, missing voiceover, or failed steps accurately and leave a concrete next action.

Cloud chat can handle research and scripting if its tools are enabled. Full local rendering needs access to the project files, Chrome, and the software in [production.md](reference/production.md). If the environment cannot run them, hand off the project and remaining commands for Claude Code or another local execution environment.
