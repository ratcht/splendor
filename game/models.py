from enum import Enum, auto
from dataclasses import dataclass, field

class Gem(Enum):
  Emerald  = auto()  # Green
  Sapphire = auto()  # Blue
  Onyx     = auto()  # Black
  Diamond  = auto()  # White
  Ruby     = auto()  # Red
  Gold     = auto()  # Gold

class CardLevel(Enum):
  Level1 = 1
  Level2 = 2
  Level3 = 3

type WinPoint = int


@dataclass(frozen=True, repr=False)
class GemStack:
  e: int = 0  # emerald
  s: int = 0  # sapphire
  o: int = 0  # onyx
  d: int = 0  # diamond
  r: int = 0  # ruby
  g: int = 0  # gold

  def __getitem__(self, gem: Gem) -> int:
    return getattr(self, gem.name[0].lower())

  def __iter__(self):
    for g in Gem:
      yield g, self[g]

  def __add__(self, other: "GemStack") -> "GemStack":
    return GemStack.from_counts({g: self[g] + other[g] for g in Gem})

  def __sub__(self, other: "GemStack") -> "GemStack":
    return GemStack.from_counts({g: self[g] - other[g] for g in Gem})

  def __le__(self, other: "GemStack") -> bool:
    return all(self[g] <= other[g] for g in Gem)

  @property
  def total(self) -> int:
    return sum(self[g] for g in Gem)

  def __repr__(self) -> str:
    parts = [f"{n}{g.name[0]}" for g, n in self if n > 0]
    return " ".join(parts) if parts else "0"

  @classmethod
  def from_counts(cls, counts: dict[Gem, int]) -> "GemStack":
    return cls(**{g.name[0].lower(): n for g, n in counts.items()})


@dataclass(frozen=True, repr=False)
class Card:
  level:  CardLevel
  gem:    Gem
  points: WinPoint
  cost:   GemStack

  def __repr__(self) -> str:
    return f"[L{self.level.value} +{self.gem.name[0]} {self.points}pt | {self.cost!r}]"


@dataclass(frozen=True, repr=False)
class Noble:
  requirements: GemStack
  points:       WinPoint

  def __repr__(self) -> str:
    return f"Noble({self.points}pt | {self.requirements!r})"


type Deck = dict[CardLevel, list[Card]]

def empty_deck() -> Deck:
  return {level: [] for level in CardLevel}
