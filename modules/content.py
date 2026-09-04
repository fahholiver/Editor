"""
Geração do roteiro do vídeo estilo "VS" (batalha) — capa "Quem vence: X ou Y?",
depois vários ROUNDS comparando os dois lados, e um encerramento com
chamada pra ação (tipo "comenta quem ganha").

Formato do roteiro (JSON):
{
    "hook_title": "QUEM VENCE: GUEPARDO OU LEÃO?",
    "item1_name": "Guepardo",
    "item2_name": "Leão",
    "item1_query": "cheetah running fast savanna",      # inglês, pra buscar vídeo
    "item2_query": "lion roaring savanna",               # inglês, pra buscar vídeo
    "rounds": [
        {
            "round_label": "Velocidade",
            "narration_item1": "O guepardo chega a 110 km/h...",
            "narration_item2": "O leão é mais lento, mas...",
            "tag_item1": "MAIS RÁPIDO",
            "tag_item2": "MAIS FORTE",
            "item1_query": "cheetah sprinting slow motion",   # opcional, sobrescreve o da capa
            "item2_query": "lion running attack"              # opcional
        },
        ...
    ],
    "outro_text": "Comenta aqui quem você acha que vence!"
}

Geração 100% opcional e gratuita, com duas fontes de IA:
1. Groq (https://console.groq.com) — nuvem, grátis, sem cartão. Funciona
   local e também hospedado (Streamlit Cloud, servidor com ngrok etc).
2. Ollama (https://ollama.com) — IA local, sem chave, só funciona rodando
   o app na mesma máquina onde o Ollama está rodando.

Sem nenhuma das duas, cai num roteiro placeholder simples pra você editar
na mão na interface.

Você também pode colar um "roteiro de exemplo" (outro vídeo que você
gostou) — ele é usado só como referência de ESTILO e RITMO pra IA, nunca
como conteúdo a copiar.
"""

import json
import requests

# Segundos médios por ROUND (2 falas: item1 + item2), usado só pra ESTIMAR
# quantos rounds gerar a partir da duração desejada.
AVG_SECONDS_PER_ROUND = 9
COVER_SECONDS = 4          # duração média estimada da cena de capa (VS)
OUTRO_SECONDS = 4          # duração média estimada da cena de encerramento

LANGUAGE_NAMES = {
    "pt": "português do Brasil",
    "en": "inglês",
    "es": "espanhol",
    "de": "alemão",
}

OLLAMA_URL = "http://localhost:11434/api/generate"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# ATENÇÃO: a Groq desativa modelos periodicamente. Se este parar de
# funcionar, veja a lista atual em https://console.groq.com/docs/models
GROQ_DEFAULT_MODEL = "openai/gpt-oss-120b"

REQUIRED_ROUND_FIELDS = ["narration_item1", "narration_item2"]
REQUIRED_TOP_FIELDS = ["hook_title", "item1_name", "item2_name", "item1_query", "item2_query", "rounds"]


def estimate_round_count(duration_seconds: int) -> int:
    usable = max(AVG_SECONDS_PER_ROUND, duration_seconds - COVER_SECONDS - OUTRO_SECONDS)
    return max(2, round(usable / AVG_SECONDS_PER_ROUND))


def is_ollama_available() -> bool:
    try:
        requests.get("http://localhost:11434", timeout=1.5)
        return True
    except Exception:
        return False


def _parse_json_obj(text: str):
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def _call_groq(prompt: str, api_key: str, model: str = GROQ_DEFAULT_MODEL) -> str:
    resp = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Groq API respondeu {resp.status_code}: {resp.text[:500]}")
    return resp.json()["choices"][0]["message"]["content"]


def _call_ollama(prompt: str, model: str = "llama3.1") -> str:
    resp = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["response"]


# ---------------------------------------------------------------------------
# Roteiro de exemplo padrão — só pra ilustrar o formato/ritmo esperado na
# caixa de "roteiro de exemplo" da interface. O usuário pode apagar e colar
# outro, ou deixar em branco.
# ---------------------------------------------------------------------------
DEFAULT_EXAMPLE_SCRIPT = """Capa: "QUEM VENCE: PATRICK JANE OU DEXTER MORGAN?"
(mostra fotos dos dois, gráfico "VS" no meio)

Round 1 - Método
- Patrick Jane: usa leitura de linguagem corporal e blefe pra desmascarar culpados.
- Dexter Morgan: segue um código rígido e só mata quem tem certeza que é culpado.

Round 2 - Ponto fraco
- Patrick Jane: é obcecado por vingança e às vezes age sozinho demais.
- Dexter Morgan: esconde uma vida dupla que pode ruir a qualquer momento.

Encerramento: "Comenta aqui quem você acha que vence essa!" """


