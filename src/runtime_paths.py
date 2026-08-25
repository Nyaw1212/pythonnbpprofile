from __future__ import annotations

from pathlib import Path
import sys


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_root() -> Path:
    """Writable app root.

    In development this is the repository root. In a PyInstaller build this is
    the folder containing the executable, so external data/credentials remain
    editable without rebuilding the EXE.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_root() -> Path:
    """Bundled resource root for HTML/CSS/JS and other packaged assets."""
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return app_root()
