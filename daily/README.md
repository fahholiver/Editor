# Vídeo diário de terror → TikTok via Buffer (às 14h)

Todo dia uma sessão agendada do Claude Code (na nuvem) faz:

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
   `media` deste repo → `raw.githubusercontent.com`) e cria o post no canal TikTok do Buffer agendado
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
| `BUFFER_TIKTOK_CHANNEL_ID` | sim | id do canal TikTok (passo acima) |
| `ELEVENLABS_API_KEY` | não | se quiser a voz ElevenLabs |
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
