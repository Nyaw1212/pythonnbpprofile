from __future__ import annotations

import re
import sys
from pathlib import Path

import webview

from src.db import DB_PATH
from src.personnel_service import PersonnelService
from src.profile_pdf import generate_profile_pdf

ROOT_DIR = Path(__file__).resolve().parent
UI_FILE = ROOT_DIR / "ui" / "index.html"


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip()
    return cleaned or "Personnel Profile"


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

    def save_profile_pdf(self, badge_number):
        person = self.personnel.get_profile(str(badge_number))
        if not person:
            return {"ok": False, "message": "Personnel record not found."}

        name_parts = [person.get("last_name"), person.get("first_name"), person.get("middle_name")]
        name = " ".join(str(part).strip() for part in name_parts if part and str(part).strip())
        default_name = _safe_filename(f"Personnel Profile - {name or badge_number}") + ".pdf"

        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = filedialog.asksaveasfilename(
                parent=root,
                title="Save Personnel Profile PDF",
                defaultextension=".pdf",
                initialfile=default_name,
                filetypes=[("PDF document", "*.pdf")],
            )
            root.destroy()
        except Exception as exc:
            return {"ok": False, "message": f"Could not open the Save As dialog: {exc}"}

        if not path:
            return {"ok": False, "cancelled": True, "message": "Save cancelled."}

        try:
            output = generate_profile_pdf(person, Path(path))
            return {"ok": True, "path": str(output), "message": f"Saved to {output}"}
        except Exception as exc:
            return {"ok": False, "message": f"Could not create PDF: {exc}"}


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
