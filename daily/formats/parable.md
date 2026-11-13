# Format: parable — a French fable/parable, retold for today, with a trending angle

Owner's idea (2026-11-10) for **kaelusuxkzx** (French, from 2026-11-11), engine **vintage** (2D cartoon in a
hand-painted 3D world, see `daily/studio/README.md`), **1:1 (1080×1080)**. It is **not horror**: a warm,
clever moral tale in French, the kind people share with friends and family.

## Source material (public domain only)
The fables of **Jean de La Fontaine** (1668–1694), and also Perrault's tales, Florian's fables and French
folk parables. These are public domain. Retell them in your own modern French words, with new characters and
a modern setting. You may quote the fable's original morale line word for word at the end, e.g. *« Rien ne
sert de courir ; il faut partir à point. »*. Never use any modern adaptation, film, cartoon or book.
Read the log: never repeat a fable.

## "Something trending" (owner's rule)
Before writing, search the web for what French people talk about **this week** (TikTok France trends,
French news: la rentrée, les soldes, Noël, les prix, la météo, the phone, social media, money, work, AI,
sport…). Then pick the fable whose morale fits that topic best and set the retelling in it:
*Le Corbeau et le Renard* → a fake influencer flatters someone into buying
the thing; *La Cigale et la Fourmi* → a December with no savings left; *Le Lièvre et la Tortue* → the friend
who "starts Monday". Keep it light and never political. Use no real people, brands or apps by name, no news
victims. Note the trend you used in insights.

## Shape (third person, present tense, 61–85 s)
1. **Hook (0–3 s): the modern situation in one line**, with the animal/character on screen, e.g.
   *« Un renard a 2 millions d'abonnés. Il n'a jamais rien acheté de sa vie. »*
2. **Setup:** who wants what (2–3 lines). The characters are animals or people, flat bean-head cartoon cards.
3. **The temptation / the mistake** (2–3 beats, each a clear visual: a prop, a gesture, a place).
4. **The turn:** the consequence lands, calmly and funnily. Nobody gets hurt.
5. **The morale (last 8–10 s):** first the original La Fontaine line (on a painted sign or a scroll in the
   world, in French), then one modern line in plain words. End on a question for the comments: *« Et toi, tu
   es plutôt cigale ou fourmi ? »*.

## Pacing and sound (different from the horror accounts — on purpose)
- **No fast-cut opening.** It is storybook pacing: **one shot per sentence, 3–6 s**, smooth gliding cameras,
  something always moving (a breeze, a blink, a bird). The light follows the story: golden for the setup,
  dusk for the mistake, a warm dawn for the morale.
- **No channel background track** (`music_bed: false`). Compose the music per scene in `work/score.json`:
  `storybook` (3/4 waltz) for the setup, `mischief` for the trick/temptation, `sad` or `tense` for the mistake,
  a short `silence` before the turn, `hopeful` for the morale. Low under the voice (the mixer sets it). Burned-in word captions as the kit does them.
- Voice: the account's voice (Rémy), warm storyteller tone.

## Look (vintage, 1:1)
1080×1080 (the square frame fits two characters side by side, which the kit's 9:16 frame could not). French
sets built from the kit's primitives and paint.js textures: a village square with a fountain, a boulangerie
front, a vineyard, a Paris roof with zinc and chimneys, a market. Signs and labels are painted in French.
Keep faces out of the bottom 140 px (TikTok UI).

## Viral formula (owner, 2026-11-13)
Apply the 5-step formula in `STORY_BRIEF.md`: the hook drops us into the modern situation with a number;
the fable's rule (the temptation) is clear by 8 s; each mistake beat is bigger than the last and has a number
or a visible object; the turn is ironic (the one who ignored the hype wins); the last line brings back a line
said at the start, reversed, then the one-word comment question (see also `curiosity.md`).

## Title / caption
Title = a modern twist on the fable title (*« Le Renard et ses abonnés »*). Caption = the comment question
+ 3–5 hashtags, e.g. *« Cigale ou fourmi ? #fable #lafontaine #morale #histoire #animation »*.
