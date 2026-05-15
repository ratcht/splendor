from typing import Protocol
from dataclasses import replace
from models import CardLevel
from table import BoardState, PlayerState, Table, TableState
from actions import Action, check_nobles


class Strategy(Protocol):
  def choose_action(self, state: TableState) -> Action: ...


def refill(board: BoardState) -> BoardState:
  dealt   = {level: list(cards) for level, cards in board.dealt_cards.items()}
  undealt = {level: list(cards) for level, cards in board.undealt_cards.items()}
  for level in CardLevel:
    while len(dealt[level]) < 4 and undealt[level]:
      dealt[level].append(undealt[level].pop())
  return replace(board, dealt_cards=dealt, undealt_cards=undealt)


def take_turn(
  board: BoardState,
  players: list[PlayerState],
  current: int,
  action: Action,
) -> tuple[BoardState, list[PlayerState]]:
  if not action.is_valid(board, players[current]):
    raise ValueError(f"invalid action: {action}")
  board, player = action.apply(board, players[current])
  board, player = check_nobles(board, player)
  board = refill(board)
  players = [*players[:current], player, *players[current + 1:]]
  return board, players


def run_game(agents: list[Strategy]) -> PlayerState:
  table = Table(len(agents))
  current = 0
  game_over = False

  while True:
    action = agents[current].choose_action(table.state(current))
    table.board, table.players = take_turn(table.board, table.players, current, action)

    if table.players[current].points >= 15:
      game_over = True

    if game_over and current == len(table.players) - 1:
      break

    current = (current + 1) % len(table.players)

  return max(table.players, key=lambda p: (p.points, -len(p.cards)))
