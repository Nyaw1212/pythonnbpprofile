from __future__ import annotations

import sqlite3
from pathlib import Path

from src.runtime_paths import app_root

ROOT_DIR = app_root()
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "personnel.db"

PROFILE_FIELDS = {
    "id_number": "TEXT",
    "batch_name": "TEXT",
    "date_entrance_duty": "TEXT",
    "birthdate": "TEXT",
    "place_of_birth": "TEXT",
    "civil_status": "TEXT",
    "citizenship": "TEXT",
    "religion": "TEXT",
    "blood_type": "TEXT",
    "height": "TEXT",
    "weight": "TEXT",
    "email": "TEXT",
    "tin": "TEXT",
    "highest_education": "TEXT",
    "address_no": "TEXT",
    "address_street": "TEXT",
    "address_barangay": "TEXT",
    "address_city": "TEXT",
    "address_province": "TEXT",
    "address_zip": "TEXT",
    "home_address": "TEXT",
    "previous_office": "TEXT",
    "father_name": "TEXT",
    "father_occupation": "TEXT",
    "father_address": "TEXT",
    "mother_name": "TEXT",
    "mother_occupation": "TEXT",
    "mother_address": "TEXT",
    "spouse_name": "TEXT",
    "spouse_occupation": "TEXT",
    "spouse_address": "TEXT",
    "personnel_status": "TEXT",
    "emergency_contact": "TEXT",
    "emergency_relationship": "TEXT",
    "emergency_number": "TEXT",
    "emergency_address": "TEXT",
    "elementary_school": "TEXT",
    "elementary_course": "TEXT",
    "elementary_address": "TEXT",
    "elementary_year_graduated": "TEXT",
    "high_school": "TEXT",
    "high_school_course": "TEXT",
    "high_school_address": "TEXT",
    "high_school_year_graduated": "TEXT",
    "college": "TEXT",
    "college_course": "TEXT",
    "college_address": "TEXT",
    "college_year_graduated": "TEXT",
    "graduate_studies": "TEXT",
    "graduate_studies_course": "TEXT",
    "graduate_studies_address": "TEXT",
    "graduate_studies_year_graduated": "TEXT",
}

BASE_SCHEMA = """
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
    updated_at TEXT,
    source_order INTEGER,
    drive_file_id TEXT,
    id_number TEXT,
    batch_name TEXT,
    date_entrance_duty TEXT,
    birthdate TEXT,
    place_of_birth TEXT,
    civil_status TEXT,
    citizenship TEXT,
    religion TEXT,
    blood_type TEXT,
    height TEXT,
    weight TEXT,
    email TEXT,
    tin TEXT,
    highest_education TEXT,
    address_no TEXT,
    address_street TEXT,
    address_barangay TEXT,
    address_city TEXT,
    address_province TEXT,
    address_zip TEXT,
    home_address TEXT,
    previous_office TEXT,
    father_name TEXT,
    father_occupation TEXT,
    father_address TEXT,
    mother_name TEXT,
    mother_occupation TEXT,
    mother_address TEXT,
    spouse_name TEXT,
    spouse_occupation TEXT,
    spouse_address TEXT,
    personnel_status TEXT,
    emergency_contact TEXT,
    emergency_relationship TEXT,
    emergency_number TEXT,
    emergency_address TEXT,
    elementary_school TEXT,
    elementary_course TEXT,
    elementary_address TEXT,
    elementary_year_graduated TEXT,
    high_school TEXT,
    high_school_course TEXT,
    high_school_address TEXT,
    high_school_year_graduated TEXT,
    college TEXT,
    college_course TEXT,
    college_address TEXT,
    college_year_graduated TEXT,
    graduate_studies TEXT,
    graduate_studies_course TEXT,
    graduate_studies_address TEXT,
    graduate_studies_year_graduated TEXT
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

def _migrate(connection: sqlite3.Connection) -> None:
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(personnel)").fetchall()}
    required = {"source_order": "INTEGER", "drive_file_id": "TEXT", **PROFILE_FIELDS}
    for name, sql_type in required.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE personnel ADD COLUMN {name} {sql_type}")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_personnel_source_order ON personnel(source_order)")

def initialize(db_path: Path | str = DB_PATH) -> None:
    with connect(db_path) as connection:
        connection.executescript(BASE_SCHEMA)
        _migrate(connection)
