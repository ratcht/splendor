from dealer import InteractiveDealer, RandomDealer
from engine import run_game
from strategy import HumanStrategy, RandomStrategy

if __name__ == "__main__":
  # swap to InteractiveDealer() to track a real-world game
  dealer = RandomDealer()

  idx, winner = run_game(
    [RandomStrategy(), RandomStrategy()], dealer=dealer, verbose=True
  )
  print(f"\nWinner: P{idx + 1} with {winner.points}pt")
