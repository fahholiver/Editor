# Vídeo diário de terror → TikTok via Buffer (às 14h)

Todo dia uma sessão agendada do Claude Code faz **um vídeo novo e diferente para cada conta TikTok**
conectada no Buffer, cada conta com seu **formato** de história (todos na animação 2D):

| conta | público / idioma | formato | voz | posta às |
|---|---|---|---|---|
| mandraketoons | Reino Unido, inglês britânico | confissão em 1ª pessoa | Daniel (ElevenLabs) | 14:00 Londres |
| anna.20263 | Alemanha, alemão | regra de terror | Conrad (nativa) | 16:00 Berlim (15:00 Londres) |
| user890997140 | França, francês | terror pela tela do celular | Henri (nativa) | 17:00 Paris (16:00 Londres) |

Tudo isso fica em `daily/accounts.json` (idioma, formato, voz, horário, tamanho do texto). Para criar um formato novo,
adicione um arquivo em `daily/formats/`.

Para cada conta:

1. **História**: o próprio Claude escreve uma história de terror curta e original em inglês (~75–100 s),
   seguindo [`STORY_BRIEF.md`](STORY_BRIEF.md) e o histórico (`stories.jsonl`) pra não repetir.
2. **VoiceOver**: [`voiceover.py`](voiceover.py) narra a história linha a linha, com pausas, e pega o
   tempo de cada palavra direto do TTS (legenda karaokê sincronizada, sem alinhamento forçado):
   - **ElevenLabs** se `ELEVENLABS_API_KEY` existir (melhor qualidade; voz padrão "Daniel", britânica);
   - senão **Edge TTS** grátis (`en-GB-RyanNeural`), sem chave.
3. **Animação**: [`bootstrap.py`](bootstrap.py) monta a pasta da história na engine do repo
   **fahholiver/Motion** (branch `claude/radiator-animation`, a mesma do *Check the Radiator*) e o Claude
   escreve os shots/efeitos e renderiza seguindo o `CLAUDE.md` de lá.
4. **Postagem**: [`publish.py`](publish.py) faz uma cópia leve do MP4, hospeda num link público (branch
   `media` deste repo → `raw.githubusercontent.com`) e cria o post em cada conta TikTok conectada no Buffer, agendado
   para **14:00** (fuso `Europe/London`, horário do Reino Unido, por padrão). Se já passou das 14h, posta na hora.

As instruções que a sessão agendada segue estão em [`DAILY_RUN.md`](DAILY_RUN.md).

## Configuração (uma vez)

### 1. Buffer
- Conecte o TikTok no Buffer (de preferência perfil Business/Creator).
- Buffer → Settings → **API** → crie uma API key.
- Descubra o id do canal TikTok:
  ```bash
  BUFFER_API_KEY=... python3 daily/buffer_api.py channels
  ```

### 2. Ambiente da nuvem (claude.ai/code → ambiente → Edit)
**Variáveis/segredos:**
| nome | obrigatório | valor |
|---|---|---|
| `BUFFER_API_KEY` | sim | chave da API do Buffer |
| `BUFFER_TIKTOK_CHANNELS` | não | em quais contas TikTok postar: `all` (padrão = todas as conectadas no Buffer) ou nomes separados por vírgula, ex. `anna.20263,strawberry.me27` |
| `ELEVENLABS_API_KEYS` | não | uma ou mais chaves ElevenLabs (`sk_...`) separadas por vírgula; usa a 1ª com crédito e passa para a próxima quando acaba (`ELEVENLABS_API_KEY` com uma só também funciona) |
| `POST_TIME` / `POST_TZ` | não | padrão `14:00` / `Europe/London` (horário do Reino Unido, já com horário de verão) |
| `PIPELINE_REF` | não | branch com a pasta `daily/` (padrão `main`; use `claude/buffer-tiktok-video-generation-lrudue` até fazer merge) |

**Acesso à rede** — libere estes domínios (hoje estão bloqueados neste ambiente):
- `api.buffer.com` — API do Buffer
- `speech.platform.bing.com` — voz Edge TTS (grátis)
- `api.elevenlabs.io` — só se usar ElevenLabs

### 3. Repositórios
A sessão precisa do `fahholiver/Editor` (este) e do `fahholiver/Motion` (engine de animação). O Buffer
baixa o vídeo do link `raw.githubusercontent.com/fahholiver/Editor/media/...`, por isso o Editor tem que
continuar **público**. Se preferir outro host (S3, Cloudinary…), passe `--video-url` no `publish.py`.

## Testar à mão
```bash
pip install -r daily/requirements.txt
# história em story.txt
python3 daily/bootstrap.py /home/user/motion minha_historia "My Title" story.txt
# ... shots/render conforme Motion/CLAUDE.md ...
python3 daily/publish.py /home/user/motion/output/minha_historia_1080x1920.mp4 \
  --slug minha_historia --title "My Title" --caption "Don't open the door. #horrorstory #scary" --dry-run
```
`--dry-run` só gera a cópia de upload, sem publicar nada.

## Observações
- **Custo**: cada execução diária é uma sessão completa do Claude Code escrevendo a animação (a parte
  mais pesada), então consome uso do seu plano todo dia.
- A API GraphQL do Buffer é nova; se o `createPost` reclamar de algum campo, rode
  `python3 daily/buffer_api.py introspect CreatePostInput` pra ver o formato atual.
