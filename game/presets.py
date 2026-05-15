from models import Card, Noble, CardLevel, Gem, GemStack, Deck
import random


# ── helpers ───────────────────────────────────────────────────────

def _build_gem_stack(e=0, d=0, s=0, o=0, r=0) -> GemStack:
  """Build a cost/requirement GemStack.
  e=Emerald, d=Diamond, s=Sapphire, o=Onyx, r=Ruby.
  Gold is always 0 for card costs and noble requirements.
  """
  return {
    Gem.Emerald:  e,
    Gem.Diamond:  d,
    Gem.Sapphire: s,
    Gem.Onyx:     o,
    Gem.Ruby:     r,
    Gem.Gold:     0,
  }


E = Gem.Emerald
D = Gem.Diamond
S = Gem.Sapphire
O = Gem.Onyx
R = Gem.Ruby
L1 = CardLevel.Level1
L2 = CardLevel.Level2
L3 = CardLevel.Level3


# ── development cards ────────────────────────────────────────────────────────
# format: (gem_bonus, points, (e, d, s, o, r))

_RAW_L1 = [
  (E, 0, (1, 0, 1, 1, 0)),
  (D, 1, (4, 0, 0, 0, 0)),
  (R, 0, (0, 3, 0, 0, 0)),
  (S, 0, (1, 1, 0, 1, 1)),
  (S, 0, (3, 0, 1, 0, 1)),
  (S, 0, (0, 1, 0, 2, 0)),
  (D, 0, (0, 0, 3, 0, 0)),
  (R, 0, (1, 2, 0, 2, 0)),
  (R, 0, (0, 1, 0, 3, 1)),
  (E, 0, (0, 0, 1, 2, 2)),
  (R, 0, (1, 2, 1, 1, 0)),
  (E, 0, (0, 0, 2, 0, 2)),
  (S, 0, (2, 0, 0, 2, 0)),
  (S, 0, (1, 1, 0, 1, 2)),
  (O, 0, (0, 2, 2, 0, 1)),
  (E, 1, (0, 0, 0, 4, 0)),
  (E, 0, (0, 1, 1, 1, 1)),
  (R, 0, (1, 1, 1, 1, 0)),
  (R, 1, (0, 4, 0, 0, 0)),
  (R, 0, (0, 2, 0, 0, 2)),
  (D, 0, (2, 0, 1, 1, 1)),
  (D, 0, (0, 0, 2, 2, 0)),
  (D, 0, (0, 3, 1, 1, 0)),
  (S, 0, (2, 1, 0, 0, 2)),
  (S, 1, (0, 0, 0, 0, 4)),
  (O, 0, (1, 1, 1, 0, 1)),
  (O, 0, (3, 0, 0, 0, 0)),
  (R, 0, (1, 0, 2, 0, 0)),
  (D, 0, (0, 0, 0, 1, 2)),
  (E, 0, (0, 2, 1, 0, 0)),
  (O, 0, (1, 1, 2, 0, 1)),
  (E, 0, (1, 1, 3, 0, 0)),
  (D, 0, (2, 0, 2, 1, 0)),
  (D, 0, (1, 0, 1, 1, 1)),
  (O, 1, (0, 0, 4, 0, 0)),
  (E, 0, (0, 0, 0, 0, 3)),
  (O, 0, (2, 2, 0, 0, 0)),
  (O, 0, (2, 0, 0, 0, 1)),
  (O, 0, (1, 0, 0, 1, 3)),
  (S, 0, (0, 0, 0, 3, 0)),
]

