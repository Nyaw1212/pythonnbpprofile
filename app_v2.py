from __future__ import annotations

import sys
from pathlib import Path

import webview

from app import Api


def _resource_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


ROOT_DIR = _resource_root()
UI_FILE = ROOT_DIR / "ui_v2" / "index.html"


if __name__ == "__main__":
    if not UI_FILE.exists():
        raise FileNotFoundError(f"V2 UI file not found: {UI_FILE}")

    api = Api()
    webview.create_window(
        "NBP Personnel Lookup V2",
        UI_FILE.as_uri(),
        js_api=api,
        width=1280,
        height=820,
        min_size=(900, 620),
    )
    webview.start(debug="--debug" in sys.argv)