- O vídeo final completo (alta qualidade) fica só na sessão; o Buffer recebe a cópia leve
  (H.264 ≤ 4 Mb/s), que o TikTok recomprime de qualquer jeito.

## Google Drive (cópia de cada vídeo + texto do VoiceOver)

Depois de postar, o `publish.py` salva no seu Drive:
```
TikTok Daily/
  anna.20263/        2026-11-06.mp4   2026-11-06.txt
  strawberry.me27/   2026-11-06.mp4   2026-11-06.txt
```
O `.txt` tem o título, o texto narrado e a legenda. Se o Drive falhar, o post sai mesmo assim.

**Configuração (uma vez, ~10 min, no computador):**
1. Acesse https://console.cloud.google.com → crie um projeto (ex.: "TikTok Daily").
2. **APIs e serviços → Biblioteca** → procure **Google Drive API** → **Ativar**.
3. **Google Auth Platform / Tela de consentimento OAuth** → tipo **Externo** → nome do app e seu e-mail →
   salve. Em **Público-alvo**, clique **Publicar app** (modo "Em produção"; senão o acesso expira em 7 dias).
   Não precisa de verificação do Google: o app só pede acesso aos arquivos que ele mesmo cria (`drive.file`).
4. **Credenciais → Criar credenciais → ID do cliente OAuth** → tipo **App para computador** → copie o
   **ID do cliente** e a **Chave secreta do cliente**.
5. Nas variáveis do ambiente do Claude, adicione `GDRIVE_CLIENT_ID=...` e `GDRIVE_CLIENT_SECRET=...`.
6. Peça ao Claude para "conectar o Drive": ele gera um link de login do Google (`gdrive.py auth`). Abra,
   autorize, e o navegador vai parar numa página de erro em `localhost` — **isso é normal**: copie o
   endereço completo dessa página e mande para o Claude, que gera o `GDRIVE_REFRESH_TOKEN`
   (`gdrive.py token '<endereço>'`). Cadastre esse valor nas variáveis do ambiente também.

Opcional: `GDRIVE_ROOT_FOLDER` muda o nome da pasta principal (padrão `TikTok Daily`).


## Como mudar daqui pra frente
- **Música de fundo**: coloque o arquivo em `daily/assets/background_music.mp3` (ou mande no chat). Ela toca
  em loop por baixo de todos os vídeos, abaixando sozinha quando a narração fala.
- **Texto maior/menor**: mude `words` da conta em `daily/accounts.json` (ex. `[250, 350]` ≈ 90–120 s).
- **Novo modelo de texto**: escreva/edite um arquivo em `daily/formats/` (forma da história, tom, título) e
  aponte a conta para ele em `accounts.json`. Detalhes de cada país ficam em `daily/locales/`.
- **Referências visuais / de áudio**: mande no chat (imagens, links de vídeos, áudios) dizendo para qual conta;
  o Claude adapta os cenários/personagens da engine e registra o pedido em `daily/insights.md`.
- **Horários**: `post_time` + `tz` de cada conta (mantenha 1 h de diferença).
- **Métricas**: todo dia o `daily/metrics.py` puxa do Buffer views, tempo médio assistido, likes e shares de
  cada post; o que funcionar vira regra em `daily/insights.md` e é aplicado nas próximas histórias.

## Vídeos de inspiração
Mande o vídeo **aqui no chat** (anexo) dizendo para qual conta é (ou "todas") e o que você gostou. O Claude mede
o ritmo (duração, cortes, gancho), olha os quadros, escreve uma ficha com as técnicas a copiar e guarda tudo no
Drive (`TikTok Daily/_inspiration/` + `_state/inspiration.md`). A rotina diária lê essa ficha antes de criar as
histórias e as cenas. Só técnicas são copiadas — nunca a história, personagens, arte ou música do vídeo.

## Relatório diário (08:07 Londres)
Uma tarefa separada e leve publica todo dia, sem análise, o relatório dos vídeos do dia anterior:
1. ranking do pior para o melhor (perfil, visualizações, retenção até o final);
2. interações por vídeo (plataforma, vídeo, @, curtidas, comentários, salvamentos, compartilhamentos).
Também fica salvo no Drive em `TikTok Daily/_reports/<data>.md`. Rodar à mão: `python3 daily/report.py --date 2026-11-05`.

## Contas que recebem cópias (sem história nova)
| vídeo original | cópia em | quando |
|---|---|---|
| mandraketoons (UK) | Coyote's Jazz (YouTube Shorts), proper_laughs_uk (Instagram Reel) | 17:00 Londres |
| anna.20263 (alemão) | Melhores Mensagens (YouTube Shorts) | 19:00 Berlim |
| user890997140 (francês) | Algorithmic Capital (YouTube Shorts) | 20:00 Paris |
Configurado em `also_post_to` no `accounts.json` (chaves Buffer 2 e 3).

## Contas com história própria (desde 2026-11-08)
| conta | idioma | formato | voz | posta às |
|---|---|---|---|---|
| thai.1382 | alemão | terror pela tela do celular | Killian (Microsoft) | 21:00 Berlim |
| kaelusuxkzx | francês | confissão em 1ª pessoa | Rémy (Microsoft) | 22:00 Paris |
