from .base import GameStore
from .in_memory import InMemoryGameStore

_store = InMemoryGameStore()


def get_game_store() -> GameStore:
  return _store


__all__ = ["GameStore", "get_game_store"]
