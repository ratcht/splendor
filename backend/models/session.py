from dataclasses import dataclass

import engine


@dataclass
class GameSession:
  id: str
  table: engine.Table
