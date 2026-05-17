from engine import run_game
from strategy import HumanStrategy
from dealer import RandomDealer, InteractiveDealer

if __name__ == "__main__":
  # swap to InteractiveDealer() to track a real-world game
  dealer = RandomDealer()

  idx, winner = run_game([HumanStrategy(), HumanStrategy()], dealer=dealer)
  print(f"\nWinner: P{idx + 1} with {winner.points}pt")
