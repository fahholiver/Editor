# Format: interactive_series — "Partie N", the viewer chooses (comment A or B)

Reference: owner's video of 2026-11-08 (school bus "Part 2": head count, driver vs Mum, tuba case). A serial in
2–4 parts on consecutive days; each part ends with a binary choice the viewer answers in the comments.

## Shape
1. **Recap hook (Part ≥ 2), first 3 s:** what happened + the choice from last time, then the consequence at once.
   We cannot read the comments, so never invent a vote result: say "Si tu as dit RESTER…" / "Tu as choisi de
   rester." — or, for Part 1, a hook that drops the viewer into a strange rule or count (*"Le chauffeur compte
   les élèves. Il en compte deux. Tu es seul."*).
2. **Second person ("tu"), present tense.** The viewer is the character.
3. **Two voices that contradict each other** — an authority on site (driver, concierge, nurse, guard) vs someone
   trusted far away on the phone (Maman, a sister, a best friend). Each gives a rule; both sound reasonable.
4. **One suspicious object or place, shown again and again** (a case, a cupboard, a lift door) — circle it in
   red each time it matters.
5. **Escalation by small facts** (a count that is off by one, a ringtone, a light, a text), each a beat.
6. **Cliffhanger + choice (last 6–8 s):** a question card: *"À QUI TU FAIS CONFIANCE ?"* + two one-word options in
   caps (*OUVRIR / FERMER*, *RESTER / DESCENDRE*), *"Commente OUVRIR ou FERMER"*, *"Partie N+1 bientôt"*.
7. **Next day:** continue the same series (read the account's last log entry: `series`, `part`, `choice`).
   Follow the option that makes the better story, phrased as above. After Part 3 or 4, end the series with a real
   ending (no question) and start a new series the day after.

## On screen (use `kit.py`, copied into the story folder)
- `kit.part_tag(ctx, n)` top-left on every shot ("Partie 2").
- `kit.red_circle(ctx, x, y, r, t, t0)` when the suspicious object is named.
- `kit.choice_card(ctx, t, t0, question, a, b, n_next)` for the final 6–8 s.
- Phone texts / calls / checklists with the engine's phone UI and `checklist()`.

## Log (publish.py)
Pass `--series "<series title>" --part N --choice "OUVRIR|FERMER"` so tomorrow's run knows where the story stands.

## Title / caption
Title = series title + part (*Le bus de nuit — Partie 2*). Caption = the question + the two words, e.g.
*"À qui tu fais confiance ? Commente OUVRIR ou FERMER 👇 #horreur #histoiredhorreur #partie2 #flippant #animation"*.
