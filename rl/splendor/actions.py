"""Fixed action index space.

   0-4   take 2 of NON_GOLD_GEMS[i]
   5-14  take 3 of TAKE3_COMBOS[i]
  15-26  buy face-up slot
  27-29  buy reserved slot
  30-41  reserve face-up slot
     42  pass
"""

from itertools import combinations

import numpy as np
from engine import (
  LEVELS,
  NON_GOLD_GEMS,
  Action,
  BoardState,
  BuyCard,
  Card,
  PlayerState,
  ReserveCard,
  TakeThreeGems,
  TakeTwoGems,
)

TAKE3_COMBOS = list(combinations(NON_GOLD_GEMS, 3))
PASS = 42
N_ACTIONS = 43


def face_up(board: BoardState, slot: int) -> Card | None:
  """Board slot 0-11 -> the card there. Shared with obs.py so both agree."""
  cards = board.dealt_cards[LEVELS[slot // 4]]
  pos = slot % 4
  return cards[pos] if pos < len(cards) else None


def decode(index: int, board: BoardState, player: PlayerState) -> Action | None:
  """Index -> engine action. None for an empty slot or for PASS."""
  if index == PASS:
    return None
  if index < 5:
    return TakeTwoGems(gem=NON_GOLD_GEMS[index])
  if index < 15:
    return TakeThreeGems(gems=TAKE3_COMBOS[index - 5])
  if index < 27:
    card = face_up(board, index - 15)
    return BuyCard(card=card) if card else None
  if index < 30:
    slot = index - 27
    reserved = player.reserved_cards
    return BuyCard(card=reserved[slot]) if slot < len(reserved) else None
  card = face_up(board, index - 30)
  return ReserveCard(card=card) if card else None


def action_mask(board: BoardState, player: PlayerState) -> np.ndarray:
  mask = np.zeros(N_ACTIONS, dtype=np.int8)
  for i in range(PASS):
    action = decode(i, board, player)
    mask[i] = action is not None and action.is_valid(board, player)
  mask[PASS] = not mask.any()
  return mask
