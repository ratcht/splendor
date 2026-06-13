from uuid import uuid4

from backend.game.base import GameStore
from typing_extensions import override

import engine
from backend.models.game import Game


class InMemoryGameStore(GameStore):
  def __init__(self) -> None:
    self._games: dict[str, Game] = {}

  @override
  def create(self, table: engine.Table) -> Game:
    game = Game(id=str(uuid4()), table=table)
    self._games[game.id] = game
    return game

  @override
  def get(self, game_id: str) -> Game | None:
    return self._games.get(game_id)
