from dataclasses import dataclass

import engine


@dataclass
class Game:
  id: str
  table: engine.Table
