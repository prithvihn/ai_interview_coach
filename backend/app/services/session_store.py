"""
Session store — simple JSON-file persistence under data/sessions/.
Each session is stored as data/sessions/<session_id>.json
"""
import json
import os
from app.config import settings


def _session_path(session_id: str) -> str:
    os.makedirs(settings.SESSIONS_DIR, exist_ok=True)
    return os.path.join(settings.SESSIONS_DIR, f"{session_id}.json")


def save_session(session_id: str, data: dict) -> None:
    with open(_session_path(session_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_session(session_id: str) -> dict | None:
    path = _session_path(session_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_all_sessions() -> list:
    os.makedirs(settings.SESSIONS_DIR, exist_ok=True)
    sessions = []
    for fname in os.listdir(settings.SESSIONS_DIR):
        if fname.endswith(".json"):
            path = os.path.join(settings.SESSIONS_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                sessions.append(json.load(f))
    return sessions
