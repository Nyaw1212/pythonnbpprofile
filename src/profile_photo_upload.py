from __future__ import annotations

import io
import json
import mimetypes
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from .runtime_paths import app_root

SPREADSHEET_ID = "1SMbMfK-2T5LroHcycjUbf__pwAYQ6wtUHQocl2EoxmU"
SHEET_NAME = "LIST"
PHOTO_ROOT_FOLDER_ID = "1JL6uRUmvAov6LFPOyYNKt6ePRGbLS8u0"
PHOTO_FOLDER_NAME = "PROFILE PHOTOS"

CREDENTIALS_DIR = app_root() / "credentials"
CLIENT_FILE = CREDENTIALS_DIR / "oauth_client.json"
TOKEN_FILE = CREDENTIALS_DIR / "lookup_google_token.json"
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

_DRIVE = None
_SHEETS = None
_PHOTO_FOLDER_ID = None


def _credentials() -> Credentials:
    if not CLIENT_FILE.exists():
        raise FileNotFoundError(f"OAuth client file not found: {CLIENT_FILE}")

    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def drive_service():
    global _DRIVE
    if _DRIVE is None:
        _DRIVE = build("drive", "v3", credentials=_credentials(), cache_discovery=False)
    return _DRIVE


def sheets_service():
    global _SHEETS
    if _SHEETS is None:
        _SHEETS = build("sheets", "v4", credentials=_credentials(), cache_discovery=False)
    return _SHEETS


def _escape_query(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _profile_photo_folder_id() -> str:
    global _PHOTO_FOLDER_ID
    if _PHOTO_FOLDER_ID:
        return _PHOTO_FOLDER_ID

    service = drive_service()
    name = _escape_query(PHOTO_FOLDER_NAME)
    query = (
        f"'{PHOTO_ROOT_FOLDER_ID}' in parents and trashed = false and "
        f"mimeType = 'application/vnd.google-apps.folder' and name = '{name}'"
    )
    result = service.files().list(q=query, fields="files(id,name)", pageSize=10).execute()
    files = result.get("files", [])
    if files:
        _PHOTO_FOLDER_ID = files[0]["id"]
        return _PHOTO_FOLDER_ID

    created = service.files().create(
        body={
            "name": PHOTO_FOLDER_NAME,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [PHOTO_ROOT_FOLDER_ID],
        },
        fields="id",
    ).execute()
    _PHOTO_FOLDER_ID = created["id"]
    return _PHOTO_FOLDER_ID


def _column_letter(index_zero_based: int) -> str:
    value = index_zero_based + 1
    letters = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _drivefile_column() -> str:
    result = sheets_service().spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!1:1",
    ).execute()
    headers = [str(v).strip().upper() for v in (result.get("values") or [[]])[0]]
    for wanted in ("DRIVEFILEID", "DRIVE FILE ID"):
        if wanted in headers:
            return _column_letter(headers.index(wanted))
    raise ValueError("The LIST sheet does not contain a DRIVEFILEID header.")


def upload_profile_photo(*, image_path: str | Path, badge_number: str, rank: str, full_name: str, source_order: int | None) -> dict:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Photo file not found: {path}")
    if source_order is None:
        raise ValueError("Personnel source row is unavailable. Sync the Google Sheet first, then try again.")

    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    if not mime.startswith("image/"):
        raise ValueError("Please select an image file.")

    extension = path.suffix.lower() or ".jpg"
    clean_name = " ".join(str(full_name or "").split())
    filename = f"{badge_number} - {rank} {clean_name}".strip() + extension

    drive = drive_service()
    uploaded = drive.files().create(
        body={"name": filename, "parents": [_profile_photo_folder_id()]},
        media_body=MediaFileUpload(str(path), mimetype=mime, resumable=False),
        fields="id,name,webViewLink,mimeType",
    ).execute()
    file_id = uploaded["id"]

    column = _drivefile_column()
    sheet_row = int(source_order) + 1
    sheets_service().spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!{column}{sheet_row}",
        valueInputOption="RAW",
        body={"values": [[file_id]]},
    ).execute()

    return {
        "ok": True,
        "file_id": file_id,
        "filename": uploaded.get("name", filename),
        "web_view_link": uploaded.get("webViewLink"),
        "sheet_row": sheet_row,
    }


def download_private_drive_image(file_id: str) -> tuple[bytes, str] | None:
    """Download a private Drive image when Lookup OAuth has already been authorized.

    This deliberately does not start OAuth by itself; opening a profile should never
    unexpectedly launch a browser. Add Photo creates the token when authorization is needed.
    """
    if not TOKEN_FILE.exists():
        return None
    try:
        service = drive_service()
        meta = service.files().get(fileId=file_id, fields="mimeType").execute()
        mime = str(meta.get("mimeType") or "image/jpeg")
        request = service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buffer.getvalue(), mime
    except Exception:
        return None
