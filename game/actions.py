from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from models import Card, Deck, Gem, GemStack, empty_gem_stack
from table import BoardState, PlayerState


class Action(ABC):
  @abstractmethod
  def is_valid(self, board: BoardState, player: PlayerState) -> bool: ...

  @abstractmethod
  def apply(self, board: BoardState, player: PlayerState) -> tuple[BoardState, PlayerState]: ...


def _transfer(src: GemStack, dst: GemStack, amount: GemStack) -> tuple[GemStack, GemStack]:
  src = {g: v - amount[g] for g, v in src.items()}
  dst = {g: v + amount[g] for g, v in dst.items()}
  return src, dst

def _remove_card(dealt: Deck, card: Card) -> Deck:
  return {lvl: [c for c in cards if c != card] for lvl, cards in dealt.items()}

def _can_afford(card: Card, player: PlayerState) -> bool:
  discounts = player.discounts
  gold_needed = 0
  for gem, cost in card.cost.items():
    gold_needed += max(0, cost - discounts[gem] - player.gems[gem])
  return gold_needed <= player.gems[Gem.Gold]

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

  def is_valid(self, board: BoardState, player: PlayerState) -> bool:
    return board.available_gems[self.gem] >= 4

  def apply(self, board: BoardState, player: PlayerState) -> tuple[BoardState, PlayerState]:
    take = {**empty_gem_stack(), self.gem: 2}
    board_gems, gems = _transfer(board.available_gems, player.gems, take)
    gems, board_gems = _transfer(gems, board_gems, self.returns)
    return replace(board, available_gems=board_gems), replace(player, gems=gems)


@dataclass
class TakeThreeGems(Action):
  gems: tuple[Gem, Gem, Gem]
  returns: GemStack = field(default_factory=empty_gem_stack)

  def is_valid(self, board: BoardState, player: PlayerState) -> bool:
    return (
      len(set(self.gems)) == 3
      and all(board.available_gems[g] >= 1 for g in self.gems)
    )

  def apply(self, board: BoardState, player: PlayerState) -> tuple[BoardState, PlayerState]:
    take = {**empty_gem_stack(), **{g: 1 for g in self.gems}}
    board_gems, gems = _transfer(board.available_gems, player.gems, take)
    gems, board_gems = _transfer(gems, board_gems, self.returns)
    return replace(board, available_gems=board_gems), replace(player, gems=gems)


@dataclass
class BuyCard(Action):
  card: Card

  def is_valid(self, board: BoardState, player: PlayerState) -> bool:
    on_board   = any(self.card in cards for cards in board.dealt_cards.values())
    in_reserve = self.card in player.reserved_cards
    return (on_board or in_reserve) and _can_afford(self.card, player)

  def apply(self, board: BoardState, player: PlayerState) -> tuple[BoardState, PlayerState]:
    pay = _payment(self.card, player)
    gems, board_gems = _transfer(player.gems, board.available_gems, pay)
    reserved = [c for c in player.reserved_cards if c != self.card]
    return (
      replace(board, dealt_cards=_remove_card(board.dealt_cards, self.card), available_gems=board_gems),
      replace(player, cards=[*player.cards, self.card], reserved_cards=reserved, gems=gems)
    )


@dataclass
class ReserveCard(Action):
  card: Card
  returns: GemStack = field(default_factory=empty_gem_stack)

  def is_valid(self, board: BoardState, player: PlayerState) -> bool:
    on_board = any(self.card in cards for cards in board.dealt_cards.values())
    return on_board and len(player.reserved_cards) < 3

  def apply(self, board: BoardState, player: PlayerState) -> tuple[BoardState, PlayerState]:
    gold = {**empty_gem_stack(), Gem.Gold: 1 if board.available_gems[Gem.Gold] > 0 else 0}
    board_gems, gems = _transfer(board.available_gems, player.gems, gold)
    gems, board_gems = _transfer(gems, board_gems, self.returns)
    return (
      replace(board, dealt_cards=_remove_card(board.dealt_cards, self.card), available_gems=board_gems),
      replace(player, reserved_cards=[*player.reserved_cards, self.card], gems=gems)
    )
