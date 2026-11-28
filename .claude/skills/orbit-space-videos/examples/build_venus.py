import json
VEN = {"kind": "venus", "seed": 4}
def sh(a, b, els, cam=None, **kw): d = {"start": a, "end": b, "els": els}; cam and d.update(cam=cam); d.update(kw); return d
def rel(a, t): return round(t - a, 2)
shots = []
# 1 hook
a, b = 0, 3.0
shots.append(sh(a, b, [
  {"type": "sun", "x": 60, "y": 1000, "r": 30},
  {"type": "planet", **VEN, "x": 1300, "y": 560, "r": 420, "light": 2.6, "spin": .03},
  {"type": "astronaut", "x": 520, "y": 640, "s": 48, "vx": 12, "rot": .35},
  {"type": "you", "x": 545, "y": 600, "lx": 330, "ly": 390, "t0": rel(a, .34)},
  {"type": "title", "text": "VENUS", "sub": "2ND PLANET FROM THE SUN", "t0": rel(a, 1.2), "dur": 1.8}],
  {"zoomFrom": 1, "zoomTo": 1.12, "fx": .62}))
# 2 calm close-up
a, b = 3.0, 6.82
shots.append(sh(a, b, [
  {"type": "planet", **VEN, "x": 960, "y": 900, "r": 900, "light": -1.9, "spin": .02},
  {"type": "caption", "text": "it looks *calm*", "t0": rel(a, 3.5), "dur": 3.0}], {"zoomFrom": 1.0, "zoomTo": 1.1, "fy": .4}))
# 3 size twin
a, b = 6.82, 10.2
shots.append(sh(a, b, [
  {"type": "lineup", "y": .66, "gap": 160, "items": [{"kind": "venus", "seed": 4, "r": 228, "label": "VENUS", "note": "12,104 km wide", "at": 0}, {"kind": "earth", "r": 240, "label": "EARTH", "note": "12,742 km wide", "at": .9}]},
  {"type": "caption", "text": "almost the *same size*", "y": .12, "t0": rel(a, 7.58), "dur": 2.5}], {"zoomFrom": 1.0, "zoomTo": 1.05}))
# 4 what kills you first
a, b = 10.2, 12.88
shots.append(sh(a, b, [
  {"type": "planet", **VEN, "x": 960, "y": 1500, "r": 1000, "light": -1.6, "spin": .02},
  {"type": "astronaut", "x": 960, "y": 420, "s": 110, "spin": .9, "vy": 30},
  {"type": "big", "text": "WHAT KILLS YOU FIRST?", "size": 120, "y": .16, "tone": "yellow", "t0": rel(a, 10.74)}], {"zoomFrom": 1.0, "zoomTo": 1.12, "fy": .4}))
# 5 wind
a, b = 12.88, 24.06
shots.append(sh(a, b, [
  {"type": "planet", **VEN, "x": 960, "y": 1900, "r": 1500, "light": -1.6, "spin": .16},
  {"type": "astronaut", "x": 300, "y": 300, "s": 80, "vx": 120, "spin": 1.6, "lamp": .5},
  {"type": "chapter", "n": "KILLER #1", "text": "THE WIND", "dur": .9},
  {"type": "counter", "label": "WIND AT THE CLOUD TOPS", "from": 0, "to": 300, "unit": "km/h", "x": .05, "y": .08, "t0": rel(a, 15.9), "t1": 1.4},
  {"type": "big", "text": "4 DAYS", "sub": "FOR THE WIND TO CIRCLE THE WHOLE PLANET", "y": .42, "size": 210, "t0": rel(a, 22.6)},
  {"type": "caption", "text": "fast enough to *drag you* around the planet", "t0": rel(a, 19.46), "dur": 3.0}], {"zoomFrom": 1.0, "zoomTo": 1.08, "panFrom": -60, "panTo": 80}))
# 6 acid clouds
a, b = 24.06, 35.1
shots.append(sh(a, b, [
  {"type": "descent", "sky": ["#ecca86", "#b98a3e"], "cols": ["#f2dca4", "#dab36a", "#b8893e"], "speed": 700, "rain": "#e8f27a"},
  {"type": "astronaut", "x": 1420, "y": 640, "s": 120, "spin": .5, "rot": -.4, "lamp": 0},
  {"type": "chapter", "n": "KILLER #2", "text": "ACID CLOUDS", "dur": .9},
  {"type": "counter", "label": "ALTITUDE", "from": 70, "to": 45, "unit": "km", "x": .05, "y": .08, "t0": rel(a, 25.7), "t1": 9},
  {"type": "caption", "text": "they're not *water*", "t0": rel(a, 28.4), "dur": 1.3},
  {"type": "pill", "text": "SULFURIC ACID", "tone": "red", "x": .66, "y": .1, "t0": rel(a, 30.16)},
  {"type": "stamp", "text": "ACID", "x": .74, "y": .6, "rot": .14, "t0": rel(a, 30.8), "dur": 1.2},
  {"type": "big", "text": "25 KM", "sub": "OF ACID CLOUD, STRAIGHT DOWN", "y": .42, "size": 220, "t0": rel(a, 32.04)}], {"zoomFrom": 1.0, "zoomTo": 1.1, "shake": 3}))
