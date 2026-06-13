import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclasses import replace

import pytest
from dealer import Dealer
from models import Card, Gem, GemStack, Level, Noble, empty_deck, empty_optional_deck
from state import BoardState, PlayerState

# ── builders ──────────────────────────────────────────────────────────────────


def card(
  level: Level = 1,
  gem: Gem = Gem.Ruby,
  points: int = 0,
  e: int = 0,
  s: int = 0,
  o: int = 0,
  d: int = 0,
  r: int = 0,
) -> Card:
  return Card(
    level=level, gem=gem, points=points, cost=GemStack(e=e, s=s, o=o, d=d, r=r)
  )


def noble(
  e: int = 0, s: int = 0, o: int = 0, d: int = 0, r: int = 0, points: int = 3
) -> Noble:
  return Noble(requirements=GemStack(e=e, s=s, o=o, d=d, r=r), points=points)


def deck_of(
  level1: list[Card | None] | None = None,
  level2: list[Card | None] | None = None,
  level3: list[Card | None] | None = None,
):
  return {1: list(level1 or []), 2: list(level2 or []), 3: list(level3 or [])}


def make_board(
  dealt: dict[Level, list[Card | None]] | None = None,
  undealt: dict[Level, list[Card]] | None = None,
  gems: GemStack | None = None,
  nobles: list[Noble] | None = None,
) -> BoardState:
  return BoardState(
    undealt_cards=undealt if undealt is not None else empty_deck(),
    dealt_cards=dealt if dealt is not None else empty_optional_deck(),
    nobles=list(nobles or []),
    available_gems=gems if gems is not None else GemStack(e=7, s=7, o=7, d=7, r=7, g=5),
  )


def make_player(
  gems: GemStack | None = None,
  cards: list[Card] | None = None,
  reserved: list[Card] | None = None,
  nobles: list[Noble] | None = None,
) -> PlayerState:
  return PlayerState(
    cards=list(cards or []),
    reserved_cards=list(reserved or []),
    nobles=list(nobles or []),
    gems=gems if gems is not None else GemStack(),
  )


# ── mocks ─────────────────────────────────────────────────────────────────────


class FakeDealer(Dealer):
  """Deterministic dealer. Provide an exact initial board; refill is a no-op by default."""

  def __init__(self, initial: BoardState, refill_fn=None):
    self._initial = initial
    self._refill_fn = refill_fn or (lambda b: b)
    self.refill_calls: list[BoardState] = []

  def initial_board(self, num_players: int) -> BoardState:
    return self._initial

  def refill(self, board: BoardState) -> BoardState:
    self.refill_calls.append(board)
    return self._refill_fn(board)


class ScriptedStrategy:
  """Plays a fixed sequence of actions. Records the states it observed."""

  def __init__(self, actions: list):
    self.actions = list(actions)
    self.observed_currents: list[int] = []
    self._idx = 0

  def choose_action(self, state):
    self.observed_currents.append(state.current)
    a = self.actions[self._idx]
    self._idx += 1
    return a


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def make_card():
  return card


@pytest.fixture
def make_noble():
  return noble


@pytest.fixture
def make_board_():
  return make_board


@pytest.fixture
def make_player_():
  return make_player


@pytest.fixture
def fake_dealer():
  return FakeDealer


@pytest.fixture
def scripted():
  return ScriptedStrategy
