"""How Blockbuster went from $6 billion to one store: 75-second preview (thriller cold open, then the title, then chapter one)."""
import sys, os
ENGINE = os.environ.get('FDS_ENGINE', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'engine'))
sys.path.insert(0, ENGINE)
from fin import *

film = Film(__file__, vo='vo.wav', words='words.json', mood='money')
T = film.cue
D = os.path.dirname(os.path.abspath(__file__))
def cr(f):
    """the credit line saved next to a photo by scripts/photos.py"""
    p = os.path.join(D, 'media', f + '.credit.txt')
    return ('Photo: ' + open(p, encoding='utf-8').read().splitlines()[0]) if os.path.exists(p) else ''

fin = Fin(film, chapter_subs={'THE GOLD RUSH': 'Dallas, 1985'})       # the [TITLE: ...] pause in script.txt makes everything before it a thriller open
film.music = {'hits': [T('bankruptcy') + .3]}

def rewind(c, t, u):
    """the year rolls back from 2010 to 2000 like a rewinding tape"""
    y = 2010 - 10 * ease(min(1, u * 1.4))
    jit = 6 * math.sin(t * 70) * (u < .7)
    text(c, str(int(round(y))), W / 2 + jit, H / 2 + 120, 380, BEBAS, TXT, 'center', 255, 8)
    if int(t * 4) % 2 == 0: text(c, '<< REWIND', W / 2, H / 2 - 230, 44, MONO, RED, 'center', 255, 10)
    for k in range(6):
        yy = (t * 900 + k * 190) % H; c.drawRect(skia.Rect(0, yy, W, yy + 3), fp('#FFFFFF', 30))

REV = [(2000, 4.96), (2001, 5.16), (2002, 5.57), (2003, 5.91), (2004, 6.05), (2005, 5.72), (2006, 5.52), (2007, 5.54), (2008, 5.29), (2010, 3.24)]

# ---------------------------------------------------------------- thriller cold open
fin.photo(0, 'media/miami_closing.jpg', frm=(.4, .45, 1.15), to=(.42, .45, 1.35))
fin.flash(T('A company with') - .1, ['media/anchorage.jpg', 'media/rockhampton.jpg', 'media/bend_inside.jpg', 'media/closing_sale.jpg'], every=.42)
fin.chart(T('files for') - .3, REV, 'Blockbuster revenue', sub='billions of dollars a year', fmt=lambda v: f'${v:.1f}B',
          xticks=[2000, 2002, 2004, 2006, 2008, 2010], events=[(2004, 'The peak')], crash_from=2004, dur=1.1, ymin=0, ymax=7)
fin.scene(T('years earlier') - .1, rewind)
fin.number(T('for', after=T('stopped')) - .1, 50_000_000, label='The price that could have saved it', dur=.9, color=GOLD)
fin.photo(T('In the year') - .2, 'media/dallas.jpg', frm=(.45, .55, 1.1), to=(.5, .5, 1.3))
fin.photo(T('the founders') - .1, 'media/hastings.jpg', frm=(.64, .36, 1.05), to=(.62, .34, 1.2))
fin.statement(T('Their company') - .1, 'Losing money', color=RED, size=210)
fin.photo(T('It mailed') - .1, 'media/netflix_envelope.jpg', card=.5, label='Netflix, 2000: DVDs by mail', frm=(.5, .5, 1.0), to=(.5, .5, 1.06))
fin.versus(T('For', after=T('envelopes')) - .1, ('Blockbuster', '$4.96B', 'revenue in 2000', BLUE), ('Netflix', '$50M', 'the asking price', RED), delay=.6)
fin.statement(T("Blockbuster's CEO") - .2, 'Trying not to laugh', sub="Blockbuster's CEO, as Netflix co-founder Marc Randolph remembers it", color=GOLD, size=170)
fin.photo(T('That website') - .1, 'media/netflix_envelope.jpg', frm=(.5, .45, 1.35), to=(.52, .45, 1.7))

