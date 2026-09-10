import argparse

from engine import RandomDealer, run_game
from engine.strategy import HumanStrategy

from .ppo import PPO
from .selfplay import PolicyStrategy

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Play Splendor against a trained bot.")
  parser.add_argument("model", help="checkpoint name under rl/ppo/checkpoints")
  args = parser.parse_args()

  # the bot takes seat 0, the seat it trained on
  bot = PolicyStrategy(PPO.load(args.model, device="cpu"), verbose=True)
  idx, winner = run_game(
    [bot, HumanStrategy()], dealer=RandomDealer(), max_turns=200, verbose=True
  )

  if idx is None:
    print("\nDraw")
  else:
    print(f"\nWinner: {'the bot' if idx == 0 else 'you'} with {winner.points}pt")
