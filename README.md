# Gerador de Vídeos "VS" (estilo TikTok)

Gera vídeos curtos verticais no formato **"Quem vence: X ou Y?"**: você manda
uma ideia, a IA escreve um roteiro com capa + vários *rounds* de comparação
+ encerramento, você edita à vontade, e o app busca clipes de vídeo reais na
internet, gera a narração em voz natural e monta tudo em um `.mp4` pronto
pra postar — via Streamlit, rodando local e exposto com **ngrok**.

**Sem legenda de fala embutida** — o TikTok já gera isso automaticamente ao
postar, então o vídeo sai "limpo" (só título, nomes e tags de destaque).

## Como funciona

1. **Roteiro** (`modules/content.py`) — você escreve uma ideia (ex: "Guepardo
   vs Leão") e, opcionalmente, cola um roteiro de outro vídeo que gostou (só
   como referência de RITMO/ESTILO, nunca de conteúdo). A IA (Groq ou Ollama)
   gera um JSON com:
   - capa (`hook_title`, nome e termo de busca de cada lado)
   - N *rounds*, cada um com uma fala curta pra cada lado + uma "tag" de
     destaque (tipo legenda de ênfase, ex: "MAIS RÁPIDO")
   - encerramento com call-to-action (ex: "comenta quem vence")

   Sem IA configurada, cai num roteiro placeholder que você edita na mão.

2. **Mídia** (`modules/images.py`) — pra cada termo de busca, tenta nessa
   ordem: **vídeo Pexels** → **foto Pexels** (vira clipe com zoom lento) →
   **imagem DuckDuckGo** (sem precisar de chave nenhuma). Você sempre tem
   uma chave grátis da Pexels em https://www.pexels.com/api/.

3. **Narração** (`modules/tts_engine.py`) — Kokoro-82M (leve, roda em CPU)
   pra português/inglês/espanhol, com vozes naturais prontas (não clona sua
   voz). Alemão usa espeak-ng como reserva.

4. **Vídeo final** (`modules/video_builder.py`) — monta capa (split-screen +
   "VS"), um clipe em tela cheia por lado em cada round (com zoom lento tipo
   Ken Burns, nome do item e tag de destaque), e encerramento — tudo com
   transições suaves (crossfade) e, se você quiser, uma música de fundo
   baixinha por trás da narração.

## Como rodar localmente

```bash
git clone <seu-repo>
cd vs-video-app
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`.

### Requisitos de sistema

- **ffmpeg**: usado pelo moviepy pra ler/escrever vídeo. Se não tiver:
  - Linux: `sudo apt install ffmpeg espeak-ng`
  - Mac: `brew install ffmpeg espeak-ng`
  - Windows: baixe o ffmpeg em https://ffmpeg.org/download.html e adicione
    ao PATH; espeak-ng em https://github.com/espeak-ng/espeak-ng/releases
- **espeak-ng**: motor de fonética do Kokoro (e fallback total pro alemão).

## Como expor com ngrok (pra acessar de qualquer lugar / mandar link pra alguém)

1. Rode o app localmente (`streamlit run app.py`), ele sobe na porta 8501.
2. Instale o ngrok: https://ngrok.com/download (crie uma conta grátis e
   pegue seu authtoken em https://dashboard.ngrok.com/get-started/your-authtoken).
3. Configure o token uma vez: `ngrok config add-authtoken SEU_TOKEN`.
4. Em outro terminal (com o Streamlit já rodando), rode:
   ```bash
   ngrok http 8501
   ```
5. O ngrok mostra uma URL tipo `https://xxxx.ngrok-free.app` — é essa que
   você acessa/compartilha. Ela só funciona enquanto os dois processos
   (`streamlit run` e `ngrok http`) estiverem rodando na sua máquina.

> Dica: o plano grátis do ngrok gera uma URL nova toda vez que você reinicia
> o túnel. Se quiser uma URL fixa, dá pra reservar um "domínio estático"
> grátis na sua conta ngrok (`ngrok http --url=seu-dominio.ngrok-free.app 8501`).

## Configurando as chaves de API

Duas formas:

1. **Colar na interface** (campos de senha no topo do app) — mais simples
   pra testar.
2. **Salvar em `.streamlit/secrets.toml`** (recomendado pra não digitar
   toda vez): copie `.streamlit/secrets.toml.example` para
   `.streamlit/secrets.toml` e preencha:
   ```toml
   PEXELS_API_KEY = "sua_chave"
   GROQ_API_KEY = "sua_chave"
   ```
   Esse arquivo já está no `.gitignore` — nunca sobe pro GitHub.

- **Pexels** (recomendada, grátis, sem cartão): https://www.pexels.com/api/
- **Groq** (recomendada pro roteiro, grátis, sem cartão): https://console.groq.com/keys
- **Ollama** (alternativa 100% local ao Groq, sem chave nenhuma): instale em
  [ollama.com](https://ollama.com) e rode `ollama pull llama3.1`. Só
  funciona rodando na mesma máquina que o Streamlit (o ngrok só expõe a
  interface, não muda isso).

## Roteiro de exemplo

Na tela principal tem um campo opcional "roteiro de exemplo" — cole um
roteiro de outro vídeo (ex: um que você transcreveu de um vídeo que gostou)
e a IA vai usar como referência de **ritmo e tom de escrita**, nunca de
conteúdo. Tem um exemplo padrão pronto num expansor logo acima do campo, com
um botão "usar este exemplo como referência de estilo".

## Sobre resolução e performance

O vídeo é gerado em 1080x1920 (padrão TikTok/Reels) por padrão. Se a
renderização ficar muito lenta na sua máquina, abra
`modules/video_builder.py` e troque:

```python
W, H = 1080, 1920
```
por
```python
W, H = 720, 1280
```

## Sobre direitos autorais

Os clipes vêm da Pexels (banco de vídeos/fotos de uso livre, sem precisar de
atribuição) ou, no fallback, de busca aberta no DuckDuckGo — que **pode**
trazer conteúdo com direitos autorais de terceiros. Pra uso comercial ou
postagem em massa, prefira sempre resultados vindos da Pexels (configure a
chave!) e evite o fallback do DuckDuckGo.

## Sobre postar automaticamente no TikTok

Este projeto só gera o `.mp4`. Postar automaticamente exige a TikTok Content
Posting API (precisa de aprovação de app pelo TikTok for Developers) — pode
ser adicionado depois, num módulo separado.
