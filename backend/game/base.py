from abc import ABC, abstractmethod

from backend.models.game import Game

import engine


class GameStore(ABC):
  @abstractmethod
  def create(self, table: engine.Table) -> Game:
    pass

  @abstractmethod
  def get(self, game_id: str) -> Game | None:
    pass
