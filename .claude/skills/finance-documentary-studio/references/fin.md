# The finance look: episode file reference

    from fin import *
    film = Film(__file__, vo='vo.wav', words='words.json', mood='money')
    T = film.cue                    # T('phrase') -> time the phrase starts; T('no', after=T('answer')); film.end('phrase')
    fin = Fin(film, chapter_subs={'THE GOLD RUSH': 'Dallas, 1985'})
    film.music = {'hits': [T('bankrupt')]}           # optional: risers into impacts at these times; 'drops': [(a, b)] near silence

Shots follow each other with quick crossfades (0.45 s). Each starts at its time and lasts until the next one.

| Shot | Use it for | Call |
|---|---|---|
| photo | a real place, product, person, store | `fin.photo(t, 'media/x.jpg', frm=(fx, fy, zoom), to=(fx, fy, zoom))` slow push; `card=.5, label='Netflix, 2000'` shows it whole on a white card |
| chart | anything over time (revenue, stores, share price) | `fin.chart(t, [(2000, 4.96), ...], 'Revenue', sub='billions a year', fmt=lambda v: f'${v:.1f}B', events=[(2004, 'The peak')], crash_from=2004, dur=2.5)` |
| number | one huge number | `fin.number(t, 6_100_000_000, label='Revenue, 2004', sub='one year of rentals', dur=1.3, color=GREEN)` (`prefix=''` for counts, `v0` to count down) |
| bars | comparing a few things | `fin.bars(t, [('Blockbuster', 9094, BLUE), ('Netflix', 0, RED)], 'Stores, 2004')` |
| versus | the core conflict | `fin.versus(t, ('Blockbuster', '$6B', 'a year', BLUE), ('Netflix', '$50M', 'asking price', RED))` |
| statement | the key line of a paragraph | `fin.statement(t, 'Trying not to laugh', sub='...', color=GOLD)` |
| clipping | proof: the real article, filing or press release with the key line highlighted as it's said | screenshot: `fin.clipping(t, 'media/clip_10k.png', mark=[(.08, .41, .93, .45)], at=T('six billion'), source='sec.gov', note='Form 10-K, 2004')`; no screenshot: `fin.clipping(t, outlet='Mental Floss', headline='...', body='exact published text', phrase='exact words to mark', at=T('800'), dur=2.2, source='mentalfloss.com')` |
| flash | fast montage in the cold open | `fin.flash(t, ['media/a.jpg', 'media/b.jpg'], every=.42)` |
| scene | anything custom | `fin.scene(t, fn)` with `fn(c, t, u)` drawing on 1920x1080 over the dark background |

Thriller cold open: everything before the `[TITLE: ...]` pause gets letterbox bars, hard cuts with a glitch, a red pulse on the heartbeat, and a heartbeat + ticking-clock score with a riser into the title (`Fin(film, thriller=False)` turns it off). The title card is drawn by itself in the pause.

Overlays (inside `@fin.screen def words(c, t): ...`, each with a start and end time):
- `datestamp(c, t, t0, t1, 'SEPTEMBER 23, 2010', 'BLOCKBUSTER FILES FOR BANKRUPTCY', y=...)` typed date line with a red cursor (cold open).
- `credit_line(c, t, t0, t1, 'Photo: ...')` on every photo. In the example `cr('file.jpg')` reads the saved credit.
- `tag(c, t, t0, t1, 'Dallas, Texas', 'The first store opens', 'Where it started')` lower-left tag (kind in a green pill).
- `name_tag(c, t, t0, t1, 'Reed Hastings', 'Netflix co-founder', note, x=120, y=560)` beside a person's photo.
- `year_badge(c, t, t0, t1, 2004, 'The peak')` top-left; the year can be a function of t.
- `stamp(c, t, t0, 'BANKRUPT', RED, y=..., size=..., t1=...)` slams a word on screen (adds a thud).
- `ticker(c, t, t0, t1, [('STORES', '9,094', GREEN), ('LATE FEES 2000', '$800M', GOLD)])` along the bottom (green = up arrow, red = down).
- `quote(c, t, t0, t1, 'words', 'who', 'source')` only for real, sourced quotes.
- `title_card(c, t, t0, t1, 'The rise and fall of', 'Blockbuster', sub)`.

Colours: `GREEN` growth, `RED` the fall, `GOLD` events and money facts, `BLUE` / `CYAN` the other side. Chapter cards (CHAPTER 01, title, a little chart line) come by themselves in the narrator's pauses.

