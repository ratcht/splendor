import random

import numpy as np
import torch as t
from engine import RandomDealer, RandomStrategy, Table, take_turn

from rl.ppo import PPO, PolicyStrategy, SnapshotPool, rate
from rl.splendor import N_ACTIONS, N_OBS, PASS, SplendorEnv, action_mask


def model():
  t.manual_seed(0)
  return PPO(n_actions=N_ACTIONS, d_state=N_OBS, device="cpu")


def table(seed=0):
  return Table(2, dealer=RandomDealer(random.Random(seed)))


# ── policy as a strategy ──────────────────────────────────────────────────────


def test_only_plays_legal_actions():
  strategy = PolicyStrategy(model())
  tbl = table()

  for _ in range(30):
    state = tbl.state()
    player = state.players[state.current]
    action = strategy.choose_action(state)

    if action is None:
      assert not action_mask(state.board, player)[:PASS].any()
    else:
      assert action.is_valid(state.board, player)
      take_turn(tbl, action)
    tbl.advance()


def test_plays_a_full_episode_as_the_env_opponent():
  strategy = PolicyStrategy(model())
  env = SplendorEnv(opponent=lambda _: strategy)
  obs, _ = env.reset(seed=0)

  done = False
  for _ in range(500):
    action = int(np.flatnonzero(obs["action_mask"])[0])
    obs, _, terminated, truncated, _ = env.step(action)
    done = terminated or truncated
    if done:
      break
  assert done


# ── pool ──────────────────────────────────────────────────────────────────────


def test_snapshots_do_not_track_training():
  # a live reference would let the opponent improve alongside the learner
  ppo = model()
  pool = SnapshotPool()
  pool.add(ppo)
  before = [p.clone() for p in pool.snapshots[-1].policy.parameters()]

  with t.no_grad():
    for p in ppo.policy.parameters():
      p.add_(1.0)

  after = pool.snapshots[-1].policy.parameters()
  assert all(t.equal(a, b) for a, b in zip(before, after))


def test_empty_pool_plays_random():
  assert isinstance(SnapshotPool()(random.Random(0)), RandomStrategy)


def test_pool_draws_both_snapshots_and_random():
  pool = SnapshotPool()
  pool.add(model())
  drawn = {type(pool(random.Random(seed))) for seed in range(50)}
  assert drawn == {PolicyStrategy, RandomStrategy}


def test_pool_is_bounded():
  pool = SnapshotPool(capacity=2)
  for _ in range(4):
    pool.add(model())
  assert len(pool.snapshots) == 2


# ── elo ───────────────────────────────────────────────────────────────────────


def test_rate_scores_every_entrant():
  rng = random.Random(0)
  entrants = {"a": RandomStrategy(rng), "b": RandomStrategy(rng)}
  ratings = rate(entrants, games=4, rng=rng)
  assert set(ratings) == {"a", "b"}
