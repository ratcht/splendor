from enum import Enum, auto
from dataclasses import dataclass, field

class Gem(Enum):
	Emerald=auto()
	Sapphire=auto()
	Onyx=auto()
	Diamond=auto()
	Ruby=auto()
	Gold=auto()

class CardLevel(Enum):
	Level1=1
	Level2=2
	Level3=3

type WinPoint = int
type GemStack = dict[Gem, int]

def empty_gem_stack() -> GemStack:
  return {gem: 0 for gem in Gem}

@dataclass
class Card:
	level: CardLevel
	gem: Gem
	points: WinPoint
	cost: GemStack

@dataclass
class Noble:
	requirements: GemStack # cards with gem
	points: WinPoint

type Deck = dict[CardLevel, list[Card]]

def empty_deck() -> Deck:
  return {level: [] for level in CardLevel}