Rhythm that works: photo → number → photo → chart → stamp → photo → versus. Never more than two number shots in a row; a new visual with almost every sentence; a stamp only at the one big turn of a chapter.
After a chapter card the first shot is always a photo, never a statement or counter (their text would cross-fade over the card's title), and no text repeats the card: if the card says "Minnesota, 1886", don't follow it with a "MINNESOTA, 1886" statement or an 1886 year badge.
Never show the same photo in more than two shots in a row; use another photo, a chart or a clipping between them.
Text placement: tags sit bottom-left, credits bottom-right, year badges top-left; don't put a stamp on top of a statement's subtitle (use `y=H - 140`).

## Source clippings (the proof shots)
One or two per chapter, on the line that carries the chapter: the revenue in the 10-K, the bankruptcy press release, the court filing, the CEO's real quote in a newspaper. The card slides in tilted, pushes in on the marked line, and a yellow marker sweeps across it while the narrator says it (cue `at` on the first spoken word of that line, `dur` about the time it takes to say it).
- **Screenshot (best):** the user saves a screenshot of the page as `media/clip_<what>.png` (ask for it in the asset list). Run `python3 scripts/grid.py media/clip_<what>.png`, look at the `.grid.png`, and give one box per line of the passage in `mark` (fractions: x0, y0, x1, y1, with a little room above and below the letters). Check it with `stills`: the yellow must sit exactly on the words.
- **No screenshot:** give the exact published wording (`body`, copied from the page, never paraphrased) and the words to mark (`phrase`, copied exactly from `body`). The card says "quoted text, layout recreated" by itself. Keep `body` to two or three sentences.
- Always `source=` the site (sec.gov, nytimes.com) and add the clipping's quote and URL to `sources.md`. Never invent a clipping or make a screenshot of something that wasn't published.
- No tag or ticker under a clipping (the Source label sits bottom-left).

## Shorts (vertical, made on purpose)
A Short is its own video, not the long film boxed into a phone screen.
- Script, 25 to 35 seconds (70 to 90 words): line one is the most shocking fact ("This company could have owned Netflix for fifty million dollars."); one idea; short sentences; the last line loops back to the first ("...all because of a fifty million dollar no.").
- Voice: `python3 scripts/voice.py script.txt vo.wav --voice am_michael --short` (a normal read with short gaps between sentences: brisk, not rushed). With an ElevenLabs file, ask for normal speed and no long pauses.
- **The captions are the only words on screen**, plus the small photo credits. No callouts of any kind: no tags, name tags, year badges, statements, counters, stamps, versus cards, clippings, tickers or end card. Real photos (vertical crops, set `frm`/`to` on the subject, a slow push) carry the picture; a chart is fine with an empty title (`fin.chart(t, pts, '', ...)`). A new picture every 2 to 3 seconds and never one photo for more than 3 seconds (switch photo, or cut to a second crop of it); `Fin(film, xfade=.2, thriller=False)`. A chart must show what the narrator is saying at that moment (if the line is about losses, chart the losses, not revenue).
- Episode file in `short/`: `os.environ['FDS_VERTICAL'] = '1'` before `from fin import *`. Captions (3 words at a time, the spoken word in green) are on by default; credits sit small at the bottom left.
- The link to the full video goes in the Short's description and YouTube's related-video setting, not on screen.
- Upload: a title under 60 characters, one line that links the full video, 3 or 4 hashtags with #shorts.

## Archive footage (optional)

`scripts/footage.py search "<era, place or thing>"` lists free clips (Wikimedia Commons videos, and the public-domain Prelinger Archives and US government films on the Internet Archive). Watch the clip in the browser, note the second where the good part starts, then `get <id> media/ --start S --dur D --name short_name` and use `fin.footage(T('...'), 'media/short_name.mp4', start=0, speed=1)`.

- Photos stay the base of the film. Add 2 to 5 clips of 3 to 8 seconds where a real moving picture exists: the city and the year, the headquarters, a shopping centre of that decade, a trading floor.
- Free film of one named company is rare, and there is little after about 1985. Search the place and the decade ("Chicago 1974", "department store 1950s"), not only the company name. If nothing fits, use none.
- Every clip gets a `credit_line` (the credit is saved next to the clip) and a `tag` with the place and year, worded so era footage is never mistaken for the company itself ("An American shopping centre / Archive film, 1957").
- Look at the frames you will use (`episode.py stills`) before rendering: old reels contain slates, leader and unrelated scenes.
- Add the footage credits to upload.md and sources.md with the photo credits.
