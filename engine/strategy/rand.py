import random

from ..actions import Action, legal_actions
from ..state import TableState

# ── strategy ──────────────────────────────────────────────────────────────────


class RandomStrategy:
  def choose_action(self, state: TableState) -> Action:
    actions = legal_actions(state.board, state.players[state.current])
    if not actions:
      raise RuntimeError("No legal actions available")
    return random.choice(actions)
