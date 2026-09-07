import gymnasium as gym
import numpy as np
import pytest
from rl.splendor.actions import N_ACTIONS, PASS
from rl.splendor.env import LEARNER, SplendorEnv


def play(env, seed, rng, limit=500):
  obs, _ = env.reset(seed=seed)
  for step in range(limit):
    action = int(rng.choice(np.flatnonzero(obs["action_mask"])))
    obs, reward, terminated, truncated, _ = env.step(action)
    yield obs, reward, terminated, truncated
    if terminated or truncated:
      return


# ── gymnasium contract ────────────────────────────────────────────────────────


def test_illegal_action_raises():
  # Loud on purpose. Coercing an illegal action to a no-op would hide a broken
  # mask and let the policy train against rules the engine does not enforce.
  # This is also why gymnasium's check_env cannot be used here: it samples the
  # action space uniformly, ignoring the mask.
  env = SplendorEnv()
  obs, _ = env.reset(seed=0)
  illegal = int(np.flatnonzero(1 - obs["action_mask"])[0])
  with pytest.raises(ValueError):
    env.step(illegal)


def test_spaces():
  env = SplendorEnv()
  obs, _ = env.reset(seed=0)
  assert env.action_space == gym.spaces.Discrete(N_ACTIONS)
  assert env.observation_space.contains(obs)


def test_same_seed_gives_same_deal():
  a, b = SplendorEnv(), SplendorEnv()
  first, _ = a.reset(seed=7)
  second, _ = b.reset(seed=7)
  other, _ = a.reset(seed=8)
  assert (first["obs"] == second["obs"]).all()
  assert not (first["obs"] == other["obs"]).all()


# ── episodes ──────────────────────────────────────────────────────────────────


def test_random_episodes_finish_with_a_terminal_reward():
  rng = np.random.default_rng(0)
  outcomes = []
  for seed in range(20):
    for obs, reward, terminated, truncated in play(SplendorEnv(), seed, rng):
      if terminated or truncated:
        outcomes.append(reward)
        assert terminated != truncated
      else:
        assert reward == 0.0  # sparse: nothing until the game ends
  assert len(outcomes) == 20
  assert set(outcomes) <= {-1.0, 0.0, 1.0}


def test_control_returns_to_the_learner_after_each_step():
  rng = np.random.default_rng(1)
  env = SplendorEnv()
  for _, _, terminated, truncated in play(env, 0, rng):
    if not (terminated or truncated):
      assert env.table.current == LEARNER


def test_truncates_at_max_turns():
  rng = np.random.default_rng(2)
  env = SplendorEnv(max_turns=3)
  steps = [t for t in play(env, 0, rng)]
  assert len(steps) == 3
  assert steps[-1][3] is True  # truncated
  assert steps[-1][2] is False  # not terminated


def test_pass_is_accepted():
  env = SplendorEnv()
  env.reset(seed=0)
  before = env.table.players[LEARNER].gems
  env.step(PASS)
  assert env.table.players[LEARNER].gems == before


def test_opponent_is_pluggable():
  calls = []

  def spy(state, mask, rng):
    calls.append(state.current)
    return int(np.flatnonzero(mask)[0])

  env = SplendorEnv(opponent=spy)
  obs, _ = env.reset(seed=0)
  env.step(int(np.flatnonzero(obs["action_mask"])[0]))
  assert calls == [1]  # opponent played exactly one turn, from seat 1
