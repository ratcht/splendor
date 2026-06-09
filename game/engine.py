from state import PlayerState
from table import Table
from actions import Action, check_nobles
from strategy.interface import Strategy
from dealer import Dealer


def take_turn(table: Table, action: Action) -> None:
  player = table.players[table.current]
  if not action.is_valid(table.board, player):
    raise ValueError(f"invalid action: {action}")
  board, player = action.apply(table.board, player)
  board, player = check_nobles(board, player)
  table.board = table.dealer.refill(board)
  table.players[table.current] = player


def run_game(agents: list[Strategy], dealer: Dealer = None, max_turns: int = 100, verbose: bool = False) -> tuple[int, PlayerState]:
  table     = Table(len(agents), dealer=dealer)
  game_over = False

  for _ in range(max_turns):
    if verbose:
      print(f"\n{table.state()!r}\n")

    action = agents[table.current].choose_action(table.state())
    take_turn(table, action)

    if table.players[table.current].points >= 15:
      game_over = True

    if game_over and table.current == table.num_players - 1:
      break

    table.advance()

  return max(enumerate(table.players), key=lambda x: (x[1].points, -len(x[1].cards)))