# 7 pressure
a, b = 35.1, 52.6
shots.append(sh(a, b, [
  {"type": "descent", "sky": ["#b06a22", "#4a2208"], "cols": ["#c98a40", "#a2621f", "#7a4212"], "speed": 380, "alpha": .85},
  {"type": "astronaut", "x": 480, "y": 520, "s": 100, "spin": .25, "rot": .2, "lamp": .6},
  {"type": "chapter", "n": "KILLER #3", "text": "THE PRESSURE", "dur": .9},
  {"type": "counter", "label": "ALTITUDE", "from": 45, "to": 0, "unit": "km", "x": .05, "y": .08, "t0": rel(a, 36.3), "t1": 15},
  {"type": "pill", "text": "AIR: 96.5% CARBON DIOXIDE", "x": .05, "y": .26, "t0": rel(a, 39.9)},
  {"type": "gauge", "label": "AIR PRESSURE (EARTH = 1×)", "to": 92, "max": 100, "unit": "×", "x": .5, "y": .52, "r": 180, "t0": rel(a, 44.2), "t1": 1.2},
  {"type": "depth", "label": "A SUBMARINE FEELS THIS AT", "max": 1000, "to": 900, "x": .79, "y": .24, "t0": rel(a, 48.86)},
  {"type": "caption", "text": "*92×* harder than Earth's air", "t0": rel(a, 45.22), "dur": 3.4}], {"zoomFrom": 1.04, "zoomTo": 1.0, "shake": 2}))
# 8 heat
a, b = 52.6, 66.9
shots.append(sh(a, b, [
  {"type": "surface", "kind": "venus", "heat": 2.4, "rocks": True},
  {"type": "astronaut", "x": 860, "y": 860, "s": 90, "rot": .6, "lamp": .4},
  {"type": "chapter", "n": "KILLER #4", "text": "THE HEAT", "dur": .9},
  {"type": "thermo", "from": 20, "to": 465, "max": 500, "label": "SURFACE TEMPERATURE", "x": .12, "y": .78, "t0": rel(a, 54.6), "t1": 1.4},
  {"type": "caption", "text": "day *or* night", "t0": rel(a, 58.3), "dur": 2.4},
  {"type": "pill", "text": "HOTTER THAN MERCURY", "tone": "red", "x": .6, "y": .12, "t0": rel(a, 61.34)},
  {"type": "melt", "x": .72, "y": .78, "t0": rel(a, 64.6)},
  {"type": "stamp", "text": "MELTS LEAD", "x": .72, "y": .44, "rot": -.1, "t0": rel(a, 65.58)}], {"zoomFrom": 1.0, "zoomTo": 1.07, "fx": .3, "fy": .6}))
# 9 Venera 13
a, b = 66.9, 85.42
shots.append(sh(a, b, [
  {"type": "surface", "kind": "venus", "heat": 2.6, "rocks": True},
  {"type": "probe", "x": 1300, "y": 900, "s": 230, "drop": 2.4, "t0": rel(a, 67.5), "dead": rel(a, 84.48) - rel(a, 67.5), "cook": 17},
  {"type": "tag", "text": "VENERA 13 · 1982", "x": .05, "y": .06, "t0": rel(a, 69.58)},
  {"type": "timer", "label": "BUILT TO SURVIVE", "to": 1920, "x": .05, "y": .15, "t0": rel(a, 74.84), "t1": 1.2},
  {"type": "timer", "label": "ACTUALLY SURVIVED", "to": 7620, "x": .05, "y": .35, "t0": rel(a, 77.52), "t1": 2.6, "dead": rel(a, 84.48) - rel(a, 77.52)},
  {"type": "caption", "text": "*colour photos* of the ground", "t0": rel(a, 81.4), "dur": 2.4},
  {"type": "stamp", "text": "COOKED", "x": .7, "y": .32, "rot": -.12, "t0": rel(a, 84.48)}], {"zoomFrom": 1.0, "zoomTo": 1.12, "fx": .66, "fy": .78}))
# 10 wrong world: spin and sunrise
a, b = 85.42, 93.76
shots.append(sh(a, b, [
  {"type": "planet", **VEN, "x": 960, "y": 560, "r": 330, "light": -2.4, "spin": -.06},
  {"type": "caption", "text": "things would feel *wrong*", "t0": rel(a, 86.24), "dur": 2.6},
  {"type": "pill", "text": "ONE SPIN = 243 EARTH DAYS", "x": .06, "y": .3, "t0": rel(a, 90.28)},
  {"type": "pill", "text": "ONE TRIP AROUND THE SUN = 225 DAYS", "x": .94, "y": .62, "align": "right", "t0": rel(a, 92.5), "tone": "red"}], {"zoomFrom": 1.0, "zoomTo": 1.08}))
