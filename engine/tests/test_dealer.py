import random
from dataclasses import replace

import pytest
from conftest import card, make_board
from dealer import RandomDealer
from models import LEVELS, Gem, GemStack
from presets import ALL_CARDS

# ── refill behavior ───────────────────────────────────────────────────────────


def test_refill_replaces_empty_slot():
  first = card(level=1, points=1)
  second = card(level=1, points=2)
  third = card(level=1, points=3)
  spare = card(level=1, points=10)
  replacement = card(level=1, points=11)
  board = make_board(
    dealt={1: [first, None, second, third], 2: [], 3: []},
    undealt={1: [spare, replacement], 2: [], 3: []},
  )

  new_board = RandomDealer().refill(board)

  assert new_board.dealt_cards[1] == [first, replacement, second, third]
  assert new_board.undealt_cards[1] == [spare]


def test_refill_leaves_empty_slot_when_undealt_empty():
  first = card(points=1)
  second = card(points=2)
  third = card(points=3)
  dealt = [first, None, second, third]
  board = make_board(
    dealt={1: list(dealt), 2: [], 3: []},
    undealt={1: [], 2: [], 3: []},
  )

  new_board = RandomDealer().refill(board)

  assert new_board.dealt_cards[1] == dealt


def test_refill_does_not_touch_full_level():
  c_dealt = [card(points=i) for i in range(4)]
  c_undealt = [card(points=10)]
  board = make_board(
    dealt={1: list(c_dealt), 2: [], 3: []},
    undealt={1: list(c_undealt), 2: [], 3: []},
  )

  new_board = RandomDealer().refill(board)

  assert new_board.dealt_cards[1] == c_dealt
  assert new_board.undealt_cards[1] == c_undealt


def test_refill_partial_when_undealt_insufficient():
  first = card(points=1)
  second = card(points=2)
  replacement = card(points=10)
  board = make_board(
    dealt={1: [None, first, None, second], 2: [], 3: []},
    undealt={1: [replacement], 2: [], 3: []},
  )

  new_board = RandomDealer().refill(board)

  assert new_board.dealt_cards[1] == [replacement, first, None, second]
  assert new_board.undealt_cards[1] == []


# ── initial_board contract ────────────────────────────────────────────────────


def test_initial_board_structure():
  random.seed(0)  # deterministic shuffle
  board = RandomDealer().initial_board(num_players=2)

  for lvl in LEVELS:
    assert len(board.dealt_cards[lvl]) == 4
    # dealt ∪ undealt at each level must equal the full preset for that level.
    union = set(board.dealt_cards[lvl]) | set(board.undealt_cards[lvl])
    assert union == set(ALL_CARDS[lvl])
    assert len(union) == len(ALL_CARDS[lvl])  # no duplication

  assert len(board.nobles) == 3  # num_players + 1
  assert board.available_gems == GemStack(e=7, s=7, o=7, d=7, r=7, g=5)
