from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from .db import DB_PATH, connect, initialize

EXPECTED_HEADERS = {
    "RECORD ID": "record_id",
    "BADGE NUMBER": "badge_number",
    "RANK": "rank",
    "LAST NAME": "last_name",
    "FIRST NAME": "first_name",
    "MIDDLE NAME": "middle_name",
    "SUFFIX": "suffix",
    "CAMP": "camp",
    "OFFICE": "office",
    "GENDER": "gender",
    "CLASSIFICATION": "classification",
    "TYPE": "personnel_type",
    "DUPLICATE STATUS": "duplicate_status",
    "DUPLICATE TYPE": "duplicate_type",
    "CREATED AT": "created_at",
    "UPDATED AT": "updated_at",
}

INSERT_SQL = """
INSERT INTO personnel (
    record_id, badge_number, rank, last_name, first_name, middle_name,
    suffix, camp, office, gender, classification, personnel_type,
    duplicate_status, duplicate_type, created_at, updated_at
) VALUES (
    :record_id, :badge_number, :rank, :last_name, :first_name, :middle_name,
    :suffix, :camp, :office, :gender, :classification, :personnel_type,
    :duplicate_status, :duplicate_type, :created_at, :updated_at
)
ON CONFLICT(badge_number) DO UPDATE SET
    record_id=excluded.record_id,
    rank=excluded.rank,
    last_name=excluded.last_name,
    first_name=excluded.first_name,
    middle_name=excluded.middle_name,
    suffix=excluded.suffix,
    camp=excluded.camp,
    office=excluded.office,
    gender=excluded.gender,
    classification=excluded.classification,
    personnel_type=excluded.personnel_type,
    duplicate_status=excluded.duplicate_status,
    duplicate_type=excluded.duplicate_type,
    created_at=excluded.created_at,
    updated_at=excluded.updated_at;
"""


def normalize(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def normalize_badge(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return normalize(value)


def import_workbook(
    workbook_path: Path | str,
    db_path: Path | str = DB_PATH,
    worksheet_name: str = "LIST",
) -> int:
    workbook_path = Path(workbook_path)
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")

    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    if worksheet_name not in workbook.sheetnames:
        raise ValueError(f"Worksheet '{worksheet_name}' was not found.")

    sheet = workbook[worksheet_name]
    rows = sheet.iter_rows(values_only=True)
    raw_headers = next(rows, None)
    if not raw_headers:
        raise ValueError("Worksheet is empty.")

    headers = [str(value).strip().upper() if value is not None else "" for value in raw_headers]
    column_map = {
        index: EXPECTED_HEADERS[header]
        for index, header in enumerate(headers)
        if header in EXPECTED_HEADERS
    }

    required = {"badge_number", "last_name", "first_name"}
    found = set(column_map.values())
    missing = sorted(required - found)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    initialize(db_path)
    imported = 0

    with connect(db_path) as connection:
        for values in rows:
            record = {field: None for field in EXPECTED_HEADERS.values()}
            for index, field in column_map.items():
                if index >= len(values):
                    continue
                value = values[index]
                record[field] = normalize_badge(value) if field == "badge_number" else normalize(value)

            if not record["badge_number"]:
                continue

            connection.execute(INSERT_SQL, record)
            imported += 1

    workbook.close()
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description="Import NBPattendance personnel into SQLite.")
    parser.add_argument("workbook", help="Path to NBPattendance.xlsx")
    parser.add_argument("--sheet", default="LIST", help="Worksheet name (default: LIST)")
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite database path")
    args = parser.parse_args()

    count = import_workbook(args.workbook, args.db, args.sheet)
    print(f"Imported {count} personnel record(s) into {args.db}")


if __name__ == "__main__":
    main()