a, b = 93.76, 97.78
shots.append(sh(a, b, [
  {"type": "surface", "kind": "venus", "heat": 1.5, "cols": ["#3a1a0a", "#a24e18", "#e0904a", "#8a3e14", "#62280c", "#3a1606"]},
  {"type": "sun", "x": 260, "y": 820, "r": 34, "vy": -70},
  {"type": "astronaut", "x": 1300, "y": 820, "s": 90, "rot": 0, "flip": True, "lamp": 0},
  {"type": "pill", "text": "← WEST", "x": .06, "y": .1, "t0": .4},
  {"type": "caption", "text": "the sun rises in the *west*", "t0": rel(a, 95.54), "dur": 2.1}], {"zoomFrom": 1.0, "zoomTo": 1.06}))
# 11 volcanoes + real radar images
a, b = 97.78, 112.38
shots.append(sh(a, b, [
  {"type": "surface", "kind": "venus", "volcano": .62, "heat": 1.6},
  {"type": "caption", "text": "the ground might not be *still*", "t0": 0, "dur": 2.3},
  {"type": "evidence", "src": "media/PIA00271.jpg", "credit": "NASA/JPL · Magellan radar map", "tag": "REAL NASA RADAR · UNDER THE CLOUDS", "x": .5, "y": .47, "w": 760, "h": 600, "t0": rel(a, 100.26), "dur": 5.9, "zoom": .12},
  {"type": "evidence", "src": "media/PIA00106.jpg", "credit": "NASA/JPL · Magellan radar, height exaggerated 10×", "tag": "REAL NASA RADAR · MAAT MONS VOLCANO", "x": .5, "y": .47, "w": 1100, "h": 620, "t0": rel(a, 106.14), "rot": .012, "zoom": .1},
  {"type": "pill", "text": "A VENT CHANGED SHAPE IN 8 MONTHS", "tone": "red", "x": .5, "y": .84, "t0": rel(a, 107.68), "align": "right"},
  {"type": "stamp", "text": "STILL ERUPTING?", "tone": "yellow", "x": .72, "y": .2, "rot": .08, "size": 70, "t0": rel(a, 110.6)}], {"zoomFrom": 1.0, "zoomTo": 1.08, "fx": .62}))
# 12 the twist
a, b = 112.38, 114.38
shots.append(sh(a, b, [{"type": "big", "text": "BUT…", "size": 300, "tone": "yellow", "t0": 0}], {"zoomFrom": 1.0, "zoomTo": 1.1}))
a, b = 114.38, 125.94
shots.append(sh(a, b, [
  {"type": "descent", "sky": ["#fbe6b6", "#e9c27a"], "cols": ["#fff1cf", "#f2d79a", "#e0b56c"], "speed": 60, "alpha": .95},
  {"type": "astronaut", "x": 900, "y": 470, "s": 120, "rot": .1, "lamp": 0},
  {"type": "counter", "label": "ALTITUDE", "from": 50, "to": 50, "unit": "km", "x": .05, "y": .08, "t0": rel(a, 115.68), "t1": .5},
  {"type": "gauge", "label": "AIR PRESSURE (EARTH = 1×)", "from": 92, "to": 1, "max": 100, "unit": "×", "x": .78, "y": .5, "r": 160, "t0": rel(a, 117.68), "t1": 1.6},
  {"type": "caption", "text": "roughly what you feel *right now*", "t0": rel(a, 119.0), "dur": 2.4},
  {"type": "stamp", "text": "EARTH-LIKE", "tone": "green", "x": .32, "y": .22, "rot": -.1, "t0": rel(a, 122.24)}], {"zoomFrom": 1.0, "zoomTo": 1.06}))
a, b = 125.94, 131.42
shots.append(sh(a, b, [
  {"type": "descent", "sky": ["#fbe6b6", "#e9c27a"], "cols": ["#fff1cf", "#f2d79a", "#e0b56c"], "speed": 50, "alpha": .95},
  {"type": "airship", "x": 980, "y": 430, "s": 170},
  {"type": "pill", "text": "NASA STUDY · HAVOC CONCEPT", "x": .05, "y": .08, "t0": .2},
  {"type": "caption", "text": "floating *above the acid*", "t0": rel(a, 129.12), "dur": 2.2}], {"zoomFrom": 1.1, "zoomTo": 1.0, "panFrom": 40, "panTo": -40}, trans="fade"))
a, b = 131.42, 138.4
shots.append(sh(a, b, [
  {"type": "planet", **VEN, "x": 1250, "y": 560, "r": 400, "light": 2.6, "spin": .03},
  {"type": "astronaut", "x": 540, "y": 520, "s": 48, "rot": .3, "vx": -6},
  {"type": "caption", "text": "it will never let you *land*", "t0": rel(a, 131.5), "dur": 2.0},
  {"type": "caption", "text": "as long as you never *come down*", "t0": rel(a, 135.5), "dur": 2.6}], {"zoomFrom": 1.12, "zoomTo": 1.0, "fx": .62}, trans="fade"))
json.dump({"width": 1920, "height": 1080, "fps": 30, "shots": shots}, open("venus.json", "w"), indent=1)
print(len(shots), "shots, ends", shots[-1]["end"])
