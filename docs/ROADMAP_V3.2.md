# Neo-Hack v3.2 Roadmap — Proposed Improvements

## Release Context

v3.1 delivers a complete turn-based cyber warfare game with RL-driven AI, partial observability, and GCP deployment. This document proposes improvements for v3.2 based on v3.1 test coverage analysis, architectural review, and gameplay feedback.

---

## 1. Deep RL Training Pipeline (Priority: HIGH)

### Current State
v3.1 uses CPU-only rule-based and random agents. Self-play training loop exists but lacks neural network policy optimization.

### Proposed Changes
- **Integrate Stable-Baselines3 (SB3)** for PPO/A2C training with neural network policies
- **Curriculum learning**: Start with easy scenarios, progressively increase difficulty
- **Model checkpointing**: Save best model per difficulty level to `models/` directory
- **GPU-accelerated training**: Support CUDA for faster convergence
- **Hyperparameter tuning**: Optuna integration for automated HP search

### Files
```
backend/src/rl/sb3_training.py         [NEW - PPO/A2C training with SB3]
backend/src/rl/curriculum.py           [NEW - Progressive difficulty scheduler]
backend/src/rl/hyperparameter_search.py [NEW - Optuna-based HP tuning]
backend/src/rl/models/                  [NEW - Saved model directory]
```

### Success Criteria
- Expert agent achieves >80% win rate vs rule-based baseline
- Training completes in <4 hours on single GPU
- Model inference <50ms on CPU

---

## 2. Multiplayer WebSocket Real-Time Sync (Priority: HIGH)

### Current State
v3.1 has Firestore sync with in-memory fallback, but no real-time WebSocket push for turn updates. Frontend polls or requires manual refresh.

### Proposed Changes
- **WebSocket turn notifications**: Push turn changes, action results, and game-over events
- **Reconnection handling**: Auto-reconnect with state replay on disconnect
- **Spectator mode**: Read-only WebSocket channel for observers
- **Latency measurement**: Client-side RTT tracking for adaptive sync

### Files
```
backend/src/cloud/websocket_sync.py    [NEW - WebSocket event broadcaster]
backend/src/rl_agent/ws_routes.py      [NEW - WebSocket endpoints]
build/web/scripts/ws-game-client.js    [NEW - Frontend WS client]
```

### Success Criteria
- Turn updates delivered to opponent in <100ms
- Graceful reconnection within 5 seconds
- Support 50 concurrent spectators per match

---

## 3. Enhanced Partial Observability & Fog of War (Priority: HIGH)

### Current State
Attacker sees discovered topology; defender sees full topology but only detected compromises. Observation is a flat vector.

### Proposed Changes
- **Graph Neural Network (GNN) observations**: Encode topology as graph, not flat vector
- **Noisy observations**: Add noise to alert level and detection based on distance
- **Memory decay**: Previously observed but unvisited nodes fade from attacker view
- **Information gain actions**: Dedicated reconnaissance actions that reveal more info at higher detection risk

### Files
```
backend/src/rl/gnn_observation.py      [NEW - Graph-based observation encoder]
backend/src/rl/observation_noise.py    [NEW - Observation noise model]
backend/src/game/fog_of_war.py         [NEW - Memory decay and visibility]
```

### Success Criteria
- GNN observation improves agent win rate by 5% over flat vector
- Noise model creates meaningful information asymmetry
- Fog of war tested with 10+ node networks

---

## 4. Frontend Turn-Based UX Polish (Priority: MEDIUM)

### Current State
v3.1 frontend components (TurnHUD, ActionMenu, MissionPanel, AlertMeter) are implemented but not integrated into the game engine loop. No animation transitions between turns.

### Proposed Changes
- **Integrate components into `game-engine.js`**: Wire TurnHUD/ActionMenu to actual game session API
- **Turn transition animations**: Smooth fade between attacker/defender turns with role-specific color themes
- **Node selection on globe**: Click nodes on 3D globe to set action targets
- **Action preview**: Show success probability and resource cost before confirming
- **Replay viewer**: Browser-based replay playback with timeline scrubber
- **Mobile responsive**: Touch-friendly action menu for tablet play

### Files
```
build/web/scripts/game-engine-v3.js    [NEW - Turn-based game engine integration]
build/web/scripts/components/ReplayViewer.js [NEW - Replay timeline component]
build/web/scripts/animations/TurnTransition.js [NEW - Turn switch animations]
build/web/styles/responsive.css        [NEW - Mobile/tablet styles]
```

### Success Criteria
- End-to-end human vs AI game playable in browser
- 60fps animation during turn transitions
- Playable on 768px+ screens

---

## 5. Advanced Scenario System (Priority: MEDIUM)

### Current State
3 built-in scenarios (tutorial, default, advanced). JSON loading supported but no scenario editor or dynamic generation.

### Proposed Changes
- **Procedural scenario generation**: Random network topologies with configurable difficulty
- **Scenario editor API**: CRUD endpoints for custom scenario creation
- **Campaign mode**: Sequential scenarios with persistent player state
- **Community scenarios**: Upload/download scenario packs

