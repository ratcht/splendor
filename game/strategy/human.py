from typing import TypeVar
from models import Gem, GemStack, empty_gem_stack
from state import TableState, PlayerState
from actions import Action, ActionType, TakeTwoGems, TakeThreeGems, BuyCard, ReserveCard

T = TypeVar('T')

NON_GOLD_GEMS = [g for g in Gem if g != Gem.Gold]
BACK_KEY = 'b'


class Back(Exception): pass


# ── input primitives ──────────────────────────────────────────────────────────

def pick(prompt: str, options: list[T], display=str, allow_back: bool = True) -> T:
  hint = f" ({BACK_KEY} to go back)" if allow_back else ""
  for i, o in enumerate(options):
    print(f"  {i + 1}. {display(o)}")
  while True:
    raw = input(f"{prompt}{hint}: ").strip().lower()
    if allow_back and raw == BACK_KEY:
      raise Back
    try:
      choice = int(raw) - 1
      if 0 <= choice < len(options):
        return options[choice]
      print(f"  Pick 1-{len(options)}.")
    except ValueError:
      print("  Enter a number.")

def parse_gem(raw: str, available: list[Gem]) -> Gem | None:
  raw = raw.lower()
  for g in available:
    if raw == g.name[0].lower() or raw == g.name.lower():
      return g
  return None

def fmt_gem_options(available: list[Gem]) -> str:
  return ', '.join(f"({g.name[0]}){g.name[1:]}" for g in available)

def pick_gem(prompt: str, available: list[Gem]) -> Gem:
  print(f"  Options: {fmt_gem_options(available)}")
  while True:
    raw = input(f"{prompt} ({BACK_KEY} to go back): ").strip()
    if raw.lower() == BACK_KEY:
      raise Back
    gem = parse_gem(raw, available)
    if gem is not None:
      return gem
    print("  Unknown gem.")

def prompt_returns(player: PlayerState, taking: int) -> GemStack:
  excess = player.total_gems + taking - 10
  if excess <= 0:
    return empty_gem_stack()
  returns   = empty_gem_stack()
  remaining = excess
  available = [g for g in Gem if player.gems[g] > 0]
  print(f"  You must return {excess} gem(s). Options: {fmt_gem_options(available)}")
  while remaining > 0:
    raw = input(f"  Return which gem? ({remaining} left, {BACK_KEY} to go back): ").strip()
    if raw.lower() == BACK_KEY:
      raise Back
    gem = parse_gem(raw, available)
    if gem is None:
      print("  Unknown gem.")
    elif player.gems[gem] - returns[gem] <= 0:
      print("  You dont have any more of that gem.")
    else:
      returns[gem] += 1
      remaining -= 1
  return returns


# ── action builders ───────────────────────────────────────────────────────────

def take_two(board, player) -> TakeTwoGems | None:
  eligible = [g for g in NON_GOLD_GEMS if board.available_gems[g] >= 4]
  if not eligible:
    print("  No gem has 4+ available."); return None
  try:
    gem = pick_gem("Which gem", eligible)
    return TakeTwoGems(gem=gem, returns=prompt_returns(player, 2))
  except Back:
    return None

def take_three(board, player) -> TakeThreeGems | None:
  eligible = [g for g in NON_GOLD_GEMS if board.available_gems[g] >= 1]
  if len(eligible) < 3:
    print("  Not enough gem colors available."); return None
  print("  Pick 3 different gems:")
  try:
    g1 = pick_gem("First gem",  eligible)
    g2 = pick_gem("Second gem", [g for g in eligible if g != g1])
    g3 = pick_gem("Third gem",  [g for g in eligible if g not in (g1, g2)])
    return TakeThreeGems(gems=(g1, g2, g3), returns=prompt_returns(player, 3))
  except Back:
    return None

def buy_card(board, player) -> BuyCard | None:
  affordable  = [c for cards in board.dealt_cards.values() for c in cards if BuyCard(c).is_valid(board, player)]
  affordable += [c for c in player.reserved_cards if BuyCard(c).is_valid(board, player)]
  if not affordable:
    print("  You cant afford any cards."); return None
  try:
    return BuyCard(card=pick("Which card", affordable, display=repr))
  except Back:
    return None

def reserve_card(board, player) -> ReserveCard | None:
  all_cards = [c for cards in board.dealt_cards.values() for c in cards]
  if len(player.reserved_cards) >= 3:
    print("  Reserve limit reached (3)."); return None
  if not all_cards:
    print("  No cards on board."); return None
  gold = 1 if board.available_gems[Gem.Gold] > 0 else 0
  try:
    return ReserveCard(card=pick("Which card", all_cards, display=repr), returns=prompt_returns(player, gold))
  except Back:
    return None


# ── strategy ──────────────────────────────────────────────────────────────────

class HumanStrategy:
  def choose_action(self, state: TableState) -> Action:
    board  = state.board
    player = state.players[state.current]

    print(f"\n{state!r}\n")

    while True:
      match pick(f"P{state.current + 1} action", list(ActionType), allow_back=False):
        case ActionType.TakeTwo:   result = take_two(board, player)
        case ActionType.TakeThree: result = take_three(board, player)
        case ActionType.Buy:       result = buy_card(board, player)
        case ActionType.Reserve:   result = reserve_card(board, player)
      if result is not None:
        return result
