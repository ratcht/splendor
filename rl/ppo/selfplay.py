import random
from collections import deque
from collections.abc import Mapping
from copy import deepcopy
from itertools import combinations

import torch as t
from elote import EloCompetitor
from engine import Action, RandomDealer, RandomStrategy, Strategy, TableState, run_game

from rl.splendor import PASS, action_mask, decode, encode

from .ppo import PPO, split_obs


class PolicyStrategy:
  """A frozen policy playing the seat to move"""

  def __init__(self, ppo: PPO):
    self.ppo = ppo
    self.device = str(next(ppo.parameters()).device)

  def choose_action(self, state: TableState) -> Action | None:
    player = state.players[state.current]
    obs, mask = split_obs(
      {
        "obs": encode(state, state.current)[None],
        "action_mask": action_mask(state.board, player)[None],
      },
      self.device,
    )
    with t.no_grad():
      action, _, _ = self.ppo.select_action(obs, mask)

    index = int(action)
    return None if index == PASS else decode(index, state.board, player)


class SnapshotPool:
  """Past policies to train against: 70% latest, 20% older, 10% random"""

  def __init__(self, capacity: int = 20):
    self.snapshots: deque[PPO] = deque(maxlen=capacity)

  def add(self, ppo: PPO) -> None:
    self.snapshots.append(deepcopy(ppo).to("cpu").eval().requires_grad_(False))

  def __call__(self, rng: random.Random) -> Strategy:
    roll = rng.random()
    if not self.snapshots or roll < 0.1:
      return RandomStrategy(rng)
    ppo = self.snapshots[-1] if roll < 0.8 else rng.choice(self.snapshots)
    return PolicyStrategy(ppo)


def rate(
  entrants: Mapping[str, Strategy], games: int, rng: random.Random
) -> dict[str, float]:
  """Round-robin Elo"""
  ratings = {name: EloCompetitor() for name in entrants}
  for a, b in combinations(entrants, 2):
    for i in range(games):
      seats = [a, b] if i % 2 else [b, a]
      winner, _ = run_game(
        [entrants[name] for name in seats], RandomDealer(rng), max_turns=200
      )
      if winner is None:
        ratings[a].tied(ratings[b])
      else:
        ratings[seats[winner]].beat(ratings[seats[1 - winner]])
  return {name: elo.rating for name, elo in ratings.items()}
