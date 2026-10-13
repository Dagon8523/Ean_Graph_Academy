"""SQLite-backed sessions for a single QA API worker. TTL survives restarts."""
import json
import sqlite3
from pathlib import Path
from time import time, monotonic
from uuid import UUID

from apps.api.src.schemas.conversation import Profile
from src.services.conversation_service import Session, SessionStore


class PersistentSessionStore(SessionStore):
    def __init__(self, path, ttl=3600, maximum=100):
        super().__init__(ttl, maximum)
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, touched REAL NOT NULL, payload TEXT NOT NULL)")
            db.execute("DELETE FROM sessions WHERE touched < ?", (time() - ttl,))
            rows = db.execute("SELECT id, touched, payload FROM sessions ORDER BY touched DESC LIMIT ?", (maximum,)).fetchall()
        for identifier, touched, payload in rows:
            data = json.loads(payload)
            self.sessions[UUID(identifier)] = Session(
                profile=Profile.model_validate(data['profile']),
                skipped=set(data['skipped']), history=data['history'],
                asked=set(data['asked']), evidence=data['evidence'],
                filters=data['filters'],
                touched=monotonic() - max(0, time() - touched),
            )

    def save(self, identifier, session):
        payload = json.dumps(dict(profile=session.profile.model_dump(),
                                  skipped=sorted(session.skipped), history=session.history,
                                  asked=sorted(session.asked), evidence=session.evidence,
                                  filters=session.filters), ensure_ascii=False)
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM sessions WHERE touched < ?", (time() - self.ttl,))
            db.execute("INSERT OR REPLACE INTO sessions VALUES (?, ?, ?)",
                       (str(identifier), time(), payload))

    def delete(self, identifier):
        super().delete(identifier)
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM sessions WHERE id = ?", (str(identifier),))
