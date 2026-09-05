"""
TTS leve via Microsoft Edge TTS (pacote `edge-tts`) — SEM PyTorch, sem
download de modelo, ideal pro plano grátis do Streamlit Cloud (pouca RAM).
Usa as mesmas vozes neurais gratuitas do recurso "Ler em voz alta" do
navegador Edge, chamando o serviço da Microsoft pela internet (sem precisar
de chave de API).

Troca feita a partir do Kokoro-82M: o Kokoro carrega PyTorch e baixa pesos
de rede neural na primeira chamada, o que estourava a memória (~1GB) do
plano grátis do Streamlit Community Cloud e derrubava o app (erro de saúde
/ "connection reset by peer" nos logs). O Edge TTS não usa PyTorch nem
modelo local — só faz uma chamada de rede — e continua com vozes naturais.

IMPORTANTE: precisa de internet (o Streamlit Cloud tem). Se rodar 100%
offline, ou se o serviço da Microsoft falhar, cai automaticamente pro
espeak-ng (sempre funciona, mas soa mais robótico).

pip install edge-tts
Precisa também do pacote de sistema `ffmpeg` (converter mp3 -> wav) e
`espeak-ng` (fallback) — ambos já estão no packages.txt.
"""

import os
import asyncio
import subprocess
import edge_tts

LANGUAGES = {
    "Português (BR)": "pt",
    "English": "en",
    "Español": "es",
    "Deutsch": "de",
}

# Vozes neurais gratuitas do Edge TTS, uma padrão por idioma.
_DEFAULT_VOICE = {
    "pt": "pt-BR-FranciscaNeural",
    "en": "en-US-AriaNeural",
    "es": "es-ES-ElviraNeural",
    "de": "de-DE-KatjaNeural",
}

# Código de idioma esperado pelo espeak-ng (fallback offline).
_ESPEAK_LANG = {"pt": "pt-br", "en": "en", "es": "es", "de": "de"}


def synthesize(text: str, out_path: str, reference_voice_path: str | None = None,
               language_id: str = "pt", voice: str | None = None, **_ignored) -> str:
    """
    Gera um arquivo de áudio .wav a partir do texto.

    reference_voice_path: ignorado (mantido só por compatibilidade) — o
                           Edge TTS não clona voz a partir de áudio.
    language_id: "pt", "en", "es" ou "de".
    voice: nome de uma voz do Edge TTS (ex: "pt-BR-AntonioNeural",
           "en-US-GuyNeural"...). Se None, usa uma voz padrão do idioma.
    """
    voice_name = voice or _DEFAULT_VOICE.get(language_id, "en-US-AriaNeural")
    tmp_mp3 = out_path + ".tmp.mp3"
    try:
        asyncio.run(_edge_tts_save(text, tmp_mp3, voice_name))
        _convert_to_wav(tmp_mp3, out_path)
        return out_path
    except Exception as e:
        print(f"[tts_engine] Erro ao gerar áudio com Edge TTS: {e}")
        return _synthesize_espeak(text, out_path, language_id)
    finally:
        if os.path.exists(tmp_mp3):
            os.remove(tmp_mp3)


async def _edge_tts_save(text: str, out_path: str, voice: str, timeout: float = 20.0):
    communicate = edge_tts.Communicate(text, voice)
    await asyncio.wait_for(communicate.save(out_path), timeout=timeout)


def _convert_to_wav(src_path: str, out_path: str):
    """Edge TTS entrega mp3 — o resto do pipeline (moviepy, cálculo de
    duração) espera .wav, então converte na hora com ffmpeg."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", src_path, "-ar", "24000", "-ac", "1", out_path],
        check=True, capture_output=True,
    )


def _synthesize_espeak(text: str, out_path: str, language_id: str = "pt") -> str:
    """Fallback offline: sempre funciona (não depende de internet nem da
    Microsoft), mas soa mais robótico que o Edge TTS."""
    espeak_lang = _ESPEAK_LANG.get(language_id, "en")
    try:
        subprocess.run(
            ["espeak-ng", "-v", espeak_lang, "-w", out_path, text],
            check=True, encoding="utf-8"
        )
        return out_path
    except Exception as e:
        print(f"[tts_engine] Erro ao gerar áudio com espeak-ng: {e}")
        raise
