import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclasses import replace
import pytest

from models import Gem, GemStack, Card, Noble, CardLevel, empty_deck
from state import BoardState, PlayerState
from dealer import Dealer


# ── builders ──────────────────────────────────────────────────────────────────

def card(level: CardLevel = CardLevel.Level1, gem: Gem = Gem.Ruby, points: int = 0,
         e: int = 0, s: int = 0, o: int = 0, d: int = 0, r: int = 0) -> Card:
  return Card(level=level, gem=gem, points=points, cost=GemStack(e=e, s=s, o=o, d=d, r=r))

def noble(e: int = 0, s: int = 0, o: int = 0, d: int = 0, r: int = 0, points: int = 3) -> Noble:
  return Noble(requirements=GemStack(e=e, s=s, o=o, d=d, r=r), points=points)

def deck_of(level1: list[Card] = (), level2: list[Card] = (), level3: list[Card] = ()):
  return {CardLevel.Level1: list(level1), CardLevel.Level2: list(level2), CardLevel.Level3: list(level3)}

def make_board(dealt: dict[CardLevel, list[Card]] | None = None,
               undealt: dict[CardLevel, list[Card]] | None = None,
               gems: GemStack | None = None,
               nobles: list[Noble] = ()) -> BoardState:
  return BoardState(
    undealt_cards=undealt if undealt is not None else empty_deck(),
    dealt_cards=dealt if dealt is not None else empty_deck(),
    nobles=list(nobles),
    available_gems=gems if gems is not None else GemStack(e=7, s=7, o=7, d=7, r=7, g=5),
  )

def make_player(gems: GemStack | None = None,
                cards: list[Card] = (),
                reserved: list[Card] = (),
                nobles: list[Noble] = ()) -> PlayerState:
  return PlayerState(
    cards=list(cards),
    reserved_cards=list(reserved),
    nobles=list(nobles),
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
