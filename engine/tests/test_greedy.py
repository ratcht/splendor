import random

from conftest import FakeDealer, card, make_board, make_player, noble
from engine.actions import BuyCard
from engine.dealer import RandomDealer
from engine.engine import run_game, take_turn
from engine.models import Gem, GemStack
from engine.strategy.greedy import GreedyStrategy
from engine.strategy.rand import RandomStrategy
from engine.table import Table


def table_with(board, player):
  table = Table(2, dealer=FakeDealer(initial=board))
  table.players[0] = player
  return table


def choose(board, player):
  state = table_with(board, player).state()
  return GreedyStrategy(random.Random(0)).choose_action(state)


# ── action choice ─────────────────────────────────────────────────────────────


def test_only_plays_legal_actions():
  greedy = GreedyStrategy(random.Random(0))
  table = Table(2, dealer=RandomDealer(random.Random(0)))

  for _ in range(20):
    state = table.state()
    action = greedy.choose_action(state)
    assert action.is_valid(state.board, state.players[state.current])
    take_turn(table, action)
    table.advance()


def test_buys_instead_of_taking_gems():
  target = card(level=1, gem=Gem.Ruby, points=1, e=1)
  board = make_board(dealt={1: [target], 2: [], 3: []})

  assert choose(board, make_player(gems=GemStack(e=1))) == BuyCard(card=target)


def test_prefers_the_higher_point_card():
  cheap = card(level=1, gem=Gem.Ruby, points=0, e=1)
  rich = card(level=1, gem=Gem.Onyx, points=2, e=1)
  board = make_board(dealt={1: [cheap, rich], 2: [], 3: []})

  assert choose(board, make_player(gems=GemStack(e=1))) == BuyCard(card=rich)


def test_prefers_the_card_that_earns_a_noble():
  rubies = [card(gem=Gem.Ruby) for _ in range(3)]
  completes = card(level=1, gem=Gem.Ruby, points=0, e=1)
  other = card(level=1, gem=Gem.Onyx, points=0, e=1)
  board = make_board(dealt={1: [completes, other], 2: [], 3: []}, nobles=[noble(r=4)])
  player = make_player(gems=GemStack(e=1), cards=rubies)

  assert choose(board, player) == BuyCard(card=completes)


# ── strength ──────────────────────────────────────────────────────────────────


def test_beats_random():
  rng = random.Random(0)
  games = 20
  wins = 0

  for i in range(games):
    seats = [GreedyStrategy(rng), RandomStrategy(rng)]
    if i % 2:
      seats.reverse()
    idx, _ = run_game(seats, dealer=RandomDealer(rng), max_turns=200)
    wins += idx is not None and isinstance(seats[idx], GreedyStrategy)

  assert wins / games > 0.8
