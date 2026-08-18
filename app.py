from __future__ import annotations

import sys
from pathlib import Path

import webview

from src.db import DB_PATH
from src.personnel_service import PersonnelService

ROOT_DIR = Path(__file__).resolve().parent
UI_FILE = ROOT_DIR / "ui" / "index.html"


class Api:
    def __init__(self):
        self.personnel = PersonnelService(DB_PATH)

    def search_personnel(self, query="", camp="", office="", rank="", limit=100):
        return self.personnel.search(query, camp, office, rank, limit)

    def search_personnel_paged(self, query="", camp="", office="", rank="", page=1, page_size=25):
        return self.personnel.search_paged(query, camp, office, rank, page, page_size)

    def get_profile(self, badge_number):
        return self.personnel.get_profile(str(badge_number))

    def get_filters(self):
        return self.personnel.filters()

    def get_stats(self):
        return self.personnel.stats()


if __name__ == "__main__":
    if not UI_FILE.exists():
        raise FileNotFoundError(f"UI file not found: {UI_FILE}")

    api = Api()
    webview.create_window(
        "NBP Personnel Lookup",
        UI_FILE.as_uri(),
        js_api=api,
        width=1280,
        height=800,
        min_size=(900, 600),
    )
    webview.start(debug="--debug" in sys.argv)
