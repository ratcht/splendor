import random
import pytest

from dataclasses import replace
from models import Gem, GemStack, CardLevel
from dealer import RandomDealer
from presets import ALL_CARDS

from conftest import card, make_board


# ── refill behavior ───────────────────────────────────────────────────────────

def test_refill_replenishes_to_four():
  c_dealt   = [card(level=CardLevel.Level1, points=i) for i in range(2)]
  c_undealt = [card(level=CardLevel.Level1, points=10 + i) for i in range(5)]
  board = make_board(
    dealt   = {CardLevel.Level1: list(c_dealt), CardLevel.Level2: [], CardLevel.Level3: []},
    undealt = {CardLevel.Level1: list(c_undealt), CardLevel.Level2: [], CardLevel.Level3: []},
  )

  new_board = RandomDealer().refill(board)

  assert len(new_board.dealt_cards[CardLevel.Level1]) == 4
  assert len(new_board.undealt_cards[CardLevel.Level1]) == 3


def test_refill_noop_when_undealt_empty():
  c_dealt = [card(points=i) for i in range(2)]  # only 2 dealt
  board = make_board(
    dealt   = {CardLevel.Level1: list(c_dealt), CardLevel.Level2: [], CardLevel.Level3: []},
    undealt = {CardLevel.Level1: [],             CardLevel.Level2: [], CardLevel.Level3: []},
  )

  new_board = RandomDealer().refill(board)

  assert new_board.dealt_cards[CardLevel.Level1] == c_dealt


def test_refill_does_not_touch_full_level():
  c_dealt   = [card(points=i) for i in range(4)]
  c_undealt = [card(points=10)]
  board = make_board(
    dealt   = {CardLevel.Level1: list(c_dealt), CardLevel.Level2: [], CardLevel.Level3: []},
    undealt = {CardLevel.Level1: list(c_undealt), CardLevel.Level2: [], CardLevel.Level3: []},
  )

  new_board = RandomDealer().refill(board)

  assert new_board.dealt_cards[CardLevel.Level1] == c_dealt
  assert new_board.undealt_cards[CardLevel.Level1] == c_undealt


def test_refill_partial_when_undealt_insufficient():
  # dealt has 2, undealt has only 1 → dealt becomes 3 (not 4), undealt becomes 0.
  c_dealt   = [card(points=i) for i in range(2)]
  c_undealt = [card(points=10)]
  board = make_board(
    dealt   = {CardLevel.Level1: list(c_dealt), CardLevel.Level2: [], CardLevel.Level3: []},
    undealt = {CardLevel.Level1: list(c_undealt), CardLevel.Level2: [], CardLevel.Level3: []},
  )

  new_board = RandomDealer().refill(board)

  assert len(new_board.dealt_cards[CardLevel.Level1]) == 3
  assert new_board.undealt_cards[CardLevel.Level1] == []


# ── initial_board contract ────────────────────────────────────────────────────

def test_initial_board_structure():
  random.seed(0)  # deterministic shuffle
  board = RandomDealer().initial_board(num_players=2)

  for lvl in CardLevel:
    assert len(board.dealt_cards[lvl]) == 4
    # dealt ∪ undealt at each level must equal the full preset for that level.
    union = set(board.dealt_cards[lvl]) | set(board.undealt_cards[lvl])
    assert union == set(ALL_CARDS[lvl])
    assert len(union) == len(ALL_CARDS[lvl])  # no duplication

  assert len(board.nobles) == 3  # num_players + 1
  assert board.available_gems == GemStack(e=7, s=7, o=7, d=7, r=7, g=5)