### Files
```
backend/src/rl/scenarios/generator.py  [NEW - Procedural scenario generation]
backend/src/rl/scenarios/editor.py     [NEW - Scenario CRUD]
backend/src/rl/scenarios/campaign.py   [NEW - Campaign progression]
```

### Success Criteria
- Generated scenarios are solvable by expert agent
- Campaign of 10 missions with escalating difficulty
- Scenario validation catches impossible configurations

---

## 6. Security Hardening (Priority: MEDIUM)

### Current State
v3.1 has rate limiting, input validation, and action authorization, but JWT auth is not enforced on game session endpoints. No anti-cheat for action timing.

### Proposed Changes
- **JWT enforcement on all game endpoints**: Middleware integration with FastAPI dependency injection
- **Anti-cheat**: Server-side action timing validation (min 500ms between actions)
- **Session isolation**: Verify player owns session before allowing actions
- **Audit logging**: Log all game actions with player ID and timestamp for dispute resolution
- **CORS hardening**: Restrict origins to known frontend domains

### Files
```
backend/src/middleware/jwt_auth.py      [NEW - JWT dependency for FastAPI]
backend/src/middleware/anti_cheat.py    [NEW - Action timing validator]
backend/src/middleware/audit_log.py     [NEW - Action audit logger]
```

### Success Criteria
- All game endpoints require valid JWT
- Rapid-fire actions are rate-limited and logged
- Audit log queryable by session and player

---

## 7. Observability & Monitoring (Priority: MEDIUM)

### Current State
Basic health checks and logging. No structured metrics, tracing, or alerting.

### Proposed Changes
- **Prometheus metrics**: Game session count, turn latency, RL inference time, error rates
- **OpenTelemetry tracing**: Distributed traces across backend ↔ RL agent
- **Grafana dashboards**: Pre-built dashboards for game health, player activity, AI performance
- **Alerting**: PagerDuty/Slack alerts for error spikes, high latency, service downtime

### Files
```
backend/src/middleware/metrics.py       [NEW - Prometheus metrics middleware]
infrastructure/grafana-dashboards/      [NEW - Dashboard JSON exports]
infrastructure/prometheus.yml           [NEW - Prometheus config]
```

---

## 8. Test Coverage Improvements (Priority: LOW)

### Current Coverage (v3.1)

| Module Group | Coverage | Notes |
|-------------|----------|-------|
| v3.1 Game Core | **93%** | actions, detection, resources, replay |
| v3.1 RL Env | **88%** | env, pettingzoo, observation, action space |
| v3.1 Microservice | **93%** | main, routes, game session |
| v3.1 AI/Cloud/Security | **85%** | spoe 100%, firestore 69% (GCP paths), security 95% |
| Legacy v2.0 Backend | **25%** | engine.py, cli.py, seed.py — not in v3.1 scope |
| **Overall** | **69%** | 598 tests |

### Proposed Changes
- **Mock Firestore client**: Test Firestore code paths without GCP credentials (→ 95%)
- **Legacy backend tests**: Add tests for `engine.py`, `auth.py`, `diplomacy.py` (→ 80%)
- **Property-based testing**: Hypothesis tests for action space invariants
- **Mutation testing**: mutmut to verify test quality
- **Target**: **85% overall coverage** for v3.2 release gate

---

## 9. Performance Optimization (Priority: LOW)

### Current Benchmarks (v3.1)

| Metric | Current | Target v3.2 |
|--------|---------|-------------|
| Turn processing | <10ms | <5ms |
| RL inference (rule-based) | <1ms | <1ms |
| RL inference (neural net) | N/A | <50ms |
| Firestore sync (in-memory) | <1ms | <1ms |
| Firestore sync (GCP) | ~100ms | <100ms |
| Full 50-turn game | <3s | <2s |

### Proposed Changes
- **Action result caching**: Cache repeated observation computations
- **Numpy optimization**: Pre-allocate arrays, avoid copies
- **Connection pooling**: Firestore connection reuse
- **Load testing**: Locust test for 100 concurrent sessions

---

## 10. Documentation & Developer Experience (Priority: LOW)

### Proposed Changes
- **OpenAPI/Swagger UI**: Auto-generated from FastAPI, deployed at `/docs`
- **Contributing guide**: Setup instructions, PR process, test requirements
- **Architecture Decision Records (ADRs)**: Document key design decisions
- **Changelog automation**: Generate from conventional commits

---

## Release Plan

| Phase | Items | Timeline |
|-------|-------|----------|
| **v3.2-alpha** | #1 SB3 Training, #2 WebSocket Sync | Week 1-2 |
| **v3.2-beta** | #3 Enhanced Observability, #4 Frontend Polish | Week 3-4 |
| **v3.2-rc** | #5 Scenarios, #6 Security, #8 Coverage | Week 5 |
| **v3.2-release** | #7 Monitoring, #9 Perf, #10 Docs | Week 6 |

### Release Gate Criteria
- All v3.1 tests still passing (no regressions)
- Coverage ≥ 85%
- Expert agent win rate ≥ 80% vs baseline
- End-to-end browser game playable
- All benchmark targets met
