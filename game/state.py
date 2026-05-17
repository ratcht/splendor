from dataclasses import dataclass, field
from tabulate import tabulate
from models import Card, Noble, Deck, GemStack, WinPoint, CardLevel, empty_gem_stack, empty_deck, fmt_gems


@dataclass(repr=False)
class BoardState:
  undealt_cards:  Deck     = field(default_factory=empty_deck)
  dealt_cards:    Deck     = field(default_factory=empty_deck)
  nobles:         list[Noble] = field(default_factory=list)
  available_gems: GemStack = field(default_factory=empty_gem_stack)

  def __repr__(self) -> str:
    def fmt_card(c: Card) -> str:
      return f"[+{c.gem.name[0]} {c.points}pt | {fmt_gems(c.cost)}]"

    rows = [[f"L{lvl.value}", *(fmt_card(c) for c in self.dealt_cards[lvl])] for lvl in reversed(CardLevel)]
    nobles = '  '.join(repr(n) for n in self.nobles)
    return (
      f"Board:\n"
      f"  gems  : {fmt_gems(self.available_gems)}\n"
      f"  nobles: {nobles}\n"
      f"{tabulate(rows, tablefmt='plain')}"
    )


@dataclass(repr=False)
class PlayerState:
  cards:          list[Card]  = field(default_factory=list)
  reserved_cards: list[Card]  = field(default_factory=list)
  nobles:         list[Noble] = field(default_factory=list)
  gems:           GemStack    = field(default_factory=empty_gem_stack)

  @property
  def total_gems(self) -> int:
    return sum(self.gems.values())

  @property
  def discounts(self) -> GemStack:
    counts = empty_gem_stack()
    for card in self.cards:
      counts[card.gem] += 1
    return counts

  @property
  def points(self) -> WinPoint:
    return sum(c.points for c in self.cards) + sum(n.points for n in self.nobles)

  def __repr__(self) -> str:
    return (
      f"Player: {self.points}pt | "
      f"gems:{fmt_gems(self.gems)} | "
      f"cards:{len(self.cards)} (+{fmt_gems(self.discounts)}) | "
      f"rsrv:{len(self.reserved_cards)} | "
      f"nobles:{len(self.nobles)}"
    )


@dataclass
class TableState:
  board:   BoardState
  players: list[PlayerState]
  current: int

  def __repr__(self) -> str:
    lines = [repr(self.board)]
    for i, p in enumerate(self.players):
      marker = '>' if i == self.current else ' '
      lines.append(f"{marker} P{i+1}: {repr(p)}")
    return '\n'.join(lines)
