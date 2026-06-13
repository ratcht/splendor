import engine

from backend.models.api import GameSnapshot, GetGameResponse


def table_to_snapshot(table: engine.Table) -> GameSnapshot:
  return GameSnapshot(
    player_count=table.num_players,
    current_player=table.current,
  )


def table_to_get_game_response(table: engine.Table) -> GetGameResponse:
  return GetGameResponse(snapshot=table_to_snapshot(table))
