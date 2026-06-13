from .dealer import Dealer, RandomDealer
from .state import PlayerState, TableState


class Table:
  def __init__(self, num_players: int = 4, dealer: Dealer | None = None):
    assert 2 <= num_players <= 4

    self.num_players = num_players
    self.dealer = dealer or RandomDealer()
    self.board = self.dealer.initial_board(num_players)
    self.players = [PlayerState() for _ in range(num_players)]
    self.current = 0

  def state(self) -> TableState:
    return TableState(self.board, self.players, self.current)

  def advance(self) -> None:
    self.current = (self.current + 1) % self.num_players

  def __repr__(self) -> str:
    return repr(self.state())
