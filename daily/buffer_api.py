#!/usr/bin/env python3
"""Tiny client for Buffer's GraphQL API (https://api.buffer.com, key from Buffer > Settings > API).

    python3 buffer_api.py channels            # list organisations + channels (find your TikTok channel id)
    python3 buffer_api.py introspect [Type]   # print the fields of an input type (default CreatePostInput)

Env: BUFFER_API_KEY (required), BUFFER_API_URL (optional, default https://api.buffer.com).
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


def gql(query, variables=None):
    key = os.environ.get('BUFFER_API_KEY')
    if not key:
        sys.exit('BUFFER_API_KEY is not set (Buffer > Settings > API > create key; add it as an environment secret)')
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


def find_tiktok_channel(name=None):
    """id of a TikTok channel: the one whose name/id contains `name` (e.g. "anna.20263"), or the only one"""
    found = [c for o in organizations() for c in channels(o['id']) if 'tiktok' in str(c.get('service', '')).lower()]
    if name:
        key = name.lower().lstrip('@')
        found = [c for c in found if key in str(c.get('name', '')).lower().lstrip('@') or key == str(c['id']).lower()]
    if len(found) == 1:
        print('TikTok channel: %s (%s)' % (found[0]['id'], found[0]['name']))
        return found[0]['id']
    sys.exit('found %d matching TikTok channels - pass --channel <name or id>; candidates: %s'
             % (len(found), ', '.join('%s (%s)' % (c['id'], c['name']) for c in found) or 'none'))


def create_post(channel_id, text, video_url=None, due_at=None, mode='customScheduled', thumb_ms=None):
    """mode: customScheduled (needs due_at, ISO-8601 UTC) | addToQueue | shareNow.
    Returns the created post dict, raises on MutationError."""
    inp = {'text': text, 'channelId': channel_id, 'schedulingType': Enum('automatic'), 'mode': Enum(mode)}
    if mode == 'customScheduled':
        inp['dueAt'] = due_at
    if video_url:
        video = {'url': video_url}
        if thumb_ms is not None:
            video['metadata'] = {'thumbnailOffset': int(thumb_ms)}
        inp['assets'] = [{'video': video}]
    q = ('mutation { createPost(input: %s) { ... on PostActionSuccess { post { id text dueAt } } '
         '... on MutationError { message } } }' % lit(inp))
    res = gql(q)['createPost']
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
        for o in organizations():
            print('organization %s  %s' % (o['id'], o['name']))
            for c in channels(o['id']):
                print('   channel %-28s %-10s %s' % (c['id'], c['service'], c['name']))
    elif cmd == 'introspect':
        print(json.dumps(introspect(*sys.argv[2:3]), indent=1))
    else:
        sys.exit(__doc__)
