from __future__ import annotations

import base64
import re
from pathlib import Path
from urllib.request import Request, urlopen

ROOT_DIR = Path(__file__).resolve().parent.parent
PHOTO_CACHE_DIR = ROOT_DIR / "data" / "photos"


def extract_drive_file_id(value: str | None) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None

    if "drive.google.com" not in text and "docs.google.com" not in text:
        return text

    patterns = [
        r"/file/d/([A-Za-z0-9_-]+)",
        r"[?&]id=([A-Za-z0-9_-]+)",
        r"/d/([A-Za-z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def _cache_paths(cache_key: str) -> tuple[Path, Path]:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", cache_key).strip("_") or "photo"
    PHOTO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return PHOTO_CACHE_DIR / f"{safe}.bin", PHOTO_CACHE_DIR / f"{safe}.mime"


def _as_data_url(content: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _read_cache(cache_key: str) -> str | None:
    data_path, mime_path = _cache_paths(cache_key)
    if not data_path.exists() or not mime_path.exists():
        return None
    try:
        content = data_path.read_bytes()
        mime_type = mime_path.read_text(encoding="utf-8").strip() or "image/jpeg"
        if content:
            return _as_data_url(content, mime_type)
    except OSError:
        return None
    return None


def _write_cache(cache_key: str, content: bytes, mime_type: str) -> None:
    data_path, mime_path = _cache_paths(cache_key)
    data_path.write_bytes(content)
    mime_path.write_text(mime_type, encoding="utf-8")


def get_drive_photo_data_url(
    drive_reference: str | None,
    cache_key: str,
    force_refresh: bool = False,
) -> dict:
    if not force_refresh:
        cached = _read_cache(cache_key)
        if cached:
            return {"ok": True, "data_url": cached, "cached": True}

    file_id = extract_drive_file_id(drive_reference)
    if not file_id:
        return {"ok": False, "message": "No Drive photo is assigned."}

    sources = [
        f"https://drive.google.com/thumbnail?id={file_id}&sz=w1200",
        f"https://lh3.googleusercontent.com/d/{file_id}=w1200",
        f"https://drive.google.com/uc?export=download&id={file_id}",
    ]

    last_error = "Could not download Drive photo."
    for url in sources:
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 NBP-Personnel-Lookup",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                },
            )
            with urlopen(request, timeout=20) as response:
                content = response.read()
                mime_type = (response.headers.get_content_type() or "").lower()

            if not content or not mime_type.startswith("image/"):
                last_error = f"Drive returned {mime_type or 'non-image content'}."
                continue

            _write_cache(cache_key, content, mime_type)
            return {
                "ok": True,
                "data_url": _as_data_url(content, mime_type),
                "cached": False,
            }
        except Exception as exc:
            last_error = str(exc)

    cached = _read_cache(cache_key)
    if cached:
        return {"ok": True, "data_url": cached, "cached": True, "stale": True}

    return {"ok": False, "message": last_error}
