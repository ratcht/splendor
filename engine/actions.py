from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field, replace
from enum import Enum
from itertools import chain, combinations, combinations_with_replacement

from .models import Card, Gem, GemStack, OptionalDeck
from .state import BoardState, PlayerState

NON_GOLD_GEMS = [g for g in Gem if g != Gem.Gold]


class ActionType(Enum):
  TakeTwo = "Take 2 gems"
  TakeThree = "Take 3 gems"
  Buy = "Buy card"
  Reserve = "Reserve card"

  def __str__(self):
    return self.value


class Action(ABC):
  @classmethod
  @abstractmethod
  def legal_actions(cls, board: BoardState, player: PlayerState) -> list["Action"]: ...

  @abstractmethod
  def is_valid(self, board: BoardState, player: PlayerState) -> bool: ...

  @abstractmethod
  def apply(
    self, board: BoardState, player: PlayerState
  ) -> tuple[BoardState, PlayerState]: ...


def _enumerate_returns(pool: GemStack, excess: int) -> list[GemStack]:
  colors = [g for g in Gem if pool[g] > 0]
  results = []
  for combo in combinations_with_replacement(colors, excess):
    counts = Counter(combo)
    if all(counts[g] <= pool[g] for g in counts):
      results.append(GemStack.from_counts(dict(counts)))
  return results


def _remove_card(dealt: OptionalDeck, card: Card) -> OptionalDeck:
  return {
    lvl: [None if c == card else c for c in cards] if lvl == card.level else cards
    for lvl, cards in dealt.items()
  }


def _payment(card: Card, player: PlayerState) -> GemStack:
  discounts = player.discounts
  payments: dict[Gem, int] = {}
  gold_needed = 0
  for gem, cost in card.cost:
    effective = max(0, cost - discounts[gem])
    spent = min(effective, player.gems[gem])
    payments[gem] = spent
    gold_needed += effective - spent
  payments[Gem.Gold] = gold_needed
  return GemStack.from_counts(payments)


def _can_afford(card: Card, player: PlayerState) -> bool:
  return _payment(card, player).g <= player.gems.g


def check_nobles(
  board: BoardState, player: PlayerState
) -> tuple[BoardState, PlayerState]:
  # todo: if multiple qualify player should choose
  earned = next(
    (
      n
      for n in board.nobles
      if all(player.discounts[g] >= req for g, req in n.requirements)
    ),
    None,
  )
  if earned is None:
    return board, player
  return (
    replace(board, nobles=[n for n in board.nobles if n != earned]),
    replace(player, nobles=[*player.nobles, earned]),
  )


@dataclass
class TakeTwoGems(Action):
  gem: Gem
  returns: GemStack = field(default_factory=GemStack)

  def is_valid(self, board: BoardState, player: PlayerState) -> bool:
    return board.available_gems[self.gem] >= 4

  def apply(
    self, board: BoardState, player: PlayerState
  ) -> tuple[BoardState, PlayerState]:
    net = GemStack.from_counts({self.gem: 2}) - self.returns
    return (
      replace(board, available_gems=board.available_gems - net),
      replace(player, gems=player.gems + net),
    )

  @classmethod
  def legal_actions(cls, board: BoardState, player: PlayerState) -> list[Action]:
    eligible = [g for g in NON_GOLD_GEMS if board.available_gems[g] >= 4]
    if not eligible:
      return []
    excess = max(0, player.gems.total + 2 - 10)
    return [
      cls(gem=gem, returns=returns)
      for gem in eligible
      for returns in _enumerate_returns(
        player.gems + GemStack.from_counts({gem: 2}), excess
      )
    ]


