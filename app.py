import os
import wave
import streamlit as st

from modules.content import (
    generate_vs_script, estimate_round_count, is_ollama_available,
    DEFAULT_EXAMPLE_SCRIPT,
)
from modules.images import fetch_media_for_item
from modules.tts_engine import synthesize, LANGUAGES
from modules.video_builder import build_vs_video, build_cover_scene, build_round_scene, build_outro_scene

st.set_page_config(page_title="Gerador de Vídeos VS (estilo TikTok)", page_icon="⚔️", layout="centered")
st.title("⚔️ Gerador de vídeos \"VS\" (estilo TikTok)")
st.caption(
    "Você manda a ideia, a IA escreve um roteiro no formato \"Quem vence: X ou Y?\", "
    "você edita à vontade, e o app monta o vídeo com clipes de verdade buscados na internet."
)

OUTPUT_DIR = "output"
IMG_DIR = os.path.join(OUTPUT_DIR, "media")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Configurações gerais
# ---------------------------------------------------------------------------
st.header("⚙️ Configurações")

language_label = st.selectbox("Idioma falado da narração", list(LANGUAGES.keys()))
language = LANGUAGES[language_label]

VOICE_OPTIONS = {
    "pt": {"Feminina (Francisca)": "pt-BR-FranciscaNeural", "Masculina (Antonio)": "pt-BR-AntonioNeural"},
    "en": {"Feminina (Aria)": "en-US-AriaNeural", "Feminina (Jenny)": "en-US-JennyNeural", "Masculina (Guy)": "en-US-GuyNeural"},
    "es": {"Feminina (Elvira)": "es-ES-ElviraNeural", "Masculina (Alvaro)": "es-ES-AlvaroNeural"},
    "de": {"Feminina (Katja)": "de-DE-KatjaNeural", "Masculina (Conrad)": "de-DE-ConradNeural"},
}
voice_choices = VOICE_OPTIONS.get(language, {})
voice_label = st.selectbox("Voz da narração", list(voice_choices.keys()))
selected_voice = voice_choices[voice_label]
st.caption("🔊 Vozes neurais gratuitas do Edge TTS (Microsoft) — precisa de internet.")

st.subheader("🔑 Chaves de API")
col1, col2 = st.columns(2)
with col1:
    pexels_api_key_input = st.text_input(
        "Chave da API Pexels (vídeos/fotos)", type="password",
        help="Grátis em https://www.pexels.com/api/. Sem ela, o app cai pro "
             "DuckDuckGo Images (funciona, mas só fotos, sem vídeo).",
    )
with col2:
    groq_api_key_input = st.text_input(
        "Chave da API Groq (roteiro por IA, opcional)", type="password",
        help="Grátis em https://console.groq.com/keys. Sem ela, o app tenta "
             "o Ollama local, ou usa um roteiro placeholder editável.",
    )

try:
    pexels_api_key = pexels_api_key_input or st.secrets.get("PEXELS_API_KEY", "")
except Exception:
    pexels_api_key = pexels_api_key_input
try:
    groq_api_key = groq_api_key_input or st.secrets.get("GROQ_API_KEY", "")
except Exception:
    groq_api_key = groq_api_key_input

ollama_ok = is_ollama_available()
ollama_model = st.text_input(
    "Modelo do Ollama (usado só se não houver chave da Groq)", "llama3.1",
    help="Qualquer modelo já baixado com `ollama pull <modelo>`.",
)

if groq_api_key:
    st.success("✅ Groq configurado — roteiro será gerado por IA na nuvem.")
elif ollama_ok:
    st.success("✅ Ollama detectado rodando localmente — roteiro será gerado por IA.")
else:
    st.warning(
        "⚠️ Nenhuma IA de roteiro configurada. O roteiro sairá como um "
        "placeholder simples pra você editar na mão (ou configure Groq/Ollama acima)."
    )

if not pexels_api_key:
    st.warning(
        "⚠️ Sem chave da Pexels, o app usa DuckDuckGo Images como reserva "
        "(só fotos, sem clipes de vídeo — o vídeo final fica menos dinâmico)."
    )

