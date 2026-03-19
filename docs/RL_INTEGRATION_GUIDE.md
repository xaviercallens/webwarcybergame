# Neo-Hack v3.1 — RL Integration Guide

## Overview

Neo-Hack uses Reinforcement Learning agents trained via self-play to power AI opponents. The RL stack is built on **Gymnasium** (single-agent) and **PettingZoo** (multi-agent), with baseline agents provided for training bootstrapping.

## Environment API

### Single-Agent: `NeoHackEnv`

```python
from src.rl.neohack_env import NeoHackEnv

env = NeoHackEnv(num_nodes=10, max_turns=50, scenario="default")
obs, info = env.reset(seed=42)

# Step loop
action = env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)
```

**Observation space**: Flat `numpy.float32` vector encoding the partial observation for the current player.

**Action space**: `Discrete(15)` — actions 0-7 are attacker, 8-14 are defender. Invalid actions for the current player return a penalty.

### Multi-Agent: `NeoHackPettingZoo`

```python
from src.rl.pettingzoo_wrapper import NeoHackPettingZoo

env = NeoHackPettingZoo(num_nodes=10, max_turns=50)
env.reset()

for agent in env.agent_iter():
    obs, reward, term, trunc, info = env.last()
    if term or trunc:
        action = None
    else:
        action = env.action_space(agent).sample()
    env.step(action)
```

**Agents**: `"attacker"` and `"defender"` alternate turns.

## GameState

The central state object is `GameState` in `observation_space.py`:

| Field | Shape | Description |
|-------|-------|-------------|
| `full_topology` | `(N, N)` | Adjacency matrix (defender sees all) |
| `attacker_discovered_topology` | `(N, N)` | What attacker has scanned |
| `compromised_nodes` | `(N,)` | Ground truth compromises |
| `attacker_owned_nodes` | `(N,)` | Nodes attacker controls |
| `defender_detected_compromises` | `(N,)` | What defender has found |
| `vulnerabilities` | `(N,)` | Vulnerability level per node (0-3) |
| `patched_nodes` | `(N,)` | Whether node has been patched |
| `isolated_nodes` | `(N,)` | Whether node is quarantined |
| `alert_level` | scalar | 0-100, affects detection chances |
| `current_turn` | scalar | Current turn number |

### Partial Observability

- **Attacker** sees: owned nodes, discovered topology, alert level (noisy), vulnerabilities for scanned nodes.
- **Defender** sees: full topology, detected compromises (not undetected ones), alert level, all vulnerabilities.

## Baseline Agents

Three baseline agent types are provided in `train_agents.py`:

| Agent | Policy | Use Case |
|-------|--------|----------|
| `RandomAgent` | Uniform random action | Lower bound |
| `RuleBasedAttacker` | Prioritizes exploit → lateral → exfiltrate | Mid-tier opponent |
| `RuleBasedDefender` | Prioritizes incident response → scan → patch | Mid-tier opponent |

## Training

### Self-Play Training

```python
from src.rl.train_agents import self_play_training_loop

results = self_play_training_loop(
    attacker_agent=my_attacker,
    defender_agent=my_defender,
    n_episodes=10000,
    num_nodes=10,
    max_turns=50,
)
```

### Difficulty Levels

```python
from src.rl.train_agents import train_agents_for_difficulty

models = train_agents_for_difficulty(
    difficulty="expert",  # "novice" | "normal" | "expert"
    n_episodes=100000,
    learning_rate=3e-4,
)
```

| Difficulty | Episodes | Learning Rate | Expected Win vs Random |
|------------|----------|--------------|----------------------|
| Novice | 10,000 | 1e-3 | ~60% |
| Normal | 50,000 | 3e-4 | ~75% |
| Expert | 100,000 | 3e-4 | >80% |

## Evaluation

```python
from src.rl.evaluate_agents import run_full_evaluation

results = run_full_evaluation(
    attacker=my_attacker,
    defender=my_defender,
    n_games=100,
)
# Returns: vs_random, vs_rule_based, head_to_head win rates
```

## Scenario Configuration

Scenarios configure the game environment:

```python
from src.rl.scenarios import load_scenario, list_scenarios

scenarios = list_scenarios()
config = load_scenario("tutorial")
```

Built-in scenarios: `tutorial`, `default`, `advanced`.

Custom scenarios can be loaded from JSON:
```json
{
  "name": "Custom Scenario",
  "num_nodes": 15,
  "max_turns": 60,
  "attacker_start_node": 0,
  "target_nodes": [10, 14],
  "defender_ir_budget": 200,
  "attacker_exploit_budget": 8
}
```

## S-POE Evaluation Framework

For advanced agent evaluation using the Strategic Policy, Opponent, Environment framework:

```python
from src.ai.spoe_evaluator import SPOEEvaluator, generate_benchmark_scenarios

evaluator = SPOEEvaluator()
scenarios = generate_benchmark_scenarios(num_scenarios=20)
results = evaluator.evaluate_situational_awareness(agent, scenarios)
# Returns: mmsa_score (0-100), breakdown by object_detection, spatial, reasoning
```

## Retraining Guide

1. **Modify action costs/rates**: Edit `action_space.py` constants
2. **Add new scenarios**: Create JSON in `src/rl/scenarios/`
3. **Train new models**: Run `train_agents.py` with desired config
4. **Evaluate**: Run `evaluate_agents.py` against baselines
5. **Deploy**: Copy model files to `models/` directory and restart RL agent service
