from uuid import uuid4

from typing_extensions import override

import engine
from backend.models.session import GameSession
from backend.session.base import SessionStore


class InMemorySessionStore(SessionStore):
  def __init__(self) -> None:
    self._sessions: dict[str, GameSession] = {}

  @override
  def create(self, table: engine.Table) -> GameSession:
    session = GameSession(id=str(uuid4()), table=table)
    self._sessions[session.id] = session
    return session

  @override
  def get(self, game_id: str) -> GameSession | None:
    return self._sessions.get(game_id)
