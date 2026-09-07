import random
from typing import Any

import gymnasium as gym
import numpy as np
from engine import WIN_POINTS, PlayerState, RandomDealer, Table, TableState, take_turn

from .actions import N_ACTIONS, PASS, action_mask, decode
from .obs import N_OBS, encode

LEARNER = 0
NUM_PLAYERS = 2

type Obs = dict[str, np.ndarray]


def random_opponent(state: TableState, mask: np.ndarray, rng: np.random.Generator) -> int:
  return int(rng.choice(np.flatnonzero(mask)))


def _score(player: PlayerState) -> tuple[int, int]:
  """Engine's tie-break: more points, then fewer cards."""
  return player.points, -len(player.cards)


class SplendorEnv(gym.Env[Obs, int]):
  """Two-player Splendor. The learner is seat 0; the opponent plays inside step()."""

  def __init__(self, opponent=random_opponent, max_turns: int = 200):
    self.opponent = opponent
    self.max_turns = max_turns
    self.action_space = gym.spaces.Discrete(N_ACTIONS)
    self.observation_space = gym.spaces.Dict(
      {
        "obs": gym.spaces.Box(low=0, high=np.inf, shape=(N_OBS,), dtype=np.float32),
        "action_mask": gym.spaces.MultiBinary(N_ACTIONS),
      }
    )

  def reset(
    self, *, seed: int | None = None, options: dict[str, Any] | None = None
  ) -> tuple[Obs, dict[str, Any]]:
    super().reset(seed=seed)
    # the deal needs a python Random; derive it so reset(seed=n) is reproducible
    deal_rng = random.Random(int(self.np_random.integers(2**32)))
    self.table = Table(NUM_PLAYERS, dealer=RandomDealer(deal_rng))
    self.turns = 0
    self.reached_target = False
    self.done = False
    return self._obs(), {}

  def step(self, action: int) -> tuple[Obs, float, bool, bool, dict[str, Any]]:
    self._take(int(action))
    while not self.done and self.table.current != LEARNER:
      player = self.table.players[self.table.current]
      mask = action_mask(self.table.board, player)
      self._take(self.opponent(self.table.state(), mask, self.np_random))

    self.turns += 1
    truncated = not self.done and self.turns >= self.max_turns
    reward = self._reward() if self.done else 0.0
    return self._obs(), reward, self.done, truncated, {}

  def _take(self, index: int) -> None:
    player = self.table.players[self.table.current]
    if index != PASS:
      action = decode(index, self.table.board, player)
      if action is None:
        raise ValueError(f"no action at index {index}")
      take_turn(self.table, action)
    if self.table.players[self.table.current].points >= WIN_POINTS:
      self.reached_target = True
    # let the round finish so every player has had the same number of turns
    if self.reached_target and self.table.current == NUM_PLAYERS - 1:
      self.done = True
    else:
      self.table.advance()

  def _obs(self) -> Obs:
    return {
      "obs": encode(self.table.state(), LEARNER),
      "action_mask": action_mask(self.table.board, self.table.players[LEARNER]),
    }

  def _reward(self) -> float:
    players = self.table.players
    mine = _score(players[LEARNER])
    best = max(_score(p) for i, p in enumerate(players) if i != LEARNER)
    if mine > best:
      return 1.0
    return -1.0 if mine < best else 0.0


if "Splendor-v0" not in gym.registry:
  gym.register(id="Splendor-v0", entry_point="rl.splendor.env:SplendorEnv")
