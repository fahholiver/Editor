"""Binance: drei Hacks (2019, 2022, 2026). Vertical Short, German, about 71 s. Captions + photo credits only."""
import sys, os
os.environ['FDS_VERTICAL'] = '1'                       # must come before the engine import
ENGINE = os.environ.get('FDS_ENGINE', '/home/user/Editor/.claude/skills/finance-documentary-studio/engine')
sys.path.insert(0, ENGINE)
from fin import *

film = Film(__file__, vo='vo.wav', words='words.json', mood='money')
T = film.cue
D = os.path.dirname(os.path.abspath(__file__))
def cr(f):
    p = os.path.join(D, '..', 'media', f + '.credit.txt')
    return ('Foto: ' + open(p, encoding='utf-8').read().splitlines()[0]) if os.path.exists(p) else ''

fin = Fin(film, xfade=.2, thriller=False)
film.music = {'hits': [T('Weg'), T('Nordkorea'), T('Vierzig', nth=2)]}

# (cue, photo, start focus+zoom, end focus+zoom); None = the chart
P = [
    (0,                          'btc2.jpg',    (.50, .45, 1.0), (.52, .45, 1.2)),
    (T('Sechs Komma') - .05,     'servers.jpg', (.35, .50, 1.0), (.45, .50, 1.15)),
    (T('Weg') - .05,             'dc.jpg',      (.30, .50, 1.2), (.30, .50, 1.45)),
    (T('Am neunundzwanzigsten') - .05, 'cake.jpg', (.62, .35, 1.3), (.62, .30, 1.5)),
    (T('Geld aus') - .05,        'dc.jpg',      (.75, .50, 1.0), (.70, .50, 1.15)),
    (T('Auf zehn') - .05,        'cable.jpg',   (.45, .60, 1.0), (.45, .65, 1.2)),
    (T('Es ist der') - .05,      'servers.jpg', (.80, .50, 1.1), (.80, .45, 1.3)),
    (T('Viermal') - .05,         'eth.jpg',     (.50, .50, 1.0), (.50, .50, 1.2)),
    (T('Aber es war') - .05,     'btc2.jpg',    (.45, .40, 1.6), (.50, .40, 1.9)),
    (T('Mai') - .05,             'cz2.jpg',     (.55, .40, 1.0), (.55, .38, 1.12)),
    (T('Hacker stehlen') - .05,  'code.jpg',    (.40, .40, 1.0), (.45, .45, 1.2)),
    (T('Mit einer') - .05,       'atm.jpg',     (.40, .45, 1.0), (.40, .40, 1.15)),
    (T('Rund vierzig') - .05,    'btc2.jpg',    (.50, .50, 1.0), (.50, .50, 1.15)),
    (T('Oktober', nth=2) - .05,  'cz1.jpg',     (.30, .45, 1.0), (.30, .42, 1.15)),
    (T('Eine', after=T('Oktober', nth=2)) - .05,          'cable.jpg',   (.30, .55, 1.4), (.35, .60, 1.6)),
    (T('Der Angreifer') - .05,   'servers.jpg', (.55, .50, 1.2), (.60, .50, 1.4)),
    (T('Rund', nth=2) - .05,     'eth.jpg',     (.45, .45, 1.4), (.50, .45, 1.6)),
    (T('ganze Blockchain') - .9, 'dc.jpg',      (.50, .50, 1.1), (.50, .50, 1.3)),
    (T('Und 2026') - .05, 'laptop.jpg', (.55, .45, 1.0), (.55, .45, 1.15)),
    (T('Nach ersten') - .05, 'cake.jpg', (.70, .30, 1.4), (.70, .28, 1.6)),
    (T('Dem Laptop') - .05, 'code.jpg', (.60, .30, 1.3), (.55, .35, 1.5)),
    (T('Das FBI') - .05,         'fbi2.jpg',    (.45, .45, 1.0), (.50, .45, 1.15)),
    (T('Nordkorea') - .05,       'pyong.jpg',   (.50, .55, 1.0), (.55, .55, 1.15)),
    (T('Die Hackergruppe') - .05,'arch.jpg',    (.25, .45, 1.3), (.25, .45, 1.5)),
    (T('Bitcoin', nth=2) - .05,  'btc2.jpg',    (.40, .55, 1.3), (.45, .55, 1.5)),
    (T('Rund drei') - .05,       'fbi1.jpg',    (.50, .45, 1.0), (.50, .42, 1.15)),
    (T('Binance sagt') - .05,    'cake.jpg',    (.50, .55, 1.0), (.50, .50, 1.15)),
    (T('Vierzig', nth=2) - .2,   None,          None, None),
    (T('Drei Angriffe') - .05,   'servers.jpg', (.30, .50, 1.0), (.25, .50, 1.2)),
    (T('der', after=T('Drei Angriffe')) - .05, 'dc.jpg', (.30, .50, 1.6), (.30, .50, 1.9)),
]
HACKS = [(2019, 0.04), (2022, 0.57), (2026, 6.36)]   # billions USD, see ../sources.md
for t0, f, a, b in P:
    if f is None:
        fin.chart(t0, HACKS, '', fmt=lambda v: f'${v:.2f}B' if v < 1 else f'${v:.1f}B', xticks=[2019, 2022, 2026],
                  crash_from=2022, dur=3.0, ymin=0, ymax=7, color=GOLD)
    else:
        fin.photo(t0, '../media/' + f, frm=a, to=b)

@fin.screen
def words(c, t):
    for (t0, f, _, _), nxt in zip(P, P[1:] + [(None,)]):
        if f: credit_line(c, t, t0, (nxt[0] - .1) if nxt[0] is not None else None, cr(f))

fin.render()
film.main()
