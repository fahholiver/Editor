#!/usr/bin/env python3
"""Rotina de postagem pela planilha: lê a planilha "Postagens" no Google Drive, confere cada linha e
agenda no Buffer (todas as chaves BUFFER_API_KEY*), escrevendo o resultado de volta na planilha.

    python3 planilha.py rodar [--dry-run]   # a rotina (é o que o GitHub Actions roda todo dia)
    python3 planilha.py checar              # só confere as linhas e mostra o que faria (não posta nem escreve)
    python3 planilha.py criar               # cria a planilha + pasta "Para postar" no Drive e imprime o ID
    python3 planilha.py canais              # atualiza a aba "Canais" com todos os canais das chaves do Buffer

Colunas da aba "Postagens" (a 1ª linha é o cabeçalho; a ordem pode mudar, o nome não):
    data | hora | fuso | canal | video | legenda | titulo | status | posts_buffer | detalhe | link_publico | atualizado_em
  - data: 25/11/2026 ou 2026-11-25        hora: 17:00        fuso: vazio = PLANILHA_FUSO (America/Sao_Paulo)
  - canal: nome do canal no Buffer, vários separados por vírgula, "todos", "todos tiktok", "todos youtube"...
  - video: link do Drive, ID do arquivo, ou o nome do arquivo (procurado na pasta GDRIVE_FOLDER_ID se existir)
  - status (você escreve): vazio = postar · "pular" = ignorar · "repetir" = postar mesmo sendo vídeo+canal repetido
    status (o robô escreve): agendado → postado | erro.   Para tentar de novo uma linha com erro, apague o status
    (os canais que já deram certo nessa linha não são postados de novo).

Cada rodada:
  1. linhas "agendado": pergunta ao Buffer como está cada post → "postado" (com o link) ou "erro" (com o motivo);
  2. linhas pendentes com horário até daqui a PLANILHA_JANELA_HORAS (24 h): CHECAGEM (data/hora, fuso, canal
     existe, vídeo existe no Drive e é vídeo, legenda, repetição de vídeo+canal, título do YouTube) → se tudo
     ok, deixa o vídeo com link público e cria o post agendado no Buffer (se o horário já passou, posta na hora);
  3. tira o link público dos vídeos cujas linhas já terminaram (postado).

Env: PLANILHA_ID (ID da planilha, da URL /spreadsheets/d/<ID>/), BUFFER_API_KEY, BUFFER_API_KEY_2... (ou
BUFFER_API_KEY_<QUALQUER_NOME>), e o acesso ao Google de UMA destas formas:
  - GDRIVE_CREDENTIALS = JSON da conta de serviço (compartilhe a planilha e a pasta com o e-mail dela como Editor), ou
  - GDRIVE_CLIENT_ID + GDRIVE_CLIENT_SECRET + GDRIVE_FULL_REFRESH_TOKEN (o mesmo login do Drive da rotina diária).
Opcionais: GDRIVE_FOLDER_ID, PLANILHA_FUSO, PLANILHA_JANELA_HORAS, PLANILHA_ABA (padrão "Postagens"),
SECRETS_JSON (o GitHub Actions passa todos os secrets de uma vez por aqui).
"""
import datetime as dt
import json
import os
import re
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SHEETS = 'https://sheets.googleapis.com/v4/spreadsheets'
DRIVE = 'https://www.googleapis.com/drive/v3'
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
COLS = ['data', 'hora', 'fuso', 'canal', 'video', 'legenda', 'titulo', 'status', 'posts_buffer', 'detalhe',
        'link_publico', 'atualizado_em']
BOT_COLS = ['status', 'posts_buffer', 'detalhe', 'link_publico', 'atualizado_em']
FINAL = {'postado', 'pular'}


def load_secrets_json():
    """GitHub Actions: SECRETS_JSON = toJSON(secrets) -> every secret becomes an env var (so a new
    BUFFER_API_KEY_X secret works without editing the workflow)"""
    raw = os.environ.get('SECRETS_JSON')
    if not raw:
        return
    for k, v in json.loads(raw).items():
        if k != 'github_token' and isinstance(v, str) and v and not os.environ.get(k):
            os.environ[k] = v


load_secrets_json()
import buffer_api  # noqa: E402  (after the secrets are in the env)


# ---------------------------------------------------------------- Google auth + small API helpers

_TOKEN = []


