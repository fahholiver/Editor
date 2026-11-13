# Vídeos diários → TikTok via Buffer

Todo dia uma sessão agendada do Claude segue a skill [`.claude/skills/daily-shorts/SKILL.md`](../.claude/skills/daily-shorts/SKILL.md):
lê as métricas, as ideias e as inspirações, escreve uma história nova por conta, narra (ElevenLabs/Edge), anima,
posta no Buffer e arquiva no Drive (`TikTok Daily/`).

## Contas com história própria (`accounts.json`)
| conta | idioma | formato | visual (engine) | posta às | cópias |
|---|---|---|---|---|---|
| mandraketoons | inglês UK | confissão | Motion | 14:00 Londres | Coyote's Jazz (YT), proper_laughs_uk (IG) 17:00 |
| anna.20263 | alemão | regra de terror | Motion + pixel_arcade | 16:00 Berlim | Melhores Mensagens (YT) 19:00 |
| user890997140 | francês | série interativa | **cartoon** (skill `cartoon-audio-short`) | 17:00 Paris | Algorithmic Capital (YT) 20:00 |
| thai.1382 | alemão | guia de sobrevivência | vox 1:1 | 21:00 Berlim | — |
| kaelusuxkzx | francês | parábola | vintage 1:1 | 22:00 Paris | — |

## Contas da fila do Drive (vídeos prontos, sem história)
strawberry.me27, julia__lives, stevevrcxj0 — todo dia às 14:00 Londres, legenda `#emotional #respectpeople`.
`queue_post.py` dá **um vídeo diferente para cada conta** (ordem pelo nome do arquivo: 01_, 02_…), manda cada um
para a lixeira do Drive depois que o Buffer confirma o envio e segura os que ainda estão esperando, então o mesmo
vídeo nunca vai para duas contas. Se houver menos vídeos que contas, as primeiras da lista recebem.

## Como mudar
- **Conta / formato / voz / horário / tamanho**: `accounts.json` (formatos em `formats/`, países em `locales/`).
  Mudança com data: `"changes_from": {"AAAA-MM-DD": {...}}`; conta nova: `"active_from"`.
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
