from __future__ import annotations

import re
import sys
from pathlib import Path

import webview

from src.db import DB_PATH
from src.google_sheet_sync import sync_google_sheet
from src.personnel_service import PersonnelService
from src.photo_service import get_drive_photo_data_url
from src.profile_pdf import generate_profile_pdf
from src.profile_photo_upload import upload_profile_photo


def _resource_root() -> Path:
    """Return the directory containing bundled read-only app resources."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


ROOT_DIR = _resource_root()
UI_FILE = ROOT_DIR / "ui" / "index.html"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1SMbMfK-2T5LroHcycjUbf__pwAYQ6wtUHQocl2EoxmU/edit#gid=0"


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip()
    return cleaned or "Personnel Profile"


def _full_name(person: dict) -> str:
    return " ".join(
        str(part).strip()
        for part in (
            person.get("first_name"),
            person.get("middle_name"),
            person.get("last_name"),
            person.get("suffix"),
        )
        if part and str(part).strip()
    )


class Api:
    def __init__(self):
        self.personnel = PersonnelService(DB_PATH)

    def search_personnel(self, query="", camp="", office="", rank="", limit=100):
        return self.personnel.search(query, camp, office, rank, limit)

    def search_personnel_paged(self, query="", camp="", office="", rank="", page=1, page_size=25):
        return self.personnel.search_paged(query, camp, office, rank, page, page_size)

    def get_profile(self, badge_number):
        return self.personnel.get_profile(str(badge_number))

    def get_profile_photo(self, badge_number):
        person = self.personnel.get_profile(str(badge_number))
        if not person:
            return {"ok": False, "message": "Personnel record not found."}
        return get_drive_photo_data_url(
            person.get("drive_file_id"),
            cache_key=str(person.get("badge_number") or badge_number),
        )

    def add_profile_photo(self, badge_number):
        person = self.personnel.get_profile(str(badge_number))
        if not person:
            return {"ok": False, "message": "Personnel record not found."}

        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = filedialog.askopenfilename(
                parent=root,
                title="Select Personnel Photo",
                filetypes=[
                    ("Image files", "*.jpg *.jpeg *.png *.webp"),
                    ("JPEG", "*.jpg *.jpeg"),
                    ("PNG", "*.png"),
                    ("WebP", "*.webp"),
                ],
            )
            root.destroy()
        except Exception as exc:
            return {"ok": False, "message": f"Could not open photo picker: {exc}"}

        if not path:
            return {"ok": False, "cancelled": True, "message": "Photo selection cancelled."}

        try:
            result = upload_profile_photo(
                image_path=path,
                badge_number=str(person.get("badge_number") or badge_number),
                rank=str(person.get("rank") or ""),
                full_name=_full_name(person),
                source_order=person.get("source_order"),
            )
            self.personnel.update_drive_file_id(str(badge_number), result["file_id"])
            return {
                "ok": True,
                **result,
                "message": "Photo uploaded to Drive and DRIVEFILEID updated in Google Sheets.",
            }
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    def get_filters(self):
        return self.personnel.filters()

    def get_stats(self):
        return self.personnel.stats()

    def sync_google_sheet(self):
        try:
            return sync_google_sheet(DB_PATH)
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    def open_google_sheet(self):
        try:
            import webbrowser

            opened = webbrowser.open(SHEET_URL, new=2)
            return {"ok": bool(opened), "url": SHEET_URL}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

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
