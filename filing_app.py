from __future__ import annotations

from pathlib import Path
import sys

import webview

from src.db import DB_PATH
from src.filing_service import save_local_filing_copy
from src.personnel_service import PersonnelService

ROOT_DIR = Path(__file__).resolve().parent
UI_FILE = ROOT_DIR / "filing_ui" / "index.html"


class FilingApi:
    def __init__(self):
        self.personnel = PersonnelService(DB_PATH)

    def search_personnel(self, query="", limit=100):
        return self.personnel.search(query=query, limit=limit)

    def get_profile(self, badge_number):
        return self.personnel.get_profile(str(badge_number))

    def save_local_copy(self, data_base64, filename, rank, full_name, document_type="LEAVE"):
        return save_local_filing_copy(
            data_base64=data_base64,
            filename=filename,
            rank=rank,
            full_name=full_name,
            document_type=document_type,
        )


if __name__ == "__main__":
    if not UI_FILE.exists():
        raise FileNotFoundError(f"Filing UI not found: {UI_FILE}")

    webview.create_window(
        "NBP Personnel Filing",
        UI_FILE.as_uri(),
        js_api=FilingApi(),
        width=1280,
        height=800,
        min_size=(960, 620),
    )
    webview.start(debug="--debug" in sys.argv)
