from .actions import Action, check_nobles
from .dealer import Dealer
from .state import PlayerState
from .strategy.interface import Strategy
from .table import Table

WIN_POINTS = 15


def score(player: PlayerState) -> tuple[int, int]:
  """Tie-break: more points, then fewer cards."""
  return player.points, -len(player.cards)


def take_turn(table: Table, action: Action) -> None:
  player = table.players[table.current]
  if not action.is_valid(table.board, player):
    raise ValueError(f"invalid action: {action}")
  board, player = action.apply(table.board, player)
  board, player = check_nobles(board, player)
  table.board = table.dealer.refill(board)
  table.players[table.current] = player


def run_game(
  agents: list[Strategy],
  dealer: Dealer | None = None,
  max_turns: int = 100,
  verbose: bool = False,
) -> tuple[int | None, PlayerState | None]:
  table = Table(len(agents), dealer=dealer)
  game_over = False

  for _ in range(max_turns):
    if verbose:
      print(f"\n{table.state()!r}\n")

    action = agents[table.current].choose_action(table.state())
    if action is not None:
      take_turn(table, action)

    if table.players[table.current].points >= WIN_POINTS:
      game_over = True

    if game_over and table.current == table.num_players - 1:
      break

    table.advance()

  ranked = sorted(enumerate(table.players), key=lambda p: score(p[1]), reverse=True)
  if len(ranked) > 1 and score(ranked[0][1]) == score(ranked[1][1]):
    return None, None
  return ranked[0]
