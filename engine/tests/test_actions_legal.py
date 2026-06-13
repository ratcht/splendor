import pytest
from engine.actions import ACTION_CLASSES, BuyCard, ReserveCard, TakeThreeGems, TakeTwoGems
from conftest import card, make_board, make_player
from engine.models import Gem, GemStack

# ── TakeTwoGems ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("supply,expected", [(3, 0), (4, 1), (7, 1)])
def test_take_two_only_when_supply_ge_4(supply, expected):
  board = make_board(gems=GemStack(r=supply))
  player = make_player()
  assert len(TakeTwoGems.legal_actions(board, player)) == expected


# ── TakeThreeGems ─────────────────────────────────────────────────────────────


def test_take_three_count_with_full_supply():
  # All 5 non-gold colors available → C(5,3) = 10 triples, no returns required.
  board = make_board()
  player = make_player()
  actions = TakeThreeGems.legal_actions(board, player)
  assert len(actions) == 10


def test_take_three_count_with_4_colors_available():
  board = make_board(gems=GemStack(e=1, s=1, o=1, d=1, r=0))  # 4 colors available
  player = make_player()
  actions = TakeThreeGems.legal_actions(board, player)
  assert len(actions) == 4  # C(4,3)


def test_take_three_none_when_fewer_than_3_colors():
  board = make_board(gems=GemStack(e=1, s=1))  # only 2 colors
  player = make_player()
  assert TakeThreeGems.legal_actions(board, player) == []


def test_take_three_enumerates_returns_when_over_10():
  # Player at 9 gems; takes 3 → 12; must return 2 from a 7-gem pool.
  board = make_board(gems=GemStack(e=1, s=1, o=1))
  player = make_player(gems=GemStack(d=4, r=5))  # 9 gems, no overlap with takes
  actions = TakeThreeGems.legal_actions(board, player)

  # One triple is possible (E,S,O), and after taking the pool is {d:4, r:5, e:1, s:1, o:1}
  # excess=2 → multisets of size 2 capped by pool counts.
  triples = {a.gems for a in actions}
  assert triples == {(Gem.Emerald, Gem.Sapphire, Gem.Onyx)}

  # All actions must produce valid post-state (total of 10 gems).
  for action in actions:
    _, new_player = action.apply(board, player)
    assert new_player.gems.total == 10


# ── BuyCard ───────────────────────────────────────────────────────────────────


def test_buy_includes_board_and_reserved():
  on_board = card(r=1)
  reserved = card(e=1)
  board = make_board(
    dealt={1: [on_board], 2: [], 3: []},
  )
  player = make_player(gems=GemStack(r=1, e=1), reserved=[reserved])
  actions = BuyCard.legal_actions(board, player)
  buys = {a.card for a in actions}
  assert buys == {on_board, reserved}


def test_buy_excludes_unaffordable():
  cheap = card(r=1)
  expensive = card(r=5)
  board = make_board(
    dealt={1: [cheap, expensive], 2: [], 3: []},
  )
  player = make_player(gems=GemStack(r=1))
  actions = BuyCard.legal_actions(board, player)
  assert [a.card for a in actions] == [cheap]


# ── ReserveCard ───────────────────────────────────────────────────────────────


def test_reserve_empty_when_three_reserved():
  some = card()
  three_reserved = [card(points=i) for i in range(3)]
  board = make_board(
    dealt={1: [some], 2: [], 3: []},
  )
  player = make_player(reserved=three_reserved)
  assert ReserveCard.legal_actions(board, player) == []


def test_reserve_no_returns_when_under_10_gems():
  c = card()
  board = make_board(
    dealt={1: [c], 2: [], 3: []},
    gems=GemStack(g=5),  # gold available
  )
  player = make_player(gems=GemStack(e=3))  # under 10
  actions = ReserveCard.legal_actions(board, player)
  assert len(actions) == 1  # exactly one option per board card, no return needed


def test_reserve_enumerates_returns_when_at_10_gems():
  c = card()
  board = make_board(
    dealt={1: [c], 2: [], 3: []},
    gems=GemStack(g=5),
  )
  # Player has 10 gems; reserving gains 1 gold → 11; must return 1.
  player = make_player(gems=GemStack(e=2, s=2, o=2, d=2, r=2))
  actions = ReserveCard.legal_actions(board, player)
  # Return 1 from {e,s,o,d,r,g} where pool has e:2, s:2, o:2, d:2, r:2, g:1 → 6 options.
  assert len(actions) == 6


# ── meta-tests across action classes ──────────────────────────────────────────


@pytest.mark.parametrize("cls", ACTION_CLASSES)
def test_all_legal_actions_pass_is_valid(cls):
  # Locks the invariant: legal_actions ⊆ valid actions. If a class's enumerator
  # ever drifts from its validator, this fires.
  c1 = card(level=1, gem=Gem.Ruby, points=1, e=1)
  c2 = card(level=1, gem=Gem.Onyx, points=0, e=1, s=2)
  c3 = card(level=2, gem=Gem.Sapphire, points=2, e=2, r=3)
  board = make_board(
    dealt={1: [c1, c2], 2: [c3], 3: []},
    gems=GemStack(e=4, s=4, o=4, d=2, r=2, g=3),
  )
  player = make_player(gems=GemStack(e=2, s=1, g=1))

  actions = cls.legal_actions(board, player)
  for action in actions:
    assert action.is_valid(board, player), (
      f"{action} from legal_actions failed is_valid"
    )


@pytest.mark.parametrize("cls", ACTION_CLASSES)
def test_legal_actions_returns_no_duplicates(cls):
  # Catches enumeration bugs that yield the same action twice. Uses a
  # gem-overflow board state so take-2/take-3/reserve all generate returns,
  # which is where duplication would most easily creep in.
  c = card()
  board = make_board(
    dealt={1: [c], 2: [], 3: []},
    gems=GemStack(e=4, s=4, o=4, d=4, r=4, g=5),
  )
  player = make_player(gems=GemStack(e=2, s=2, o=2, d=2, r=2))  # 10 gems

  actions = cls.legal_actions(board, player)
  # Dataclass __eq__ compares all fields; duplicate enumeration would show here.
  assert len(actions) == len(set(map(repr, actions))), (
    f"{cls.__name__} produced duplicate legal actions"
  )
