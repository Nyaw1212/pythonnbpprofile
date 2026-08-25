from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.runtime_paths import app_root, is_frozen

ROOT_DIR = app_root()
CREDENTIALS_DIR = ROOT_DIR / "credentials"
CLIENT_FILE = CREDENTIALS_DIR / "oauth_client.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"
FOLDER_CACHE_FILE = CREDENTIALS_DIR / "drive_folder_cache.json"
ROOT_FOLDER_ID = "1JL6uRUmvAov6LFPOyYNKt6ePRGbLS8u0"
SCOPES = ["https://www.googleapis.com/auth/drive"]

_FOLDER_CACHE: dict[str, str] | None = None
_SERVICE = None


def _dev_credentials_dir() -> Path | None:
    if not is_frozen():
        return None
    # Typical development build layout:
    # repo/dist/NBP Personnel Filing/NBP Personnel Filing.exe
    exe_dir = Path(sys.executable).resolve().parent
    repo_candidate = exe_dir.parent.parent
    candidate = repo_candidate / "credentials"
    return candidate if candidate.exists() else None


def _ensure_packaged_credentials() -> None:
    """Copy existing dev credentials beside the EXE on first packaged run.

    This keeps secrets out of Git/PyInstaller while avoiding manual copying after
    every local rebuild. For a portable install on another PC, the credentials
    folder still needs to be provided beside the EXE once.
    """
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    source_dir = _dev_credentials_dir()
    if not source_dir:
        return
    for name in ("oauth_client.json", "token.json", "drive_folder_cache.json"):
        source = source_dir / name
        destination = CREDENTIALS_DIR / name
        if source.exists() and not destination.exists():
            shutil.copy2(source, destination)


def _validate_client_file() -> None:
    _ensure_packaged_credentials()
    if not CLIENT_FILE.exists():
        raise FileNotFoundError(
            f"OAuth client file not found: {CLIENT_FILE}. "
            "Place the credentials folder beside NBP Personnel Filing.exe."
        )
    try:
        payload = json.loads(CLIENT_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Could not read OAuth client JSON: {exc}") from exc

    if "installed" not in payload:
        if "web" in payload:
            raise ValueError(
                "The OAuth JSON is for a Web application. Create a new OAuth client in "
                "Google Auth Platform > Clients with Application type = Desktop app, "
                "download that JSON, and save it as credentials/oauth_client.json."
            )
        raise ValueError(
            "The OAuth JSON is not a Desktop app client. Create an OAuth client with "
            "Application type = Desktop app and download its JSON."
        )


def _credentials() -> Credentials:
    _validate_client_file()
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _service():
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = build("drive", "v3", credentials=_credentials(), cache_discovery=False)
    return _SERVICE


def _escape_query(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def _load_folder_cache() -> dict[str, str]:
    global _FOLDER_CACHE
    if _FOLDER_CACHE is not None:
        return _FOLDER_CACHE
    _ensure_packaged_credentials()
    try:
        data = json.loads(FOLDER_CACHE_FILE.read_text(encoding="utf-8")) if FOLDER_CACHE_FILE.exists() else {}
        _FOLDER_CACHE = data if isinstance(data, dict) else {}
    except Exception:
        _FOLDER_CACHE = {}
    return _FOLDER_CACHE


def _save_folder_cache() -> None:
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    FOLDER_CACHE_FILE.write_text(json.dumps(_load_folder_cache(), indent=2), encoding="utf-8")


def _cache_key(parent_id: str, name: str) -> str:
    return f"{parent_id}|{name.strip().casefold()}"


def _get_or_create_folder(service, parent_id: str, name: str) -> str:
    cache = _load_folder_cache()
    key = _cache_key(parent_id, name)
    cached_id = cache.get(key)
    if cached_id:
        return cached_id

    safe_name = _escape_query(name)
    query = (
        f"'{parent_id}' in parents and trashed = false and "
        f"mimeType = 'application/vnd.google-apps.folder' and name = '{safe_name}'"
    )
    result = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id,name)",
        pageSize=10,
    ).execute()
    matches = result.get("files", [])
    if matches:
        folder_id = matches[0]["id"]
    else:
        folder = service.files().create(
            body={
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            },
            fields="id",
        ).execute()
        folder_id = folder["id"]

    cache[key] = folder_id
    _save_folder_cache()
    return folder_id


def upload_filed_document(
    *,
    local_path: str | Path,
    person_folder: str,
    category: str,
    year: str,
    month: str,
) -> dict:
    path = Path(local_path)
    if not path.exists():
        return {"ok": False, "message": f"Local filed copy not found: {path}"}

    try:
        service = _service()
        person_id = _get_or_create_folder(service, ROOT_FOLDER_ID, person_folder)
        category_id = _get_or_create_folder(service, person_id, category.upper())
        year_id = _get_or_create_folder(service, category_id, year)
        month_id = _get_or_create_folder(service, year_id, month)

        media = MediaFileUpload(str(path), resumable=False)
        uploaded = service.files().create(
            body={"name": path.name, "parents": [month_id]},
            media_body=media,
            fields="id,name,webViewLink",
        ).execute()

        return {
            "ok": True,
            "file_id": uploaded.get("id"),
            "filename": uploaded.get("name", path.name),
            "web_view_link": uploaded.get("webViewLink"),
            "folder_id": month_id,
            "message": "Uploaded to Google Drive.",
        }
    except Exception as exc:
        return {"ok": False, "message": str(exc)}
