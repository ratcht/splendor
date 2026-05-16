from dataclasses import replace
from models import CardLevel
from table import BoardState, PlayerState, Table
from actions import Action, check_nobles
from strategy.interface import Strategy


def refill(board: BoardState) -> BoardState:
  dealt, undealt = {}, {}
  for lvl in CardLevel:
    d, u = board.dealt_cards[lvl], board.undealt_cards[lvl]
    take = min(4 - len(d), len(u))
    if take <= 0:
      dealt[lvl], undealt[lvl] = d, u
    else:
      dealt[lvl], undealt[lvl] = [*d, *u[-take:]], u[:-take]
  return replace(board, dealt_cards=dealt, undealt_cards=undealt)


def take_turn(table: Table, action: Action) -> None:
  player = table.players[table.current]
  if not action.is_valid(table.board, player):
    raise ValueError(f"invalid action: {action}")
  board, player = action.apply(table.board, player)
  board, player = check_nobles(board, player)
  table.board = refill(board)
  table.players[table.current] = player


def run_game(agents: list[Strategy]) -> tuple[int, PlayerState]:
  table     = Table(len(agents))
  game_over = False

  while True:
    action = agents[table.current].choose_action(table.state())
    take_turn(table, action)

    if table.players[table.current].points >= 15:
      game_over = True

    if game_over and table.current == table.num_players - 1:
      break

    table.advance()

  return max(enumerate(table.players), key=lambda x: (x[1].points, -len(x[1].cards)))
