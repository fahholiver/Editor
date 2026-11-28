#!/usr/bin/env python3
"""Build the synthetic 16-second demo. For an episode, copy and retime this file."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from vidlib import A169, NX, N, V, finish, init, sh

init(sys.argv[1])
sh(0, 'box', src='Synthetic demo clip',
   boxes=[V('demo', 0, A169, 'Test pattern · example video')],
   notes=[N('Evidence window', NX, 300, 0.8, arrow=[[1240, 410], [1080, 510]])])
sh(4, 'title', lines=['Engineering', 'Failures'], kicker='MMH DEMO',
   sub='A short technical check')
sh(8, 'blueprint', kind='structure', title='Illustrative bridge · not to scale',
   paths=[
       dict(d='M 270 590 H 1650', at=8.2),
       dict(d='M 420 590 L 650 440 L 880 590 L 1110 440 L 1340 590', at=8.6),
       dict(d='M 650 590 V 800 M 1110 590 V 800', at=9.0, color='yellow'),
   ], labels=[dict(text='Pier', x=1150, y=690, at=9.4, color='yellow')])
sh(12, 'blueprint', kind='chain', title='Illustrative sequence',
   nodes=[
       dict(label='Power loss', at=12.1),
       dict(label='Ship strike', at=13.0),
       dict(label='Span falls', at=13.9, accent=True),
   ])
finish(cuts=[0, 8, 16], names=['hook', 'mechanism'], tags=[], music=[], sfx=[],
       archive={'demo': {'file': 'real/demo.mp4'}}, end=16)
