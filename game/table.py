from models import Card, Noble, Deck, Gem, GemStack, WinPoint, CardLevel, empty_gem_stack, empty_deck, fmt_gems
from presets import new_deck, new_nobles, new_starting_gems, deal
from dataclasses import dataclass, field

@dataclass(repr=False)
class BoardState:
	undealt_cards: Deck = field(default_factory=empty_deck)
	dealt_cards: Deck = field(default_factory=empty_deck)

	nobles: list[Noble] = field(default_factory=list)
	available_gems: GemStack = field(default_factory=empty_gem_stack)

	def __repr__(self) -> str:
		nobles = '  '.join(repr(n) for n in self.nobles)
		lines = [
			f"  gems  : {fmt_gems(self.available_gems)}",
			f"  nobles: {nobles}",
		]
		for level in CardLevel:
			cards = self.dealt_cards[level]
			row = '  '.join(repr(c) for c in cards) if cards else '(empty)'
			lines.append(f"  L{level.value}    : {row}")
		return "Board:\n" + '\n'.join(lines)

@dataclass(repr=False)
class PlayerState:
	# cards
	cards: list[Card] = field(default_factory=list)
	reserved_cards: list[Card] = field(default_factory=list)
	nobles: list[Noble] = field(default_factory=list)

	# scores
	gems: GemStack = field(default_factory=empty_gem_stack)

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


def new_board_state(num_players: int) -> BoardState:
	dealt, remaining = deal(new_deck())
	return BoardState(
		undealt_cards=remaining,
		dealt_cards=dealt,
		nobles=new_nobles(k=num_players+1),
		available_gems=new_starting_gems(),
	)

def new_player_state() -> PlayerState:
	return PlayerState()


@dataclass
class TableState:
	board: BoardState
	players: list[PlayerState]
	current: int


class Table:
	def __init__(self, num_players: int = 4):
		assert 2 <= num_players <= 4

		self.num_players = num_players
		self.board       = new_board_state(num_players)
		self.players     = [new_player_state() for _ in range(num_players)]
		self.current     = 0

	def state(self) -> TableState:
		return TableState(self.board, self.players, self.current)

	def advance(self) -> None:
		self.current = (self.current + 1) % self.num_players

	def __repr__(self) -> str:
		lines = [f"=== Splendor ({self.num_players}p) ===", repr(self.board)]
		for i, p in enumerate(self.players):
			lines.append(f"P{i+1}: {repr(p)}")
		return '\n'.join(lines)