# ---------------------------------------------------------------- after the title: the empire
fin.photo(T('At its peak') - .3, 'media/anchorage.jpg', frm=(.5, .55, 1.0), to=(.5, .45, 1.25))
fin.photo(T('had more than') - .1, 'media/rockhampton.jpg', frm=(.5, .4, 1.05), to=(.48, .36, 1.2))
fin.number(T('made around') - .2, 6_100_000_000, label='Revenue, 2004', sub='one year of rentals', dur=1.3)
fin.number(T('In 2000 alone') - .1, 800_000_000, label='Late fees, 2000', sub='paid by people who returned a tape late', dur=1.6, color=GOLD)
fin.clipping(T('it collected') - .1, outlet='Mental Floss', headline='15 Fast-Forward Facts About Blockbuster Video',
             body='The company profited enormously from late fees, which accrued after the one- or three-day rental term had expired. '
                  'In 2000, $800 million, or 16 percent of total revenue, came from fines.',
             phrase='$800 million, or 16 percent of total revenue, came from fines.', at=T('800'), dur=2.2, source='mentalfloss.com')
fin.photo(T('Today') - .2, 'media/bend.jpg', frm=(.72, .28, 1.7), to=(.7, .27, 1.95))

# ---------------------------------------------------------------- chapter one: the gold rush
fin.photo(film.chapter_at('THE GOLD RUSH') + 1.6, 'media/dallas.jpg', frm=(.6, .5, 1.0), to=(.55, .5, 1.15))
fin.statement(T('A software guy') - .2, 'David Cook', sub='He ran a software company for oil and gas firms', color=CYAN, size=200)
fin.number(T('opened a video') + .3, 8000, prefix='', label='Tapes on day one', sub='more than any video store in town', dur=1.0, color=CYAN)
fin.photo(T('bright lights') - .2, 'media/bend_inside.jpg', frm=(.4, .5, 1.0), to=(.6, .5, 1.15))


@fin.screen
def words(c, t):
    datestamp(c, t, .05, T('A company with') - .3, 'SEPTEMBER 23, 2010', 'BLOCKBUSTER FILES FOR BANKRUPTCY')
    credit_line(c, t, 0, T('A company with') - .3, cr('miami_closing.jpg'))
    stamp(c, t, T('bankruptcy'), 'BANKRUPT', RED, y=H / 2 + 120, t1=T('years earlier') - .2)
    datestamp(c, t, T('In the year') + .1, T('the founders') - .2, '2000', 'DALLAS, TEXAS', y=H - 220)
    credit_line(c, t, T('In the year'), T('the founders') - .2, cr('dallas.jpg'))
    name_tag(c, t, T('the founders') + .3, T('Their company') - .3, 'Reed Hastings', 'Netflix co-founder', cr('hastings.jpg'), x=120, y=560)
    credit_line(c, t, T('It mailed'), T('For', after=T('envelopes')) - .3, cr('netflix_envelope.jpg'))
    stamp(c, t, T('no', after=T('answer')), 'NO', RED, y=H - 215, size=170, t1=T('That website') - .3)
    credit_line(c, t, T('That website'), T('Netflix', after=T('That website')) + 1.0, cr('netflix_envelope.jpg'))

    year_badge(c, t, T('At its peak'), T('made around') - .4, 2004, 'The peak')
    credit_line(c, t, T('At its peak'), T('had more than') - .3, cr('anchorage.jpg'))
    tag(c, t, T('had more than') + .2, T('made around') - .4, 'More than 9,000 stores', '84,300 employees worldwide, 2004', 'At the peak')
    credit_line(c, t, T('had more than'), T('made around') - .4, cr('rockhampton.jpg'))
    ticker(c, t, T('made around') - .2, T('it collected') - .2, [('STORES', '9,094', GREEN), ('EMPLOYEES', '84,300', GREEN), ('REVENUE 2004', '$6.1B', GREEN), ('LATE FEES 2000', '$800M', GOLD)])
    tag(c, t, T('Today') + .1, film.chapter_at('THE GOLD RUSH') - .2, 'Bend, Oregon', 'The last Blockbuster on Earth', 'Still open')
    credit_line(c, t, T('Today'), film.chapter_at('THE GOLD RUSH') - .2, cr('bend.jpg'))

    year_badge(c, t, film.chapter_at('THE GOLD RUSH') + 2.2, T('A software guy') - .4, 1985, 'October 19')
    tag(c, t, T('Dallas', after=60) - .2, T('A software guy') - .4, 'Dallas, Texas', 'The first Blockbuster opens', 'Where it started')
    credit_line(c, t, film.chapter_at('THE GOLD RUSH') + 1.6, T('A software guy') - .4, cr('dallas.jpg'))
    credit_line(c, t, T('bright lights'), None, cr('bend_inside.jpg'))


fin.render()
film.main()
