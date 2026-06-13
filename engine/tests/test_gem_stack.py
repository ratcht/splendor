import pytest
from collections import Counter

from models import Gem, GemStack


def test_add_combines_per_color():
  a = GemStack(e=2, r=1, g=3)
  b = GemStack(e=1, s=4, g=2)
  result = a + b
  assert result == GemStack(e=3, s=4, r=1, g=5)


def test_sub_can_produce_negative():
  # apply() math relies on this: `board.available_gems - net` where net may
  # exceed what's available in some components after the subtraction algebra.
  a = GemStack(e=1)
  b = GemStack(e=3, r=2)
  result = a - b
  assert result.e == -2
  assert result.r == -2
  assert result.s == 0


def test_le_per_component():
  assert GemStack(e=1, r=1) <= GemStack(e=2, r=1)
  assert GemStack(e=1, r=1) <= GemStack(e=1, r=1)
  assert not (GemStack(e=2) <= GemStack(e=1))
  # equal in 5 components, exceeds in 1 → not <=
  assert not (GemStack(e=1, s=1, o=1, d=1, r=1, g=2) <= GemStack(e=1, s=1, o=1, d=1, r=1, g=1))


def test_total_includes_gold():
  # Design choice: total sums all six colors, including gold.
  assert GemStack(e=3, g=2).total == 5


def test_iter_yields_all_six_pairs_in_gem_order():
  stack = GemStack(r=2)
  pairs = list(stack)
  assert len(pairs) == 6
  assert [g for g, _ in pairs] == list(Gem)
  assert dict(pairs)[Gem.Ruby] == 2


def test_from_counts_partial_dict():
  stack = GemStack.from_counts({Gem.Ruby: 3})
  assert stack.r == 3
  assert stack.e == 0 and stack.s == 0 and stack.o == 0 and stack.d == 0 and stack.g == 0


@pytest.mark.parametrize("gem,attr", [
  (Gem.Emerald,  "e"),
  (Gem.Sapphire, "s"),
  (Gem.Onyx,     "o"),
  (Gem.Diamond,  "d"),
  (Gem.Ruby,     "r"),
  (Gem.Gold,     "g"),
])
def test_getitem_matches_attribute(gem, attr):
  stack = GemStack(e=1, s=2, o=3, d=4, r=5, g=6)
  assert stack[gem] == getattr(stack, attr)


def test_repr_empty_renders_zero():
  assert repr(GemStack()) == "0"


def test_repr_shows_only_nonzero_and_includes_gold():
  s = repr(GemStack(e=2, g=1))
  assert "2E" in s and "1G" in s
  # zero components must not appear
  assert "0" not in s
  for token in ("0E", "0S", "0O", "0D", "0R", "0G"):
    assert token not in s
