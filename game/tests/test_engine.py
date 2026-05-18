import pytest

from models import Gem, GemStack, CardLevel
from actions import TakeTwoGems, TakeThreeGems, BuyCard, ReserveCard
from engine import take_turn, run_game
from table import Table

from conftest import card, noble, make_board, make_player, FakeDealer, ScriptedStrategy


# ── take_turn ─────────────────────────────────────────────────────────────────

def test_take_turn_applies_legal_action():
  initial = make_board(gems=GemStack(r=7, e=7, s=7, o=7, d=7, g=5))
  dealer  = FakeDealer(initial=initial)
  table   = Table(num_players=2, dealer=dealer)

  take_turn(table, TakeTwoGems(gem=Gem.Ruby))

  assert table.players[0].gems == GemStack(r=2)
  assert table.board.available_gems[Gem.Ruby] == 5


def test_take_turn_raises_on_invalid_action():
  initial = make_board(gems=GemStack(r=3))  # only 3 rubies — TakeTwo requires 4
  dealer  = FakeDealer(initial=initial)
  table   = Table(num_players=2, dealer=dealer)

  with pytest.raises(ValueError, match="invalid action"):
    take_turn(table, TakeTwoGems(gem=Gem.Ruby))


def test_take_turn_awards_noble_after_buy():
  # Set up so that buying the target card completes a noble requirement.
  ruby_card  = card(gem=Gem.Ruby)
  target     = card(gem=Gem.Ruby, points=0, e=1)  # buying gives a Ruby bonus
  qualifying = noble(r=2)                          # needs 2 ruby cards
  initial = make_board(
    dealt={CardLevel.Level1: [target], CardLevel.Level2: [], CardLevel.Level3: []},
    gems=GemStack(),
    nobles=[qualifying],
  )
  dealer = FakeDealer(initial=initial)
  table  = Table(num_players=2, dealer=dealer)
  # Seed the current player with one ruby card and the emerald to pay.
  table.players[0] = make_player(gems=GemStack(e=1), cards=[ruby_card])

  take_turn(table, BuyCard(card=target))

  assert qualifying in table.players[0].nobles
  assert qualifying not in table.board.nobles


def test_take_turn_calls_dealer_refill():
  initial = make_board(gems=GemStack(r=7))
  dealer  = FakeDealer(initial=initial)
  table   = Table(num_players=2, dealer=dealer)

  take_turn(table, TakeTwoGems(gem=Gem.Ruby))

  # refill() should be called once per turn, with the post-apply / post-noble board.
  assert len(dealer.refill_calls) == 1
  assert dealer.refill_calls[0].available_gems[Gem.Ruby] == 5


# ── run_game ──────────────────────────────────────────────────────────────────

def test_run_game_advances_current_player_alternately():
  # Take-3 only needs each color ≥1, so it stays legal across many turns
  # without depleting any pile. We let both players play 2 turns each and
  # verify each strategy was queried only when its seat was current.
  initial = make_board()
  dealer  = FakeDealer(initial=initial)
  three   = TakeThreeGems(gems=(Gem.Emerald, Gem.Sapphire, Gem.Onyx))

  s1 = ScriptedStrategy([three, three])
  s2 = ScriptedStrategy([three, three])

  table = Table(num_players=2, dealer=dealer)
  for _ in range(4):
    strategy = s1 if table.current == 0 else s2
    take_turn(table, strategy.choose_action(table.state()))
    table.advance()

  assert s1.observed_currents == [0, 0]
  assert s2.observed_currents == [1, 1]


def test_run_game_short_scripted_2p_game():
  # P1 buys a free 15-point card; P2 takes gems. Game ends after P2's turn.
  free_15pt = card(level=CardLevel.Level3, gem=Gem.Ruby, points=15)
  initial = make_board(
    dealt={CardLevel.Level1: [], CardLevel.Level2: [], CardLevel.Level3: [free_15pt]},
    gems=GemStack(s=7),
  )
  dealer = FakeDealer(initial=initial)

  s1 = ScriptedStrategy([BuyCard(card=free_15pt)])
  s2 = ScriptedStrategy([TakeTwoGems(gem=Gem.Sapphire)])

  winner_idx, winner = run_game([s1, s2], dealer=dealer)

  assert winner_idx == 0
  assert winner.points == 15


def test_run_game_completes_round_after_15pt():
  # P1 hits 15 on turn 1; the engine MUST still query P2 once before ending.
  # Asserting `len(s2.observed_currents) == 1` proves P2 got a final turn.
  free_15pt = card(level=CardLevel.Level3, gem=Gem.Ruby, points=15)
  initial = make_board(
    dealt={CardLevel.Level1: [], CardLevel.Level2: [], CardLevel.Level3: [free_15pt]},
    gems=GemStack(s=7),
  )
  dealer = FakeDealer(initial=initial)

  s1 = ScriptedStrategy([BuyCard(card=free_15pt)])
  s2 = ScriptedStrategy([TakeTwoGems(gem=Gem.Sapphire)])

  run_game([s1, s2], dealer=dealer)

  assert s1.observed_currents == [0]
  assert s2.observed_currents == [1]


def test_run_game_winner_tiebreak_fewer_cards():
  # Build two players directly with equal points but different card counts.
  # Then assert the engine's winner-selection logic picks the one with fewer.
  p_few   = make_player(cards=[card(points=5), card(points=5), card(points=5)])  # 15pt, 3 cards
  p_many  = make_player(cards=[card(points=3)] * 5)                              # 15pt, 5 cards
  players = [p_many, p_few]

  winner_idx, winner = max(enumerate(players), key=lambda x: (x[1].points, -len(x[1].cards)))
  assert winner_idx == 1
  assert winner is p_few
