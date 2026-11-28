"""Blockbuster, the vertical Short (1080x1920, about 33 s): its own script, voiced with voice.py --short.
Shorts rule: the captions are the only words on screen (plus small photo credits). No callouts, tags, stamps, counters,
clippings or end card: real photos and one clean chart carry the picture, a new one every 2 to 3 seconds."""
import sys, os
os.environ['FDS_VERTICAL'] = '1'                       # must come before the engine import
ENGINE = os.environ.get('FDS_ENGINE', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'engine'))
sys.path.insert(0, ENGINE)
from fin import *

film = Film(__file__, vo='vo.wav', words='words.json', mood='money')
T = film.cue
D = os.path.dirname(os.path.abspath(__file__))
def cr(f):
    p = os.path.join(D, '..', 'media', f + '.credit.txt')
    return ('Photo: ' + open(p, encoding='utf-8').read().splitlines()[0]) if os.path.exists(p) else ''

fin = Fin(film, xfade=.2, thriller=False)            # captions on by default in vertical
film.music = {'hits': [T('no', after=T('answer')), T('bankrupt')]}
REV = [(2000, 4.96), (2001, 5.16), (2002, 5.57), (2003, 5.91), (2004, 6.05), (2005, 5.72), (2006, 5.52), (2007, 5.54), (2008, 5.29), (2010, 3.24)]

P = [   # (cue, photo, start focus+zoom, end focus+zoom)
    (0,                         'miami_closing.jpg',    (.30, .45, 1.0), (.33, .45, 1.15)),
    (T('Netflix') - .05,        'netflix_envelope.jpg', (.50, .50, 1.0), (.52, .48, 1.18)),
    (T('In 2000') - .05,        'hastings.jpg',         (.62, .40, 1.0), (.62, .37, 1.12)),
    (T('It mailed') - .05,      'netflix_envelope.jpg', (.40, .55, 1.5), (.46, .50, 1.75)),
    (T('Its founders') - .05,   'dallas.jpg',           (.45, .50, 1.0), (.55, .48, 1.15)),
    (T('offered') - .05,        'anchorage.jpg',        (.50, .45, 1.0), (.50, .40, 1.15)),
]
for t0, f, a, b in P: fin.photo(t0, '../media/' + f, frm=a, to=b)
fin.photo(T('50', after=T('Blockbuster')) - .05, '../media/netflix_envelope.jpg', frm=(.5, .5, 1.3), to=(.5, .5, 1.5))
fin.photo(T('Blockbuster made') - .05, '../media/bend_inside.jpg', frm=(.4, .5, 1.0), to=(.6, .5, 1.1))
fin.photo(T("Blockbuster's CEO") - .05, '../media/rockhampton.jpg', frm=(.5, .45, 1.0), to=(.5, .42, 1.15))
fin.photo(T('The answer') - .05, '../media/closing_sale.jpg', frm=(.5, .5, 1.1), to=(.5, .5, 1.3))
fin.chart(T('years later') - .2, REV, '', fmt=lambda v: f'${v:.1f}B', xticks=[2000, 2002, 2004, 2006, 2008, 2010], crash_from=2004, dur=1.6, ymin=0, ymax=7)
fin.photo(T('Today') - .05, '../media/bend.jpg', frm=(.70, .40, 1.0), to=(.70, .38, 1.12))
fin.photo(T('all because') - .05, '../media/netflix_envelope.jpg', frm=(.5, .5, 1.6), to=(.5, .5, 1.9))

@fin.screen
def words(c, t):
    for (t0, f, _, _), nxt in zip(P, P[1:] + [(T('50', after=T('Blockbuster')) - .1,)]):
        credit_line(c, t, t0, nxt[0] - .1, cr(f))
    for a_, b_, f in ((T('50', after=T('Blockbuster')), T('Blockbuster made') - .1, 'netflix_envelope.jpg'),
                      (T('Blockbuster made'), T("Blockbuster's CEO") - .1, 'bend_inside.jpg'),
                      (T("Blockbuster's CEO"), T('The answer') - .1, 'rockhampton.jpg'),
                      (T('The answer'), T('years later') - .3, 'closing_sale.jpg'),
                      (T('Today'), T('all because') - .1, 'bend.jpg'),
                      (T('all because'), None, 'netflix_envelope.jpg')):
        credit_line(c, t, a_, b_, cr(f))

fin.render()
film.main()