st.divider()

# ---------------------------------------------------------------------------
# 1. Ideia do vídeo + roteiro de exemplo (estilo/ritmo)
# ---------------------------------------------------------------------------
st.header("1. Ideia do vídeo")
idea = st.text_input(
    "Sobre o que é a comparação?",
    "Guepardo vs Leão: quem vence numa disputa de velocidade e força?",
    help="Pode ser qualquer coisa: dois animais, dois personagens, dois "
         "produtos, duas épocas... a IA vai inventar os rounds de comparação.",
)

duration_seconds = st.slider("Duração aproximada do vídeo (segundos)", 20, 150, 50, step=5)
n_rounds = estimate_round_count(duration_seconds)
st.caption(f"Isso deve gerar em torno de **{n_rounds} rounds** de comparação (+ capa e encerramento).")

with st.expander("📋 Ver roteiro de exemplo (só formato/estilo, não é copiado)"):
    st.text(DEFAULT_EXAMPLE_SCRIPT)
    if st.button("Usar este exemplo como referência de estilo"):
        st.session_state.example_script_value = DEFAULT_EXAMPLE_SCRIPT

example_script = st.text_area(
    "Roteiro de exemplo (opcional) — cole aqui um vídeo que você gostou, "
    "pra IA imitar o RITMO e o TOM (o conteúdo/tema não é copiado)",
    value=st.session_state.get("example_script_value", ""),
    height=140,
    key="example_script_value",
)

st.subheader("🎵 Música de fundo (opcional)")
music_file = st.file_uploader("Trilha sonora (mp3/wav) para tocar baixinho por trás da narração", type=["mp3", "wav"])
music_path = None
if music_file:
    os.makedirs("assets", exist_ok=True)
    music_path = "assets/background_music.mp3"
    with open(music_path, "wb") as f:
        f.write(music_file.read())
    st.audio(music_path)

if "vs_script" not in st.session_state:
    st.session_state.vs_script = None

if st.button("📝 Gerar roteiro"):
    with st.spinner("Gerando roteiro..."):
        st.session_state.vs_script = generate_vs_script(
            idea, duration_seconds, language,
            example_script=example_script or None,
            groq_api_key=groq_api_key or None,
            use_ollama=ollama_ok, ollama_model=ollama_model,
        )

