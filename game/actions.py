from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field, replace
from models import Card, Deck, Gem, GemStack, empty_gem_stack
from state import BoardState, PlayerState

from itertools import combinations_with_replacement
from collections import Counter


class ActionType(Enum):
  TakeTwo   = "Take 2 gems"
  TakeThree = "Take 3 gems"
  Buy       = "Buy card"
  Reserve   = "Reserve card"

  def __str__(self): return self.value


class Action(ABC):
	@classmethod
	@abstractmethod
	def legal_actions(cls, board: BoardState, player: PlayerState) -> list[Actions]: ...

	@staticmethod
  @abstractmethod
  def is_valid(self, board: BoardState, player: PlayerState) -> bool: ...

  @abstractmethod
  def apply(self, board: BoardState, player: PlayerState) -> tuple[BoardState, PlayerState]: ...


def _transfer(src: GemStack, dst: GemStack, amount: GemStack) -> tuple[GemStack, GemStack]:
  src = {g: v - amount[g] for g, v in src.items()}
  dst = {g: v + amount[g] for g, v in dst.items()}
  return src, dst

def _enumerate_returns(pool: GemStack, excess: int) -> list[GemStack]:
  colors = [g for g in Gem if pool[g] > 0]
  results = []
  for combo in combinations_with_replacement(colors, excess):
    counts = Counter(combo)
    if all(counts[g] <= pool[g] for g in counts):
      results.append({**empty_gem_stack(), **counts})
  return results

def _remove_card(dealt: Deck, card: Card) -> Deck:
  return {lvl: [c for c in cards if c != card] for lvl, cards in dealt.items()}

def _payment(card: Card, player: PlayerState) -> GemStack:
  discounts = player.discounts
  payment = empty_gem_stack()
  gold_needed = 0
  for gem, cost in card.cost.items():
    effective = max(0, cost - discounts[gem])
    spent = min(effective, player.gems[gem])
    payment[gem] = spent
    gold_needed += effective - spent
  payment[Gem.Gold] = gold_needed
  return payment

def _can_afford(card: Card, player: PlayerState) -> bool:
  return _payment(card, player)[Gem.Gold] <= player.gems[Gem.Gold]

def check_nobles(board: BoardState, player: PlayerState) -> tuple[BoardState, PlayerState]:
  # todo: if multiple qualify player should choose
  earned = next((n for n in board.nobles if all(player.discounts[g] >= req for g, req in n.requirements.items())), None)
  if earned is None:
    return board, player
  return (
    replace(board, nobles=[n for n in board.nobles if n != earned]),
    replace(player, nobles=[*player.nobles, earned])
  )


@dataclass
class TakeTwoGems(Action):
  gem: Gem
  returns: GemStack = field(default_factory=empty_gem_stack)

	@staticmethod
  def is_valid(gem: Gem, board: BoardState, player: PlayerState) -> bool:
    return board.available_gems[gem] >= 4

  def apply(self, board: BoardState, player: PlayerState) -> tuple[BoardState, PlayerState]:
    take = {**empty_gem_stack(), self.gem: 2}
    board_gems, gems = _transfer(board.available_gems, player.gems, take)
    gems, board_gems = _transfer(gems, board_gems, self.returns)
    return replace(board, available_gems=board_gems), replace(player, gems=gems)

	def legal_actions(cls, board: BoardState, player: PlayerState) -> list[TakeTwoGems]:
		eligible = [g for g in NON_GOLD_GEMS if board.available_gems[g] >= 4]
		if not eligible: return []

		excess = max(0, player.total_gems + 2 - 10)

		return [
			cls(gem=gem, returns=returns)
			for gem in eligible
			for returns in _enumerate_returns({g: player.gems[g] + (2 if g == gem else 0) for g in Gem}, excess)
		]



