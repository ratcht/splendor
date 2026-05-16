from typing import TypeVar
from models import Gem, GemStack, empty_gem_stack
from table import TableState, PlayerState
from actions import Action, ActionType, TakeTwoGems, TakeThreeGems, BuyCard, ReserveCard

T = TypeVar('T')

NON_GOLD_GEMS = [g for g in Gem if g != Gem.Gold]


# ── input primitives ──────────────────────────────────────────────────────────

def pick(prompt: str, options: list[T], display=str) -> T:
  for i, o in enumerate(options):
    print(f"  {i + 1}. {display(o)}")
  while True:
    try:
      choice = int(input(f"{prompt}: ")) - 1
      if 0 <= choice < len(options):
        return options[choice]
      print(f"  Pick 1-{len(options)}.")
    except ValueError:
      print("  Enter a number.")

def pick_gem(prompt: str, available: list[Gem]) -> Gem:
  print(f"  Options: {', '.join(g.name for g in available)}")
  while True:
    raw = input(f"{prompt}: ").strip().capitalize()
    try:
      gem = Gem[raw]
      if gem in available:
        return gem
      print("  Not available.")
    except KeyError:
      print("  Unknown gem.")

def prompt_returns(player: PlayerState, taking: int) -> GemStack:
  excess = player.total_gems + taking - 10
  if excess <= 0:
    return empty_gem_stack()
  returns   = empty_gem_stack()
  remaining = excess
  print(f"  You must return {excess} gem(s).")
  while remaining > 0:
    raw = input(f"  Return which gem? ({remaining} left): ").strip().capitalize()
    try:
      gem = Gem[raw]
      if player.gems[gem] - returns[gem] > 0:
        returns[gem] += 1
        remaining -= 1
      else:
        print("  You dont have that gem.")
    except KeyError:
      print(f"  Unknown gem. Options: {[g.name for g in NON_GOLD_GEMS]}")
  return returns


# ── action builders ───────────────────────────────────────────────────────────

def take_two(board, player) -> TakeTwoGems | None:
  eligible = [g for g in NON_GOLD_GEMS if board.available_gems[g] >= 4]
  if not eligible:
    print("  No gem has 4+ available."); return None
  gem = pick_gem("Which gem", eligible)
  return TakeTwoGems(gem=gem, returns=prompt_returns(player, 2))

def take_three(board, player) -> TakeThreeGems | None:
  eligible = [g for g in NON_GOLD_GEMS if board.available_gems[g] >= 1]
  if len(eligible) < 3:
    print("  Not enough gem colors available."); return None
  print("  Pick 3 different gems:")
  g1 = pick_gem("First gem",  eligible)
  g2 = pick_gem("Second gem", [g for g in eligible if g != g1])
  g3 = pick_gem("Third gem",  [g for g in eligible if g not in (g1, g2)])
  return TakeThreeGems(gems=(g1, g2, g3), returns=prompt_returns(player, 3))

def buy_card(board, player) -> BuyCard | None:
  affordable  = [c for cards in board.dealt_cards.values() for c in cards if BuyCard(c).is_valid(board, player)]
  affordable += [c for c in player.reserved_cards if BuyCard(c).is_valid(board, player)]
  if not affordable:
    print("  You cant afford any cards."); return None
  return BuyCard(card=pick("Which card", affordable, display=repr))

def reserve_card(board, player) -> ReserveCard | None:
  all_cards = [c for cards in board.dealt_cards.values() for c in cards]
  if len(player.reserved_cards) >= 3:
    print("  Reserve limit reached (3)."); return None
  if not all_cards:
    print("  No cards on board."); return None
  gold = 1 if board.available_gems[Gem.Gold] > 0 else 0
  return ReserveCard(card=pick("Which card", all_cards, display=repr), returns=prompt_returns(player, gold))


# ── strategy ──────────────────────────────────────────────────────────────────

class HumanStrategy:
  def choose_action(self, state: TableState) -> Action:
    board  = state.board
    player = state.players[state.current]

    print(f"\n=== Player {state.current + 1}'s turn ===")
    print(repr(board))
    print(repr(player))

    while True:
      match pick("Action", list(ActionType)):
        case ActionType.TakeTwo:   result = take_two(board, player)
        case ActionType.TakeThree: result = take_three(board, player)
        case ActionType.Buy:       result = buy_card(board, player)
        case ActionType.Reserve:   result = reserve_card(board, player)
      if result is not None:
        return result
