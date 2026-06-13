from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import engine

from . import adapters
from .game import GameStore, get_game_store
from .models.api import (
  CreateGameRequest,
  CreateGameResponse,
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


@router.get("/games/{game_id}")
def get_game(
  game_id: str,
  store: Annotated[GameStore, Depends(get_game_store)],
) -> GetGameResponse:
  game = store.get(game_id)
  if game is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="game not found")
  return adapters.table_to_get_game_response(game.table)
