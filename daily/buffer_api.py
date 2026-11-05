#!/usr/bin/env python3
"""Tiny client for Buffer's GraphQL API (https://api.buffer.com, key from Buffer > Settings > API).

    python3 buffer_api.py channels            # list organisations + channels (find your TikTok channel id)
    python3 buffer_api.py introspect [Type]   # print the fields of an input type (default CreatePostInput)

Env: BUFFER_API_KEY (+ BUFFER_API_KEY_2..9 for more Buffer accounts), BUFFER_API_URL (optional, default https://api.buffer.com).
"""
import json
import os
import sys

import requests

API = os.environ.get('BUFFER_API_URL', 'https://api.buffer.com')


class Enum(str):
    """a GraphQL enum value (written without quotes)"""


def lit(v):
    """python value -> GraphQL input literal (Buffer's examples use inline literals)"""
    if isinstance(v, Enum):
        return str(v)
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if v is None:
        return 'null'
    if isinstance(v, (int, float)):
        return json.dumps(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return '[' + ', '.join(lit(x) for x in v) + ']'
    if isinstance(v, dict):
        return '{' + ', '.join('%s: %s' % (k, lit(x)) for k, x in v.items()) + '}'
    raise TypeError(type(v))


SERVICES = ('tiktok', 'instagram', 'youtube')   # where the vertical videos can go
_KEY_ENV = ['BUFFER_API_KEY']


def api_keys():
    """env var names of the configured Buffer keys: BUFFER_API_KEY, BUFFER_API_KEY_2 ... _9 (one per Buffer account)"""
    names = ['BUFFER_API_KEY'] + ['BUFFER_API_KEY_%d' % i for i in range(2, 10)]
    return [n for n in names if os.environ.get(n)]


def use_key(env_name):
    _KEY_ENV[0] = env_name


def gql(query, variables=None):
    key = os.environ.get(_KEY_ENV[0])
    if not key:
        sys.exit('%s is not set (Buffer > Settings > API > create key; add it as an environment variable)' % _KEY_ENV[0])
    r = requests.post(API, json={'query': query, 'variables': variables or {}}, timeout=60,
                      headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        j = r.json()
    except ValueError:
        raise RuntimeError('Buffer API %d: %s' % (r.status_code, r.text[:500]))
    if r.status_code != 200 or j.get('errors'):
        raise RuntimeError('Buffer API %d: %s' % (r.status_code, json.dumps(j.get('errors') or j)[:1500]))
    return j['data']


def organizations():
    return gql('query { account { organizations { id name } } }')['account']['organizations']


def channels(org_id):
    q = 'query { channels(input: {organizationId: %s}) { id name service } }' % lit(org_id)
    return gql(q)['channels']


def all_channels(services=SERVICES):
    """every TikTok / Instagram / YouTube channel across all configured Buffer keys, tagged with its key and org"""
    out = []
    for env in api_keys():
        use_key(env)
        for o in organizations():
            for c in channels(o['id']):
                if str(c.get('service', '')).lower() in services:
                    out.append(dict(c, key_env=env, org=o['id']))
    use_key('BUFFER_API_KEY')
    return out


def find_channels(spec='all', services=SERVICES):
    """channel dicts for spec = 'all' or comma-separated names/ids ('anna.20263,my_insta')"""
    found = all_channels(services)
    if not spec or spec.strip().lower() == 'all':
        if not found:
            sys.exit('no channel connected in Buffer')
        return found
    out = []
    for want in [w.strip().lower().lstrip('@') for w in spec.split(',') if w.strip()]:
        m = [c for c in found if want == str(c.get('name', '')).lower().lstrip('@') or want == str(c['id']).lower()]
        m = m or [c for c in found if want in str(c.get('name', '')).lower()]
        if len(m) != 1:
            sys.exit('channel "%s": %d matches; connected: %s'
                     % (want, len(m), ', '.join('%s (%s)' % (c['name'], c['service']) for c in found) or 'none'))
        out.append(m[0])
    return out


def tiktok_channels():
    return all_channels(('tiktok',))


def find_tiktok_channels(spec='all'):
    """[(id, name)] - kept for compatibility"""
    return [(c['id'], c['name']) for c in find_channels(spec, ('tiktok',))]


def find_tiktok_channel(name=None):
    return find_tiktok_channels(name or 'all')[0][0]


def create_post(channel, text, video_url=None, due_at=None, mode='customScheduled', thumb_ms=None, title=''):
    """channel: a dict from find_channels (or a bare TikTok channel id). mode: customScheduled (needs due_at,
    ISO-8601 UTC) | addToQueue | shareNow. Returns the created post dict, raises on MutationError."""
    if isinstance(channel, str):
        channel = {'id': channel, 'service': 'tiktok', 'key_env': 'BUFFER_API_KEY'}
    use_key(channel.get('key_env', 'BUFFER_API_KEY'))
    service = str(channel.get('service', 'tiktok')).lower()
    # the story, voice and animation are AI-generated: label it where the platform asks for it
    meta = {'tiktok': {'tiktok': {'isAiGenerated': True}},
            'instagram': {'instagram': {'type': Enum('reel'), 'shouldShareToFeed': True, 'isAiGenerated': True}},
            'youtube': {'youtube': {'title': (title or text)[:95], 'privacy': Enum('public'), 'madeForKids': False,
                                    'isAiGenerated': True}}}.get(service, {})
    inp = {'text': text, 'channelId': channel['id'], 'schedulingType': Enum('automatic'), 'mode': Enum(mode),
           'needsApproval': False}
    if meta:
        inp['metadata'] = meta
    if mode == 'customScheduled':
        inp['dueAt'] = due_at
    if video_url:
        video = {'url': video_url}
        if thumb_ms is not None:
            video['metadata'] = {'thumbnailOffset': int(thumb_ms)}
        inp['assets'] = [{'video': video}]
    q = ('mutation { createPost(input: %s) { ... on PostActionSuccess { post { id text dueAt } } '
         '... on MutationError { message } } }' % lit(inp))
    try:
        res = gql(q)['createPost']
    finally:
        use_key('BUFFER_API_KEY')
    if 'post' not in res:
        raise RuntimeError('Buffer createPost failed: %s' % res.get('message', res))
    return res['post']


def introspect(name='CreatePostInput'):
    q = '''query($n: String!) { __type(name: $n) { name kind
             inputFields { name type { name kind ofType { name kind ofType { name kind } } } }
             fields { name } enumValues { name } } }'''
    return gql(q, {'n': name})['__type']


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'channels'
    if cmd == 'channels':
        for c in all_channels(('tiktok', 'instagram', 'youtube', 'facebook', 'twitter', 'linkedin', 'threads')):
            print('%-12s %-26s %-10s %s' % (c['key_env'][-6:], c['id'], c['service'], c['name']))
    elif cmd == 'introspect':
        print(json.dumps(introspect(*sys.argv[2:3]), indent=1))
    else:
        sys.exit(__doc__)
