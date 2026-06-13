import random

from ..actions import ACTION_CLASSES, Action
from ..state import TableState

# ── strategy ──────────────────────────────────────────────────────────────────


class RandomStrategy:
  def choose_action(self, state: TableState) -> Action:
    board = state.board
    player = state.players[state.current]

    # pick action class
    for action_class in random.sample(ACTION_CLASSES, len(ACTION_CLASSES)):
      if avail_actions := action_class.legal_actions(board, player):
        return random.choice(avail_actions)

    raise RuntimeError("No legal actions available")
