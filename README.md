# Splendor

Building a bot to play the board game [Splendor](https://www.youtube.com/watch?v=rue8-jvbc9I), along with the game engine it runs on and, eventually, a website so anyone can play against it.

> Why? I played a game of Splendor at my internship and got beat badly. This is my way of recovering lost honor.

**Status: WIP.** The game engine and PPO self-play training are in place, and you can play against a trained checkpoint in the terminal. The website is still early: a FastAPI backend can create and fetch games, and the Next.js frontend is a starter page.

## Repository Structure

```
splendor/
├── engine/            # game engine
│   ├── models.py      # cards, gems, nobles
│   ├── state.py       # board / player / table state
│   ├── actions.py     # take gems, buy, reserve (+ legal action generation)
│   ├── dealer.py      # random and interactive card dealing
│   ├── table.py       # table setup and turn tracking
│   ├── engine.py      # turn + game loop
│   ├── strategy/      # random, greedy and human players
│   └── tests/         # pytest suite
├── backend/           # FastAPI game API
├── frontend/          # Next.js frontend scaffold
└── rl/
    ├── splendor/      # Gymnasium environment, observations and action masks
    ├── ppo/           # PPO model, self-play, training notebook and CLI
    └── examples/      # standalone RL learning examples (git submodule)
```

## How It Works

Actions take a board and player and return new ones. A `Strategy` just implements `choose_action(state) -> Action | None`, so you can drop in your own player. `None` means pass. The engine comes with three:

- `RandomStrategy` picks a random legal action
- `GreedyStrategy` looks one move ahead and scores the resulting position
- `HumanStrategy` prompts you to play interactively

`PolicyStrategy` in `rl/ppo` wraps a trained PPO model in the same interface.

Dealers control how cards come out: `RandomDealer` shuffles for simulation, `InteractiveDealer` lets you enter the cards of a real-world game to track it.

## Running

From the repo root, with the Python dependencies in `requirements.txt` installed:

```bash
python -m engine.main        # random vs random, verbose
```

Swap the strategies or dealer in `engine/main.py` to play yourself or follow a physical game.

To play against a trained bot:

```bash
python -m rl.ppo.run latest
```

This loads `rl/ppo/checkpoints/latest.pt`. Train a model first, or use the name of another saved checkpoint without the `.pt` extension.

### Website

Start the API from the repo root:

```bash
python -m uvicorn backend.app:app --reload
```

Start the frontend in a separate terminal:

```bash
cd frontend
pnpm install
pnpm dev
```

The API docs are at `http://localhost:8000/docs`, and the frontend is at `http://localhost:3000`. Playing a game through the website isn't wired up yet.

## Tests

From the repo root:

```bash
python -m pytest engine/tests rl/splendor/tests rl/ppo/tests
```

## RL

`rl/splendor` wraps the engine as `Splendor-v0`, a two-player Gymnasium environment. The learner takes seat 0, and each step includes the opponent's reply. Illegal actions are masked out. Rewards are sparse: `+1` for a win, `-1` for a loss, and `0` otherwise. This avoids reward hacking, which can arise from rewarding intermediate actions like buying a card or taking a gem. The median game takes ~30 steps and is capped at 200 learner turns, so a 256-step rollout typically contains several completed games, giving GAE terminal reward signal to work with despite the sparsity.

Training lives in `rl/ppo/train.ipynb`. Run it with the notebook working directory set to `rl/ppo`. It collects 256-step rollouts from 24 parallel environments, then updates the policy with clipped PPO and GAE. The critic starts with zero value predictions. Opponents start out random, then come from a mix of frozen policy snapshots and random play. The notebook saves checkpoints and includes win-rate and Elo evaluation.

### `rl/examples`

Standalone reinforcement learning implementations I'm working through alongside the bot: tabular Q-learning, SARSA, REINFORCE, A2C, DQN and PPO, on grid worlds and Gymnasium environments.

These live in a git submodule. If the folder is empty after cloning:

```bash
git submodule update --init --recursive
```
