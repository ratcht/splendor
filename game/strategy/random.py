from typing import TypeVar
from models import Gem, GemStack
from state import TableState, PlayerState
from actions import Action, ActionType, TakeTwoGems, TakeThreeGems, BuyCard, ReserveCard
from itertools import chain, combinations

NON_GOLD_GEMS = [g for g in Gem if g != Gem.Gold]


# def available_take_three(player: PlayerState, board: BoardState) -> list[Action]:
# 	eligible = [g for g in NON_GOLD_GEMS if board.available_gems[g] >= 1]
#   if len(eligible) < 3:
#   	return []

# 	options = list(combinations(eligible, 3))

# 	actions = [TakeThreeGems(gems=options[i], returns=)]

# def available_actions(player: PlayerState, board: BoardState) -> list[Action]:
# 	actions = []
# 	actions.extend(
# 		chain(
# 			available_take_three(),
# 			available_take_two(),
# 			available_buy_card(),
# 			available_reserve_card()
# 		)
# 	)

# 	return actions

# ── strategy ──────────────────────────────────────────────────────────────────

# class RandomStrategy:
#   def choose_action(self, state: TableState) -> Action:
#     board  = state.board
#     player = state.players[state.current]

#     print(f"\n{state!r}\n")

#     while True:
#       match pick(f"P{state.current + 1} action", list(ActionType), allow_back=False):
#         case ActionType.TakeTwo:   result = take_two(board, player)
#         case ActionType.TakeThree: result = take_three(board, player)
#         case ActionType.Buy:       result = buy_card(board, player)
#         case ActionType.Reserve:   result = reserve_card(board, player)
#       if result is not None:
#         return result
