import random

from engine import (
  BoardState,
  BuyCard,
  Gem,
  GemStack,
  PlayerState,
  ReserveCard,
  Table,
  TakeThreeGems,
  TakeTwoGems,
  legal_actions,
  take_turn,
)
from rl.splendor.actions import PASS, TAKE3_COMBOS, action_mask, decode


def no_returns(action) -> bool:
  return getattr(action, "returns", GemStack()).total == 0


def walk(rng: random.Random, table: Table, steps: int):
  """Yield states from a random game, picking an action type before an action."""
  for _ in range(steps):
    player = table.players[table.current]
    actions = legal_actions(table.board, player)
    if not actions:
      return
    yield table.board, player
    groups: dict[type, list] = {}
    for a in actions:
      groups.setdefault(type(a), []).append(a)
    take_turn(table, rng.choice(groups[rng.choice(list(groups))]))
    if player.points >= 15:
      return
    table.advance()


# ── layout ────────────────────────────────────────────────────────────────────


def test_take3_combos_are_distinct_and_gold_free():
  assert len(TAKE3_COMBOS) == 10
  assert len(set(TAKE3_COMBOS)) == 10
  assert all(Gem.Gold not in combo for combo in TAKE3_COMBOS)


def test_decode_covers_every_block():
  table = Table(2)
  board, player = table.board, table.players[0]
  assert isinstance(decode(0, board, player), TakeTwoGems)
  assert isinstance(decode(14, board, player), TakeThreeGems)
  assert isinstance(decode(15, board, player), BuyCard)
  assert isinstance(decode(41, board, player), ReserveCard)


def test_decode_none_for_empty_slots():
  board = BoardState(dealt_cards={1: [None, None, None, None], 2: [], 3: []})
  player = PlayerState()
  assert decode(15, board, player) is None
  assert decode(19, board, player) is None
  assert decode(27, board, player) is None


# ── mask ──────────────────────────────────────────────────────────────────────


def test_mask_matches_engine_legality():
  # the mask must equal exactly the legal actions that need no gem returns
  rng = random.Random(0)
  for _ in range(20):
    for board, player in walk(rng, Table(2), steps=60):
      mask = action_mask(board, player)
      actual = {repr(decode(i, board, player)) for i in range(PASS) if mask[i]}
      expected = {repr(a) for a in legal_actions(board, player) if no_returns(a)}
      assert actual == expected


def test_mask_is_never_empty():
  rng = random.Random(1)
  for _ in range(20):
    for board, player in walk(rng, Table(2), steps=40):
      assert action_mask(board, player).any()


def test_pass_is_legal_only_when_nothing_else_is():
  rng = random.Random(1)
  stuck_seen = False
  for _ in range(20):
    for board, player in walk(rng, Table(2), steps=40):
      mask = action_mask(board, player)
      if mask[:PASS].any():
        assert not mask[PASS]
      else:
        assert mask[PASS]
        stuck_seen = True
  assert stuck_seen, "the stuck case should be reachable, otherwise this proves nothing"


def test_mask_blocks_takes_at_capacity():
  board = Table(2).board
  player = PlayerState(gems=GemStack(e=2, s=2, o=2, d=2, r=1))  # 9 gems
  mask = action_mask(board, player)
  assert not mask[0:5].any()  # take 2 needs 2 free slots
  assert not mask[5:15].any()  # take 3 needs 3
  assert mask[30:42].any()  # reserve gains 1 gold, still fits
