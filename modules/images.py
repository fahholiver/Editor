"""
Busca e download de mídia (vídeo de estoque, com foto como reserva) pra usar
como fundo das cenas do vídeo VS.

Ordem de tentativa pra cada busca:
1. Pexels Videos  (precisa de chave gratuita — https://www.pexels.com/api/)
2. Pexels Photos  (mesma chave; vira um clipe com efeito Ken Burns no vídeo)
3. DuckDuckGo Images (sem precisar de chave nenhuma — pip install ddgs)

Assim o app funciona mesmo sem chave da Pexels (com qualidade menor), e fica
melhor e mais dinâmico com a chave configurada.

pip install requests pillow ddgs
"""

import os
import requests
from PIL import Image
from io import BytesIO

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_URL = "https://api.pexels.com/v1/search"


def _pexels_headers(api_key: str) -> dict:
    return {"Authorization": api_key}


def download_file(url: str, out_path: str, timeout: int = 30) -> bool:
    """Baixa um arquivo binário (usado pros vídeos)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                f.write(chunk)
        return os.path.getsize(out_path) > 1024
    except Exception as e:
        print(f"[images] Falha ao baixar arquivo {url}: {e}")
        return False


def download_image(url: str, out_path: str, min_size: int = 300) -> bool:
    """Baixa e valida uma imagem. Retorna True se deu certo."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        if min(img.size) < min_size:
            return False
        img.save(out_path, "JPEG", quality=90)
        return True
    except Exception as e:
        print(f"[images] Falha ao baixar imagem {url}: {e}")
        return False


# ---------------------------------------------------------------------------
# Pexels Videos
# ---------------------------------------------------------------------------

def _pick_video_file(video_item: dict, max_width: int = 1280) -> str | None:
    """Escolhe o arquivo .mp4 de melhor qualidade dentro de um limite de
    largura (pra não baixar vídeos gigantes e deixar a renderização lenta)."""
    files = [f for f in video_item.get("video_files", []) if f.get("file_type") == "video/mp4"]
    if not files:
        return None
    within_budget = [f for f in files if f.get("width") and f["width"] <= max_width]
    candidates = within_budget or files
    candidates.sort(key=lambda f: f.get("width", 0), reverse=True)
    return candidates[0].get("link")


def search_pexels_videos(query: str, api_key: str, per_page: int = 6,
                          orientation: str = "portrait") -> list[dict]:
    resp = requests.get(
        PEXELS_VIDEO_URL, headers=_pexels_headers(api_key),
        params={"query": query, "per_page": per_page, "orientation": orientation},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("videos", [])


def fetch_video_for_item(query: str, out_path: str, api_key: str,
                          min_duration: int = 2, max_duration: int = 25,
                          fallback_query: str | None = None) -> bool:
    """Busca e baixa um clipe de vídeo de estoque da Pexels. Retorna True se
    conseguiu salvar um arquivo em out_path."""
    if not api_key:
        return False

    def _try(q: str, orientation: str) -> bool:
        try:
            videos = search_pexels_videos(q, api_key, orientation=orientation)
        except Exception as e:
            print(f"[images] Pexels video search falhou p/ '{q}': {e}")
            return False
        # Prioriza vídeos com duração dentro da faixa desejada, mas usa
        # qualquer resultado se nenhum bater exatamente com a faixa.
        in_range = [v for v in videos if min_duration <= v.get("duration", 0) <= max_duration]
        for v in (in_range or videos):
            url = _pick_video_file(v)
            if url and download_file(url, out_path):
                return True
        return False

    if _try(query, "portrait"):
        return True
    # Muitos clipes bons só existem na horizontal — tenta de novo sem
    # restringir orientação (o video_builder faz o "cover crop" depois).
    if _try(query, "landscape"):
        return True
    if fallback_query and fallback_query.strip().lower() != query.strip().lower():
        if _try(fallback_query, "portrait") or _try(fallback_query, "landscape"):
            return True
    return False


# ---------------------------------------------------------------------------
# Pexels Photos (fallback — vira clipe com Ken Burns no video_builder)
# ---------------------------------------------------------------------------

def fetch_photo_for_item(query: str, out_path: str, api_key: str,
                          fallback_query: str | None = None) -> bool:
    if not api_key:
        return False

    def _try(q: str) -> bool:
        try:
            resp = requests.get(
                PEXELS_PHOTO_URL, headers=_pexels_headers(api_key),
                params={"query": q, "per_page": 5, "orientation": "portrait"},
                timeout=15,
            )
            resp.raise_for_status()
            photos = resp.json().get("photos", [])
        except Exception as e:
            print(f"[images] Pexels photo search falhou p/ '{q}': {e}")
            return False
        for p in photos:
            src = p.get("src", {})
            url = src.get("large2x") or src.get("large") or src.get("original")
            if url and download_image(url, out_path):
                return True
        return False

    if _try(query):
        return True
    if fallback_query and fallback_query.strip().lower() != query.strip().lower():
        return _try(fallback_query)
    return False


# ---------------------------------------------------------------------------
# DuckDuckGo Images — última reserva, não precisa de chave nenhuma
# ---------------------------------------------------------------------------

def fetch_image_for_item(query: str, out_path: str, max_attempts: int = 5,
                          fallback_query: str | None = None) -> bool:
    from ddgs import DDGS

    def _try_query(q: str) -> bool:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(q, max_results=max_attempts))
        except Exception as e:
            print(f"[images] DuckDuckGo falhou p/ '{q}': {e}")
            return False
        for r in results:
            url = r.get("image")
            if url and download_image(url, out_path):
                return True
        return False

    if _try_query(query):
        return True
    if fallback_query and fallback_query.strip().lower() != query.strip().lower():
        return _try_query(fallback_query)
    return False


# ---------------------------------------------------------------------------
# Função única usada pelo app: vídeo primeiro, depois foto, depois DuckDuckGo
# ---------------------------------------------------------------------------

def fetch_media_for_item(query: str, out_dir: str, base_name: str,
                          pexels_api_key: str | None = None,
                          fallback_query: str | None = None) -> tuple[str, str] | None:
    """Tenta, em ordem: vídeo Pexels -> foto Pexels -> imagem DuckDuckGo.
    Retorna (tipo, caminho) onde tipo é "video" ou "image", ou None se nada
    funcionou (nesse caso o item deve ser pulado ou usar um termo mais simples)."""
    os.makedirs(out_dir, exist_ok=True)

    if pexels_api_key:
        video_path = os.path.join(out_dir, f"{base_name}.mp4")
        if fetch_video_for_item(query, video_path, pexels_api_key, fallback_query=fallback_query):
            return ("video", video_path)

        image_path = os.path.join(out_dir, f"{base_name}.jpg")
        if fetch_photo_for_item(query, image_path, pexels_api_key, fallback_query=fallback_query):
            return ("image", image_path)

    image_path = os.path.join(out_dir, f"{base_name}.jpg")
    if fetch_image_for_item(query, image_path, fallback_query=fallback_query):
        return ("image", image_path)

    return None
