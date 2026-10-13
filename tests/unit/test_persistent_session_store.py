import sqlite3
from time import time
import pytest
from src.services.persistent_session_store import PersistentSessionStore
from src.services.conversation_service import SessionMissing


def test_restart_preserves_profile_history_and_delete(tmp_path):
    path = tmp_path / 'sessions.sqlite3'
    store = PersistentSessionStore(path)
    identifier, session = store.acquire(None)
    session.profile.learning_goal = 'finanzas'
    session.history = [{'role': 'user', 'content': 'Quiero finanzas'}]
    session.asked.add('education')
    session.filters = {'level': 'pregrado'}
    store.save(identifier, session)
    session.lock.release()
    restarted = PersistentSessionStore(path)
    _, restored = restarted.acquire(identifier)
    assert restored.profile.learning_goal == 'finanzas'
    assert restored.history == session.history
    assert restored.asked == {'education'}
    assert restored.filters == {'level': 'pregrado'}
    restored.lock.release()
    restarted.delete(identifier)
    with pytest.raises(SessionMissing):
        PersistentSessionStore(path).acquire(identifier)


def test_expired_sessions_do_not_return_after_restart(tmp_path):
    path = tmp_path / 'sessions.sqlite3'
    store = PersistentSessionStore(path, ttl=60)
    identifier, session = store.acquire(None)
    store.save(identifier, session)
    session.lock.release()
    with sqlite3.connect(path) as db:
        db.execute('UPDATE sessions SET touched = ?', (time() - 120,))
    with pytest.raises(SessionMissing):
        PersistentSessionStore(path, ttl=60).acquire(identifier)
