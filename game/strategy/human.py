from typing import Callable, TypeVar

from actions import (
  ACTION_TYPE_TO_CLASS,
  Action,
  ActionType,
  BuyCard,
  ReserveCard,
  TakeThreeGems,
  TakeTwoGems,
)
from state import BoardState, PlayerState, TableState

T = TypeVar("T")
BACK_KEY = "b"


class Back(Exception):
  pass


# ── input primitives ──────────────────────────────────────────────────────────


def pick(prompt: str, options: list[T], display=callable, allow_back: bool = True) -> T:
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


# ── action display ────────────────────────────────────────────────────────────


def fmt_action_primary(action: Action) -> str:
  """Display an action ignoring its `returns` field."""
  match action:
    case TakeTwoGems(gem=gem):
      return f"Take 2 {gem.name[0]}"
    case TakeThreeGems(gems=gems):
      return f"Take {', '.join(g.name[0] for g in gems)}"
    case BuyCard(card=card):
      return f"Buy {card!r}"
    case ReserveCard(card=card):
      return f"Reserve {card!r}"
    case _:
      return repr(action)


# ── action builder ────────────────────────────────────────────────────────────


def build_action(
  action_type: ActionType, board: BoardState, player: PlayerState
) -> Action | None:
  cls = ACTION_TYPE_TO_CLASS[action_type]
  actions = cls.legal_actions(board, player)
  if not actions:
    print(f"  No legal {action_type} actions.")
    return None

  groups: dict[str, list[Action]] = {}
  for a in actions:
    groups.setdefault(fmt_action_primary(a), []).append(a)

  try:
    chosen = pick("Which", list(groups.keys()), display=str)
    options = groups[chosen]
    if len(options) == 1:
      return options[0]
    return pick("Return", options, display=lambda a: repr(a.returns))
  except Back:
    return None


# ── strategy ──────────────────────────────────────────────────────────────────


class HumanStrategy:
  def choose_action(self, state: TableState) -> Action:
    board = state.board
    player = state.players[state.current]

    while True:
      action_type = pick(
        f"P{state.current + 1} action", list(ActionType), allow_back=False
      )
      result = build_action(action_type, board, player)
      if result is not None:
        return result
