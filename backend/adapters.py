import engine
from backend.models.api import (
  BoardSnapshot,
  GameSnapshot,
  GetGameResponse,
  PlayerSnapshot,
)


def player_to_snapshot(player: engine.PlayerState) -> PlayerSnapshot:
  return PlayerSnapshot(
    points=player.points,
    gem_count=player.gems.total,
    card_count=len(player.cards),
    reserved_count=len(player.reserved_cards),
    noble_count=len(player.nobles),
  )


def gem_stack_to_snapshot(gems: engine.GemStack) -> dict[str, int]:
  return {gem.name.lower(): count for gem, count in gems}


def board_to_snapshot(board: engine.BoardState) -> BoardSnapshot:
  return BoardSnapshot(available_gems=gem_stack_to_snapshot(board.available_gems))


def table_to_snapshot(table: engine.Table) -> GameSnapshot:
  return GameSnapshot(
    current_player_index=table.current,
    players=[player_to_snapshot(player) for player in table.players],
    board=board_to_snapshot(table.board),
  )


def table_to_get_game_response(table: engine.Table) -> GetGameResponse:
  return GetGameResponse(snapshot=table_to_snapshot(table))
