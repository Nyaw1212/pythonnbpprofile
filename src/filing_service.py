from __future__ import annotations

import base64
import re
from datetime import datetime
from pathlib import Path

LOCAL_ROOT = Path.home() / "Documents" / "NBP Personnel Files"


def _safe_component(value: str) -> str:
    text = re.sub(r'[<>:"/\\|?*]+', "-", str(value or "").strip())
    text = re.sub(r"\s+", " ", text).strip(" .-")
    return text or "Unknown"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}_{counter:02d}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def save_local_filing_copy(
    *,
    data_base64: str,
    filename: str,
    rank: str,
    full_name: str,
    document_type: str = "LEAVE",
    filed_at: datetime | None = None,
) -> dict:
    filed_at = filed_at or datetime.now()
    filename = _safe_component(filename)
    person_folder = _safe_component(f"{rank} {full_name}")
    year = str(filed_at.year)
    month = filed_at.strftime("%m - %B").upper()
    category = _safe_component(document_type).upper()

    destination_dir = LOCAL_ROOT / person_folder / category / year / month
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = _unique_path(destination_dir / filename)

    try:
        payload = base64.b64decode(data_base64, validate=True)
    except Exception as exc:
        return {"ok": False, "message": f"Could not read uploaded file: {exc}"}

    if not payload:
        return {"ok": False, "message": "The uploaded file is empty."}

    destination.write_bytes(payload)
    return {
        "ok": True,
        "path": str(destination),
        "filename": destination.name,
        "folder": str(destination_dir),
        "message": f"Local copy saved to {destination}",
    }
