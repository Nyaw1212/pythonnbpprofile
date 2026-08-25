from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import webview

from src.db import DB_PATH
from src.drive_filing_service import upload_filed_document
from src.filing_service import save_local_filing_copy
from src.personnel_service import PersonnelService
from src.runtime_paths import resource_root

UI_FILE = resource_root() / "filing_ui" / "index.html"


class FilingApi:
    def __init__(self):
        self.personnel = PersonnelService(DB_PATH)

    def search_personnel(self, query="", limit=100):
        return self.personnel.search(query=query, limit=limit)

    def get_profile(self, badge_number):
        return self.personnel.get_profile(str(badge_number))

    def file_document(self, data_base64, filename, rank, full_name, document_type="LEAVE"):
        filed_at = datetime.now()
        local = save_local_filing_copy(
            data_base64=data_base64,
            filename=filename,
            rank=rank,
            full_name=full_name,
            document_type=document_type,
            filed_at=filed_at,
        )
        if not local.get("ok"):
            return local

        person_folder = f"{rank} {full_name}".strip()
        drive = upload_filed_document(
            local_path=local["path"],
            person_folder=person_folder,
            category=document_type,
            year=str(filed_at.year),
            month=filed_at.strftime("%m - %B").upper(),
        )

        if not drive.get("ok"):
            return {
                "ok": False,
                "local_saved": True,
                "local": local,
                "drive": drive,
                "message": f"Local copy saved, but Drive upload failed: {drive.get('message', 'Unknown error')}",
            }

        return {
            "ok": True,
            "local_saved": True,
            "drive_uploaded": True,
            "local": local,
            "drive": drive,
            "message": "Document filed locally and uploaded to Google Drive.",
        }


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
