from dataclasses import replace
from typing import Protocol

from .models import LEVELS, Card, Gem, GemStack, Level, Noble, empty_optional_deck
from .presets import (
  ALL_CARDS,
  ALL_NOBLES,
  deal,
  new_deck,
  new_nobles,
  new_starting_gems,
)
from .state import BoardState


class Dealer(Protocol):
  def initial_board(self, num_players: int) -> BoardState: ...
  def refill(self, board: BoardState) -> BoardState: ...


# ========== random ==========


class RandomDealer:
  def initial_board(self, num_players: int) -> BoardState:
    dealt, remaining = deal(new_deck())
    return BoardState(
      undealt_cards=remaining,
      dealt_cards=dealt,
      nobles=new_nobles(k=num_players + 1),
      available_gems=new_starting_gems(),
    )

  def refill(self, board: BoardState) -> BoardState:
    dealt = {lvl: list(cards) for lvl, cards in board.dealt_cards.items()}
    undealt = {lvl: list(cards) for lvl, cards in board.undealt_cards.items()}
    for lvl in LEVELS:
      for i, card in enumerate(dealt[lvl]):
        if card is None and undealt[lvl]:
          dealt[lvl][i] = undealt[lvl].pop()
    return replace(board, dealt_cards=dealt, undealt_cards=undealt)


# ========== interactive ==========


class InteractiveDealer:
  def initial_board(self, num_players: int) -> BoardState:
    print("\n=== Initial setup ===")
    dealt = empty_optional_deck()
    undealt = {lvl: list(ALL_CARDS[lvl]) for lvl in LEVELS}

    for lvl in reversed(LEVELS):
      print(f"\nDeal 4 L{lvl} cards:")
      for _ in range(4):
        card = _prompt_card(lvl, undealt[lvl])
        dealt[lvl].append(card)
        undealt[lvl].remove(card)

    nobles = _prompt_nobles(num_players + 1)
    return BoardState(
      undealt_cards=undealt,
      dealt_cards=dealt,
      nobles=nobles,
      available_gems=new_starting_gems(),
    )

  def refill(self, board: BoardState) -> BoardState:
    dealt = {lvl: list(cards) for lvl, cards in board.dealt_cards.items()}
    undealt = {lvl: list(cards) for lvl, cards in board.undealt_cards.items()}
    for lvl in LEVELS:
      holes = [i for i, card in enumerate(dealt[lvl]) if card is None]
      if not holes or not undealt[lvl]:
        continue
      print(f"\nL{lvl} needs {len(holes)} card(s) to refill:")
      for i in holes:
        if not undealt[lvl]:
          break
        card = _prompt_card(lvl, undealt[lvl])
        dealt[lvl][i] = card
        undealt[lvl].remove(card)
    return replace(board, dealt_cards=dealt, undealt_cards=undealt)


def _parse_card(raw: str) -> tuple[Gem, int, GemStack] | None:
  bonus, points = None, None
  cost: dict[Gem, int] = {}
  for tok in raw.lower().replace("|", " ").split():
    if tok.startswith("+") and len(tok) == 2:
      bonus = next((g for g in Gem if g.name[0].lower() == tok[1]), None)
      if bonus is None:
        return None
    elif tok.endswith("pt"):
      try:
        points = int(tok[:-2])
      except ValueError:
        return None
    else:
      i = 0
      while i < len(tok) and tok[i].isdigit():
        i += 1
      if i == 0 or i == len(tok):
        return None
      gem = next((g for g in Gem if g.name[0].lower() == tok[i:]), None)
      if gem is None:
        return None
      cost[gem] = int(tok[:i])
  if bonus is None or points is None:
    return None
  return bonus, points, GemStack.from_counts(cost)


def _find_card(raw: str, available: list[Card]) -> Card | None:
  parsed = _parse_card(raw)
  if not parsed:
    return None
  bonus, points, cost = parsed
  return next(
    (c for c in available if c.gem == bonus and c.points == points and c.cost == cost),
    None,
  )


def _prompt_card(level: Level, available: list[Card]) -> Card:
  print("  Format: +<gem> <pts>pt <cost>   e.g. +E 1pt 4D")
  while True:
    raw = input(f"  L{level} card: ").strip()
    card = _find_card(raw, available)
    if card is not None:
      return card
    print(f"  No matching L{level} card in remaining pool.")


def _prompt_nobles(k: int) -> list[Noble]:
  print(f"\nPick {k} nobles:")
  for i, n in enumerate(ALL_NOBLES):
    print(f"  {i + 1}. {n!r}")
  selected: list[Noble] = []
  while len(selected) < k:
    raw = input(f"  Noble {len(selected) + 1}: ").strip()
    try:
      idx = int(raw) - 1
      if 0 <= idx < len(ALL_NOBLES) and ALL_NOBLES[idx] not in selected:
        selected.append(ALL_NOBLES[idx])
      else:
        print("  Invalid or already picked.")
    except ValueError:
      print("  Enter a number.")
  return selected