def _build_vs_prompt(idea: str, n_rounds: int, language: str,
                      target_seconds: int | None = None,
                      example_script: str | None = None) -> str:
    lang_name = LANGUAGE_NAMES.get(language, "português do Brasil")

    example_block = ""
    if example_script and example_script.strip():
        example_block = f"""
Use o roteiro ABAIXO só como INSPIRAÇÃO de estilo, ritmo e tom de escrita \
(frases curtas, ganchos, jeito de comparar). NÃO copie o conteúdo/tema dele, \
é só uma referência de como escrever:
---
{example_script.strip()}
---
"""

    length_hint = ""
    if target_seconds:
        per_round_seconds = max(5, round((target_seconds - COVER_SECONDS - OUTRO_SECONDS) / max(1, n_rounds)))
        per_line_seconds = max(2, round(per_round_seconds / 2))
        approx_words = max(6, round(per_line_seconds * 2.3))
        length_hint = (
            f"\nCada fala de narração (narration_item1, narration_item2, hook_title, outro_text) "
            f"deve ter por volta de {approx_words} palavras, pra cada round durar perto de "
            f"{per_round_seconds}s falado e o vídeo inteiro durar perto de {target_seconds}s no total."
        )

    return f"""IDIOMA OBRIGATÓRIO: {lang_name}. Todo texto (exceto os campos que terminam em \
"_query") deve estar 100% em {lang_name}, sem nenhuma palavra em outro idioma.
{example_block}
Crie o roteiro de um vídeo curto estilo TikTok/Reels no formato "VS" (batalha), \
comparando dois lados sobre o tema/ideia: "{idea}".

O roteiro tem 3 partes:

1. CAPA (gancho inicial, pergunta tipo "quem vence?"):
- "hook_title": frase de efeito, curta e chamativa, em CAIXA ALTA, tipo \
"QUEM VENCE: X OU Y?" — em {lang_name}.
- "item1_name": nome curto de exibição do lado 1 (1 a 3 palavras), em {lang_name}.
- "item2_name": nome curto de exibição do lado 2 (1 a 3 palavras), em {lang_name}.
- "item1_query": TERMO DE BUSCA DE VÍDEO em inglês (4-7 palavras), bem visual e \
específico, pra achar um clipe representativo do lado 1 num banco de vídeos de \
estoque (Pexels). Ex: "cheetah running fast savanna slow motion".
- "item2_query": mesma ideia, em inglês, pro lado 2, visualmente BEM diferente \
do item1_query pra não confundir.

2. ROUNDS (exatamente {n_rounds} rounds, cada um comparando um aspecto diferente \
do tema — ex: velocidade, força, inteligência, popularidade, custo, etc, o que \
fizer mais sentido pro tema):
Para cada round, retorne um objeto com:
- "round_label": nome curto do critério comparado nesse round (1 a 3 palavras), em {lang_name}.
- "narration_item1": 1 frase curta e direta sobre o lado 1 nesse critério, em {lang_name}. \
DEVE poder ser entendida sozinha (pode citar o nome do item1 ou não, mas tem que fazer sentido).
- "narration_item2": 1 frase curta e direta sobre o lado 2 no MESMO critério, em {lang_name}, \
faça uma comparação/contraste com o que foi dito sobre o item1.
- "tag_item1": 1 a 3 palavras de destaque pra aparecer na tela durante a fala do item1 \
(tipo uma legenda de ênfase, em CAIXA ALTA), em {lang_name}. Ex: "MAIS RÁPIDO".
- "tag_item2": mesma ideia pro item2, em {lang_name}, contrastando com a tag_item1.
- "item1_query": TERMO DE BUSCA DE VÍDEO em inglês (4-7 palavras) específico pra ESSE \
round (pode ser diferente do item1_query da capa, pra variar as imagens). Ex, se o round \
é sobre velocidade: "cheetah sprinting slow motion chase".
- "item2_query": mesma ideia, em inglês, pro item2 nesse round.

3. ENCERRAMENTO:
- "outro_text": frase curta de call-to-action convidando o espectador a comentar quem \
acha que vence, ou continuar assistindo, em {lang_name}. Ex: "Comenta aqui quem vence essa!"
{length_hint}
Lembrete final: TODOS os campos, EXCETO os que terminam em "_query", devem estar em \
{lang_name}. Os campos "*_query" (item1_query, item2_query da capa e de cada round) \
devem estar SEMPRE em inglês.

Responda APENAS com um JSON válido no formato:
{{"hook_title": "...", "item1_name": "...", "item2_name": "...", "item1_query": "...", \
"item2_query": "...", "rounds": [{{"round_label": "...", "narration_item1": "...", \
"narration_item2": "...", "tag_item1": "...", "tag_item2": "...", "item1_query": "...", \
"item2_query": "..."}}, ... exatamente {n_rounds} rounds ...], "outro_text": "..."}}
Sem nenhum texto antes ou depois, sem markdown, sem explicações."""


