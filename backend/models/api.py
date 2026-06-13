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
