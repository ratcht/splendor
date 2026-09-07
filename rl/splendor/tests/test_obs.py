import random

import numpy as np
from engine import (
  NON_GOLD_GEMS,
  BoardState,
  BuyCard,
  Card,
  Gem,
  GemStack,
  PlayerState,
  Table,
  TableState,
  legal_actions,
  take_turn,
)
from rl.splendor.actions import decode
from rl.splendor.obs import (
  BOARD_SLOTS,
  CARD,
  N_OBS,
  NOBLE,
  NOBLE_SLOTS,
  PLAYER,
  RESERVE_SLOTS,
  encode,
)

CARDS_AT = 6
NOBLES_AT = CARDS_AT + BOARD_SLOTS * CARD
SELF_AT = NOBLES_AT + NOBLE_SLOTS * NOBLE
OPP_AT = SELF_AT + PLAYER
SELF_RES_AT = OPP_AT + PLAYER
OPP_RES_AT = SELF_RES_AT + RESERVE_SLOTS * CARD


def card(gem=Gem.Ruby, points=0, **cost) -> Card:
  return Card(level=1, gem=gem, points=points, cost=GemStack(**cost))


def slot(v, n):
  return v[CARDS_AT + n * CARD : CARDS_AT + (n + 1) * CARD]


# ── shape and ranges ──────────────────────────────────────────────────────────


def test_shape_and_dtype():
  v = encode(Table(2).state(), 0)
  assert v.shape == (N_OBS,)
  assert v.dtype == np.float32


def test_values_are_finite_and_non_negative():
  rng = random.Random(0)
  table = Table(2)
  for _ in range(50):
    v = encode(table.state(), table.current)
    assert np.isfinite(v).all()
    assert (v >= 0).all()
    actions = legal_actions(table.board, table.players[table.current])
    if not actions:
      break
    take_turn(table, rng.choice(actions))
    table.advance()


def test_encoding_is_deterministic():
  state = Table(2).state()
  assert (encode(state, 0) == encode(state, 0)).all()


# ── card regions ──────────────────────────────────────────────────────────────


def test_card_region_has_one_bonus_bit_or_is_empty():
  v = encode(Table(2).state(), 0)
  for n in range(BOARD_SLOTS):
    block = slot(v, n)
    bonus = block[5:10]
    assert bonus.sum() in (0.0, 1.0)
    if bonus.sum() == 0.0:
      assert not block.any()


def test_unfilled_reserved_slots_are_zero():
  board = Table(2).board
  me = PlayerState(reserved_cards=[card(e=1)])
  state = TableState(board, [me, PlayerState()], 0)
  v = encode(state, 0)
  assert v[SELF_RES_AT : SELF_RES_AT + CARD].any()  # slot 0 filled
  assert not v[SELF_RES_AT + CARD : SELF_RES_AT + RESERVE_SLOTS * CARD].any()
  assert not v[OPP_RES_AT : OPP_RES_AT + RESERVE_SLOTS * CARD].any()


def test_empty_board_slot_is_zero():
  board = BoardState(dealt_cards={1: [None, card(e=1), None, None], 2: [], 3: []})
  v = encode(TableState(board, [PlayerState(), PlayerState()], 0), 0)
  assert not slot(v, 0).any()
  assert slot(v, 1).any()
  assert not slot(v, 4).any()  # L2 has no slots at all


# ── perspective ───────────────────────────────────────────────────────────────


def test_seat_swaps_player_and_reserved_blocks():
  board = Table(2).board
  p0 = PlayerState(gems=GemStack(e=3), reserved_cards=[card(e=1)])
  p1 = PlayerState(gems=GemStack(r=5))
  state = TableState(board, [p0, p1], 0)
  a, b = encode(state, 0), encode(state, 1)

  assert (a[SELF_AT:OPP_AT] == b[OPP_AT:SELF_RES_AT]).all()
  assert (a[OPP_AT:SELF_RES_AT] == b[SELF_AT:OPP_AT]).all()
  assert (a[SELF_RES_AT:OPP_RES_AT] == b[OPP_RES_AT:]).all()
  assert (a[OPP_RES_AT:] == b[SELF_RES_AT:OPP_RES_AT]).all()
  assert (a[:SELF_AT] == b[:SELF_AT]).all()  # board is seat independent


# ── alignment with the action layer ───────────────────────────────────────────


def test_card_slots_align_with_buy_action_indices():
  # If these drift, the policy reads one card and acts on another, silently.
  rng = random.Random(1)
  for _ in range(10):
    table = Table(2)
    for _ in range(30):
      board, player = table.board, table.players[table.current]
      v = encode(table.state(), table.current)
      for n in range(BOARD_SLOTS):
        action, block = decode(15 + n, board, player), slot(v, n)
        if action is None:
          assert not block.any()
          continue
        assert isinstance(action, BuyCard)
        for i, g in enumerate(NON_GOLD_GEMS):
          assert block[i] == action.card.cost[g]
        assert block[10] == action.card.points
      actions = legal_actions(board, player)
      if not actions:
        break
      take_turn(table, rng.choice(actions))
      if player.points >= 15:
        break
      table.advance()