@dataclass
class TakeThreeGems(Action):
  gems: tuple[Gem, Gem, Gem]
  returns: GemStack = field(default_factory=GemStack)

  def is_valid(self, board: BoardState, player: PlayerState) -> bool:
    return len(set(self.gems)) == 3 and all(
      board.available_gems[g] >= 1 for g in self.gems
    )

  def apply(
    self, board: BoardState, player: PlayerState
  ) -> tuple[BoardState, PlayerState]:
    net = GemStack.from_counts(dict.fromkeys(self.gems, 1)) - self.returns
    return (
      replace(board, available_gems=board.available_gems - net),
      replace(player, gems=player.gems + net),
    )

  @classmethod
  def legal_actions(cls, board: BoardState, player: PlayerState) -> list[Action]:
    eligible = [g for g in NON_GOLD_GEMS if board.available_gems[g] >= 1]
    if len(eligible) < 3:
      return []
    excess = max(0, player.gems.total + 3 - 10)
    return [
      cls(gems=gems, returns=returns)
      for gems in combinations(eligible, 3)
      for returns in _enumerate_returns(
        player.gems + GemStack.from_counts(dict.fromkeys(gems, 1)), excess
      )
    ]


@dataclass
class BuyCard(Action):
  card: Card

  def is_valid(self, board: BoardState, player: PlayerState) -> bool:
    on_board = any(self.card in cards for cards in board.dealt_cards.values())
    in_reserve = self.card in player.reserved_cards
    return (on_board or in_reserve) and _can_afford(self.card, player)

  def apply(
    self, board: BoardState, player: PlayerState
  ) -> tuple[BoardState, PlayerState]:
    pay = _payment(self.card, player)
    reserved = [c for c in player.reserved_cards if c != self.card]
    return (
      replace(
        board,
        dealt_cards=_remove_card(board.dealt_cards, self.card),
        available_gems=board.available_gems + pay,
      ),
      replace(
        player,
        cards=[*player.cards, self.card],
        reserved_cards=reserved,
        gems=player.gems - pay,
      ),
    )

  @classmethod
  def legal_actions(cls, board: BoardState, player: PlayerState) -> list[Action]:
    candidates = chain(
      (c for cards in board.dealt_cards.values() for c in cards if c is not None),
      player.reserved_cards,
    )
    return [cls(card=c) for c in candidates if _can_afford(c, player)]


@dataclass
class ReserveCard(Action):
  card: Card
  returns: GemStack = field(default_factory=GemStack)

  def is_valid(self, board: BoardState, player: PlayerState) -> bool:
    on_board = any(self.card in cards for cards in board.dealt_cards.values())
    return on_board and len(player.reserved_cards) < 3

  def apply(
    self, board: BoardState, player: PlayerState
  ) -> tuple[BoardState, PlayerState]:
    gold = GemStack(g=1 if board.available_gems.g > 0 else 0)
    net = gold - self.returns
    return (
      replace(
        board,
        dealt_cards=_remove_card(board.dealt_cards, self.card),
        available_gems=board.available_gems - net,
      ),
      replace(
        player,
        reserved_cards=[*player.reserved_cards, self.card],
        gems=player.gems + net,
      ),
    )

  @classmethod
  def legal_actions(cls, board: BoardState, player: PlayerState) -> list[Action]:
    if len(player.reserved_cards) >= 3:
      return []
    all_cards = [
      c for cards in board.dealt_cards.values() for c in cards if c is not None
    ]
    if not all_cards:
      return []
    gold_gained = 1 if board.available_gems.g > 0 else 0
    excess = max(0, player.gems.total + gold_gained - 10)
    pool = player.gems + GemStack(g=gold_gained)
    return [
      cls(card=card, returns=returns)
      for card in all_cards
      for returns in _enumerate_returns(pool, excess)
    ]


ACTION_TYPE_TO_CLASS: dict[ActionType, type[Action]] = {
  ActionType.TakeTwo: TakeTwoGems,
  ActionType.TakeThree: TakeThreeGems,
  ActionType.Buy: BuyCard,
  ActionType.Reserve: ReserveCard,
}
ACTION_CLASSES: list[type[Action]] = list(ACTION_TYPE_TO_CLASS.values())


def legal_actions(board: BoardState, player: PlayerState) -> list[Action]:
  return [
    action
    for action_cls in ACTION_CLASSES
    for action in action_cls.legal_actions(board, player)
  ]