# ---------------------------------------------------------------------------
# 2. Revisar e editar o roteiro
# ---------------------------------------------------------------------------
if st.session_state.vs_script:
    script = st.session_state.vs_script
    st.header("2. Revise e edite o roteiro")

    script["hook_title"] = st.text_input("Título de gancho (capa)", script["hook_title"])

    c1, c2 = st.columns(2)
    with c1:
        script["item1_name"] = st.text_input("Nome — Lado 1", script["item1_name"])
        script["item1_query"] = st.text_input("Busca de vídeo — Lado 1 (inglês)", script["item1_query"])
    with c2:
        script["item2_name"] = st.text_input("Nome — Lado 2", script["item2_name"])
        script["item2_query"] = st.text_input("Busca de vídeo — Lado 2 (inglês)", script["item2_query"])

    st.subheader("Rounds")
    edited_rounds = st.data_editor(
        script["rounds"], num_rows="dynamic", use_container_width=True,
        column_config={
            "round_label": "Critério",
            "narration_item1": st.column_config.TextColumn("Fala — Lado 1", width="large"),
            "narration_item2": st.column_config.TextColumn("Fala — Lado 2", width="large"),
            "tag_item1": "Tag — Lado 1",
            "tag_item2": "Tag — Lado 2",
            "item1_query": "Busca vídeo — Lado 1 (EN)",
            "item2_query": "Busca vídeo — Lado 2 (EN)",
        },
    )
    script["rounds"] = edited_rounds

    script["outro_text"] = st.text_input("Texto de encerramento (call-to-action)", script.get("outro_text", ""))
    st.session_state.vs_script = script

    # -----------------------------------------------------------------
    # 3. Renderizar vídeo final
    # -----------------------------------------------------------------
    st.header("3. Gerar vídeo")
    if st.button("🎥 Renderizar vídeo final"):
        progress = st.progress(0.0, text="Iniciando...")
        n = len(script["rounds"])
        total_steps = 2 + n * 2 + 1  # capa + (video+audio por lado por round) + encerramento
        step_counter = [0]

        def bump(text):
            step_counter[0] += 1
            progress.progress(min(step_counter[0] / total_steps, 1.0), text=text)

        # --- Capa ---
        cover_media1 = fetch_media_for_item(
            script["item1_query"], IMG_DIR, "cover_item1", pexels_api_key,
            fallback_query=script["item1_name"],
        )
        cover_media2 = fetch_media_for_item(
            script["item2_query"], IMG_DIR, "cover_item2", pexels_api_key,
            fallback_query=script["item2_name"],
        )
        bump("Buscando clipes da capa...")

        hook_audio = os.path.join(AUDIO_DIR, "hook.wav")
        synthesize(script["hook_title"], hook_audio, language_id=language, voice=selected_voice)
        bump("Gerando voz da capa...")

        cover_scene = build_cover_scene(script, cover_media1, cover_media2, hook_audio)
        scenes = [cover_scene]

        # --- Rounds ---
        for idx, rnd in enumerate(script["rounds"]):
            q1 = str(rnd.get("item1_query") or script["item1_query"])
            q2 = str(rnd.get("item2_query") or script["item2_query"])

            media1 = fetch_media_for_item(q1, IMG_DIR, f"round{idx}_item1", pexels_api_key,
                                           fallback_query=script["item1_name"])
            bump(f"Round {idx+1}/{n}: buscando clipe do lado 1...")
            audio1 = os.path.join(AUDIO_DIR, f"round{idx}_item1.wav")
            synthesize(str(rnd["narration_item1"]), audio1, language_id=language, voice=selected_voice)
            bump(f"Round {idx+1}/{n}: gerando voz do lado 1...")
            scenes.append(build_round_scene(
                script["item1_name"], media1, str(rnd.get("tag_item1", "")), audio1,
                accent_color=(255, 214, 10, 255),
            ))

            media2 = fetch_media_for_item(q2, IMG_DIR, f"round{idx}_item2", pexels_api_key,
                                           fallback_query=script["item2_name"])
            bump(f"Round {idx+1}/{n}: buscando clipe do lado 2...")
            audio2 = os.path.join(AUDIO_DIR, f"round{idx}_item2.wav")
            synthesize(str(rnd["narration_item2"]), audio2, language_id=language, voice=selected_voice)
            bump(f"Round {idx+1}/{n}: gerando voz do lado 2...")
            scenes.append(build_round_scene(
                script["item2_name"], media2, str(rnd.get("tag_item2", "")), audio2,
                accent_color=(90, 200, 255, 255),
            ))

        # --- Encerramento ---
        outro_audio = os.path.join(AUDIO_DIR, "outro.wav")
        synthesize(script.get("outro_text", ""), outro_audio, language_id=language, voice=selected_voice)
        scenes.append(build_outro_scene(script, cover_media1, cover_media2, outro_audio))
        bump("Gerando encerramento...")

        out_path = os.path.join(OUTPUT_DIR, "video_final.mp4")
        build_vs_video(scenes, out_path, music_path=music_path)
        progress.progress(1.0, text="Pronto!")

        all_audio = [hook_audio] + [
            os.path.join(AUDIO_DIR, f"round{idx}_item{side}.wav")
            for idx in range(n) for side in (1, 2)
        ] + [outro_audio]
        total_audio_s = sum(
            wave.open(p).getnframes() / wave.open(p).getframerate()
            for p in all_audio if os.path.exists(p)
        )

        st.success(f"Vídeo gerado com sucesso! Duração real da narração: ~{total_audio_s:.0f}s "
                   f"(você pediu {duration_seconds}s — o vídeo final é um pouco maior por causa "
                   f"das transições e folgas entre cenas).")
        st.video(out_path)
        with open(out_path, "rb") as f:
            st.download_button("⬇️ Baixar vídeo", f, file_name="video_final.mp4")
