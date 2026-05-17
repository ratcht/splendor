from typing import Protocol
from state import TableState
from actions import Action


class Strategy(Protocol):
  def choose_action(self, state: TableState) -> Action: ...
