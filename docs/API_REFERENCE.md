# Neo-Hack v3.1 API Reference

## Base URLs

| Service | URL | Description |
|---------|-----|-------------|
| Backend | `http://localhost:8000` | Main game backend |
| RL Agent | `http://localhost:8001` | RL agent microservice |

---

## Health & Status

### `GET /health`
Health check for both services.

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "version": "3.1.0",
  "agents_loaded": 6
}
```

---

## AI Decision Endpoints

### `POST /ai/decide`
Get RL agent's action decision for a given game observation.

**Request Body**:
```json
{
  "role": "attacker",
  "difficulty": "normal",
  "observation": [0.0, 1.0, 0.5, ...]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | string | Yes | `"attacker"` or `"defender"` |
| `difficulty` | string | Yes | `"novice"`, `"normal"`, or `"expert"` |
| `observation` | float[] | Yes | Flattened observation vector |

**Response** `200 OK`:
```json
{
  "action": 2,
  "confidence": 0.85,
  "action_name": "PHISHING"
}
```

### `GET /ai/actions/{role}`
List available actions for a role.

**Path Parameters**: `role` — `"attacker"` or `"defender"`

**Response** `200 OK`:
```json
{
  "role": "attacker",
  "actions": [
    {"id": 0, "name": "SCAN_NETWORK", "description": "..."},
    {"id": 1, "name": "EXPLOIT_VULNERABILITY", "description": "..."},
    ...
  ]
}
```

---

## Scenario Endpoints

### `GET /scenarios`
List all available game scenarios.

**Response** `200 OK`:
```json
{
  "scenarios": [
    {"id": "tutorial", "name": "Tutorial Scenario", "difficulty": "easy"},
    {"id": "default", "name": "Default Scenario", "difficulty": "medium"},
    {"id": "advanced", "name": "Advanced Scenario", "difficulty": "hard"}
  ]
}
```

### `GET /scenarios/{scenario_id}`
Get full scenario configuration.

**Response** `200 OK`:
```json
{
  "id": "tutorial",
  "name": "Tutorial Scenario",
  "num_nodes": 5,
  "max_turns": 20,
  "attacker_start_node": 0,
  "target_nodes": [4],
  "defender_ir_budget": 100,
  "attacker_exploit_budget": 5
}
```

---

## Game Session Endpoints

### `POST /game/sessions`
Create a new game session.

**Request Body**:
```json
{
  "scenario_id": "tutorial",
  "attacker_type": "human",
  "defender_type": "ai",
  "ai_difficulty": "normal"
}
```

**Response** `200 OK`:
```json
{
  "session_id": "abc-123-def",
  "scenario": "tutorial",
  "current_player": "attacker",
  "turn": 1,
  "game_over": false
}
```

### `GET /game/sessions`
List all active game sessions.

**Response** `200 OK`:
```json
{
  "sessions": [
    {"session_id": "abc-123", "scenario": "tutorial", "turn": 5, "game_over": false}
  ]
}
```

### `GET /game/sessions/{session_id}`
Get current game state for a session.

**Response** `200 OK`:
```json
{
  "session_id": "abc-123",
  "turn": 5,
  "current_player": "defender",
  "game_over": false,
  "winner": null,
  "alert_level": 25,
  "attacker_nodes": 2,
  "defender_detected": 1
}
```

### `POST /game/sessions/{session_id}/action`
Submit a player action.

**Request Body**:
```json
{
  "session_id": "abc-123",
  "player": "attacker",
  "action": 1,
  "target_node": 3
}
```

**Response** `200 OK`:
```json
{
  "session_id": "abc-123",
  "turn": 6,
  "current_player": "defender",
  "game_over": false,
  "winner": null,
  "action_result": {
    "action": "EXPLOIT_VULNERABILITY",
    "success": true,
    "detected": false,
    "stealth_cost": 15
  }
}
```

### `GET /game/sessions/{session_id}/observation/{role}`
Get partial observation for a player role.

**Path Parameters**: `role` — `"attacker"` or `"defender"`

**Response** `200 OK`:
```json
{
  "session_id": "abc-123",
  "role": "attacker",
  "observation": [0.0, 1.0, 0.5, ...],
  "observation_dict": {
    "owned_nodes": [0, 3],
    "discovered_topology": [[0,1], [1,3]],
    "alert_level": 25
  }
}
```

### `DELETE /game/sessions/{session_id}`
Delete a game session.

**Response** `200 OK`:
```json
{"deleted": true, "session_id": "abc-123"}
```

---

## Action IDs

### Attacker Actions (0-7)

| ID | Name | AP Cost | Base Success | Detection Chance |
|----|------|---------|-------------|-----------------|
| 0 | `SCAN_NETWORK` | 1 | 95% | 5% |
| 1 | `EXPLOIT_VULNERABILITY` | 2 | 70% | 30% |
| 2 | `PHISHING` | 1 | 60% | 20% |
| 3 | `INSTALL_MALWARE` | 2 | 75% | 25% |
| 4 | `ELEVATE_PRIVILEGES` | 2 | 65% | 35% |
| 5 | `LATERAL_MOVEMENT` | 1 | 80% | 15% |
| 6 | `EXFILTRATE_DATA` | 3 | 70% | 40% |
| 7 | `CLEAR_LOGS` | 1 | 85% | 10% |

### Defender Actions (0-6)

| ID | Name | AP Cost | Effect |
|----|------|---------|--------|
| 0 | `MONITOR_LOGS` | 1 | Detect compromises on target + neighbors |
| 1 | `SCAN_FOR_MALWARE` | 1 | Deep scan target node for infections |
| 2 | `APPLY_PATCH` | 2 | Fix vulnerabilities, chance to remove compromise |
| 3 | `ISOLATE_HOST` | 1 | Quarantine node from network |
| 4 | `RESTORE_BACKUP` | 3 | Full node cleanup and restore |
| 5 | `FIREWALL_RULE` | 1 | Block connections, increase detection |
| 6 | `INCIDENT_RESPONSE` | 2 | Global scan + cleanup + alert boost |

---

## Error Responses

| Status | Meaning |
|--------|---------|
| `400` | Invalid input (bad action, wrong turn, invalid node) |
| `403` | Unauthorized (wrong role, not your session) |
| `404` | Session or model not found |
| `429` | Rate limit exceeded (100 req/min for game actions) |
| `500` | Internal server error |

**Error format**:
```json
{
  "detail": "Not your turn. Current player: defender"
}
```
