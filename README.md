# NBP Personnel Lookup

A clean Python desktop application for fast, offline personnel search and profile viewing.

## V1 architecture

- **Desktop shell:** PyWebView
- **UI:** HTML + CSS + JavaScript
- **Local data:** SQLite
- **Initial source:** `NBPattendance.xlsx` (`LIST` worksheet)
- **Planned sync sources:** Google Sheets and Neon PostgreSQL

The application always searches the local SQLite database. Remote sources will synchronize into SQLite so the lookup remains fast and usable offline.

## Setup

Requires Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Import the current NBPattendance workbook

Put your exported `NBPattendance.xlsx` somewhere on your PC, then run:

```powershell
python -m src.import_excel "C:\path\to\NBPattendance.xlsx"
```

This creates `data/personnel.db`. The database is intentionally ignored by Git because it is local runtime data.

## Run the app

```powershell
python app.py
```

Use development mode when you want PyWebView debugging enabled:

```powershell
python app.py --debug
```

## Current V1 features

- Local SQLite personnel database
- Import/update from the `LIST` sheet of `NBPattendance.xlsx`
- Search by name, badge number, or rank
- Filter by camp, office, and rank
- Click a result to open a basic personnel profile
- Web-style local desktop interface
- Works without internet after the local database has been imported

## Planned next steps

1. Google Sheets synchronization using the existing NBPattendance sheet.
2. Neon PostgreSQL synchronization.
3. Google Drive personnel photo cache.
4. Expanded profile page.
5. Printable personnel profile/PDF.
6. Packaging as a Windows `.exe`.

## Secrets

Do **not** commit Google credentials, Neon connection strings, or other secrets. `.env`, credential JSON files, and local databases are excluded by `.gitignore`.

Copy `.env.example` to `.env` when remote synchronization is added.
