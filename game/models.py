from enum import Enum, auto
from dataclasses import dataclass, field

class Gem(Enum):
	Emerald=auto() # Green
	Sapphire=auto() # Blue
	Onyx=auto() # Black
	Diamond=auto() # White
	Ruby=auto() # Red
	Gold=auto() # Gold

class CardLevel(Enum):
	Level1=1
	Level2=2
	Level3=3

type WinPoint = int
type GemStack = dict[Gem, int]

def empty_gem_stack() -> GemStack:
  return {gem: 0 for gem in Gem}

def fmt_gems(stack: GemStack) -> str:
  parts = [f"{v}{g.name[0]}" for g, v in stack.items() if v > 0]
  return ' '.join(parts) if parts else '0'

@dataclass(repr=False)
class Card:
	level: CardLevel
	gem: Gem
	points: WinPoint
	cost: GemStack

	def __repr__(self) -> str:
		return f"[L{self.level.value} +{self.gem.name[0]} {self.points}pt | {fmt_gems(self.cost)}]"

@dataclass(repr=False)
class Noble:
	requirements: GemStack
	points: WinPoint

	def __repr__(self) -> str:
		return f"Noble({self.points}pt | {fmt_gems(self.requirements)})"

type Deck = dict[CardLevel, list[Card]]

def empty_deck() -> Deck:
  return {level: [] for level in CardLevel}
