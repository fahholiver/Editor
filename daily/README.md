# Vídeos diários → TikTok via Buffer

Todo dia uma sessão agendada do Claude segue a skill [`.claude/skills/daily-shorts/SKILL.md`](../.claude/skills/daily-shorts/SKILL.md):
lê as métricas, as ideias e as inspirações, escreve uma história nova por conta, narra (ElevenLabs/Edge), anima,
posta no Buffer e arquiva no Drive (`TikTok Daily/`).

## Quem posta, quando e o quê: a planilha "Buffer Contas" (Google Sheets, pode ser privada)
Uma linha por conta, todas as horas em horário de Londres:

| Conta principal | Hora de postagem | Conta repostagem | País-Língua | Modelo-skill | Gerar s/n |
|---|---|---|---|---|---|
| mandraketoons | 14:00 | Coyote's Jazz, proper_laughs_uk | UK-Inglês | confession | s |
| strawberry.me27 | 14:00 | | | | n |

- **Gerar = s**: história nova todo dia (sessão diária). **Gerar = n**: vídeo pronto da fila do Drive
  (`queue_post.py`, um arquivo diferente para cada conta, que vai para a lixeira depois de postado).
- **Mesma conta em várias linhas** (ex. 14:00 e 20:00) = várias postagens no dia, **cada uma um vídeo diferente**
  (história nova para cada horário, ou um arquivo diferente da fila).
- **Conta repostagem**: nomes dos canais no Buffer separados por vírgula; postam o mesmo vídeo no mesmo horário.
- **País-Língua**: UK/Inglês, Alemanha/Alemão, França/Francês (ou en-GB, de-DE, fr-FR).
- **Modelo-skill**: formato (`confession`, `rule_horror`, `interactive_series`, `survival_guide`, `parable`,
  `curiosity`, e as skills documentário `finance_doc` / `space_killer` / `engineering_failure`) e/ou engine
  (`motion`, `vintage`, `vox`, `cartoon`, `finance`, `orbit`, `engfail`) e/ou estilo (`pixel_arcade`), separados por `/`:
  ex. `parable/vintage`.
- Lida com o seu login do Google (`GDRIVE_FULL_REFRESH_TOKEN`); cada leitura fica salva em Drive
  `_state/accounts_sheet.csv` e é usada se o Google falhar. Planilha vazia/cabeçalho errado → `accounts.json` como antes.
  Conferir: `python3 daily/sheet.py`.
- A fila do Drive roda às 13:35 de Londres: uma conta Gerar = n com horário antes disso posta quando a tarefa roda.

## Laboratório viral (antes de cada vídeo) — `viral_lab.py`
Ciclo por conta: **pesquisar** vídeos virais das últimas 24 h no nicho da conta (TikTok via Apify, palavras do
formato + idioma em `viral/niches.json`) → **padrões** (hashtags, temas, ganchos, duração, velocidade de views) →
**3 roteiros originais** → **avaliar** (rubrica de 9 critérios: gancho, retenção, payoff, trend, originalidade,
comentários, loop, emoção, visual; análise feita pelo Claude + checagens medidas) → **melhorar** →
**selecionar** o melhor. Só um roteiro **aprovado** vira vídeo — **nota final ≥ 80/100 e gancho ≥ 9/10 em todo vídeo** (regra do dono, 2026-11-23): o
`bootstrap.py`/`studio.py` recusam o resto. A nota vai para o log e o `metrics.py` compara com as views reais.
- Por conta em `accounts.json` (opcional): `niche_keywords` (palavras extras), `viral_min_plays` (padrão 100000),
  `viral_threshold` (só pode subir acima de 80).
- **Banco de roteiros** (economia de tokens): os outros roteiros do dia que também passaram (gancho ≥ 9, nota ≥ 80)
  ficam em Drive `_state/script_bank.jsonl`; nos próximos 3 dias a conta usa um deles (`bank-take`) em vez de
  pesquisar, escrever e avaliar de novo. Partes de série interativa não entram no banco.
- Chaves do Apify (rotativas): variável `APIFY_TOKENS` com várias chaves separadas por vírgula; usa a 1ª com crédito e,
  quando acaba (limite do mês / 402 / 403), passa para a próxima — igual às chaves da ElevenLabs. Uma só: `APIFY_TOKEN`; `APIFY_ACTOR`
  (padrão `themineworks~tiktok-search-scraper`).
- Histórico em Drive `_state/viral_lab.jsonl` e `_state/viral_research_<formato>_<língua>.json`.
- A nota é uma avaliação heurística do roteiro, **não** uma probabilidade real de viralizar.

## Como mudar
- **Conta / horário / formato / repostagem / gerar**: a planilha (acima).
- **Voz / tamanho por conta**: `accounts.json` (conta nova sem entrada usa `_languages`); formatos em `formats/`,
  países em `locales/`.
- **Visual**: `engine` = `motion` | `vintage` | `vox` | `cartoon` (`studio/README.md`); `visual_style` para o Motion.
- **Ideias**: documento do Drive "IDEIAS — escreva aqui" (`conta: ideia`, uma por linha) e "IDEIAS VISUAIS" (imagens).
- **Inspiração**: mande o vídeo no chat dizendo para qual conta; vira uma ficha em `_state/inspiration.md`.
- **Música**: composta por cena (`score.json`), baixa sob a voz; a trilha do canal vem do Drive.
- Tudo é marcado como gerado por IA (decisão final de 2026-11-10).

## Configuração (já feita)
Variáveis do ambiente: `BUFFER_API_KEY` (+ `BUFFER_API_KEY_2…4`), `ELEVENLABS_API_KEYS`, `GDRIVE_CLIENT_ID`,
`GDRIVE_CLIENT_SECRET`, `GDRIVE_REFRESH_TOKEN` (arquivos do app) e `GDRIVE_FULL_REFRESH_TOKEN` (fila: pasta criada
à mão; `python3 daily/gdrive.py auth --full` e depois `token --full '<endereço>'`). Rede: `api.buffer.com`,
`api.elevenlabs.io`, `speech.platform.bing.com`, `api.apify.com`, Google APIs; `APIFY_TOKENS` (laboratório viral). Canais: `python3 daily/buffer_api.py channels`.
Teste sem postar: `publish.py … --dry-run`; fila: `queue_post.py --folder <id> --list`.

## Postagem pela planilha
Fica no repositório **fahholiver/TikTok-drive-buffer** (GitHub Actions, todo dia às 17:00 de Londres).
