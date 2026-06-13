from dataclasses import FrozenInstanceError

import pytest
from models import Card, Gem, GemStack, Noble


def test_card_hashable_and_usable_as_set_member():
  c1 = Card(1, Gem.Ruby, points=1, cost=GemStack(e=2, s=1))
  c2 = Card(1, Gem.Ruby, points=1, cost=GemStack(e=2, s=1))
  c3 = Card(1, Gem.Ruby, points=2, cost=GemStack(e=2, s=1))

  assert c1 == c2
  assert hash(c1) == hash(c2)
  assert c1 in {c2}
  assert c3 not in {c1, c2}


def test_card_is_frozen():
  c = Card(1, Gem.Ruby, points=1, cost=GemStack(e=1))
  with pytest.raises(FrozenInstanceError):
    c.points = 5  # type: ignore[misc]
