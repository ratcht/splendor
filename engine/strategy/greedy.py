import random
from dataclasses import dataclass

from ..actions import Action, _payment, check_nobles, legal_actions
from ..models import Card
from ..state import BoardState, PlayerState, TableState


@dataclass(frozen=True)
class Weights:
  points: float = 1.0
  discount: float = 1.0
  noble: float = 0.15
  need: float = 0.08
  gem: float = 0.03


def _shortfall(card: Card, player: PlayerState) -> int:
  return max(0, _payment(card, player).g - player.gems.g)


def _noble_gap(board: BoardState, player: PlayerState) -> int:
  discounts = player.discounts
  gaps = (
    sum(max(0, req - discounts[g]) for g, req in noble.requirements)
    for noble in board.nobles
  )
  return min(gaps, default=0)


def value(board: BoardState, player: PlayerState, w: Weights) -> float:
  cards = [c for cards in board.dealt_cards.values() for c in cards if c]
  need = min(
    (_shortfall(c, player) for c in cards + player.reserved_cards), default=0
  )
  return (
    w.points * player.points
    + w.discount * player.discounts.total
    + w.gem * player.gems.total
    - w.noble * _noble_gap(board, player)
    - w.need * need
  )


class GreedyStrategy:
  """One-ply search: play the action whose resulting state scores highest."""

  def __init__(self, rng: random.Random | None = None, weights: Weights | None = None):
    self.rng = rng or random.Random()
    self.weights = weights or Weights()

  def choose_action(self, state: TableState) -> Action | None:
    board = state.board
    player = state.players[state.current]
    actions = legal_actions(board, player)
    if not actions:
      return None
    self.rng.shuffle(actions)
    return max(
      actions,
      key=lambda a: value(*check_nobles(*a.apply(board, player)), self.weights),
    )
