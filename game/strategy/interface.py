from typing import Protocol
from table import TableState
from actions import Action


class Strategy(Protocol):
  def choose_action(self, state: TableState) -> Action: ...