_RAW_L2 = [
  (R, 2, (0, 0, 0, 5, 0)),
  (D, 2, (0, 0, 0, 3, 5)),
  (O, 3, (0, 0, 0, 6, 0)),
  (E, 1, (2, 3, 0, 0, 3)),
  (R, 1, (0, 2, 0, 3, 2)),
  (E, 2, (0, 4, 2, 1, 0)),
  (D, 1, (0, 2, 3, 0, 3)),
  (S, 1, (2, 0, 2, 0, 3)),
  (S, 2, (0, 5, 3, 0, 0)),
  (O, 1, (2, 3, 2, 0, 0)),
  (O, 2, (0, 5, 0, 0, 0)),
  (E, 2, (3, 0, 5, 0, 0)),
  (D, 1, (3, 0, 0, 2, 2)),
  (S, 2, (0, 2, 0, 4, 1)),
  (R, 2, (2, 1, 4, 0, 0)),
  (R, 2, (0, 3, 0, 5, 0)),
  (S, 1, (3, 0, 2, 3, 0)),
  (D, 2, (1, 0, 0, 2, 4)),
  (D, 2, (0, 0, 0, 0, 5)),
  (R, 1, (0, 0, 3, 3, 2)),
  (E, 2, (5, 0, 0, 0, 0)),
  (E, 1, (0, 2, 3, 2, 0)),
  (E, 3, (6, 0, 0, 0, 0)),
  (R, 3, (0, 0, 0, 0, 6)),
  (O, 2, (5, 0, 0, 0, 3)),
  (S, 3, (0, 0, 6, 0, 0)),
  (D, 3, (0, 6, 0, 0, 0)),
  (S, 2, (0, 0, 5, 0, 0)),
  (O, 1, (3, 3, 0, 2, 0)),
  (O, 2, (4, 0, 1, 0, 2)),
]

_RAW_L3 = [
  (D, 3, (3, 0, 3, 3, 5)),
  (O, 4, (3, 0, 0, 3, 6)),
  (S, 4, (0, 7, 0, 0, 0)),
  (S, 4, (0, 6, 3, 3, 0)),
  (E, 4, (3, 3, 6, 0, 0)),
  (E, 3, (0, 5, 3, 3, 3)),
  (S, 3, (3, 3, 0, 5, 3)),
  (R, 3, (3, 3, 5, 3, 0)),
  (S, 5, (0, 7, 3, 0, 0)),
  (D, 4, (0, 0, 0, 7, 0)),
  (R, 4, (6, 0, 3, 0, 3)),
  (O, 3, (5, 3, 3, 0, 3)),
  (O, 4, (0, 0, 0, 0, 7)),
  (D, 5, (0, 3, 0, 7, 0)),
  (D, 4, (0, 3, 0, 6, 3)),
  (R, 5, (7, 0, 0, 0, 3)),
  (R, 4, (7, 0, 0, 0, 0)),
  (E, 4, (0, 0, 7, 0, 0)),
  (O, 5, (0, 0, 0, 3, 7)),
  (E, 5, (3, 0, 7, 0, 0)),
]


def _build_cards(raw: list, level: CardLevel) -> list[Card]:
  return [Card(level, gem, pts, _build_gem_stack(*cost)) for gem, pts, cost in raw]


# ── noble raw data ───────────────────────────────────────────────────────────
# each noble is worth 3 points
# format: (e, d, s, o, r) required card bonuses.

_RAW_NOBLES = [
  (4, 0, 4, 0, 0),
  (0, 0, 0, 4, 4),
  (3, 3, 3, 0, 0),
  (0, 3, 0, 3, 3),
  (0, 4, 0, 4, 0),
  (4, 0, 0, 0, 4),
  (0, 4, 4, 0, 0),
  (3, 0, 3, 0, 3),
  (3, 0, 0, 3, 3),
  (0, 3, 3, 3, 0),
]


# ── public ─────────────────────────────────────────────────────────

ALL_CARDS: Deck = {
  CardLevel.Level1: _build_cards(_RAW_L1, L1),
  CardLevel.Level2: _build_cards(_RAW_L2, L2),
  CardLevel.Level3: _build_cards(_RAW_L3, L3),
}

ALL_NOBLES: list[Noble] = [
  Noble(requirements=_build_gem_stack(*req), points=3)
  for req in _RAW_NOBLES
]

def new_deck() -> Deck:
  deck = {level: cards.copy() for level, cards in ALL_CARDS.items()}
  for cards in deck.values():
    random.shuffle(cards)
  return deck

def new_nobles(k: int = 5) -> list[Noble]:
	return random.sample(ALL_NOBLES, k=k)

def new_starting_gems() -> GemStack:
	return {
    Gem.Emerald:  7,
    Gem.Diamond:  7,
    Gem.Sapphire: 7,
    Gem.Onyx:     7,
    Gem.Ruby:     7,
    Gem.Gold:     5,
	}

def deal(deck: Deck, n: int = 4) -> tuple[Deck, Deck]:
  dealt     = {level: cards[:n] for level, cards in deck.items()}
  remaining = {level: cards[n:] for level, cards in deck.items()}
  return dealt, remaining
