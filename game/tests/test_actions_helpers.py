import pytest

from models import Gem, GemStack, CardLevel
from actions import _enumerate_returns, _payment, _can_afford, _remove_card, check_nobles

from conftest import card, noble, make_board, make_player


# ── _enumerate_returns ────────────────────────────────────────────────────────

def test_enumerate_returns_excess_zero_yields_single_empty():
  # Invariant: apply() always gets at least one return option, even when nothing
  # needs to be returned. The empty GemStack is that option.
  result = _enumerate_returns(GemStack(e=5, r=3), excess=0)
  assert result == [GemStack()]


def test_enumerate_returns_respects_pool_cap():
  # pool has only 1 emerald and 1 sapphire; excess 2 means the ONLY valid
  # return is one of each — not two of one color.
  result = _enumerate_returns(GemStack(e=1, s=1), excess=2)
  assert result == [GemStack(e=1, s=1)]


def test_enumerate_returns_full_multisets_no_duplicates():
  # pool {e:2, s:2}, excess 2 → exactly 3 multisets: {e:2}, {e:1,s:1}, {s:2}
  result = _enumerate_returns(GemStack(e=2, s=2), excess=2)
  assert len(result) == 3
  assert GemStack(e=2) in result
  assert GemStack(e=1, s=1) in result
  assert GemStack(s=2) in result


# ── _payment / _can_afford ────────────────────────────────────────────────────

def test_payment_uses_discounts():
  # Card costs 3 ruby; player has 2 ruby-bonus cards → effective cost 1 ruby.
  ruby_bonus = card(gem=Gem.Ruby)
  target     = card(r=3)
  player     = make_player(gems=GemStack(r=2), cards=[ruby_bonus, ruby_bonus])
  pay = _payment(target, player)
  assert pay == GemStack(r=1)


def test_payment_uses_gold_when_short_on_regular_gems():
  target = card(r=3)
  player = make_player(gems=GemStack(r=1, g=2))
  pay = _payment(target, player)
  assert pay.r == 1   # spent all ruby
  assert pay.g == 2   # filled the rest with gold


def test_payment_fully_discounted_returns_zero():
  ruby_card = card(gem=Gem.Ruby)
  target    = card(r=2)
  player    = make_player(cards=[ruby_card, ruby_card])
  pay = _payment(target, player)
  assert pay == GemStack()


@pytest.mark.parametrize("player_ruby,player_gold,can_buy", [
  (3, 0, True),   # exact ruby
  (2, 1, True),   # ruby + 1 gold covers
  (1, 1, False),  # 1+1 < 3 → not enough
  (0, 3, True),   # all gold
  (0, 2, False),  # 2 gold < 3 cost
])
def test_can_afford(player_ruby, player_gold, can_buy):
  target = card(r=3)
  player = make_player(gems=GemStack(r=player_ruby, g=player_gold))
  assert _can_afford(target, player) is can_buy


# ── _remove_card ──────────────────────────────────────────────────────────────

def test_remove_card_only_rebuilds_relevant_level():
  c1 = card(level=CardLevel.Level1, gem=Gem.Ruby, points=1)
  c2 = card(level=CardLevel.Level2, gem=Gem.Onyx, points=2)
  c3 = card(level=CardLevel.Level3, gem=Gem.Diamond, points=3)
  dealt = {CardLevel.Level1: [c1], CardLevel.Level2: [c2], CardLevel.Level3: [c3]}

  result = _remove_card(dealt, c1)

  assert result[CardLevel.Level1] == [None]
  # Identity preserved on non-matching levels — no copy made.
  assert result[CardLevel.Level2] is dealt[CardLevel.Level2]
  assert result[CardLevel.Level3] is dealt[CardLevel.Level3]


# ── check_nobles ──────────────────────────────────────────────────────────────

def test_check_nobles_awards_qualifying_noble():
  ruby_card = card(gem=Gem.Ruby)
  emerald_card = card(gem=Gem.Emerald)
  qualifying = noble(r=1, e=1)
  board  = make_board(nobles=[qualifying])
  player = make_player(cards=[ruby_card, emerald_card])

  new_board, new_player = check_nobles(board, player)

  assert new_board.nobles == []
  assert new_player.nobles == [qualifying]


def test_check_nobles_no_op_when_unqualified():
  ruby_card = card(gem=Gem.Ruby)
  too_demanding = noble(r=3, e=3)
  board  = make_board(nobles=[too_demanding])
  player = make_player(cards=[ruby_card])

  new_board, new_player = check_nobles(board, player)

  assert new_board.nobles == [too_demanding]
  assert new_player.nobles == []


def test_check_nobles_picks_first_when_multiple_qualify():
  # Documents current behavior — when ties exist, player should choose, but
  # the implementation currently grabs the first.
  cards = [card(gem=Gem.Ruby), card(gem=Gem.Emerald)]
  n1 = noble(r=1, e=1, points=3)
  n2 = noble(r=1, e=1, points=4)  # different points so we can distinguish
  board  = make_board(nobles=[n1, n2])
  player = make_player(cards=cards)

  new_board, new_player = check_nobles(board, player)

  assert new_player.nobles == [n1]
  assert new_board.nobles == [n2]
