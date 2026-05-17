from engine import run_game
from strategy import HumanStrategy

if __name__ == "__main__":
  idx, winner = run_game([HumanStrategy(), HumanStrategy()])
  print(f"\nWinner: P{idx + 1} with {winner.points}pt")
