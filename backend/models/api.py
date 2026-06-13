from pydantic import BaseModel, ConfigDict, Field

from .enums import PlayerType


class APIModel(BaseModel):
  model_config = ConfigDict(extra="forbid")


class PlayerConfig(APIModel):
  name: str
  type: PlayerType
  strategy: str | None = None


class CreateGameRequest(APIModel):
  players: list[PlayerConfig] = Field(min_length=2, max_length=4)


class CreateGameResponse(APIModel):
  game_id: str


class GetGameRequest(APIModel):
  game_id: str


class PlayerSnapshot(APIModel):
  points: int
  gem_count: int
  card_count: int
  reserved_count: int
  noble_count: int


class BoardSnapshot(APIModel):
  available_gems: dict[str, int]


class GameSnapshot(APIModel):
  current_player_index: int
  players: list[PlayerSnapshot]
  board: BoardSnapshot


class GetGameResponse(APIModel):
  snapshot: GameSnapshot
