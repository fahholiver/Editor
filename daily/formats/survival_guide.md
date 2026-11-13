# Format: survival_guide — "Blackout": what to do (and NOT do) when the power is gone for days

Owner's idea (2026-11-10) for **thai.1382** (German, from 2026-11-11), engine **vox** (paper-collage case file,
see `daily/studio/README.md`), **1:1 (1080×1080)**. It is **not horror**: a calm, useful, practical survival
guide for German households about a cyberattack on the grid or a power cut lasting several days. Write
natively in German, set in Germany (Mietwohnung, Altbau, Hochhaus, Supermarkt, Sparkasse, Feuerwehr, 112).

## Each video = one concrete question
Never "everything about blackouts". One topic per day, as a short series ("Blackout – Teil 3: Wasser"), e.g.:
the first hour · water · food without a fridge · heating in winter · light without fire risk · phone and news
when the network is gone (battery/crank radio, UKW) · cash when card payments and ATMs stop · medicines and
neighbours who need help · fridge/freezer: what to throw away · toilets when the pumps stop · a cyberattack on
your bank or your city's IT · the 10-day shopping list · myths (things people do that are dangerous).
Read the log: continue the series in order, never repeat a topic until all are done.

## Shape (second person "du", present tense, short sentences, 61–80 s)
1. **Hook (0–3 s): a concrete situation + a stake**, one line, e.g. *„Tag zwei ohne Strom. Dein Wasserhahn
   gibt nur noch ein Röcheln von sich.“* The first frame already shows it (a cut-out tap, a dark window grid).
2. **Why it matters (1–2 lines):** the mechanism, plainly (pumps need electricity, mobile masts run on
   batteries for only a few hours…).
3. **3 × „Mach das“** (green tick tags) — concrete, cheap, doable today.
4. **2 × „Mach das NICHT“** (red cross tags) — the common, dangerous mistakes (e.g. a gas/charcoal grill or
   camping stove indoors → carbon monoxide; candles left alone; opening the freezer again and again).
5. **The one number to remember** as a big Slam headline (e.g. *„2 Liter pro Person und Tag“*).
6. **Ending (last 4–5 s):** what tomorrow's part is + a question for the comments (*„Was fehlt in deinem
   Vorrat? Schreib's in die Kommentare.“*). The final line makes viewers want the next part.

## Facts — correctness is mandatory
Only advice from official German sources: **BBK** (Bundesamt für Bevölkerungsschutz und Katastrophenhilfe,
bbk.bund.de, "Ratgeber für Notfallvorsorge und richtiges Handeln in Notsituationen" + checklist), Feuerwehr,
Verbraucherzentrale, BSI (for cyberattacks). Check each number with a web search / fetch of bbk.bund.de before
you write it. Known base facts (checked 2026-11-10): supplies for about **10 days** (even 3 days helps);
water **2 litres per person per day** (1.5 to drink + 0.5 for cooking) → 20 l per person for 10 days; food
≈ 2,000–2,200 kcal per person per day. No medical advice beyond "keep a supply of your regular medicines,
ask your doctor/pharmacy". No panic, no politics, no fake scenarios presented as real news, no named real
attacks or companies. If a fact can't be confirmed, leave it out.

## Pacing and sound (different from the horror accounts — on purpose)
- **No fast-cut opening.** One idea per scene, **3–6 s per scene**, calm camera drift; the energy comes from
  the headlines slamming in on their word and the marks drawing themselves on.
- **No channel background track** (`music_bed: false`). Compose the music per scene in `work/score.json`:
  `curious` under the hook, `calm` under the tips, `tense` under the "NICHT" part, a `silence` cue right before
  the key number, `hopeful` at the end. Low under the voice (the mixer sets it).
  Paper/tape sounds on cut-outs, pen scratches on ticks and crosses.
- Voice: the account's voice (Killian), neutral and reassuring, a bit slower than the horror videos.

## Look (Vox case file, 1:1)
`SQUARE_LOOK` (rich paper, grain). Cut-outs: torch, battery radio, water bottles, tins, a fuse box, a grid map
of the street going dark block by block, a phone with no bars, a "Kassenbon" shopping list, a calendar page
"Tag 1 / Tag 2 / Tag 3". Green ✓ and red ✗ stamps. Keep everything inside the square with a 60 px margin, the
bottom 140 px free (TikTok UI). Headlines ≤ 20 characters per line (German words are long — split them).

## Viral formula (owner, 2026-11-13)
Apply the 5-step formula in `STORY_BRIEF.md`: the hook is the situation already happening (Tag 2, the tap
rattles); the "rules" are the Mach das / Mach das NICHT tags, numbered (*„Regel eins: …“*); each beat raises
the stake with a number (hours of battery, litres, degrees); before the key number, a cliffhanger question
(*„Was machst du zuerst – A: … oder B: …?“*) and the ending asks *„A oder B? Schreib's in die Kommentare.“* plus
the next part.

## Title / caption
Title = the series + the topic (*„Blackout – Teil 2: Wasser“*). Caption = the hook question + 3–5 hashtags,
e.g. *„Hast du 20 Liter Wasser zu Hause? #blackout #stromausfall #notfallvorsorge #krisenvorsorge #wissen“*.
