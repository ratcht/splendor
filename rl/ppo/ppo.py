from pathlib import Path
from typing import Annotated

import torch as t
import torch.nn as nn

DEVICE = "cuda" if t.cuda.is_available() else "cpu"
CHECKPOINTS = Path(__file__).parent / "checkpoints"


class PPO(nn.Module):
  """PPO with illegal actions masked out of every action distribution."""

  def __init__(
    self, n_actions: int, d_state: int, hidden: int = 256, lr=7e-4, device=DEVICE
  ):
    super().__init__()

    self._n_actions = n_actions
    self._d_state = d_state
    self.device = device

    self.policy = nn.Sequential(
      nn.Linear(d_state, hidden),
      nn.ReLU(),
      nn.Linear(hidden, hidden),
      nn.ReLU(),
      nn.Linear(hidden, n_actions),
    )

    self.critic = nn.Sequential(
      nn.Linear(d_state, hidden),
      nn.ReLU(),
      nn.Linear(hidden, hidden),
      nn.ReLU(),
      nn.Linear(hidden, 1),
    )

    # Zero-init to avoid arbitrary bootstrap advantages before any outcomes are observed
    nn.init.zeros_(self.critic[-1].weight)
    nn.init.zeros_(self.critic[-1].bias)

    self.policy_optim = t.optim.Adam(self.policy.parameters(), lr=lr)
    self.critic_optim = t.optim.Adam(self.critic.parameters(), lr=lr)

  def save(self, name: str) -> None:
    CHECKPOINTS.mkdir(exist_ok=True)
    t.save(
      {
        "n_actions": self._n_actions,
        "d_state": self._d_state,
        "weights": self.state_dict(),
      },
      CHECKPOINTS / f"{name}.pt",
    )

  @classmethod
  def load(cls, name: str, device=DEVICE) -> "PPO":
    checkpoint = t.load(CHECKPOINTS / f"{name}.pt", map_location=device)
    ppo = cls(
      n_actions=checkpoint["n_actions"], d_state=checkpoint["d_state"], device=device
    )
    ppo.load_state_dict(checkpoint["weights"])
    return ppo.to(device)

  def forward(
    self,
    obs: Annotated[t.Tensor, "batch obs_shape"],
    mask: Annotated[t.Tensor, "batch n_actions"],
  ):
    action_logits = self.policy(obs)
    # finfo.min rather than -inf: -inf gives NaN gradients if a row is fully masked
    action_logits = action_logits.masked_fill(~mask, t.finfo(action_logits.dtype).min)
    state_values = self.critic(obs)

    return action_logits, state_values

  def select_action(
    self,
    obs: Annotated[t.Tensor, "n_envs obs_shape"],
    mask: Annotated[t.Tensor, "n_envs n_actions"],
  ) -> tuple[
    Annotated[t.Tensor, "n_envs"],
    Annotated[t.Tensor, "n_envs"],
    Annotated[t.Tensor, "n_envs"],
  ]:
    action_logits, state_values = self.forward(obs, mask)
    action_dist = t.distributions.Categorical(logits=action_logits)
    actions = action_dist.sample()
    action_log_probs = action_dist.log_prob(actions)

    return actions, action_log_probs, state_values

  def evaluate(
    self,
    obs: Annotated[t.Tensor, "minibatch_size obs_shape"],
    actions: Annotated[t.Tensor, "minibatch_size"],
    mask: Annotated[t.Tensor, "minibatch_size n_actions"],
  ):
    action_logits, state_values = self.forward(obs, mask)
    action_dist = t.distributions.Categorical(logits=action_logits)
    action_log_probs = action_dist.log_prob(actions)

    return action_log_probs, state_values, action_dist.entropy()

  def update_params(self, policy_loss: t.Tensor, critic_loss: t.Tensor):
    self.policy_optim.zero_grad()
    self.critic_optim.zero_grad()

    policy_loss.backward()
    critic_loss.backward()

    nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
    nn.utils.clip_grad_norm_(self.critic.parameters(), 0.5)

    self.policy_optim.step()
    self.critic_optim.step()


def split_obs(obs: dict, device=DEVICE) -> tuple[t.Tensor, t.Tensor]:
  """Vector env Dict observation -> (float obs tensor, bool action mask)."""
  return (
    t.tensor(obs["obs"], dtype=t.float32, device=device),
    t.tensor(obs["action_mask"], dtype=t.bool, device=device),
  )
