import random

from ..actions import Action, legal_actions, primary_key
from ..state import TableState

# ── strategy ──────────────────────────────────────────────────────────────────


class RandomStrategy:
  def __init__(self, rng: random.Random | None = None):
    self.rng = rng or random.Random()

  def choose_action(self, state: TableState) -> Action | None:
    actions = legal_actions(state.board, state.players[state.current])
    if not actions:
      return None
    # uniform over decisions, not over their discard variants
    groups: dict[tuple, list[Action]] = {}
    for action in actions:
      groups.setdefault(primary_key(action), []).append(action)
    return self.rng.choice(groups[self.rng.choice(list(groups))])
