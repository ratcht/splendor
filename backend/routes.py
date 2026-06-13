from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import engine

from .game import GameStore, get_game_store
from .models.api import (
  CreateGameRequest,
  CreateGameResponse,
  GetGameRequest,
  GetGameResponse,
)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
  return {"status": "ok"}


@router.post("/games")
def create_game(
  request: CreateGameRequest,
  store: Annotated[GameStore, Depends(get_game_store)],
) -> CreateGameResponse:
  game = store.create(engine.Table(num_players=len(request.players)))
  return CreateGameResponse(game_id=game.id)


def get_game_request(game_id: str) -> GetGameRequest:
  return GetGameRequest(game_id=game_id)


@router.get("/games/{game_id}")
def get_game(
  request: Annotated[GetGameRequest, Depends(get_game_request)],
  store: Annotated[GameStore, Depends(get_game_store)],
) -> GetGameResponse:
  game = store.get(request.game_id)
  if game is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="game not found")
  return GetGameResponse(
    player_count=game.table.num_players,
    current_player=game.table.current,
  )
