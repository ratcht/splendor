import gymnasium as gym
import numpy as np
import torch as t
import torch.nn.functional as F

import rl.splendor  # noqa: F401  registers Splendor-v0
from rl.ppo import PPO, split_obs
from rl.splendor import N_ACTIONS, N_OBS

DEVICE = "cpu"


def model():
  t.manual_seed(0)
  return PPO(n_actions=N_ACTIONS, d_state=N_OBS, device=DEVICE)


def batch(n=16, legal=(0, 5, 17, 42)):
  obs = t.randn(n, N_OBS)
  mask = t.zeros(n, N_ACTIONS, dtype=t.bool)
  mask[:, list(legal)] = True
  return obs, mask


# ── critic initialization ─────────────────────────────────────────────────────


def test_critic_initially_predicts_zero():
  ppo = model()
  obs, mask = batch()
  _, values = ppo.forward(obs, mask)
  assert t.equal(values, t.zeros_like(values))


def test_zero_initialized_critic_can_learn():
  ppo = model()
  obs, mask = batch()
  log_probs, values, _ = ppo.evaluate(obs, t.zeros(len(obs), dtype=t.long), mask)
  targets = t.ones_like(values)
  loss = F.mse_loss(values, targets)

  ppo.update_params(log_probs.mean() * 0, loss)

  with t.no_grad():
    new_values = ppo.critic(obs)
    assert F.mse_loss(new_values, targets) < loss


# ── masking ───────────────────────────────────────────────────────────────────


def test_only_legal_actions_are_sampled():
  ppo = model()
  obs, mask = batch(n=256)
  actions, _, _ = ppo.select_action(obs, mask)
  assert mask.gather(1, actions[:, None]).all()


def test_masked_actions_have_negligible_probability():
  ppo = model()
  obs, mask = batch()
  logits, _ = ppo.forward(obs, mask)
  probs = t.softmax(logits, dim=-1)
  assert probs[~mask].max() < 1e-12
  assert t.allclose(probs.sum(-1), t.ones(len(obs)), atol=1e-5)


def test_evaluate_reproduces_select_action_log_probs():
  # a different distribution in evaluate makes the ratio exp(new - old) meaningless
  ppo = model()
  obs, mask = batch(n=64)
  actions, log_probs, values = ppo.select_action(obs, mask)
  again, values_again, entropy = ppo.evaluate(obs, actions, mask)

  assert t.allclose(log_probs, again, atol=1e-6)
  assert t.allclose(values, values_again, atol=1e-6)
  assert (entropy >= 0).all()


def test_unmasked_evaluate_would_differ():
  # without the mask the distributions differ, so the test above is not vacuous
  ppo = model()
  obs, mask = batch(n=64)
  actions, log_probs, _ = ppo.select_action(obs, mask)
  all_legal = t.ones_like(mask)
  wrong, _, _ = ppo.evaluate(obs, actions, all_legal)
  assert not t.allclose(log_probs, wrong, atol=1e-3)


# ── integration with the env ──────────────────────────────────────────────────


def test_split_obs_matches_model_inputs():
  envs = gym.make_vec("Splendor-v0", num_envs=4)
  obs_dict, _ = envs.reset(seed=0)
  obs, mask = split_obs(obs_dict, DEVICE)
  assert obs.shape == (4, N_OBS) and obs.dtype == t.float32
  assert mask.shape == (4, N_ACTIONS) and mask.dtype == t.bool
  assert mask.any(dim=-1).all()  # never a fully masked row


def test_rollout_and_update_runs_against_the_real_env():
  n_envs, n_rollout = 2, 8
  envs = gym.make_vec("Splendor-v0", num_envs=n_envs)
  ppo = model()
  before = [p.clone() for p in ppo.policy.parameters()]

  obs_dict, _ = envs.reset(seed=0)
  obs, mask = split_obs(obs_dict, DEVICE)
  rows = []
  with t.no_grad():
    for _ in range(n_rollout):
      actions, log_probs, values = ppo.select_action(obs, mask)
      states, rewards, terminated, truncated, _ = envs.step(actions.cpu().numpy())
      rows.append((obs, mask, actions, log_probs, values.squeeze(-1)))
      obs, mask = split_obs(states, DEVICE)

  b_obs, b_mask, b_actions, b_log_probs, b_values = (t.cat(x) for x in zip(*rows))
  advantages = t.randn(len(b_obs))

  new_log_probs, new_values, entropy = ppo.evaluate(b_obs, b_actions, b_mask)
  ratio = t.exp(new_log_probs - b_log_probs)
  assert t.allclose(ratio, t.ones_like(ratio), atol=1e-5)  # same policy, ratio == 1

  policy_loss = -t.min(ratio * advantages, ratio.clamp(0.8, 1.2) * advantages).mean()
  critic_loss = F.mse_loss(new_values.squeeze(-1), b_values + advantages)
  assert t.isfinite(policy_loss) and t.isfinite(critic_loss)

  ppo.update_params(policy_loss, critic_loss)
  after = list(ppo.policy.parameters())
  assert any(not t.equal(a, b) for a, b in zip(before, after))
