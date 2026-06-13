from abc import ABC, abstractmethod

import engine
from backend.models.session import GameSession


class SessionStore(ABC):
  @abstractmethod
  def create(self, table: engine.Table) -> GameSession:
    pass

  @abstractmethod
  def get(self, game_id: str) -> GameSession | None:
    pass
