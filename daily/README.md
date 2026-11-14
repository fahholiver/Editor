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
- **Conta repostagem**: nomes dos canais no Buffer separados por vírgula; postam o mesmo vídeo no mesmo horário.
- **País-Língua**: UK/Inglês, Alemanha/Alemão, França/Francês (ou en-GB, de-DE, fr-FR).
- **Modelo-skill**: formato (`confession`, `rule_horror`, `interactive_series`, `survival_guide`, `parable`,
  `curiosity`) e/ou engine (`motion`, `vintage`, `vox`, `cartoon`) e/ou estilo (`pixel_arcade`), separados por `/`:
  ex. `parable/vintage`.
- Lida com o seu login do Google (`GDRIVE_FULL_REFRESH_TOKEN`); cada leitura fica salva em Drive
  `_state/accounts_sheet.csv` e é usada se o Google falhar. Planilha vazia/cabeçalho errado → `accounts.json` como antes.
  Conferir: `python3 daily/sheet.py`.
- A fila do Drive roda às 13:35 de Londres: uma conta Gerar = n com horário antes disso posta quando a tarefa roda.

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
`api.elevenlabs.io`, `speech.platform.bing.com`, Google APIs. Canais: `python3 daily/buffer_api.py channels`.
Teste sem postar: `publish.py … --dry-run`; fila: `queue_post.py --folder <id> --list`.
