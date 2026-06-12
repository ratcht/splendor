from enum import Enum

import numpy as np

class Action(Enum):
  Up = 0
  Right = 1
  Left = 2
  Down = 3


DIRECTIONS = {
  Action.Up: (0, 1),
  Action.Right: (1, 0),
  Action.Left: (-1, 0),
  Action.Down: (0, -1),
}

N_ACTIONS = 4

type State = list[int]
type Reward = float


class Environment:
  def __init__(self, dim: tuple[int, int]):
    self.dim = dim
    self.prev_pos: State = [0, 0]
    self.pos: State = [0, 0]
    self.goal = [dim[0] - 1, dim[1] - 1]

  def _has_reached_goal(self) -> bool:
    return self.pos == self.goal

  def step(self, action: Action) -> tuple[Reward, bool]:
    dx, dy = DIRECTIONS[action]

    new_pos_0 = max(0, min(self.pos[0] + dx, self.dim[0] - 1))
    new_pos_1 = max(0, min(self.pos[1] + dy, self.dim[1] - 1))

    # update history
    self.pos[0], self.prev_pos[0] = new_pos_0, self.pos[0]
    self.pos[1], self.prev_pos[1] = new_pos_1, self.pos[1]

    return (0.0, True) if self._has_reached_goal() else (-1.0, False)  # reward

  def reset(self) -> None:
    self.pos = [0, 0]
    self.prev_pos = [0, 0]

  def render(self) -> None:
    for y in range(self.dim[1]):
      row = ""
      for x in range(self.dim[0]):
        if [x, y] == self.pos == self.goal:
          row += "AG "
        elif [x, y] == self.pos:
          row += "A "
        elif [x, y] == self.goal:
          row += "G "
        else:
          row += ". "
      print(row)
    print()

