from types import Card, Noble, Deck, Gem, empty_gem_stack, empty_deck, WinPoint
from presets import CARDS, NOBLES, new_deck, new_nobles, new_starting_gems

@dataclass
class BoardState:
	undealt_cards: Deck = field(default_factory=empty_deck)
	dealt_cards: Deck = field(default_factory=empty_deck)

	nobles: list[Noble] = field(default_factory=list)
	available_gems: GemStack = field(default_factory=empty_gem_stack)

@dataclass
class PlayerState:
	# cards
	cards: list[Card] = field(default_factory=list)
	reserved_cards: list[Card] = field(default_factory=list)
	nobles: list[Noble] = field(default_factory=list)

	# scores
	gems: GemStack = field(default_factory=empty_gem_stack)
	points: WinPoint = 0

	@property
	def total_gems(self) -> int:
    return sum(self.gems.values())

	@property
	def discounts(self) -> GemStack:
		counts = empty_gem_stack()
		for card in self.cards:
			counts[card.gem] += 1
    return counts

def new_board_state(num_players: int) -> BoardState:
	return BoardState(
		undealt_cards=new_deck(),
		nobles=new_nobles(k=num_players+1),
		available_gems=new_starting_gems(),
	)

def new_player_state() -> PlayerState:
	return PlayerState()


class Table:
	def __init__(self, num_players: int):
		assert 2 <= num_players <= 4

		self.num_players = num_players
		self.board = new_board_state(self.num_players)
		self.players = [
			new_player_state() for _ in range(self.num_players)
		]
