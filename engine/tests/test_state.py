from models import Gem, GemStack

from conftest import card, noble, make_player


def test_discounts_empty_when_no_cards():
  assert make_player().discounts == GemStack()


def test_discounts_counts_by_gem_color():
  cards = [card(gem=Gem.Ruby), card(gem=Gem.Ruby), card(gem=Gem.Sapphire)]
  player = make_player(cards=cards)
  assert player.discounts == GemStack(r=2, s=1)


def test_points_sums_cards_and_nobles():
  player = make_player(
    cards=[card(points=2), card(points=3)],
    nobles=[noble(points=3)],
  )
  assert player.points == 8
