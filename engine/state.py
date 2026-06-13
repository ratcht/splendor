from collections import Counter
from dataclasses import dataclass, field

from tabulate import tabulate

from .models import (
  LEVELS,
  Card,
  Deck,
  GemStack,
  Noble,
  OptionalDeck,
  WinPoint,
  empty_deck,
  empty_optional_deck,
)


@dataclass(repr=False)
class BoardState:
  undealt_cards: Deck = field(default_factory=empty_deck)
  dealt_cards: OptionalDeck = field(default_factory=empty_optional_deck)
  nobles: list[Noble] = field(default_factory=list)
  available_gems: GemStack = field(default_factory=GemStack)

  def __repr__(self) -> str:
    def fmt_card(c: Card | None) -> str:
      return f"[+{c.gem.name[0]} {c.points}pt | {c.cost!r}]" if c else "[_]"

    rows = [
      [f"L{lvl}", *(fmt_card(c) for c in self.dealt_cards[lvl])]
      for lvl in reversed(LEVELS)
    ]
    nobles = "  ".join(repr(n) for n in self.nobles)
    return (
      f"Board:\n"
      f"  gems  : {self.available_gems!r}\n"
      f"  nobles: {nobles}\n"
      f"{tabulate(rows, tablefmt='plain')}"
    )


@dataclass(repr=False)
class PlayerState:
  cards: list[Card] = field(default_factory=list)
  reserved_cards: list[Card] = field(default_factory=list)
  nobles: list[Noble] = field(default_factory=list)
  gems: GemStack = field(default_factory=GemStack)

  @property
  def discounts(self) -> GemStack:
    return GemStack.from_counts(Counter(card.gem for card in self.cards))

  @property
  def points(self) -> WinPoint:
    return sum(c.points for c in self.cards) + sum(n.points for n in self.nobles)

  def __repr__(self) -> str:
    return (
      f"Player: {self.points}pt | "
      f"gems:{self.gems!r} | "
      f"cards:{len(self.cards)} (+{self.discounts!r}) | "
      f"rsrv:{len(self.reserved_cards)} | "
      f"nobles:{len(self.nobles)}"
    )


@dataclass
class TableState:
  board: BoardState
  players: list[PlayerState]
  current: int

  def __repr__(self) -> str:
    lines = [repr(self.board)]
    for i, p in enumerate(self.players):
      marker = ">" if i == self.current else " "
      lines.append(f"{marker} P{i + 1}: {repr(p)}")
    return "\n".join(lines)
