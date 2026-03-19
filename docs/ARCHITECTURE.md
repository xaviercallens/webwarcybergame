# Neo-Hack v3.1 Architecture

## System Overview

Neo-Hack v3.1 is a turn-based cyber warfare game with RL-driven AI opponents. The architecture separates concerns into five layers: Game Core, RL Environment, AI Service, Cloud Infrastructure, and Frontend.

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND                               │
│  TurnHUD │ ActionMenu │ MissionPanel │ AlertMeter │ Feedback │
└──────────────────────┬───────────────────────────────────────┘
                       │ REST / WebSocket
┌──────────────────────┴───────────────────────────────────────┐
│                    BACKEND (FastAPI)                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Game Session │  │ RL Agent     │  │ Security Middleware  │ │
│  │ Management   │  │ Microservice │  │ (Rate Limit, Auth)  │ │
│  └──────┬──────┘  └──────┬───────┘  └─────────────────────┘ │
│         │                │                                    │
│  ┌──────┴──────────────┐ │  ┌──────────────────────────────┐ │
│  │    GAME CORE        │ │  │   RL ENVIRONMENT             │ │
│  │ TurnManager         │ │  │ NeoHackEnv (Gymnasium)       │ │
│  │ ActionExecutor      │ │  │ NeoHackPettingZoo            │ │
│  │ DetectionEngine     │ │  │ ActionSpace / ObsSpace       │ │
│  │ ResourceManager     │ │  │ ScenarioLoader               │ │
│  │ VictoryConditions   │ │  │ TrainAgents / EvalAgents     │ │
│  │ ReplayRecorder      │ │  └──────────────────────────────┘ │
│  └─────────────────────┘ │                                    │
└──────────────────────────┴───────────────────────────────────┘
                       │
┌──────────────────────┴───────────────────────────────────────┐
│                   CLOUD (GCP)                                 │
│  Cloud Run (backend) │ Cloud Run (RL agent) │ Firestore       │
│  Cloud SQL           │ Cloud Storage        │ Cloud Functions  │
└──────────────────────────────────────────────────────────────┘
```

## Module Breakdown

### 1. Game Core (`backend/src/game/`)

| Module | Responsibility |
|--------|---------------|
| `turn_manager.py` | Turn scheduling, action points, player switching, game phases |
| `actions/action_executor.py` | Central action dispatcher with resource/stealth integration |
| `actions/attacker_actions.py` | 8 attacker actions with probabilistic outcomes |
| `actions/defender_actions.py` | 7 defender actions with detection/mitigation logic |
| `detection_engine.py` | Stealth/alert system, detection events, defender awareness |
| `resources.py` | Attacker/defender resource budgets, action cost calculation |
| `victory_conditions.py` | Win/loss criteria, scenario objectives, game end checks |
| `replay_recorder.py` | Match event recording, trajectory extraction for RL training |

### 2. RL Environment (`backend/src/rl/`)

| Module | Responsibility |
|--------|---------------|
| `neohack_env.py` | Custom Gymnasium env with turn-based gameplay |
| `pettingzoo_wrapper.py` | Multi-agent wrapper for 2-player alternating turns |
| `action_space.py` | Action definitions, costs, success rates, stealth costs |
| `observation_space.py` | GameState, partial observability (fog of war) |
| `train_agents.py` | Self-play training, baseline agents (Random, RuleBased) |
| `evaluate_agents.py` | Evaluation vs random, rule-based, head-to-head |
| `scenarios/scenario_loader.py` | Built-in scenarios, JSON loading, validation |

### 3. RL Agent Microservice (`backend/src/rl_agent/`)

| Module | Responsibility |
|--------|---------------|
| `main.py` | FastAPI app with `/ai/decide`, `/ai/actions`, `/scenarios`, `/health` |
| `game_session.py` | Session lifecycle, action submission, state management |
| `routes.py` | Game session CRUD routes (`/game/sessions/*`) |

### 4. AI Evaluation (`backend/src/ai/`)

| Module | Responsibility |
|--------|---------------|
| `spoe_evaluator.py` | S-POE framework (MM-SA-Bench, PsyR-OM-Bench) |

### 5. Cloud Infrastructure (`backend/src/cloud/`)

| Module | Responsibility |
|--------|---------------|
| `firestore_sync.py` | Real-time multiplayer state sync (Firestore + in-memory fallback) |

### 6. Security (`backend/src/middleware/`)

| Module | Responsibility |
|--------|---------------|
| `security.py` | Rate limiting, input validation, action authorization |

## Data Flow: Turn Execution

```
1. Player selects action via ActionMenu (frontend)
2. POST /game/sessions/{id}/action → routes.py
3. GameSession.submit_action()
   a. NeoHackEnv.step(action) → updates GameState
   b. TurnManager.process_action() → switches turns
   c. GameEndConditions.check_game_end() → win/loss check
4. Response: observation, reward, game_over, winner
5. If AI opponent: GET observation → POST /ai/decide → submit AI action
6. ReplayRecorder logs each turn for replay/training
```

## Key Design Decisions

- **Partial observability**: Attacker sees only discovered topology; defender sees full topology but only detected compromises.
- **Probabilistic actions**: All actions use configurable base rates modified by game state (patches, isolation, alert level).
- **In-memory fallback**: Firestore sync degrades gracefully to dict-based storage when GCP is unavailable.
- **Separation of env and game logic**: NeoHackEnv wraps game mechanics for RL; ActionExecutor provides the same logic for API sessions.
- **Numpy serialization**: `_sanitize_numpy()` converts numpy types for JSON/Pydantic compatibility.

## Directory Structure

```
backend/
├── src/
│   ├── rl/                    # Gymnasium env + training
│   │   ├── neohack_env.py
│   │   ├── pettingzoo_wrapper.py
│   │   ├── action_space.py
│   │   ├── observation_space.py
│   │   ├── train_agents.py
│   │   ├── evaluate_agents.py
│   │   └── scenarios/
│   ├── game/                  # Turn-based game mechanics
│   │   ├── turn_manager.py
│   │   ├── detection_engine.py
│   │   ├── resources.py
│   │   ├── victory_conditions.py
│   │   ├── replay_recorder.py
│   │   └── actions/
│   ├── rl_agent/              # FastAPI microservice
│   │   ├── main.py
│   │   ├── game_session.py
│   │   └── routes.py
│   ├── ai/                    # S-POE evaluation
│   ├── cloud/                 # Firestore sync
│   └── middleware/            # Security
├── tests/
│   ├── rl/                    # 48 tests
│   ├── game/                  # 137 tests
│   ├── rl_agent/              # 21 tests
│   ├── integration/           # 8 tests
│   ├── security/              # 15 tests
│   └── benchmarks/            # 7 tests
├── Dockerfile.rl_agent
└── pyproject.toml

build/web/
├── scripts/
│   ├── components/            # TurnHUD, ActionMenu, MissionPanel, AlertMeter
│   └── animations/            # ActionFeedback
└── styles/
    └── turn-based.css

infrastructure/
├── cloudbuild-rl-agent.yaml
└── cloudbuild-multi-service.yaml
```
