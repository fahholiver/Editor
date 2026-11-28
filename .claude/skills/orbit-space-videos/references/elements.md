# Orbit scene format

```json
{ "width": 1920, "height": 1080, "fps": 30, "tokens": { "y": "#FFC93C" },
  "shots": [ { "start": 0, "end": 3.0, "trans": "whip", "cam": {...}, "bg": {...}, "els": [ ... ] } ] }
```
- Times are in seconds. A shot runs from `start` to `end` (taken from the word times). Shots follow each other with no gaps.
- `trans`: `whip` (default, a short motion smear at the cut) or `fade` (0.5 s crossfade). Use `fade` for calm moments and the ending.
- `cam`: `zoomFrom`/`zoomTo` (1.0 → 1.05–1.15 is a slow push), `fx`/`fy` (the zoom centre, 0–1), `panFrom`/`panTo`/`panYFrom`/`panYTo` (px), `shake` (px, for falls).
- `bg` (space shots only): `top`/`bottom` colours, `nebula` `[[x, y, radius, colour, alpha], ...]`, `stars` (0–1).
- World coordinates are pixels on a 1920×1080 frame. Overlay `x`/`y` are fractions of the screen (0–1) unless noted.
- Every element takes `t0` (seconds after its shot starts) and optionally `dur`.

## World elements (move with the camera)
| type | fields |
|---|---|
| `planet` | `kind`: venus, mars, jupiter, saturn (with rings), neptune, earth, moon, mercury, io · `x y r` · `light` (radians the light comes from; -2.4 = top-left, 2.6 = bottom-left) · `spin` (texture turns per second, negative = backwards) · `seed` · `label`. A huge `r` with the centre below the frame makes a horizon. |
| `sun` | `x y r`, `surface: true` for a close-up with boiling plasma, `vx`/`vy` to make it rise |
| `blackhole` | `x y r` |
| `astronaut` | `x y s` (height px) · `rot` · `spin` (rad/s) · `vx`/`vy` (px/s) · `lamp` (0–1 headlamp beam) · `flip` |
| `descent` | Falling through cloud decks, full screen. `sky: [top, bottom]` · `cols: [far, mid, near]` · `speed` · `alpha` · `rain` (colour for acid/methane rain) · `bolts: [t, ...]` (lightning flashes) |
| `surface` | Standing on the ground, full screen. `kind`: venus, mars, moon · `cols` (6 colours to override) · `heat` (shimmer px) · `rocks` · `volcano` (x as a fraction, glowing peak) |
| `probe` | Venera-style lander. `x y s` · `drop` (seconds to fall in from above) · `dead` (t when its light dies) · `cook` (seconds to glow red) |
| `rocket` | `x y s rot vx vy` |
| `airship` | Floating habitat. `x y s` |

## Overlays (fixed on screen)
| type | fields |
|---|---|
| `you` | The red "YOU" label and curved arrow. `x y` = the point to aim at (world px), `lx ly` = where the label sits, `text` (default YOU) |
| `title` | Big planet name, top left. `text sub dur` |
| `caption` | Keyword caption, bottom centre. `text` with `*word*` = yellow and `!word!` = red · `dur` · `y` · `size` |
| `chapter` | Full-screen yellow circle wipe. `n` ("KILLER #2") · `text` ("ACID CLOUDS") · `dur` (about 0.9) |
| `big` | Huge number or word. `text` · `sub` · `x y size` · `tone`: yellow, red |
| `pill` | Fact chip. `text x y` · `tone: "red"` for the shocking one · `align: "right"` |
| `tag` | Small corner label. `text x y` |
| `stamp` | Verdict stamp that slams in. `text x y rot size` · `tone`: red (default), yellow, green |
| `counter` | Number that runs. `label from to unit x y t1` (seconds to run) · `decimals` |
| `gauge` | Half-circle dial. `label from to max unit x y r t1`. Turns red above 80 % of `max`. |
| `thermo` | Thermometer. `from to min max label x y t1`. Turns blue below zero. |
| `depth` | Ocean depth bar with a sinking submarine. `label max to x y` |
| `melt` | Lead block melting into a puddle. `x y` |
| `timer` | Clock counting up to `to` seconds. `label x y t1 dead` (turns red when the probe dies) |
| `lineup` | Planets side by side. `items: [{kind, r, label, note, at}]` · `y gap`. `kind: "sun"` works too. |
| `fit` | "N Earths fit inside": `big` (planet kind) · `count` · `show` (dots drawn) · `label x y r t1` |
| `radar` | Sweeping scope. `label x y r` · `blips: [{x, y, label, red}]` (x and y from -1 to 1) |
| `evidence` | Real image in a white frame. `src` (path relative to the scene file) · `credit` · `tag` · `x y w h rot zoom fx fy dur` |
| `flash` | White flash. `dur a` |

## Props and infographics (for gags, comparisons and proof)
Every joke in the script should land on one of these. Unless noted, `x`/`y` are screen fractions.
| type | fields |
|---|---|
| `label` | Small bold uppercase text, the default way to put words on screen. `text x y size align` · `tone` red/yellow/green · `underline: true` (red rule) · `sub` |
| `receipt` | A till receipt that rises into frame. `title` · `items: [[name, qty], ...]` · `total` · `x y w rot`. Use it for "it keeps a receipt for every meal" style jokes. |
| `doc` | An official paper. `org title` · `fields: [[label, value], ...]` (or none for blank lines) · `stamp stampAt stampTone` (red/green) · `x y w h rot` |
| `loading` | A progress box. `text` ("TRANSLATING…") · `to` (0–1) · `t1` · `tone`. Pair it with a `stamp` "CANCEL" for the punchline. |
| `options` | The survival-game list. `title` · `items: [{text, at, out}]`: an item lights up at `at` and is struck through at `out` · `verdict: {text, at}` · `showAll` |
| `panels` | Split screen. `titles: [...]` (2–3) · `bg: [...]` · `stagger`. Put other elements inside each third or half. |
| `stick` | Stick-figure "YOU" for everyday comparisons. `x y s pose` (stand/wave/panic/sit) · `label` · `col` |
| `eyes` | A dark room full of eyes watching a panicking stick figure. `lookX lookY n` ("trying to sneak out of a room that's already watching you") |
| `balance` | A balance scale. `left right` labels · `tilt` (+ = right side heavier) |
| `pie` | A pie chart. `slices: [{v, label, col}]` · `title r` · `stat: {label, big, small}` side box |
| `icons` | An isotype grid that counts down. `count cols from to` · `icon` dot/planet/astronaut/rocket/person · `label caption big` · `size col` |
| `xray` | A body scan. `part` lungs/heart/brain/blood · `label title s` |
| `meters` | Level meters side by side (a "volume contest"). `title` · `bars: [{label, level, note, at}]` |
| `orbitmap` | A small solar-system diagram, the space version of a map inset. `highlight` (ring index) · `label n ring angles` |
| `clip` | Real video in a white frame (or `full: true`). `src` (mp4/mov/webm, converted automatically) · `from` (start second) · `rate credit tag zoom x y w h dur` |
| `scan` | The "you're being scanned" effect: green tint and sweep. `text` |
| `endcard` | Thanks + comment bubble + WATCH NEXT box. `text ask` |
