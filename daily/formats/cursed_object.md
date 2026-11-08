# Format: cursed_object — one magic object, used too many times, backfires

Reference: owner's video of 2026-11-08 (3D school cartoon: a boy, a pen that erases memories, a teacher).
Take only the technique, never that story, characters, object or ending. Used by **thai.1382** (German, from
2026-11-09): write natively in German, set in Germany (Schule, Büro, Supermarkt, Wartezimmer, WG-Küche); the
English lines below only show the shape (*„Lena hat heute eine Prüfung. Sie hat nicht gelernt.“*).

## Shape (third person, present tense, very short sentences)
1. **Hook in the first 3 s = problem + object + power**, two lines:
   *“Tom has a job interview today. He has a lighter that skips ten seconds of time.”*
   Problem first (line 1, on a wide shot), the object and its rule second (line 2, on a close-up of the face
   then the object in hand). The rule must be one clear sentence the viewer can predict with.
2. **Use #1 — small and clever:** the problem appears, he uses the object, it works. The other character
   (boss, teacher, neighbour, mother) is confused: a big “?” over their head, a short pause.
3. **Use #2 — greedier:** *“New idea.”* (smug close-up). Works again, the other character is more confused.
4. **Use #3 → #N — too much:** speed up (beats 1.5 s), count the uses aloud (*“the fifth click… the tenth”*),
   each use shown as the same white flash. Side effects grow on the other character, not on the hero.
5. **The reversal (one line):** the side effect lands somewhere he didn't expect — it's now creepy, not funny
   (the other character has forgotten everything, is stuck, has swapped places with him…). Show it calm and
   quiet: one wide, still shot, 3–4 s, no flash.
6. **Ending = a question to the viewer** (last 4–5 s): *“What should Tom do now? Tell me in the comments.”*
   + the Like / Follow pill buttons popping in
   (German: *„Was soll Tom jetzt tun? Schreib's in die Kommentare.“*). Never explain the ending.

Mandatory: the hero is never hurt and nobody is shown hurt; the horror is the consequence, told with a deadpan
voice. It is dark comedy that turns uncanny, not gore.

## Pacing (from the reference, measured)
- A cut every **~2.4 s on average**; the first cut at **2.0 s**; 2 cuts in the first 7 s; in step 4 every
  **1.2–1.5 s**. Never hold a shot longer than 4 s except the reversal shot.
- Alternate **face close-up (reaction) ↔ wide of the room** — every reaction gets its own close-up: worried
  (frown), smug (grin, object raised), confused (other character + “?”), blank (the reversal).
- Each use of the object = 0.3 s white flash over the whole frame + a few sparkle particles; a short camera
  zoom-in on the object just before.
- Re-use the same 3–4 camera set-ups again and again (hero close-up, other character close-up, room wide,
  object insert) — repetition makes the escalation readable.

## Movement — the constant hip sway (key to the look)
Every character on screen is **never still**: the whole body above the hips rocks side to side around the hip
point, about **1 cycle per second, ±6°**, with a small bob on each side; the head counter-tilts a beat later; legs
stay planted. Each character has a different phase so they never move in sync (background extras too).
Happy / smug: bigger and faster (±10–12°, 1.6 cycles/s). The other character's “?” beat: slow (0.6 /s).
The reversal shot is the **only moment the sway stops** — sudden stillness is what makes it creepy.
Use `kit.py` (copied into the story folder by bootstrap.py):
- `ctx.save(); kit.hip_sway(ctx, t, hip_x, hip_y, phase); <torso, arms, head>; ctx.restore()` + `kit.head_lag(t, phase)`
- `kit.flash(ctx, t, t_use, W, H)` on each use, `kit.question_mark(ctx, x, y, t, t0)` over the confused one,
  `kit.end_pills(ctx, t, t_end, W, H)` (Gefällt mir / Folgen) for the last 4–5 s.

## Look
- **Bright daytime, saturated, toy-like** (classroom, office, supermarket, kitchen, waiting room): warm floor,
  pastel walls, one colour per character (cap, cardigan, tie) so they are recognisable at a glance.
- Characters: big round heads, big eyes, simple mouths that change per beat (frown / grin / O). Max 2 main
  characters + optional silent extras in the background.
- Captions: **2–3 words at a time**, white with dark outline, **one key word yellow/orange**, lower-middle of
  the frame (above the UI zone).

## Sound
Narrator neutral and slightly amused, fast. A soft “click/whoosh” on every use; light playful music that
drops out at the reversal (silence makes it creepy).

## Length
The account limits still apply (65–125 s): aim for **65–75 s** (≈ 170–200 words) — 5–7 uses of the object.

## Title / caption
Title = the object (*Das Sprung-Feuerzeug*, *Die Stumm-Fernbedienung*). Caption = the rule as a question + 4–6 hashtags, e.g.
*„Was würdest du damit überspringen? #animation #geschichte #schwarzerhumor #storytime #gruselig“*.