@dataclass
class TakeThreeGems(Action):
  gems: tuple[Gem, Gem, Gem]
  returns: GemStack = field(default_factory=empty_gem_stack)

	@staticmethod
  def is_valid(gems: tuple[Gem, Gem, Gem], board: BoardState, player: PlayerState) -> bool:
    return (
      len(set(gems)) == 3
      and all(board.available_gems[g] >= 1 for g in gems)
    )

  def apply(self, board: BoardState, player: PlayerState) -> tuple[BoardState, PlayerState]:
    take = {**empty_gem_stack(), **{g: 1 for g in self.gems}}
    board_gems, gems = _transfer(board.available_gems, player.gems, take)
    gems, board_gems = _transfer(gems, board_gems, self.returns)
    return replace(board, available_gems=board_gems), replace(player, gems=gems)

	def legal_actions(cls, board: BoardState, player: PlayerState) -> list[TakeThreeGems]:
		eligible = [g for g in NON_GOLD_GEMS if board.available_gems[g] >= 1]
		if not eligible: return []
		eligible_sets = combinations(eligible, 3)

		excess = max(0, player.total_gems + 3 - 10)

		return [
			cls(gems=gems, returns=returns)
			for gems in eligible_sets
			for returns in _enumerate_returns({g: player.gems[g] + (1 if g in gems else 0) for g in Gem}, excess)
		]

@dataclass
class BuyCard(Action):
  card: Card

	@staticmethod
  def is_valid(card: Card, board: BoardState, player: PlayerState) -> bool:
    on_board   = any(card in cards for cards in board.dealt_cards.values())
    in_reserve = card in player.reserved_cards
    return (on_board or in_reserve) and _can_afford(card, player)

  def apply(self, board: BoardState, player: PlayerState) -> tuple[BoardState, PlayerState]:
    pay = _payment(self.card, player)
    gems, board_gems = _transfer(player.gems, board.available_gems, pay)
    reserved = [c for c in player.reserved_cards if c != self.card]
    return (
      replace(board, dealt_cards=_remove_card(board.dealt_cards, self.card), available_gems=board_gems),
      replace(player, cards=[*player.cards, self.card], reserved_cards=reserved, gems=gems)
    )

	def legal_actions(cls, board: BoardState, player: PlayerState) -> list[BuyCard]:
	  affordable  = [
			cls(c) for cards in chain(board.dealt_cards.values(), player.reserved_cards)
			for c in cards
			if cls.is_valid(c, board, player)
		]
	  if not affordable: return []



@dataclass
class ReserveCard(Action):
  card: Card
  returns: GemStack = field(default_factory=empty_gem_stack)

	@staticmethod
  def is_valid(card: Card, board: BoardState, player: PlayerState) -> bool:
    on_board = any(card in cards for cards in board.dealt_cards.values())
    return on_board and len(player.reserved_cards) < 3

  def apply(self, board: BoardState, player: PlayerState) -> tuple[BoardState, PlayerState]:
    gold = {**empty_gem_stack(), Gem.Gold: 1 if board.available_gems[Gem.Gold] > 0 else 0}
    board_gems, gems = _transfer(board.available_gems, player.gems, gold)
    gems, board_gems = _transfer(gems, board_gems, self.returns)
    return (
      replace(board, dealt_cards=_remove_card(board.dealt_cards, self.card), available_gems=board_gems),
      replace(player, reserved_cards=[*player.reserved_cards, self.card], gems=gems)
    )

	def legal_actions(cls, board: BoardState, player: PlayerState) -> list[ReserveCard]:
		all_cards = [c for cards in board.dealt_cards.values() for c in cards]

		if len(player.reserved_cards) >= 3: return []
		if not all_cards: return []

		excess = max(0, player.total_gems + 3 - 10)

		return [
			cls(card=card, returns=returns)
			for card in all_cards
			for returns in _enumerate_returns({g: player.gems[g] + (1 if g == Gems.Gold else 0) for g in Gem}, excess)
		]
