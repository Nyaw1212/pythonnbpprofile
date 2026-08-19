from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

from openpyxl import Workbook

from .db import DB_PATH, connect, initialize
from .import_excel import EXPECTED_HEADERS, INSERT_SQL, normalize, normalize_badge, normalize_drive_file_id

SPREADSHEET_ID = "1SMbMfK-2T5LroHcycjUbf__pwAYQ6wtUHQocl2EoxmU"
SHEET_GID = "0"
ROOT_DIR = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = ROOT_DIR / "NBPattendance.xlsx"


def _download_csv() -> list[list[str]]:
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_GID}"
    request = Request(url, headers={"User-Agent": "NBPPersonnelLookup/1.0"})
    with urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text)))


def _write_snapshot(rows: list[list[str]], path: Path = SNAPSHOT_PATH) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "LIST"
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def sync_google_sheet(db_path: Path | str = DB_PATH) -> dict:
    rows = _download_csv()
    if not rows:
        raise ValueError("Google Sheet returned no data.")

    headers = [str(value).strip().upper() for value in rows[0]]
    column_map = {index: EXPECTED_HEADERS[header] for index, header in enumerate(headers) if header in EXPECTED_HEADERS}
    missing = sorted({"badge_number", "last_name", "first_name"} - set(column_map.values()))
    if missing:
        raise ValueError(f"Google Sheet is missing required columns: {', '.join(missing)}")

    initialize(db_path)
    imported = 0
    with connect(db_path) as connection:
        for source_order, values in enumerate(rows[1:], start=1):
            record = {field: None for field in EXPECTED_HEADERS.values()}
            for index, field in column_map.items():
                if index >= len(values):
                    continue
                value = values[index]
                if field == "badge_number":
                    record[field] = normalize_badge(value)
                elif field == "drive_file_id":
                    record[field] = normalize_drive_file_id(value)
                else:
                    record[field] = normalize(value)
            if not record["badge_number"]:
                continue
            record["source_order"] = source_order
            connection.execute(INSERT_SQL, record)
            imported += 1

    _write_snapshot(rows)
    return {"ok": True, "count": imported, "synced_at": datetime.now().isoformat(timespec="seconds"), "snapshot": str(SNAPSHOT_PATH)}
