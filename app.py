import os
import tempfile
import urllib.request
import streamlit as st
import soundfile as sf
from ollama import Client
from kokoro_onnx import Kokoro
from moviepy.editor import TextClip, AudioFileClip

# Função para garantir que os arquivos do Kokoro existam localmente
def download_kokoro_files():
    files = {
        "kokoro-v0_7.onnx": "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/kokoro-v0_7.onnx",
        "voices.json": "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices.json"
    }
    for file_name, url in files.items():
        if not os.path.exists(file_name):
            with st.spinner(f"Baixando {file_name} (necessário para a narração)..."):
                urllib.request.urlretrieve(url, file_name)

# Executa a verificação dos arquivos do Kokoro
download_kokoro_files()

# Configuração da página
st.set_page_config(page_title="Gerador de Vídeo com Ollama + Kokoro", page_icon="🎬", layout="wide")

st.title("🎬 Gerador de Vídeo: Ideia ➔ Roteiro ➔ Áudio ➔ Vídeo")

# Sidebar
st.sidebar.header("1. Configurações do Ollama")
ollama_host = st.sidebar.text_input("URL do Servidor Ollama", value="http://localhost:11434")
model_name = st.sidebar.text_input("Nome do Modelo", value="llama3")

st.sidebar.header("2. Configurações do Vídeo")
language_code = st.sidebar.selectbox("Idioma", options=["pt", "en", "es"], index=0)
voice_name = st.sidebar.text_input("Voz do Kokoro", value="pf_dora" if language_code == "pt" else "af_heart")
bg_color = st.sidebar.color_picker("Cor de Fundo", value="#000000")
text_color = st.sidebar.color_picker("Cor do Texto", value="#FFFFFF")
fontsize = st.sidebar.slider("Tamanho da Fonte", min_value=20, max_value=100, value=45)

# Input da ideia
idea_input = st.text_area(
    "Digite sua ideia de vídeo:",
    placeholder="Exemplo: Fale sobre 3 dicas rápidas para melhorar a produtividade de manhã.",
    height=100
)

if "generated_script" not in st.session_state:
    st.session_state.generated_script = ""

# Etapa 1: Gerar Roteiro via Ollama
if st.button("1. Gerar Roteiro com Ollama"):
    if not idea_input.strip():
        st.warning("Insira uma ideia primeiro.")
    else:
        with st.spinner("Conectando ao Ollama e gerando o roteiro..."):
            try:
                client = Client(host=ollama_host)
                prompt = (
                    f"Você é um roteirista de vídeos curtos. "
                    f"Crie um roteiro de locução direto, sem marcações de cena ou direções de câmera (apenas o texto a ser lido). "
                    f"Idioma: {language_code}. Ideia: {idea_input}"
                )
                
                response = client.generate(model=model_name, prompt=prompt)
                st.session_state.generated_script = response['response'].strip()
                st.success("Roteiro gerado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao conectar com Ollama: {e}")

# Etapa 2: Gerar Vídeo a partir do Roteiro
if st.session_state.generated_script:
    script_text = st.text_area("Roteiro Gerado (Edite se necessário):", value=st.session_state.generated_script, height=150)
    
    if st.button("2. Gerar Vídeo Final", type="primary"):
        with st.spinner("Gerando áudio com Kokoro TTS..."):
            try:
                # Carregar o modelo do Kokoro
                kokoro = Kokoro("kokoro-v0_7.onnx", "voices.json")
                samples, sample_rate = kokoro.create(
                    script_text, 
                    voice=voice_name, 
                    speed=1.0, 
                    lang=language_code
                )
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
                    audio_path = tmp_audio.name
                    sf.write(audio_path, samples, sample_rate)

                # Renderizar vídeo
                with st.spinner("Renderizando vídeo com MoviePy..."):
                    audio_clip = AudioFileClip(audio_path)
                    duration = audio_clip.duration + 0.4
                    
                    txt_clip = TextClip(
                        script_text,
                        fontsize=fontsize,
                        color=text_color,
                        bg_color=bg_color,
                        size=(1080, 1920),
                        method='caption'
                    ).set_duration(duration)
                    
                    video_clip = txt_clip.set_audio(audio_clip)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
                        output_video_path = tmp_video.name
                    
                    video_clip.write_videofile(
                        output_video_path,
                        fps=24,
                        codec="libx264",
                        audio_codec="aac"
                    )

                    audio_clip.close()
                    video_clip.close()

                st.success("Vídeo concluído!")
                st.video(output_video_path)

                with open(output_video_path, "rb") as file:
                    st.download_button(
                        label="📥 Baixar Vídeo (.mp4)",
                        data=file,
                        file_name="video_gerado.mp4",
                        mime="video/mp4"
                    )

            except Exception as e:
                st.error(f"Erro ao processar áudio/vídeo: {e}")
