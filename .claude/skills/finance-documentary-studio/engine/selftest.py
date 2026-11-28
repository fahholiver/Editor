"""Setup check: draws one finance frame (a chart that crashes, a year badge, a tag) and saves selftest.png next to this folder."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skia
from fin import _chart, finish, year_badge, tag, short, W, H, GREEN
surf = skia.Surface(W, H); c = surf.getCanvas()
s = dict(t0=0, pts=[(2000, 4.96), (2002, 5.57), (2004, 6.05), (2006, 5.52), (2008, 5.29), (2010, 3.24)], title='Revenue', sub='The studio is ready',
         fmt=lambda v: short(v * 1e9), xticks=[2000, 2002, 2004, 2006, 2008, 2010], events=[(2004, 'Peak')], crash_from=2004, color=GREEN, dur=3)
_chart(c, s, 5); year_badge(c, 5, 0, None, 2010, 'Setup check'); finish(c, 5)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'selftest.png'); surf.makeImageSnapshot().save(out); print('ok', os.path.abspath(out))
