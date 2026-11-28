# Script formula: finance documentaries

The viewer clicked for one question ("how did they lose?", "how do they make so much?"). Answer it at the end, but show the size of the stakes in the first 20 seconds.

## Shape (about 150 words a minute)
1. **Thriller cold open (25 to 40 s).** Write it like the first minute of a crime film. Short lines, each its own paragraph (each paragraph break is a dramatic pause):
   - Start on the end, with a date: "September 23rd, 2010." Then what happened, flat: "A company with thousands of stores files for bankruptcy."
   - The rewind and the stakes: "Ten years earlier, it could have stopped all of it. For fifty million dollars."
   - The fatal moment, told as a scene: who walked in, what they offered, what was said ("Blockbuster's CEO was trying not to laugh. The answer was no.").
   - The reveal as the last line: "That website was Netflix."
2. **The title** on its own line: `[TITLE: HOW BLOCKBUSTER WENT FROM | $6 BILLION TO ONE STORE]` (small line | big line). It's not spoken: the voice leaves a 3.4-second silence and the title slams in. Shape: "How X went from [peak] to [end]", "Why X lost [huge number]", "How X made [number] and lost it all". Two numbers that clash beat any adjective.
3. **Chapters** with `[CHAPTER: CHAPTER ONE | THE GOLD RUSH]` on their own line: the rise, the peak, the mistake, the challenger, the fall, what happened next. Every chapter ends on a hook into the next.
4. **One number per beat.** Each number gets its own sentence so the screen can show it big. Give it a human scale: "eight hundred million dollars in late fees, from people who returned a tape late".
5. **People and decisions.** Name the people who decided (CEOs, founders), say what they decided, when, and what they knew then. No villains: explain why the decision looked smart at the time.
6. **The lesson**, said simply near the end (what the business actually depended on), then a callback to the cold open.

## Lines
- Say numbers the way people say them: "six billion dollars", "nine thousand stores", "in 2004".
- Say the source for anything surprising ("according to the company's own annual report").
- Short spoken sentences. One dry joke every two or three minutes.
- No em dashes, no "not just X but Y", no "let's dive in", no "little did they know". Run the humanizer.
- Call to action once, after the first chapter's payoff ("If you like these business stories, like the video so YouTube shows you more of them"), never at the very end.
- Nothing that sounds like investment advice. This is history, not "buy this stock".

## Chapter and title markers
`[TITLE: small line | big line]` once, at the end of the cold open (own voice: a 3-second pause there). `[CHAPTER: CHAPTER ONE | THE GOLD RUSH]` for chapters. The free voice turns it into a 2.2-second pause and saves its time in `chapters.json`. One every 2 to 3 minutes. Own voice (ElevenLabs): a 2-second pause at each marker (`<break time="2s" />`).

## Timing map for 15 minutes
0:00 thriller cold open · 0:35 title · 0:40 the scale (peak numbers) · 1:00 CHAPTER ONE the rise · 3:00 CHAPTER TWO the peak · 5:30 CHAPTER THREE the mistake · 8:00 CHAPTER FOUR the challenger · 10:30 CHAPTER FIVE the fall · 13:00 what happened next · 14:20 the lesson and the callback.
A preview (60 to 90 s) is the cold open, the title, the scale and the start of chapter one.
