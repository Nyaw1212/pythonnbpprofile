from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "personnel.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS personnel (
    record_id TEXT,
    badge_number TEXT PRIMARY KEY,
    rank TEXT,
    last_name TEXT,
    first_name TEXT,
    middle_name TEXT,
    suffix TEXT,
    camp TEXT,
    office TEXT,
    gender TEXT,
    classification TEXT,
    personnel_type TEXT,
    duplicate_status TEXT,
    duplicate_type TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_personnel_last_name ON personnel(last_name);
CREATE INDEX IF NOT EXISTS idx_personnel_first_name ON personnel(first_name);
CREATE INDEX IF NOT EXISTS idx_personnel_camp ON personnel(camp);
CREATE INDEX IF NOT EXISTS idx_personnel_office ON personnel(office);
CREATE INDEX IF NOT EXISTS idx_personnel_rank ON personnel(rank);
"""


def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize(db_path: Path | str = DB_PATH) -> None:
    with connect(db_path) as connection:
        connection.executescript(SCHEMA)
