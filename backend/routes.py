from typing import Annotated

from fastapi import APIRouter, Depends

import engine

from .models.api import CreateGameRequest, CreateGameResponse
from .session import SessionStore, get_session_store

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
  return {"status": "ok"}


@router.post("/games")
def create_game(
  request: CreateGameRequest,
  store: Annotated[SessionStore, Depends(get_session_store)],
) -> CreateGameResponse:
  session = store.create(engine.Table(num_players=len(request.players)))
  return CreateGameResponse(game_id=session.id)
