from dataclasses import dataclass

from env.grid_world import State, Action, Reward, N_ACTIONS

import numpy as np

rng = np.random.default_rng(seed=0)

@dataclass
class Parameters:
  alpha: float  # step size
  epsilon: float  # e-greedy
  gamma: float  # discount factor


def select_action(q_table: np.ndarray, state: State, epsilon: float) -> Action:
  # using e-greedy method

  q: np.ndarray = q_table[*state]
  assert q.shape == (N_ACTIONS,)

  # exploratory
  if rng.random() < epsilon:
    a = rng.integers(0, N_ACTIONS)
  else:
    a = int(rng.choice(np.flatnonzero(q == q.max())))  # break ties randomly

  return Action(a)


def update(
  q_table: np.ndarray,
  state: State,
  new_state: State,
  action: Action,
  next_action: Action,
  reward: Reward,
  done: bool,
  params: Parameters,
):
  q_next = (1 - done) * q_table[*new_state, next_action.value] # target dependent on next action
  td_error = reward + params.gamma * q_next - q_table[*state, action.value]
  q_table[*state, action.value] += params.alpha * td_error