def _extract_vs_script(data) -> dict | None:
    """Valida que o JSON retornado tem os campos mínimos necessários."""
    if not isinstance(data, dict):
        return None
    if not all(k in data for k in REQUIRED_TOP_FIELDS):
        return None
    rounds = data.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        return None
    valid_rounds = [r for r in rounds if isinstance(r, dict) and all(k in r for k in REQUIRED_ROUND_FIELDS)]
    if not valid_rounds:
        return None
    data["rounds"] = valid_rounds
    data.setdefault("outro_text", "")
    return data


def generate_vs_script_fallback(idea: str, n_rounds: int, language: str = "pt") -> dict:
    """Roteiro placeholder pra quando nenhuma IA está disponível — edite os
    textos manualmente na interface antes de gerar o áudio/vídeo."""
    t = {
        "pt": {
            "hook": "QUEM VENCE: {a} OU {b}?",
            "n1": "Isto é {a}. Edite esta fala antes de gerar o vídeo.",
            "n2": "Isto é {b}. Edite esta fala antes de gerar o vídeo.",
            "tag1": "LADO 1", "tag2": "LADO 2",
            "outro": "Comenta aqui quem você acha que vence!",
        },
        "en": {
            "hook": "WHO WINS: {a} OR {b}?",
            "n1": "This is {a}. Edit this line before generating the video.",
            "n2": "This is {b}. Edit this line before generating the video.",
            "tag1": "SIDE 1", "tag2": "SIDE 2",
            "outro": "Comment below who you think wins!",
        },
        "es": {
            "hook": "¿QUIÉN GANA: {a} O {b}?",
            "n1": "Esto es {a}. Edita esta frase antes de generar el video.",
            "n2": "Esto es {b}. Edita esta frase antes de generar el video.",
            "tag1": "LADO 1", "tag2": "LADO 2",
            "outro": "¡Comenta quién crees que gana!",
        },
        "de": {
            "hook": "WER GEWINNT: {a} ODER {b}?",
            "n1": "Das ist {a}. Bearbeite diesen Satz vor dem Rendern.",
            "n2": "Das ist {b}. Bearbeite diesen Satz vor dem Rendern.",
            "tag1": "SEITE 1", "tag2": "SEITE 2",
            "outro": "Kommentiere, wer deiner Meinung nach gewinnt!",
        },
    }.get(language) or {}
    a, b = f"{idea} A", f"{idea} B"
    rounds = [
        {
            "round_label": f"Round {i+1}",
            "narration_item1": t["n1"].format(a=a),
            "narration_item2": t["n2"].format(b=b),
            "tag_item1": t["tag1"],
            "tag_item2": t["tag2"],
            "item1_query": a,
            "item2_query": b,
        }
        for i in range(n_rounds)
    ]
    return {
        "hook_title": t["hook"].format(a=a, b=b),
        "item1_name": a,
        "item2_name": b,
        "item1_query": a,
        "item2_query": b,
        "rounds": rounds,
        "outro_text": t["outro"],
    }


def generate_vs_script(idea: str, target_seconds: int, language: str = "pt",
                        example_script: str | None = None,
                        groq_api_key: str | None = None,
                        use_ollama: bool = False,
                        ollama_model: str = "llama3.1") -> dict:
    """Gera o roteiro completo do vídeo VS a partir de uma ideia/tema.
    Tenta Groq -> Ollama -> placeholder sem IA, nessa ordem."""
    n_rounds = estimate_round_count(target_seconds)
    prompt = _build_vs_prompt(idea, n_rounds, language, target_seconds, example_script)

    if groq_api_key:
        try:
            data = _parse_json_obj(_call_groq(prompt, groq_api_key))
            script = _extract_vs_script(data)
            if script:
                script["rounds"] = script["rounds"][:n_rounds]
                return script
            print("[content] Groq retornou JSON incompleto, tentando próxima opção.")
        except Exception as e:
            print(f"[content] Falha ao usar Groq ({e}), tentando próxima opção.")

    if use_ollama:
        try:
            data = _parse_json_obj(_call_ollama(prompt, ollama_model))
            script = _extract_vs_script(data)
            if script:
                script["rounds"] = script["rounds"][:n_rounds]
                return script
            print("[content] Ollama retornou JSON incompleto, usando fallback sem IA.")
        except Exception as e:
            print(f"[content] Falha ao usar Ollama ({e}), usando fallback sem IA.")

    return generate_vs_script_fallback(idea, n_rounds, language)
