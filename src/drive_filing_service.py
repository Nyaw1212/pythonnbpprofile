from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_DIR = ROOT_DIR / "credentials"
CLIENT_FILE = CREDENTIALS_DIR / "oauth_client.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"
ROOT_FOLDER_ID = "1JL6uRUmvAov6LFPOyYNKt6ePRGbLS8u0"
SCOPES = ["https://www.googleapis.com/auth/drive"]


def _credentials() -> Credentials:
    if not CLIENT_FILE.exists():
        raise FileNotFoundError(f"OAuth client file not found: {CLIENT_FILE}")

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
    return build("drive", "v3", credentials=_credentials(), cache_discovery=False)


def _escape_query(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def _get_or_create_folder(service, parent_id: str, name: str) -> str:
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
        return matches[0]["id"]

    folder = service.files().create(
        body={
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        },
        fields="id",
    ).execute()
    return folder["id"]


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

        media = MediaFileUpload(str(path), resumable=True)
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
