import copy

import pytest
from actions import BuyCard, ReserveCard, TakeThreeGems, TakeTwoGems
from conftest import card, make_board, make_player
from models import Gem, GemStack


def test_take_two_transfers_gems():
  board = make_board(gems=GemStack(r=7))
  player = make_player(gems=GemStack(e=1))

  action = TakeTwoGems(gem=Gem.Ruby)
  new_board, new_player = action.apply(board, player)

  assert new_board.available_gems == GemStack(r=5)
  assert new_player.gems == GemStack(e=1, r=2)


def test_take_two_with_returns_balances():
  board = make_board(gems=GemStack(r=7))
  player = make_player(
    gems=GemStack(e=4, s=4)
  )  # 8 gems; +2 ruby → 10; no return required
  # Force a return scenario: player at 9, +2 = 11 → must return 1.
  player = make_player(gems=GemStack(e=4, s=5))
  action = TakeTwoGems(gem=Gem.Ruby, returns=GemStack(e=1))

  new_board, new_player = action.apply(board, player)

  # Net: +2 ruby to player, -1 emerald to player; mirror on board.
  assert new_player.gems == GemStack(e=3, s=5, r=2)
  assert new_board.available_gems == GemStack(e=1, r=5)


def test_take_three_transfers_three_distinct():
  board = make_board(gems=GemStack(e=7, s=7, o=7, d=7, r=7, g=5))
  player = make_player()

  action = TakeThreeGems(gems=(Gem.Emerald, Gem.Sapphire, Gem.Onyx))
  new_board, new_player = action.apply(board, player)

  assert new_player.gems == GemStack(e=1, s=1, o=1)
  assert new_board.available_gems == GemStack(e=6, s=6, o=6, d=7, r=7, g=5)


def test_take_three_with_returns_balances():
  board = make_board(gems=GemStack(e=7, s=7, o=7))
  # Player at 9 gems; take 3 → 12; must return 2.
  player = make_player(gems=GemStack(d=5, r=4))
  action = TakeThreeGems(
    gems=(Gem.Emerald, Gem.Sapphire, Gem.Onyx),
    returns=GemStack(d=1, r=1),
  )

  new_board, new_player = action.apply(board, player)

  assert new_player.gems.total == 10
  assert new_player.gems == GemStack(d=4, r=3, e=1, s=1, o=1)
  assert new_board.available_gems == GemStack(e=6, s=6, o=6, d=1, r=1)


def test_buy_from_board_pays_and_grants_card():
  target = card(level=1, gem=Gem.Ruby, points=1, e=2, s=1)
  board = make_board(
    dealt={1: [target], 2: [], 3: []},
    gems=GemStack(),
  )
  player = make_player(gems=GemStack(e=2, s=1))

  new_board, new_player = BuyCard(card=target).apply(board, player)

  assert new_board.dealt_cards[1] == [None]
  assert target in new_player.cards
  assert new_player.gems == GemStack()
  assert new_board.available_gems == GemStack(e=2, s=1)


def test_buy_from_reserve_removes_from_reserve_not_board():
  target = card(level=2, gem=Gem.Onyx, points=2, r=3)
  other = card(level=2, gem=Gem.Diamond, points=0, e=2)
  board = make_board(dealt={1: [], 2: [other], 3: []}, gems=GemStack())
  player = make_player(gems=GemStack(r=3), reserved=[target])

  new_board, new_player = BuyCard(card=target).apply(board, player)

  # The "other" card is untouched on the board.
  assert new_board.dealt_cards[2] == [other]
  assert target not in new_player.reserved_cards
  assert target in new_player.cards


def test_buy_with_full_discount_pays_zero():
  ruby_bonus = card(gem=Gem.Ruby)
  target = card(level=2, gem=Gem.Onyx, points=2, r=2)
  board = make_board(
    dealt={1: [], 2: [target], 3: []},
    gems=GemStack(),
  )
  player = make_player(gems=GemStack(), cards=[ruby_bonus, ruby_bonus])

  new_board, new_player = BuyCard(card=target).apply(board, player)

  assert new_player.gems == GemStack()
  assert new_board.available_gems == GemStack()  # no payment
  assert target in new_player.cards


def test_reserve_gains_gold_when_available():
  target = card()
  board = make_board(
    dealt={1: [target], 2: [], 3: []},
    gems=GemStack(g=5),
  )
  player = make_player()

  new_board, new_player = ReserveCard(card=target).apply(board, player)

  assert target in new_player.reserved_cards
  assert new_board.dealt_cards[1] == [None]
  assert new_player.gems == GemStack(g=1)
  assert new_board.available_gems == GemStack(g=4)


def test_reserve_no_gold_when_supply_empty():
  target = card()
  board = make_board(
    dealt={1: [target], 2: [], 3: []},
    gems=GemStack(g=0),
  )
  player = make_player()

  new_board, new_player = ReserveCard(card=target).apply(board, player)

  assert target in new_player.reserved_cards
  assert new_player.gems == GemStack()
  assert new_board.available_gems == GemStack()


def test_reserve_with_returns_when_at_10_gems():
  target = card()
  board = make_board(
    dealt={1: [target], 2: [], 3: []},
    gems=GemStack(g=5),
  )
  # Player at 10 gems; reserve gains 1 gold → 11; must return 1.
  player = make_player(gems=GemStack(e=2, s=2, o=2, d=2, r=2))
  action = ReserveCard(card=target, returns=GemStack(e=1))

  new_board, new_player = action.apply(board, player)

  assert new_player.gems.total == 10
  assert new_player.gems == GemStack(e=1, s=2, o=2, d=2, r=2, g=1)
  # Board lost 1 gold (taken), gained 1 emerald (returned).
  assert new_board.available_gems == GemStack(e=1, g=4)


# ── meta: apply() must not mutate its inputs ──────────────────────────────────


@pytest.mark.parametrize(
  "action_factory,player_setup",
  [
    (lambda b, p: TakeTwoGems(gem=Gem.Ruby), lambda: make_player()),
    (
      lambda b, p: TakeThreeGems(gems=(Gem.Emerald, Gem.Sapphire, Gem.Onyx)),
      lambda: make_player(),
    ),
    (
      lambda b, p: BuyCard(card=next(iter(b.dealt_cards[1]))),
      lambda: make_player(gems=GemStack(e=2, s=1)),
    ),
    (
      lambda b, p: ReserveCard(card=next(iter(b.dealt_cards[1]))),
      lambda: make_player(),
    ),
  ],
)
def test_apply_does_not_mutate_inputs(action_factory, player_setup):
  target = card(level=1, gem=Gem.Ruby, points=1, e=2, s=1)
  board = make_board(
    dealt={1: [target], 2: [], 3: []},
  )
  player = player_setup()
  action = action_factory(board, player)

  board_snapshot = copy.deepcopy(board)
  player_snapshot = copy.deepcopy(player)

  action.apply(board, player)

  assert board == board_snapshot
  assert player == player_snapshot
