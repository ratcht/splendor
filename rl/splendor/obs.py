import numpy as np
from engine import NON_GOLD_GEMS, Card, Gem, Noble, PlayerState, TableState

from .actions import face_up

CARD = 11  # cost 5, bonus one-hot 5, points 1
NOBLE = 5  # requirements
PLAYER = 13  # gems 6, discounts 5, points 1, reserve count 1
BOARD_SLOTS = 12
NOBLE_SLOTS = 3  # num_players + 1, and v1 is 2 players
RESERVE_SLOTS = 3

N_OBS = 6 + BOARD_SLOTS * CARD + NOBLE_SLOTS * NOBLE + 2 * PLAYER + 6 * CARD


def _card(card: Card | None) -> list[float]:
  if card is None:
    return [0.0] * CARD
  return [
    *(card.cost[g] for g in NON_GOLD_GEMS),
    *(float(card.gem is g) for g in NON_GOLD_GEMS),
    card.points,
  ]


def _noble(noble: Noble | None) -> list[float]:
  if noble is None:
    return [0.0] * NOBLE
  return [noble.requirements[g] for g in NON_GOLD_GEMS]


def _player(player: PlayerState) -> list[float]:
  return [
    *(player.gems[g] for g in Gem),
    *(player.discounts[g] for g in NON_GOLD_GEMS),
    player.points,
    len(player.reserved_cards),
  ]


def _reserved(player: PlayerState) -> list[float]:
  cards = player.reserved_cards
  return [
    v
    for i in range(RESERVE_SLOTS)
    for v in _card(cards[i] if i < len(cards) else None)
  ]


def encode(state: TableState, seat: int) -> np.ndarray:
  """Encode the table from `seat`'s perspective. See rl/docs/observation-encoding.md."""
  board = state.board
  me, other = state.players[seat], state.players[1 - seat]
  nobles = board.nobles
  return np.array(
    [
      *(board.available_gems[g] for g in Gem),
      *(v for slot in range(BOARD_SLOTS) for v in _card(face_up(board, slot))),
      *(
        v
        for i in range(NOBLE_SLOTS)
        for v in _noble(nobles[i] if i < len(nobles) else None)
      ),
      *_player(me),
      *_player(other),
      *_reserved(me),
      *_reserved(other),
    ],
    dtype=np.float32,
  )
