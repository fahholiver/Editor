"""
Monta o vídeo final estilo "VS" (batalha):

    CAPA (split-screen item1/item2 + "VS" + pergunta gancho)
      -> ROUND 1 (cena item1 em tela cheia, depois cena item2 em tela cheia)
      -> ROUND 2 (idem)
      -> ... (N rounds)
      -> ENCERRAMENTO (split-screen item1/item2 + call-to-action)

Cada cena usa um clipe de vídeo de estoque (ou uma foto com efeito Ken Burns,
se não achou vídeo) como fundo, com zoom lento contínuo pra dar sensação de
movimento/edição profissional, mais textos sobrepostos (nome do item,
"tag" de destaque tipo legenda de ênfase). NÃO renderizamos a legenda da
fala palavra por palavra — o TikTok já gera isso automaticamente ao postar.

pip install moviepy pillow numpy
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    ImageClip, VideoFileClip, CompositeVideoClip, AudioFileClip,
    CompositeAudioClip, concatenate_videoclips, ColorClip,
)
from moviepy import vfx, afx

# Resolução vertical do vídeo final. 1080x1920 é o padrão do TikTok/Reels.
# Se a renderização ficar muito lenta/pesada na sua máquina (ou num servidor
# gratuito), reduza pra (720, 1280) — a queda de qualidade é pequena.
W, H = 1080, 1920

FADE = 0.35          # duração do crossfade entre cenas (segundos)
ZOOM_END = 1.09       # zoom lento contínuo aplicado no fundo de cada cena
SCENE_PADDING = 0.45  # folga extra no fim de cada cena, além da duração do áudio

# ---------------------------------------------------------------------------
# Fonte com suporte a acentos (á, é, ã, ç...) — mesma estratégia do projeto
# original: prioriza a fonte embutida em assets/fonts/, cai pro sistema
# operacional só se ela não existir.
# ---------------------------------------------------------------------------
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_BUNDLED_FONT_BOLD = os.path.join(_MODULE_DIR, "..", "assets", "fonts", "DejaVuSans-Bold.ttf")
_BUNDLED_FONT_REGULAR = os.path.join(_MODULE_DIR, "..", "assets", "fonts", "DejaVuSans.ttf")

_FONT_CANDIDATES = [
    _BUNDLED_FONT_BOLD,
    _BUNDLED_FONT_REGULAR,
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS
    "C:\\Windows\\Fonts\\arialbd.ttf",                      # Windows
]
_FONT_FOUND = None


def _resolve_font(font: str | None) -> str | None:
    global _FONT_FOUND
    if font:
        return font
    if _FONT_FOUND:
        return _FONT_FOUND
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            _FONT_FOUND = path
            return path
    print("[video_builder] ⚠️ Nenhuma fonte encontrada — verifique assets/fonts/.")
    return None


def _load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont:
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
               max_width: int, stroke_width: int = 0) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font, stroke_width=stroke_width)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _render_pill_text(text: str, font_path: str | None, font_size: int = 44,
                       max_width: int = 700, fg=(255, 255, 255, 255),
                       bg=(0, 0, 0, 190), pad_x: int = 30, pad_y: int = 16,
                       radius: int = 26) -> np.ndarray:
    """Texto (uma ou mais linhas) sobre uma caixinha arredondada semi-
    transparente — usado pra nomes dos itens, título de gancho e encerramento."""
    font = _load_font(font_path, font_size)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines = _wrap_text(probe, text, font, max_width - pad_x * 2)

    line_dims = [probe.textbbox((0, 0), line, font=font) for line in lines]
    line_w = [b[2] - b[0] for b in line_dims]
    line_h = [b[3] - b[1] for b in line_dims]
    spacing = int(font_size * 0.3)

    box_w = max(line_w, default=0) + pad_x * 2
    box_h = sum(line_h) + spacing * max(0, len(lines) - 1) + pad_y * 2

    img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, box_w - 1, box_h - 1], radius=radius, fill=bg)

    y = pad_y
    for line, lw, lh in zip(lines, line_w, line_h):
        x = (box_w - lw) // 2
        draw.text((x, y), line, font=font, fill=fg)
        y += lh + spacing

    return np.array(img)


def _render_stroke_text(text: str, font_path: str | None, font_size: int = 70,
                         max_width: int = 900, fill=(255, 214, 10, 255),
                         stroke=(0, 0, 0, 255), stroke_width: int = 8) -> np.ndarray:
    """Texto grande com contorno grosso, sem caixinha de fundo — usado pro
    "VS" e pras tags de destaque (tipo legenda de ênfase curta)."""
    text = text.upper()
    font = _load_font(font_path, font_size)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines = _wrap_text(probe, text, font, max_width, stroke_width=stroke_width)

    line_dims = [probe.textbbox((0, 0), line, font=font, stroke_width=stroke_width) for line in lines]
    line_w = [b[2] - b[0] for b in line_dims]
    line_h = [b[3] - b[1] for b in line_dims]
    spacing = int(font_size * 0.25)
    pad = stroke_width + 6

    box_w = max(line_w, default=0) + pad * 2
    box_h = sum(line_h) + spacing * max(0, len(lines) - 1) + pad * 2

    img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    y = pad
    for line, lw, lh in zip(lines, line_w, line_h):
        x = (box_w - lw) // 2
        draw.text((x, y), line, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke)
        y += lh + spacing

    return np.array(img)


# ---------------------------------------------------------------------------
# Preparação do fundo de cada cena (vídeo ou foto -> clipe com zoom lento)
# ---------------------------------------------------------------------------

def _cover_resize(clip, w: int, h: int):
    """Redimensiona + corta (crop central) pra preencher exatamente w x h
    sem distorcer a proporção original (efeito 'object-fit: cover')."""
    cw, ch = clip.size
    scale = max(w / cw, h / ch)
    clip = clip.resized(scale)
    clip = clip.cropped(x_center=clip.w / 2, y_center=clip.h / 2, width=w, height=h)
    return clip


def _slow_zoom(clip, duration: float, zoom_end: float = ZOOM_END):
    """Zoom lento e contínuo (efeito Ken Burns), começando em 1.0x e
    terminando em zoom_end, pra dar sensação de câmera viva mesmo em fotos."""
    zoomed = clip.resized(lambda t: 1 + (zoom_end - 1) * min(t / max(duration, 0.01), 1))
    zoomed = zoomed.with_position("center")
    return CompositeVideoClip([zoomed], size=clip.size).with_duration(duration)


def _prepare_bg(media: tuple[str, str] | None, w: int, h: int, duration: float):
    """media = (tipo, caminho) vindo de fetch_media_for_item(). Retorna um
    clipe de fundo (sem áudio) já cortado pra w x h, com zoom lento."""
    if media is None:
        return ColorClip((w, h), color=(25, 25, 30)).with_duration(duration)

    kind, path = media
    try:
        if kind == "video":
            clip = VideoFileClip(path).without_audio()
            if clip.duration < duration:
                clip = clip.with_effects([vfx.Loop(duration=duration)])
            else:
                clip = clip.subclipped(0, duration)
            clip = _cover_resize(clip, w, h)
        else:
            clip = ImageClip(path).with_duration(duration)
            clip = _cover_resize(clip, w, h)
        return _slow_zoom(clip, duration)
    except Exception as e:
        print(f"[video_builder] Erro ao preparar mídia '{path}' ({e}), usando fundo neutro.")
        return ColorClip((w, h), color=(25, 25, 30)).with_duration(duration)


def _darken_overlay(w: int, h: int, duration: float, opacity: float = 0.18):
    return ColorClip((w, h), color=(0, 0, 0)).with_opacity(opacity).with_duration(duration)


def _bottom_gradient(w: int, h: int, duration: float, band_frac: float = 0.42):
    """Faixa escura com gradiente na parte de baixo, pra legenda/tag ficar
    legível em cima de qualquer vídeo de fundo."""
    band_h = int(h * band_frac)
    alpha = np.linspace(0, 200, band_h, dtype=np.uint8)
    alpha = np.tile(alpha.reshape(band_h, 1), (1, w))
    rgb = np.zeros((band_h, w, 3), dtype=np.uint8)
    rgba = np.dstack([rgb, alpha])
    img = ImageClip(rgba).with_position((0, h - band_h)).with_duration(duration)
    return img


# ---------------------------------------------------------------------------
# Cenas
# ---------------------------------------------------------------------------

def build_cover_scene(script: dict, media1, media2, audio_path: str, font: str = None):
    """Cena de capa: item1 em cima, item2 embaixo, 'VS' no meio, título
    gancho embaixo. Dura o tempo do áudio narrando o hook_title."""
    font = _resolve_font(font)
    audio = AudioFileClip(audio_path)
    duration = audio.duration + SCENE_PADDING
    half_h = H // 2

    top = _prepare_bg(media1, W, half_h, duration).with_position((0, 0))
    bottom = _prepare_bg(media2, W, half_h, duration).with_position((0, half_h))
    overlay = _darken_overlay(W, H, duration, opacity=0.22)

    vs_img = _render_stroke_text("VS", font, font_size=int(H * 0.09), max_width=int(W * 0.6),
                                  fill=(255, 45, 45, 255), stroke=(255, 255, 255, 255), stroke_width=10)
    vs_clip = ImageClip(vs_img).with_position("center").with_duration(duration)

    # Nomes ficam colados na linha divisória central (perto do "VS"), pra
    # não disputar espaço com o título, que fica fixo no topo.
    name1_img = _render_pill_text(script["item1_name"], font, font_size=int(H * 0.028),
                                   max_width=int(W * 0.6))
    name1_clip = ImageClip(name1_img).with_position(
        ("center", half_h - name1_img.shape[0] - int(H * 0.09))
    ).with_duration(duration)

    name2_img = _render_pill_text(script["item2_name"], font, font_size=int(H * 0.028),
                                   max_width=int(W * 0.6))
    name2_clip = ImageClip(name2_img).with_position(
        ("center", half_h + int(H * 0.09))
    ).with_duration(duration)

    title_img = _render_pill_text(script["hook_title"], font, font_size=int(H * 0.032),
                                   max_width=int(W * 0.88), bg=(0, 0, 0, 215))
    title_clip = ImageClip(title_img).with_position(("center", int(H * 0.04))).with_duration(duration)

    scene = CompositeVideoClip(
        [top, bottom, overlay, vs_clip, name1_clip, name2_clip, title_clip], size=(W, H)
    ).with_audio(audio)
    return scene


def build_round_scene(item_name: str, media, tag_text: str, audio_path: str,
                       accent_color=(255, 214, 10, 255), font: str = None):
    """Cena de um lado do round: mídia em tela cheia, nome do item no topo,
    tag de destaque na parte de baixo. Dura o tempo do áudio da fala."""
    font = _resolve_font(font)
    audio = AudioFileClip(audio_path)
    duration = audio.duration + SCENE_PADDING

    bg = _prepare_bg(media, W, H, duration)
    gradient = _bottom_gradient(W, H, duration)

    name_img = _render_pill_text(item_name, font, font_size=int(H * 0.032), max_width=int(W * 0.8))
    name_clip = ImageClip(name_img).with_position(("center", int(H * 0.05))).with_duration(duration)

    layers = [bg, gradient, name_clip]

    if tag_text and tag_text.strip():
        tag_img = _render_stroke_text(tag_text, font, font_size=int(H * 0.045), max_width=int(W * 0.85),
                                       fill=accent_color, stroke=(0, 0, 0, 255), stroke_width=7)
        tag_clip = ImageClip(tag_img).with_position(("center", int(H * 0.74))).with_duration(duration)
        layers.append(tag_clip)

    scene = CompositeVideoClip(layers, size=(W, H)).with_audio(audio)
    return scene


def build_outro_scene(script: dict, media1, media2, audio_path: str, font: str = None):
    """Cena de encerramento: item1 à esquerda, item2 à direita, texto de
    call-to-action no centro. Dura o tempo do áudio do outro_text."""
    font = _resolve_font(font)
    audio = AudioFileClip(audio_path)
    duration = audio.duration + SCENE_PADDING
    half_w = W // 2

    left = _prepare_bg(media1, half_w, H, duration).with_position((0, 0))
    right = _prepare_bg(media2, half_w, H, duration).with_position((half_w, 0))
    overlay = _darken_overlay(W, H, duration, opacity=0.35)

    outro_text = script.get("outro_text") or ""
    outro_img = _render_pill_text(outro_text, font, font_size=int(H * 0.036),
                                   max_width=int(W * 0.85), bg=(0, 0, 0, 220))
    outro_clip = ImageClip(outro_img).with_position("center").with_duration(duration)

    scene = CompositeVideoClip([left, right, overlay, outro_clip], size=(W, H)).with_audio(audio)
    return scene


# ---------------------------------------------------------------------------
# Montagem final
# ---------------------------------------------------------------------------

def _with_crossfades(clips: list, fade: float = FADE):
    if len(clips) < 2:
        return concatenate_videoclips(clips, method="compose")
    out = [clips[0]]
    for c in clips[1:]:
        out.append(c.with_effects([vfx.CrossFadeIn(fade)]))
    return concatenate_videoclips(out, method="compose", padding=-fade)


def _mix_background_music(video, music_path: str | None, volume: float = 0.12):
    if not music_path or not os.path.exists(music_path):
        return video
    try:
        music = AudioFileClip(music_path).with_effects([
            afx.AudioLoop(duration=video.duration),
            afx.MultiplyVolume(volume),
        ])
        mixed = CompositeAudioClip([video.audio, music])
        return video.with_audio(mixed)
    except Exception as e:
        print(f"[video_builder] Não consegui adicionar música de fundo ({e}), seguindo sem ela.")
        return video


def build_vs_video(scenes: list, out_path: str, music_path: str | None = None,
                    music_volume: float = 0.12, fps: int = 30) -> str:
    """scenes: lista de clipes já prontos (capa, rounds, encerramento), na
    ordem em que devem aparecer no vídeo final."""
    final = _with_crossfades(scenes, fade=FADE)
    final = _mix_background_music(final, music_path, music_volume)
    final.write_videofile(
        out_path, fps=fps, codec="libx264", audio_codec="aac",
        preset="medium", threads=4,
    )
    return out_path
