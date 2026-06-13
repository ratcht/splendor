# Splendor

Building a bot to play the board game [Splendor](https://www.youtube.com/watch?v=rue8-jvbc9I), along with the game engine it runs on and, eventually, a website so anyone can play against it.

> Why? I played a game of Splendor at my internship and got beat badly. This is my way of recovering lost honor.

**Status: WIP.** So far I have the game engine and some standalone RL samples. The bot and the website are still to come.

## Repository Structure

```
splendor/
├── engine/              # game engine
│   ├── models.py      # cards, gems, nobles
│   ├── state.py       # board / player / table state
│   ├── actions.py     # take gems, buy, reserve (+ legal action generation)
│   ├── dealer.py      # random and interactive card dealing
│   ├── engine.py      # turn + game loop
│   ├── strategy/      # pluggable player strategies
│   └── tests/         # pytest suite
├── frontend/          # Next.js frontend
└── rl-examples/       # standalone RL learning examples (Q-learning, SARSA, ...)
```

## How It Works

State is immutable. Actions take a board and player and return new ones. A `Strategy` just implements `choose_action(state) -> Action`, so you can drop in your own player. Two come built in:

- `RandomStrategy` picks a random legal action
- `HumanStrategy` prompts you to play interactively

Dealers control how cards come out: `RandomDealer` shuffles for simulation, `InteractiveDealer` lets you enter the cards of a real-world game to track it.

## Running

```bash
cd engine
python main.py        # random vs random, verbose
```

Swap the strategies or dealer in `main.py` to play yourself or follow a physical game.

## Tests

```bash
cd engine
python -m pytest
```

## `rl-examples`

Standalone reinforcement learning implementations I'm working through on the way to building an RL agent for the game. Currently: tabular Q-learning and SARSA on grid worlds.
