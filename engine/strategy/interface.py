from typing import Protocol

from ..actions import Action
from ..state import TableState


class Strategy(Protocol):
  def choose_action(self, state: TableState) -> Action | None:
    """None means pass: the player has no legal action."""
    ...
