from .base import SessionStore
from .in_memory import InMemorySessionStore

_store = InMemorySessionStore()


def get_session_store() -> SessionStore:
  return _store


__all__ = ["SessionStore", "get_session_store"]
