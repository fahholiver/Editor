# Orbit style guide

## The look
- Deep space: near-black navy with a faint purple/teal nebula, three layers of stars (parallax with the camera), film grain and a vignette. Places on a planet get their own palette (Venus: amber and rust; Mars: rust and butterscotch; the Moon: grey on black sky).
- Flat shapes with soft gradients, no outlines. The only bright colours are yellow `#FFC93C` (highlight), red `#FF3B30` (danger) and green (safe/alive).
- Text: Anton for big words, captions, stamps and numbers; Inter for labels. Captions are UPPERCASE with one or two highlighted words.

## The story grammar
1. **Hook (0–10 s):** the planet, huge, with the tiny astronaut and the red YOU arrow. Title card. One line that makes it personal ("Picture yourself floating just above Venus").
2. **Scale (optional):** a `lineup` or `fit` so the viewer feels the size.
3. **The question:** "So what would kill you first?" as a big yellow line.
4. **Killers, in the order you'd meet them,** each one bigger than the last. Each gets a `chapter` card, then 1–3 shots: the place (descent, surface or horizon), its number (counter, gauge, thermo, timer), a comparison to Earth (depth bar, lineup, "hotter than Mercury"), and a verdict `stamp`.
5. **Proof:** real NASA `evidence` images at the moment the narration says "we know because…".
6. **Strange-but-true:** one or two odd facts (the Sun rises in the west, a day longer than a year).
7. **Twist and ending:** flip the danger ("but 50 km up it's almost like Earth") and close on a line that calls back to the opening, over the planet again.

## Pacing
- Change something on screen every 1.5–3 s. Never leave a shot static for more than 4 s.
- Hard cuts (whip) on the beat. Crossfades only for calm moments and the ending.
- Numbers should finish counting exactly as the narrator says them.
- Put a stamp on the strongest word of each killer.
- Captions are 2–5 words, and never more than one at a time.

## Titles that fit
- What Would Kill You First On Venus / Mars / Jupiter / the Moon / Titan / Io
- What Would Kill You First Inside A Black Hole / On The Sun / Near A Neutron Star
- How Long Would You Survive On ___ (use the `timer` element)
- Thumbnails: the tiny YOU astronaut against the huge planet, 2–3 Anton words (white + red), a red arrow. No NASA logo.

## Editing lessons from a 7.5M-view explainer (apply these)
1. **Hold the stage, build inside it.** About 40 hard cuts in 10 minutes; a shot usually lasts 8–15 s. Keep one scene up (a planet, a cloud deck, the ground) and add things to it one at a time: a ruler, then a label, then a comparison object, then a stamp. Cut only when the place or the idea changes. When writing scene JSON, prefer fewer, longer shots with several timed elements.
2. **Every joke gets its own gag visual.** The joke line is illustrated literally with a prop: a `receipt`, a `doc` with a stamp, a `loading` bar plus a CANCEL stamp, a `stick` figure, the `eyes` room, `meters`, or a planet in a silly costume. Never let a joke play over a plain shot.
3. **YOU appears throughout, not only in the hook.** Use the astronaut or a `stick` figure for "you'd struggle to…" lines (`xray` for your body). Pay off the hook's planted mystery with `scan` or a red label on YOU.
4. **Numbers become objects.** Use `lineup`, `fit`, `icons`, `pie`, `balance`, `depth`, or a `label` next to a thing of known size. A number never appears alone.
5. **Quiet text.** Use `label` (small, bold, uppercase, one at a time, red underline for the key one) for most on-screen words. Save `caption`/`big` for 3–5 key moments.
6. **Props carry history.** A `tag` with name · date · place on every historical scene ("VENERA 13 · MARCH 1982 · VENUS"), plus a `doc` for agreements, bans and reports.
7. **On-screen honesty.** Label uncertain claims ("THEORY (1980s)", "ONE WIDELY CITED ESTIMATE") and stamp the unproven ones ("NEVER PROVEN").
8. **Split screens for comparisons** (`panels`): Earth vs Venus, you vs the planet, three dangers side by side.
9. **The survival game is the `options` list:** each option lights up, gets knocked down by a fact and a gag, and is struck through; then the red verdict.
10. **A little real footage at the proof moments only:** 3–6 short NASA `clip`s or `evidence` images per video, each with a tag and a credit.
11. **Mirror the opening at the end:** the last shot repeats the first frame (same planet, same astronaut pose), then an `endcard`.