def google_token():
    if _TOKEN:
        return _TOKEN[0]
    sa = os.environ.get('GDRIVE_CREDENTIALS')
    if sa:
        from google.oauth2.service_account import Credentials
        from google.auth.transport.requests import Request
        creds = Credentials.from_service_account_info(json.loads(sa), scopes=SCOPES)
        creds.refresh(Request())
        tok = creds.token
    else:
        rt = os.environ.get('GDRIVE_FULL_REFRESH_TOKEN')
        cid, sec = os.environ.get('GDRIVE_CLIENT_ID'), os.environ.get('GDRIVE_CLIENT_SECRET')
        if not (rt and cid and sec):
            sys.exit('falta o acesso ao Google: GDRIVE_CREDENTIALS (conta de serviço) ou '
                     'GDRIVE_CLIENT_ID + GDRIVE_CLIENT_SECRET + GDRIVE_FULL_REFRESH_TOKEN')
        r = requests.post('https://oauth2.googleapis.com/token', timeout=30, data={
            'client_id': cid, 'client_secret': sec, 'grant_type': 'refresh_token', 'refresh_token': rt})
        if r.status_code != 200:
            sys.exit('login no Google falhou %d: %s' % (r.status_code, r.text[:300]))
        tok = r.json()['access_token']
    _TOKEN.append(tok)
    return tok


def g(method, url, **kw):
    r = requests.request(method, url, headers={'Authorization': 'Bearer ' + google_token()}, timeout=60, **kw)
    if r.status_code >= 400:
        msg = r.text[:600]
        if 'has not been used in project' in msg or 'SERVICE_DISABLED' in msg:
            m = re.search(r'https://console\.developers\.google\.com/apis/api/[^\s"]+', msg)
            sys.exit('Ative a API no Google Cloud (1 clique em "Ativar"): %s' % (m.group(0) if m else msg))
        raise RuntimeError('Google %s %d: %s' % (url.split('?')[0][-60:], r.status_code, msg))
    return r.json() if r.content else {}


def col_letter(i):
    s = ''
    i += 1
    while i:
        i, rem = divmod(i - 1, 26)
        s = chr(65 + rem) + s
    return s


# ---------------------------------------------------------------- the sheet

class Sheet:
    def __init__(self, sheet_id, tab):
        self.id, self.tab = sheet_id, tab
        vals = g('GET', '%s/%s/values/%s' % (SHEETS, sheet_id, requests.utils.quote("'%s'" % tab)),
                 params={'valueRenderOption': 'UNFORMATTED_VALUE', 'dateTimeRenderOption': 'SERIAL_NUMBER'}).get('values', [])
        if not vals:
            sys.exit('a aba "%s" está vazia (precisa do cabeçalho: %s)' % (tab, ' | '.join(COLS)))
        self.header = [str(h).strip().lower() for h in vals[0]]
        missing = [c for c in COLS if c not in self.header]
        if missing:
            sys.exit('faltam colunas na aba "%s": %s' % (tab, ', '.join(missing)))
        self.rows = []
        for n, v in enumerate(vals[1:], start=2):
            row = {}
            for i, h in enumerate(self.header):
                x = v[i] if i < len(v) else ''
                # real dates/times come as serial numbers (days since 1899-12-30); everything else as text
                row[h] = x if h in ('data', 'hora') and isinstance(x, (int, float)) else str(x).strip()
            row['_n'] = n
            self.rows.append(row)
        self.pending_writes = []

    def set(self, row, **fields):
        row.update(fields)
        row['atualizado_em'] = dt.datetime.now(ZoneInfo(default_tz())).strftime('%d/%m/%Y %H:%M')
        idx = [self.header.index(c) for c in BOT_COLS]
        a, b = min(idx), max(idx)
        values = [row.get(self.header[i], '') for i in range(a, b + 1)]
        self.pending_writes.append({'range': "'%s'!%s%d:%s%d" % (self.tab, col_letter(a), row['_n'], col_letter(b), row['_n']),
                                    'values': [values]})

    def flush(self):
        if not self.pending_writes:
            return
        g('POST', '%s/%s/values:batchUpdate' % (SHEETS, self.id),
          json={'valueInputOption': 'RAW', 'data': self.pending_writes})
        self.pending_writes = []


# ---------------------------------------------------------------- checks

def default_tz():
    return os.environ.get('PLANILHA_FUSO', 'America/Sao_Paulo')


def parse_when(row):
    """-> aware datetime, or raises ValueError with a message in Portuguese"""
    tzname = row.get('fuso') or default_tz()
    try:
        zone = ZoneInfo(tzname)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError('fuso "%s" não existe (ex.: America/Sao_Paulo, Europe/London)' % tzname)
    d, h = row.get('data', ''), row.get('hora', '')
    if isinstance(d, (int, float)):            # a real date cell
        day = dt.date(1899, 12, 30) + dt.timedelta(days=int(d))
        if h == '' and d % 1:
            h = d % 1
        d = day.strftime('%d/%m/%Y')
    if isinstance(h, (int, float)):            # a real time cell (fraction of a day)
        mins = int(round((h % 1) * 1440))
        h = '%02d:%02d' % divmod(mins, 60)
    m = re.fullmatch(r'(\d{4})-(\d{1,2})-(\d{1,2})', d) or None
    if m:
        y, mo, da = map(int, m.groups())
    else:
        m = re.fullmatch(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', d)
        if not m:
            raise ValueError('data "%s" inválida (use 25/11/2026)' % d)
        da, mo = int(m.group(1)), int(m.group(2))
        y = int(m.group(3)) if m.group(3) else dt.datetime.now(zone).year
        y = y + 2000 if y < 100 else y
    m = re.fullmatch(r'(\d{1,2})[:hH](\d{2})?(?::\d{2})?', h)
    if not m:
        raise ValueError('hora "%s" inválida (use 17:00)' % h)
    try:
        return dt.datetime(y, mo, da, int(m.group(1)), int(m.group(2) or 0), tzinfo=zone)
    except ValueError:
        raise ValueError('data/hora "%s %s" não existe' % (d, h))


_CHANNELS = []


def channels():
    if not _CHANNELS:
        _CHANNELS.extend(buffer_api.all_channels(('tiktok', 'instagram', 'youtube', 'facebook', 'threads',
                                                  'twitter', 'linkedin', 'pinterest', 'bluesky')))
    return _CHANNELS


def norm(s):
    return str(s).strip().lower().lstrip('@').replace('’', "'")


def resolve_channels(spec):
    """'todos' | 'todos tiktok' | 'nome1, nome2' -> list of channel dicts; raises ValueError"""
    spec = spec.strip()
    if not spec:
        raise ValueError('coluna canal vazia')
    allc = channels()
    m = re.fullmatch(r'(?:todos|all)(?:\s+(?:os\s+)?(\w+))?', norm(spec))
    if m:
        svc = m.group(1)
        out = [c for c in allc if not svc or norm(c['service']) == svc.rstrip('s')]
        if not out:
            raise ValueError('nenhum canal "%s" no Buffer' % spec)
        return out
    out = []
    for want in [norm(w) for w in spec.split(',') if w.strip()]:
        hit = [c for c in allc if want in (norm(c['name']), norm(c['id']))]
        hit = hit or [c for c in allc if want in norm(c['name'])]
        if len(hit) != 1:
            raise ValueError('canal "%s" %s no Buffer (veja a aba Canais)' % (want, 'não existe' if not hit else 'é ambíguo'))
        out.append(hit[0])
    return out


_VIDEOS = {}


def find_video(ref):
    """Drive link / id / file name -> file dict (id, name, mimeType); raises ValueError"""
    ref = ref.strip()
    if ref not in _VIDEOS:
        try:
            _VIDEOS[ref] = _find_video(ref)
        except ValueError as e:
            _VIDEOS[ref] = e
    if isinstance(_VIDEOS[ref], ValueError):
        raise _VIDEOS[ref]
    return _VIDEOS[ref]


def _find_video(ref):
    if not ref:
        raise ValueError('coluna video vazia')
    m = re.search(r'/d/([\w-]{20,})', ref) or re.search(r'[?&]id=([\w-]{20,})', ref) or re.fullmatch(r'([\w-]{25,})', ref)
    fields = 'id,name,mimeType,size,trashed'
    if m:
        try:
            f = g('GET', '%s/files/%s' % (DRIVE, m.group(1)), params={'fields': fields, 'supportsAllDrives': 'true'})
        except RuntimeError:
            raise ValueError('vídeo não encontrado no Drive (o robô tem acesso a ele?)')
    else:
        q = "name = '%s' and trashed = false" % ref.replace('\\', '\\\\').replace("'", "\\'")
        folder = os.environ.get('GDRIVE_FOLDER_ID')
        found = g('GET', DRIVE + '/files', params={'q': q, 'fields': 'files(%s,parents)' % fields, 'pageSize': 20,
                                                    'supportsAllDrives': 'true', 'includeItemsFromAllDrives': 'true'}).get('files', [])
        if folder and len(found) > 1:
            found = [f for f in found if folder in f.get('parents', [])] or found
        if not found:
            raise ValueError('vídeo "%s" não encontrado no Drive' % ref)
        if len(found) > 1:
            raise ValueError('há %d arquivos chamados "%s" no Drive — use o link' % (len(found), ref))
        f = found[0]
    if f.get('trashed'):
        raise ValueError('o vídeo está na lixeira do Drive')
    if not str(f.get('mimeType', '')).startswith('video/'):
        raise ValueError('"%s" não é um vídeo (%s)' % (f.get('name'), f.get('mimeType')))
    return f


def share_public(fid):
    g('POST', '%s/files/%s/permissions' % (DRIVE, fid), params={'supportsAllDrives': 'true'},
      json={'role': 'reader', 'type': 'anyone'})
    return 'https://drive.usercontent.google.com/download?id=%s&export=download&confirm=t' % fid


def unshare(fid):
    perms = g('GET', '%s/files/%s/permissions' % (DRIVE, fid), params={'supportsAllDrives': 'true'}).get('permissions', [])
    for p in perms:
        if p.get('type') == 'anyone':
            g('DELETE', '%s/files/%s/permissions/%s' % (DRIVE, fid, p['id']), params={'supportsAllDrives': 'true'})


def parse_posts(cell):
    """'anna.20263=abc123, Coyote's Jazz=def456' -> {canal: id}"""
    out = {}
    for part in [p for p in cell.split(';') if '=' in p]:
        k, v = part.rsplit('=', 1)
        out[k.strip()] = v.strip()
    return out


def fmt_posts(d):
    return '; '.join('%s=%s' % kv for kv in d.items())


# ---------------------------------------------------------------- Buffer status of scheduled rows

def post_status(post_id, key_envs):
    q = ('query { post(input: {id: %s}) { id status sentAt externalLink error { message } } }' % buffer_api.lit(post_id))
    last = None
    for env in key_envs:
        buffer_api.use_key(env)
        try:
            return buffer_api.gql(q)['post']
        except Exception as e:  # noqa: BLE001 - wrong key for this post: try the next one
            last = e
    raise RuntimeError(str(last)[:200])


def refresh_scheduled(sheet, dry):
    keys = buffer_api.api_keys()
    for row in sheet.rows:
        if row.get('status', '').lower() != 'agendado':
            continue
        posts = parse_posts(row.get('posts_buffer', ''))
        sent, failed, waiting, links = [], [], [], []
        for ch, pid in posts.items():
            try:
                p = post_status(pid, keys)
            except RuntimeError as e:
                waiting.append('%s: não consegui consultar (%s)' % (ch, e))
                continue
            st = (p or {}).get('status')
            if st == 'sent':
                sent.append(ch)
                if p.get('externalLink'):
                    links.append('%s: %s' % (ch, p['externalLink']))
            elif st == 'error':
                failed.append('%s: %s' % (ch, ((p.get('error') or {}).get('message') or 'erro no Buffer')[:200]))
            else:
                waiting.append(ch)
        if failed:
            new = dict(status='erro', detalhe='falhou no Buffer → ' + ' | '.join(failed)
                       + ('. Para tentar de novo, apague o status (só os canais que falharam serão postados).'))
            # keep only the ids that went out, so a retry posts just the failed channels
            new['posts_buffer'] = fmt_posts({c: posts[c] for c in sent + waiting if c in posts})
        elif posts and not waiting:
            new = dict(status='postado', detalhe=' | '.join(links) or 'publicado em %d canal(is)' % len(sent))
        else:
            continue
        print('linha %d: %s — %s' % (row['_n'], new['status'], new['detalhe'][:150]))
        if not dry:
            sheet.set(row, **new)
    buffer_api.use_key('BUFFER_API_KEY')


# ---------------------------------------------------------------- new rows

def check_row(row, sheet, used):
    """the CHECAGEM: returns (when, targets, video) or raises ValueError listing every problem"""
    problems = []
    when = targets = video = None
    try:
        when = parse_when(row)
    except ValueError as e:
        problems.append(str(e))
    try:
        targets = resolve_channels(row.get('canal', ''))
    except ValueError as e:
        problems.append(str(e))
    try:
        video = find_video(row.get('video', ''))
    except ValueError as e:
        problems.append(str(e))
    cap = row.get('legenda', '')
    if not cap:
        problems.append('legenda vazia')
    if targets:
        if any(c['service'] == 'tiktok' for c in targets) and len(cap) > 2200:
            problems.append('legenda com %d caracteres (TikTok aceita até 2200)' % len(cap))
        if any(c['service'] == 'instagram' for c in targets) and cap.count('#') > 30:
            problems.append('mais de 30 hashtags (Instagram não aceita)')
        if any(c['service'] == 'youtube' for c in targets) and len(row.get('titulo') or cap) > 100:
            problems.append('título do YouTube com mais de 100 caracteres')
    if video and targets and row.get('status', '').lower() != 'repetir':
        done = set(parse_posts(row.get('posts_buffer', '')))
        for c in targets:
            other = used.get((video['id'], c['id']))
            if other and other != row['_n'] and c['name'] not in done:
                problems.append('o vídeo já vai/foi para %s na linha %d (escreva "repetir" no status para postar mesmo assim)'
                                % (c['name'], other))
    if problems:
        raise ValueError('; '.join(problems))
    return when, targets, video


def video_key_map(sheet):
    """(drive file id, channel id) -> row number, for rows already scheduled/posted (duplicate check)"""
    used = {}
    for row in sheet.rows:
        if row.get('status', '').lower() not in ('agendado', 'postado') or not row.get('posts_buffer'):
            continue
        try:
            v = find_video(row['video'])
            names = set(parse_posts(row['posts_buffer']))
            for c in channels():
                if c['name'] in names:
                    used.setdefault((v['id'], c['id']), row['_n'])
        except ValueError:
            pass
    return used


def process_new(sheet, dry, check_only):
    now = dt.datetime.now(dt.timezone.utc)
    horizon = now + dt.timedelta(hours=float(os.environ.get('PLANILHA_JANELA_HORAS', '24')))
    used = None
    count = {'agendados': 0, 'erros': 0, 'futuros': 0}
    for row in sheet.rows:
        st = row.get('status', '').lower()
        if st not in ('', 'repetir') or not any(row.get(c) for c in ('data', 'canal', 'video')):
            continue
        if used is None:
            used = video_key_map(sheet)
        try:
            when, targets, video = check_row(row, sheet, used)
        except ValueError as e:
            count['erros'] += 1
            print('linha %d: ERRO na checagem — %s' % (row['_n'], e))
            if not (dry or check_only):
                sheet.set(row, status='erro', detalhe='checagem: %s' % e)
            continue
        for c in targets:   # later rows of this same run see this one too (duplicate check)
            used.setdefault((video['id'], c['id']), row['_n'])
        if when.astimezone(dt.timezone.utc) > horizon:
            count['futuros'] += 1
            print('linha %d: ok, fica para depois (%s)' % (row['_n'], when.strftime('%d/%m %H:%M %Z')))
            continue
        late = when.astimezone(dt.timezone.utc) <= now + dt.timedelta(minutes=2)
        mode = 'shareNow' if late else 'customScheduled'
        due = None if late else when.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        done = parse_posts(row.get('posts_buffer', ''))
        todo = [c for c in targets if c['name'] not in done]
        print('linha %d: %s "%s" → %s %s' % (row['_n'], 'POSTAR AGORA' if late else 'agendar', video['name'],
                                            ', '.join('%s (%s)' % (c['name'], c['service']) for c in todo),
                                            '' if late else when.strftime('%d/%m %H:%M %Z')))
        if dry or check_only:
            continue
        url = share_public(video['id'])
        errors = []
        for c in todo:
            try:
                p = buffer_api.create_post(c, row['legenda'], url, due, mode, None, row.get('titulo') or '')
                done[c['name']] = p['id']
            except Exception as e:  # noqa: BLE001 - one channel failing never stops the others
                errors.append('%s: %s' % (c['name'], str(e)[:200]))
        if errors:
            count['erros'] += 1
            sheet.set(row, status='erro', posts_buffer=fmt_posts(done), link_publico='sim',
                      detalhe='Buffer recusou → %s. Para tentar de novo, apague o status.' % ' | '.join(errors))
        else:
            count['agendados'] += 1
            sheet.set(row, status='agendado', posts_buffer=fmt_posts(done), link_publico='sim',
                      detalhe=('postando agora (horário já tinha passado)' if late else
                               'agendado para %s em %d canal(is)' % (when.strftime('%d/%m %H:%M'), len(done))))
        sheet.flush()   # write as we go: a crash later never loses which posts were created
    return count


def cleanup_links(sheet, dry):
    """remove the public link of videos whose rows are all finished"""
    open_refs = {r.get('video') for r in sheet.rows if r.get('status', '').lower() not in FINAL}
    for row in sheet.rows:
        if row.get('link_publico') == 'sim' and row.get('status', '').lower() in FINAL and row.get('video') not in open_refs:
            try:
                if not dry:
                    unshare(find_video(row['video'])['id'])
                    sheet.set(row, link_publico='removido')
                print('linha %d: link público removido' % row['_n'])
            except Exception as e:  # noqa: BLE001
                print('linha %d: não consegui remover o link (%s)' % (row['_n'], e))


def run(dry=False, check_only=False):
    sid = os.environ.get('PLANILHA_ID')
    if not sid:
        sys.exit('defina PLANILHA_ID (o código da URL da planilha, depois de /spreadsheets/d/)')
    if not buffer_api.api_keys():
        sys.exit('nenhuma chave do Buffer (BUFFER_API_KEY, BUFFER_API_KEY_2, ... )')
    sheet = Sheet(sid, os.environ.get('PLANILHA_ABA', 'Postagens'))
    print('--- rotina da planilha: %d linhas, %d chaves do Buffer, %d canais ---'
          % (len(sheet.rows), len(buffer_api.api_keys()), len(channels())))
    if not check_only:
        refresh_scheduled(sheet, dry)
        sheet.flush()
    count = process_new(sheet, dry, check_only)
    if not check_only:
        cleanup_links(sheet, dry)
        sheet.flush()
    print('--- fim: %(agendados)d agendada(s), %(erros)d com erro, %(futuros)d para os próximos dias ---' % count)
    if count['erros'] and os.environ.get('GITHUB_ACTIONS'):
        sys.exit(1)   # a red ❌ in GitHub (and its e-mail) when a row needs attention


# ---------------------------------------------------------------- setup helpers

def write_channels_tab(sid):
    rows = [['canal (copie para a coluna canal)', 'rede', 'chave do Buffer', 'id']]
    rows += [[c['name'], c['service'], c['key_env'], c['id']] for c in sorted(channels(), key=lambda c: (c['service'], c['name'].lower()))]
    rows += [['todos', 'todas as redes', '', ''], ['todos tiktok', 'só TikTok', '', ''],
             ['todos youtube', 'só YouTube', '', ''], ['todos instagram', 'só Instagram', '', '']]
    g('POST', '%s/%s/values:batchUpdate' % (SHEETS, sid), json={'valueInputOption': 'RAW', 'data': [
        {'range': "'Canais'!A1:D%d" % len(rows), 'values': rows}]})
    print('aba Canais: %d canais' % (len(rows) - 5))


def create():
    """build the sheet as .xlsx (dropdowns, widths, instructions) and import it into Drive as a Google Sheet"""
    import io
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.worksheet.datavalidation import DataValidation
    chans = sorted(channels(), key=lambda c: (c['service'], c['name'].lower()))
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Postagens'
    ws.append(COLS)
    widths = [12, 7, 18, 22, 36, 50, 30, 11, 30, 50, 12, 16]
    for i, w in enumerate(widths):
        c = ws.cell(row=1, column=i + 1)
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='1F2937' if COLS[i] not in BOT_COLS else '6B7280')
        ws.column_dimensions[col_letter(i)].width = w
    ws.freeze_panes = 'A2'
    names = [c['name'] for c in chans] + ['todos', 'todos tiktok', 'todos youtube', 'todos instagram']
    dv = DataValidation(type='list', formula1="=Canais!$A$2:$A$%d" % (len(names) + 1), allow_blank=True,
                        showErrorMessage=False)
    ws.add_data_validation(dv)
    dv.add('D2:D1000')
    st = DataValidation(type='list', formula1='"pular,repetir,agendado,postado,erro"', allow_blank=True,
                        showErrorMessage=False)
    ws.add_data_validation(st)
    st.add('H2:H1000')
    for r in range(2, 1001):
        for col in ('A', 'B'):
            ws['%s%d' % (col, r)].number_format = '@'   # keep dates/times as typed text
    ch = wb.create_sheet('Canais')
    ch.append(['canal (copie para a coluna canal)', 'rede', 'chave do Buffer', 'id'])
    for c in chans:
        ch.append([c['name'], c['service'], c['key_env'], c['id']])
    for n, d in [('todos', 'todas as redes'), ('todos tiktok', 'só TikTok'), ('todos youtube', 'só YouTube'),
                 ('todos instagram', 'só Instagram')]:
        ch.append([n, d, '', ''])
    for col, w in zip('ABCD', (34, 16, 18, 28)):
        ch.column_dimensions[col].width = w
    help_ = wb.create_sheet('Como usar')
    help_.column_dimensions['A'].width = 120
    for line in [
        'COMO USAR — uma linha por vídeo. O robô roda todo dia às 17:00 (Brasília) e agenda tudo das próximas 24 h.',
        '',
        'data: 25/11/2026   ·   hora: 18:30   ·   fuso: vazio = horário de Brasília (ou Europe/London, Europe/Berlin…)',
        'canal: escolha na lista (aba Canais). Vários: separe por vírgula. "todos" = todos os canais de todas as chaves.',
        'video: cole o link do vídeo no Drive (ou só o nome do arquivo, se for único).',
        'legenda: texto + hashtags.   titulo: só para YouTube (se vazio, usa o começo da legenda).',
        '',
        'status — você escreve: vazio = postar · pular = ignorar · repetir = postar mesmo se já foi para esse canal',
        'status — o robô escreve: agendado → postado (com o link) ou erro (com o motivo em "detalhe").',
        'Deu erro? Corrija a linha e APAGUE o status: na próxima rodada ele tenta de novo (sem repetir os canais que já deram certo).',
        'Colunas cinzas (status, posts_buffer, detalhe, link_publico, atualizado_em) são preenchidas pelo robô.',
        '',
        'CHECAGEM antes de postar: data/hora válidas, canal existe no Buffer, vídeo existe no Drive e é vídeo,',
        'legenda preenchida (TikTok ≤ 2200 caracteres, Instagram ≤ 30 hashtags, título YouTube ≤ 100), e o mesmo vídeo',
        'não vai duas vezes para o mesmo canal. Se o horário já passou, posta na hora.',
        'O vídeo ganha um link público só até sair; depois o robô tira o link.',
    ]:
        help_.append([line])
    help_['A1'].font = Font(bold=True)
    for r in range(1, 20):
        help_['A%d' % r].alignment = Alignment(wrap_text=True)
    buf = io.BytesIO()
    wb.save(buf)

    parent = os.environ.get('GDRIVE_PARENT_ID')
    if not parent:
        q = "name = '%s' and mimeType = 'application/vnd.google-apps.folder' and trashed = false and 'root' in parents" \
            % os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily')
        f = g('GET', DRIVE + '/files', params={'q': q, 'fields': 'files(id)'}).get('files', [])
        parent = f[0]['id'] if f else 'root'
    folder = g('POST', DRIVE + '/files', params={'fields': 'id,webViewLink'},
               json={'name': 'Para postar', 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent]})
    meta = {'name': 'Postagens (robô Buffer)', 'parents': [parent], 'mimeType': 'application/vnd.google-apps.spreadsheet'}
    boundary = 'planilha'
    body = (('--%s\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n%s\r\n--%s\r\n'
             'Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n')
            % (boundary, json.dumps(meta), boundary)).encode() + buf.getvalue() + ('\r\n--%s--' % boundary).encode()
    r = requests.post('https://www.googleapis.com/upload/drive/v3/files', timeout=120,
                      headers={'Authorization': 'Bearer ' + google_token(),
                               'Content-Type': 'multipart/related; boundary=' + boundary},
                      params={'uploadType': 'multipart', 'fields': 'id,webViewLink'}, data=body)
    r.raise_for_status()
    s = r.json()
    print('planilha:', s['webViewLink'])
    print('PLANILHA_ID=' + s['id'])
    print('pasta "Para postar":', folder['webViewLink'])
    print('GDRIVE_FOLDER_ID=' + folder['id'])


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'rodar':
        run(dry='--dry-run' in sys.argv)
    elif cmd == 'checar':
        run(check_only=True)
    elif cmd == 'criar':
        create()
    elif cmd == 'canais':
        write_channels_tab(os.environ['PLANILHA_ID'])
    else:
        sys.exit(__doc__)
