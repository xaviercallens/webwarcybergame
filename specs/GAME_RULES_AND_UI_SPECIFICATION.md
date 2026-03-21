# Neo-Hack: Gridlock — Game Rules & Web Interface Specification

**Version:** 3.2.0  
**Date:** March 21, 2026  
**Purpose:** Complete reference for UI/UX reengineering — covers all game rules, mechanics, interface components, navigation flows, event architecture, and API contracts.

---

## Table of Contents

1. [Game Overview](#1-game-overview)
2. [Core Game Rules](#2-core-game-rules)
3. [Action System](#3-action-system)
4. [Stealth & Detection Mechanics](#4-stealth--detection-mechanics)
5. [Resource System](#5-resource-system)
6. [Victory Conditions](#6-victory-conditions)
7. [Scenarios](#7-scenarios)
8. [Factions & Diplomacy](#8-factions--diplomacy)
9. [Sentinel Lab (AI Agent)](#9-sentinel-lab-ai-agent)
10. [Application Navigation Flow](#10-application-navigation-flow)
11. [Screen Specifications](#11-screen-specifications)
12. [HUD & In-Game Panels](#12-hud--in-game-panels)
13. [Modal Dialogs](#13-modal-dialogs)
14. [Canvas & Rendering](#14-canvas--rendering)
15. [Event Bus Architecture](#15-event-bus-architecture)
16. [API Contract Reference](#16-api-contract-reference)
17. [Controls & Accessibility](#17-controls--accessibility)
18. [Design System & Theming](#18-design-system--theming)
19. [Known Issues & Gaps](#19-known-issues--gaps)
20. [Reengineering Recommendations](#20-reengineering-recommendations)

---

## 1. Game Overview

**Neo-Hack: Gridlock** is a turn-based asymmetric cyber warfare strategy game. Two roles — **Attacker** and **Defender** — compete over a network of nodes. The human player chooses a role; the opposing side is controlled by an AI agent (rule-based or PPO-trained).

- **Genre:** Turn-based strategy, cybersecurity simulation
- **Theme:** Near-future dystopian hacking / cyber warfare
- **Visual Style:** Dark terminal/CRT aesthetic with neon accents (cyan, red, amber)
- **Platform:** Web browser (desktop-first), Vite + vanilla JS frontend, FastAPI + SQLModel backend

---

## 2. Core Game Rules

### 2.1 Turn Structure

| Property | Value |
|---|---|
| Turn order | Attacker → Defender → (turn increments) → repeat |
| Action Points (AP) per turn | Configurable per scenario (default: 1 AP each) |
| Turn increment | After **both** players have acted, `current_turn++` |
| Max turns | Scenario-dependent (20–100) |
| End turn | Player can skip remaining AP via "End Turn" |

### 2.2 Game Phases

```
SETUP → ATTACKER_TURN → DEFENDER_TURN → ATTACKER_TURN → ... → GAME_OVER
```

- **SETUP**: Session created, initial state loaded
- **ATTACKER_TURN / DEFENDER_TURN**: Active player submits actions consuming AP
- **GAME_OVER**: Victory condition met or max turns reached

### 2.3 Network Topology

- Nodes are connected via an adjacency matrix (randomly generated per session)
- Each node has properties:
  - `id` (int), `name` (string, e.g. "NODE-03")
  - `owned_by`: `"attacker"` | `"defender"`
  - `defense_level` (int, 0–3): vulnerability rating
  - `discovered` (bool): whether attacker has scanned it
  - `detected` (bool): whether defender has detected compromise
  - `patched` (bool): whether defender has patched vulnerabilities
  - `isolated` (bool): whether defender has quarantined the node

### 2.4 Fog of War

- **Attacker**: Can only see discovered nodes (via SCAN_NETWORK). Undiscovered nodes are hidden.
- **Defender**: Full map visibility at all times.

---

## 3. Action System

### 3.1 Attacker Actions (8 total)

| ID | Action | Description | Base Success | Detection Chance | Stealth Cost | Resource |
|---|---|---|---|---|---|---|
| 0 | SCAN_NETWORK | Discover topology and hosts | 95% | 5% | 5 | — |
| 1 | EXPLOIT_VULNERABILITY | Compromise a host | 70% | 40% | 30 | exploit_kits |
| 2 | PHISHING | Social engineering for credentials | 60% | 20% | 15 | — |
| 3 | INSTALL_MALWARE | Persistent malware on host | 75% | 50% | 35 | malware_payloads |
| 4 | ELEVATE_PRIVILEGES | Escalate to admin access | 65% | 35% | 25 | — |
| 5 | LATERAL_MOVEMENT | Move to adjacent segment | 80% | 45% | 40 | — |
| 6 | EXFILTRATE_DATA | Steal data from compromised hosts | 70% | 60% | 50 | — |
| 7 | CLEAR_LOGS | Remove evidence from logs | 85% | 15% | 10 | — |

### 3.2 Defender Actions (7 total)

| ID | Action | Description | Resource |
|---|---|---|---|
| 0 | MONITOR_LOGS | Check logs for suspicious activity | — |
| 1 | SCAN_FOR_MALWARE | Scan hosts for infections | scan_bandwidth |
| 2 | APPLY_PATCH | Fix vulnerabilities | patches_available |
| 3 | ISOLATE_HOST | Quarantine a node | — |
| 4 | RESTORE_BACKUP | Restore from clean backup | ir_budget (5) |
| 5 | FIREWALL_RULE | Block connections | — |
| 6 | INCIDENT_RESPONSE | Active countermeasure | ir_budget (10) |

### 3.3 Action Execution Flow

```
User clicks action button
  → events.emit(ACTION_EXECUTE, { actionId, actionName, targetNode })
    → TurnController.onPlayerAction()
      → api.submitTurnAction({ session_id, player_role, action_type, action_id, target_node })
        → Backend processes action in RL environment
        → Returns { success, detected, message, details, ai_actions, game_state }
      → TurnController._applyState(game_state)
      → events.emit(GAME_STATE_UPDATE, { gameState })
      → events.emit(ACTION_RESULT, { ... })
      → If turn switched → AI takes turn automatically → returns updated state
```

---

## 4. Stealth & Detection Mechanics

### 4.1 Alert Level

- Starts at **0**, max is **100**
- Each attacker action adds its **stealth cost** to the alert level
- Alert level **increases detection chance** via multiplier: `detection = base_chance × (1 + alert_level/100 × 0.5)`
- At alert level ≥ 70: **detection threshold exceeded** → defender gets bonus actions
- At alert level ≥ 100: **game over** → defender wins ("Attacker detected and caught")

### 4.2 Stealth Level (UI)

- Displayed as `stealth_level = 100 - alert_level`
- Starts at 100%, decreases as attacker acts
- Visual indicator on HUD

### 4.3 Detection Events

- Each attacker action has a base detection chance (see table above)
- Detected actions add +20 alert on top of stealth cost
- Defender can see detection events in detection history (last 5 turns memory)

---

## 5. Resource System

### 5.1 Attacker Resources

| Resource | Default | Description |
|---|---|---|
| exploit_kits | 8–15 | Consumed by EXPLOIT_VULNERABILITY |
| malware_payloads | 3–5 | Consumed by INSTALL_MALWARE |
| time_remaining | = max_turns | Decrements each round |

### 5.2 Defender Resources

| Resource | Default | Description |
|---|---|---|
| ir_budget | 80–200 | Consumed by RESTORE_BACKUP (5) and INCIDENT_RESPONSE (10) |
| patches_available | 5–10 | Consumed by APPLY_PATCH |
| scan_bandwidth | 2–3 | Consumed by SCAN_FOR_MALWARE |

---

## 6. Victory Conditions

### 6.1 Scenario Types

| Type | Attacker Wins | Defender Wins |
|---|---|---|
| **default** | Compromise ≥ 50% of nodes | Alert level reaches 100 |
| **capture_flag** | Exfiltrate ≥ 100 data units | Isolate ≥ 5 compromised nodes |
| **survival** | Compromise ≥ 3 critical nodes | Maintain alert > 80 for 5 turns |

### 6.2 Time Limit (All Scenarios)

If `current_turn > max_turns`:
- Attacker owned > 30% nodes → **attacker wins**
- Otherwise → **defender wins**

### 6.3 Scoring

| Metric | Points |
|---|---|
| Attacker: Each owned node | +10 |
| Defender: Each detected compromise | +15 |
| Defender: Alert level | +alert_level |

---

## 7. Scenarios

### 7.1 Built-In Scenarios

| ID | Name | Nodes | Turns | AP (Atk/Def) | Type | Difficulty |
|---|---|---|---|---|---|---|
| `tutorial` | Tutorial - First Breach | 5 | 20 | 1/1 | default | Novice |
| `corporate_network` | Corporate Network Intrusion | 10 | 50 | 1/1 | default | Normal |
| `data_center` | Data Center Siege | 20 | 80 | 2/2 | capture_flag | Normal |
| `critical_infrastructure` | Critical Infrastructure Defense | 30 | 100 | 2/1 | survival | Expert |

### 7.2 Menu-Selectable Scenarios (Frontend)

| # | Label | Backend Mapping |
|---|---|---|
| 01 | CORE SYSTEMS TUTORIAL | `tutorial` |
| 02 | THE BERYLIA BANK RUN | `bank_run` → `corporate_network` |
| 03 | SILICON SILK ROAD HEIST | `heist` → `corporate_network` |
| 04 | OPERATION BLACKOUT | `blackout` → `corporate_network` |
| 05 | OPERATION CRIMSON TIDE | `crimson_tide` → custom 16-node scenario |

---

## 8. Factions & Diplomacy

### 8.1 Factions

| ID | Name | Leader | Type | Personality |
|---|---|---|---|---|
| 1 | Silicon Valley | The Architect | State | Pragmatic, data-focused, wary of alliances |
| 2 | Iron Grid | General Volkov | State | Aggressive, transactional, respects power |
| 3 | Silk Road Coalition | Chairman Wei | State | Opportunistic, trade-focused, profit-driven |
| 4 | Euro Nexus | Director Vance | State | Diplomatic, bureaucratic, stability-oriented |
| 5 | Pacific Vanguard | Commandant Sato | State | Honor-bound, defensive, unforgiving |
| 6 | Cyber Mercenaries | Proxy | Non-State (CNSA) | Greedy, pragmatic, for-hire offense (+20% offense) |
| 7 | Sentinel Vanguard | Oracle | Non-State (CNSA) | Ethical white-hat, defense-oriented (+20% defense) |
| 8 | Shadow Cartels | Cipher | Non-State (CNSA) | Chaotic, ransomware-style, cascading failures |

### 8.2 Diplomacy Chat System

- Player sends free-text message to any faction ambassador
- Backend generates AI response (Gemini API with faction persona, or mock response when API key absent)
- Chat is displayed in the Diplomatic Channel modal
- Each ambassador has a distinct personality and response style

### 8.3 Treaty Proposals

| Treaty Type | Effect |
|---|---|
| Ceasefire | Prevent attacks between factions |
| Trade Agreement | Share compute resources |
| Grand Alliance | Full strategic cooperation |

- Player proposes a treaty type to a faction
- Backend evaluates acceptance based on faction personality
- Mock mode: acceptance rate varies by faction (30%–80%)
- Accepted treaties display "ACTIVE" badge in diplomacy panel

### 8.4 Treaty Acceptance Rates (Mock Mode)

| Faction | Acceptance Rate |
|---|---|
| Silicon Valley | 60% |
| Iron Grid | 40% |
| Silk Road Coalition | 80% |
| Euro Nexus | 70% |
| Pacific Vanguard | 50% |
| Cyber Mercenaries | 60% |
| Sentinel Vanguard | 70% |
| Shadow Cartels | 30% |

---

## 9. Sentinel Lab (AI Agent)

The Sentinel Lab allows players to create and tune autonomous AI agents ("Sentinels").

### 9.1 Sentinel Policy Parameters

| Parameter | Range | Description |
|---|---|---|
| Persistence | 0.0–1.0 | How aggressively the sentinel maintains position |
| Stealth | 0.0–1.0 | How much the sentinel prioritizes stealth |
| Efficiency | 0.0–1.0 | Resource conservation vs. aggressive spending |
| Aggression | 0.0–1.0 | Offensive vs. defensive bias |

### 9.2 Sentinel Lifecycle

1. **Create** — Initialize a named sentinel
2. **Configure** — Adjust 4 policy sliders
3. **Deploy** — Activate sentinel for autonomous play
4. **Monitor** — View operational logs and radar chart

### 9.3 UI Elements

- Radar/spider chart visualization of 4 policy parameters
- 4 range sliders for real-time tuning
- Operational log feed
- SAVE POLICY / DEPLOY buttons

---

## 10. Application Navigation Flow

### 10.1 View State Machine

```
LOGIN → MENU → ROLE_SELECT → GAME ↔ PAUSE → DEBRIEF
                    ↑                              |
                    └──────────────────────────────┘
                    
MENU → SETTINGS (modal)
MENU → LEADERBOARD
GAME → DIPLOMACY (modal)
GAME → SENTINEL LAB (modal)
GAME → GAME_OVER
```

### 10.2 Screen Transitions

| From | To | Trigger |
|---|---|---|
| LOGIN | MENU | Successful auth (login/register) |
| MENU | ROLE_SELECT | Click PLAY SANDBOX or PLAY SCENARIO |
| ROLE_SELECT | GAME | Click Attacker or Defender card |
| GAME | GAME_OVER | Victory/defeat condition met |
| GAME | MENU | Click QUIT |
| GAME_OVER | GAME | Click REDEPLOY |
| GAME_OVER | MENU | Click DISCONNECT |

### 10.3 Navigation Implementation

All views are pre-rendered in `main.js` as HTML template strings, injected into `#app` on init. `navigateTo(viewName)` toggles `.active` class on `.view` elements.

---

## 11. Screen Specifications

### 11.1 Login Screen (`#view-login`)

- **Layout:** Centered vertically, dark CRT background
- **Elements:**
  - Title: "NEO-HACK / GRIDLOCK" (h1 pair)
  - Subtitle: "v3.2.0 // AUTHENTICATION REQUIRED"
  - Input: OPERATIVE_ID (text, maxlength=20)
  - Input: PASSPHRASE (password, maxlength=64)
  - Error display area (red text)
  - Buttons: ▶ LOGIN | ⊕ REGISTER
  - Status line: "AWAITING CREDENTIALS" / "AUTHENTICATING..." / "ACCESS GRANTED"

### 11.2 Main Menu (`#view-menu`)

- **Layout:** Centered, same CRT background
- **Elements:**
  - Title block (same as login)
  - Difficulty selector: BEGINNER / INTERMEDIATE / ADVANCED (dropdown)
  - Scenario selector: 5 scenarios (dropdown)
  - Buttons: ▶ PLAY SANDBOX | ⊡ PLAY SCENARIO | 🎦 RECORD PROMO | ⚙ SETTINGS
  - Player card: Username (editable), Rank, XP

### 11.3 Role Select (`#view-role_select`)

- **Layout:** Two side-by-side cards, centered
- **Attacker Card (Scarlet Protocol):**
  - Color: `--color-enemy` (#ff0055)
  - Stats: 3 AP/turn, 5 Exploit Kits, Stealth meter, Fog of War, Win condition
  - Tag: "FAST START | RESOURCE-LIMITED | HIGH RISK"
- **Defender Card (Iron Bastion):**
  - Color: `--color-player` (#00ffdd)
  - Stats: 2 AP/turn (scales at alert 50%+), 8 IR budget, Full map, Win condition
  - Tag: "SLOW START | SCALING POWER | TIME ADVANTAGE"
- **Footer:** Selected scenario + difficulty labels, BACK button
- **Interaction:** Click or Enter/Space on card starts game

### 11.4 Game View (`#view-game`)

- **Layout:** Full-screen canvas with HUD overlay layers
- **Structure:**
  ```
  #view-game
    ├── #canvas-container        (3D globe or 2D fallback canvas)
    ├── .game-ui
    │   ├── #hud-layer           (injected by ui-manager.js)
    │   ├── #btn-quit            (top-right)
    │   ├── #btn-lab             (below quit, "SENTINEL LAB")
    │   ├── #intel-feed          (bottom-right, 300×250px log panel)
    │   ├── #tutorial-panel      (bottom-center, hidden by default)
    │   ├── #hotkeys-panel       (bottom-left, key reference)
    │   └── #terminal-panel      (full-screen overlay, hidden)
  ```

### 11.5 Leaderboard (`#view-leaderboard`)

- **Layout:** Centered panel, 600px wide
- **Elements:** Table with RANK / OPERATIVE / TIER / XP columns, RETURN button

### 11.6 Game Over (`#view-gameover`)

- **Layout:** Dark overlay, centered panel
- **Elements:** Title (TOTAL DOMINANCE / NETWORK COMPROMISED), Time, Nodes Captured, XP Gained
- **Buttons:** REDEPLOY | DISCONNECT

---

## 12. HUD & In-Game Panels

### 12.1 Stats Panel (Top-Left, `#hud-stats-panel`)

- Node counts by ownership: Player / Enemy / Ally / Neutral
- Global Override percentage + progress bar
- Epoch number, Phase indicator, Timer
- Size: 400px wide

### 12.2 Node Info Panel (Top-Right, `#info-panel`)

- Appears on node selection
- Displays: Node name, Owner faction, Firewall HP bar, Compute Output
- **Action Panel** (visible during PLANNING phase on non-owned nodes):
  - BREACH button (primary)
  - SCAN button
  - CU commitment slider (1–100)
  - CONTACT AMBASSADOR button (for faction nodes only)

### 12.3 Intel Feed (Bottom-Right, `#intel-feed`)

- 300×250px log area with auto-scroll
- Shows game events chronologically
- Non-interactive (pointer-events: none)

### 12.4 Hotkeys Panel (Bottom-Left, `#hotkeys-panel`)

- Static key reference:
  - `[A]` Highlight Playable Nodes
  - `[E]` Highlight Enemy Targets
  - `` [`] `` or `[C]` Toggle Terminal CLI
  - `[Space]` Pause/Resume

### 12.5 Turn HUD (Top-Center, `.turn-hud`)

- Turn counter, Player indicator (ATTACKER/DEFENDER), AP remaining
- Timer, Alert/Stealth meters
- End Turn button

### 12.6 Toast Notifications (Top-Center, `#toast-container`)

- Auto-dismiss after 4 seconds
- Max 4 visible, oldest removed first
- Types: info (cyan border), capture (green), lost (red)
- Glitch animation on appear

### 12.7 Log Panel (Bottom, `.log-panel`)

- Collapsible with severity filtering (INFO, WARN, DANGER, SUCCESS)
- Clickable node references
- z-index: 9999, fixed position

---

## 13. Modal Dialogs

### 13.1 Diplomacy Modal (`#modal-diplomacy`)

- **Size:** 800px wide, max-height 80vh
- **Layout:** 2-column — contacts sidebar (1fr) + chat area (2fr)
- **Contacts Sidebar:**
  - State Actors (factions 2–5): Iron Grid, Silk Road, Euro Nexus, Pacific Vanguard
  - Non-State Actors CNSA (factions 6–8): Cyber Mercenaries, Sentinel Vanguard, Shadow Cartels
  - Each has color-coded icon and border
- **Chat Area:**
  - Header: Faction name + leader, status badge (NO ACCORD / ACTIVE)
  - Chat box: Scrollable message history
  - Chat input + SEND button
  - Treaty section: Type dropdown (Ceasefire / Trade / Alliance) + PROPOSE ACCORD + REVOKE ACCORD
- **Chat Message Types:**
  - OPERATIVE (player): green text
  - AMBASSADOR (AI): white text with emotion tag (e.g., `<STERN>`, `<GREEDY>`)
  - SYS: system messages (connection, errors)
- **Activation:** Click CONTACT AMBASSADOR from node info panel, or programmatic `openDiplomacyPanel(factionId)`

### 13.2 Sentinel Lab Modal (`#modal-sentinel`)

- **Size:** 800px wide, max-height 80vh
- **Layout:** 2-column — controls (1fr) + radar chart (1fr)
- **Controls Column:**
  - Sentinel name display
  - Status indicator (NOT INITIALIZED / ACTIVE / IDLE)
  - INITIALIZE SENTINEL button (hidden when active)
  - 4 policy sliders: Persistence, Stealth, Efficiency, Aggression (0–100)
  - SAVE POLICY + DEPLOY buttons
  - Operational logs feed
- **Radar Column:** Canvas-rendered spider chart of 4 parameters
- **Activation:** Click SENTINEL LAB button in game view

### 13.3 Settings Modal (`#modal-settings`)

- Master Volume slider
- Colorblind Mode toggle
- CRT FX toggle
- APPLY button

---

## 14. Canvas & Rendering

### 14.1 Rendering Modes

| Mode | Technology | Condition |
|---|---|---|
| **3D Globe** | Globe.gl + Three.js | WebGL hardware-accelerated available |
| **2D Fallback** | HTML5 Canvas 2D | WebGL unavailable or software renderer detected |

### 14.2 WebGL Detection

Software renderers force 2D fallback: SwiftShader, LLVMpipe, "Software".

### 14.3 3D Globe Rendering

- `Globe()` instance from `globe.gl`
- Transparent background over CSS space gradient
- Atmosphere glow in accent color
- Nodes rendered as colored points on globe surface
- Connections rendered as arcs between nodes

### 14.4 2D Fallback Rendering

- Canvas fills `#canvas-container` (100% × 100%)
- Background: `#0a0e17`
- Title: `[NETWORK MAP - 2D DEGRADED MODE]` (top-left, green)
- **Nodes:** Circular points (radius 6px) in circular layout
  - Blue `#4a6a9a` = Defender-owned
  - Dark red `#d94a4a` = Attacker-owned
  - Bright red `#ff6b6b` = Compromised
  - White border (0.5px) for visibility
  - Node ID label below each point
- **Connections:** Lines between connected nodes (`rgba(42, 74, 106, 0.6)`, 1.5px)
- **HUD overlay** (top-left): Turn, Player, AP, Alert, Stealth
- **Legend** (bottom-left): Color key for node types
- **Status counters** (bottom-right): Total, Compromised, Discovered counts
- **Click interaction:** Hit detection on nodes (15px radius), dispatches `nodeClicked` event

### 14.5 Rendering Event Flow

```
TurnController._applyState(state)
  → events.emit(GAME_STATE_UPDATE, { gameState })
    → main.js listener → renderer.renderGameState(gameState)
      → 3D mode: renderNodes() + renderConnections() on globe
      → 2D mode: full canvas redraw (clear → connections → nodes → HUD → legend)
```

---

## 15. Event Bus Architecture

### 15.1 Singleton Pattern

`GameEventBus` class in `game-events.js` — single instance exported as `events`.

Methods: `on(event, cb)`, `once(event, cb)`, `off(event, cb)`, `emit(event, payload)`, `clear([event])`, `debug()`.

### 15.2 Event Catalog

| Event | Constant | Payload | Description |
|---|---|---|---|
| `node:select` | NODE_SELECT | `{ nodeId, node }` | Player selects a node |
| `node:deselect` | NODE_DESELECT | `{}` | Deselect current node |
| `node:hover` | NODE_HOVER | `{ nodeId, node }` | Hover over node |
| `node:hover_end` | NODE_HOVER_END | `{}` | Hover ends |
| `action:execute` | ACTION_EXECUTE | `{ actionId, actionName, targetNode }` | Player initiates action |
| `action:result` | ACTION_RESULT | `{ success, detected, message, details }` | Action outcome |
| `action:preview` | ACTION_PREVIEW | `{ actionId, targetNode }` | Preview action effect |
| `turn:switch` | TURN_SWITCH | `{ from, to }` | Turn switches between players |
| `turn:start` | TURN_START | `{ turn, player, isMyTurn }` | New turn begins |
| `turn:end` | TURN_END | `{ turn, player }` | Turn ends |
| `game:create` | GAME_CREATE | `{ role, difficulty, scenario }` | Game session requested |
| `game:start` | GAME_START | `{ sessionId, role, gameState }` | Game begins |
| `game:over` | GAME_OVER | `{ winner, reason, score }` | Game ends |
| `game:state` | GAME_STATE | `{ ...gameState, role }` | Full state broadcast |
| `game:state:update` | GAME_STATE_UPDATE | `{ gameState, sessionId, role }` | State update for renderer |
| `alert:change` | ALERT_CHANGE | `{ oldLevel, newLevel }` | Alert level changed |
| `stealth:change` | STEALTH_CHANGE | `{ oldLevel, newLevel }` | Stealth level changed |
| `log:add` | LOG_ADD | `{ message, severity, timestamp }` | Add log entry |
| `toast:show` | TOAST_SHOW | `{ message, type }` | Show toast notification |
| `view:change` | VIEW_CHANGE | `{ from, to }` | Screen navigation |
| `console:toggle` | CONSOLE_TOGGLE | `{}` | Toggle terminal |
| `panel:toggle` | PANEL_TOGGLE | `{ panel, visible }` | Toggle UI panel |
| `hotkey:press` | HOTKEY | `{ key, action }` | Hotkey pressed |

### 15.3 Key Event Wiring

```
BREACH button → events.emit(ACTION_EXECUTE, { actionId: 1, actionName: 'EXPLOIT_VULNERABILITY', targetNode })
SCAN button   → events.emit(ACTION_EXECUTE, { actionId: 0, actionName: 'SCAN_NETWORK', targetNode })

TurnController listens: events.on(ACTION_EXECUTE, payload => this.onPlayerAction(payload))
  → Calls backend API
  → Updates state
  → Emits GAME_STATE_UPDATE, ACTION_RESULT, TURN_START, etc.
```

---

## 16. API Contract Reference

### 16.1 Authentication

| Method | Endpoint | Auth | Body | Response |
|---|---|---|---|---|
| POST | `/api/auth/register` | None | `{ username, password }` | `{ access_token, token_type, player }` |
| POST | `/api/auth/login` | None | `{ username, password }` | `{ access_token, token_type, player }` |

### 16.2 Game Session (v3.2 Turn-Based)

| Method | Endpoint | Auth | Body | Response |
|---|---|---|---|---|
| POST | `/api/game/create` | None | `{ role, difficulty, scenario }` | `{ session_id, game_state }` |
| POST | `/api/game/action` | None | `{ session_id, player_role, action_type, action_id, target_node }` | `{ success, detected, message, details, ai_actions, game_state }` |
| POST | `/api/game/end-turn` | None | `{ session_id, player_role }` | `{ ai_actions, game_state }` |
| GET | `/api/game/state/{session_id}` | None | — | `{ game_state }` |
| GET | `/api/game/scenarios` | None | — | `{ scenarios: [...] }` |

### 16.3 Game State Object

```json
{
  "current_turn": 1,
  "max_turns": 50,
  "current_player": "attacker",
  "action_points_remaining": 1,
  "alert_level": 0,
  "stealth_level": 100,
  "nodes": [
    {
      "id": 0,
      "name": "NODE-00",
      "owned_by": "defender",
      "defense_level": 2,
      "discovered": false,
      "detected": false,
      "patched": false,
      "isolated": false
    }
  ],
  "connections": [
    { "source": 0, "target": 1 }
  ],
  "discovered_nodes": [],
  "compromised_nodes": [],
  "detected_nodes": [],
  "resources": {
    "attacker": { "exploit_kits": 8, "malware_payloads": 3, "time_remaining": 50 },
    "defender": { "ir_budget": 80, "patches_available": 5, "scan_bandwidth": 2 }
  },
  "objectives": {
    "objectives": [
      { "description": "Compromise 5 nodes", "type": "attacker_compromise", "winner": "attacker", "threshold": 5, "met": false, "progress": 0.0 }
    ],
    "progress": {}
  },
  "game_over": false,
  "winner": null
}
```

### 16.4 Diplomacy

| Method | Endpoint | Auth | Body | Response |
|---|---|---|---|---|
| POST | `/api/diplomacy/chat` | Bearer | `{ faction_id, message }` | `{ reply }` |
| POST | `/api/diplomacy/propose` | Bearer | `{ target_faction_id, type, proposal_text }` | `{ status: "accepted"/"rejected" }` |
| GET | `/api/diplomacy/accords` | Bearer | — | `[{ id, type, status, ... }]` |

### 16.5 Sentinel Lab

| Method | Endpoint | Auth | Body | Response |
|---|---|---|---|---|
| GET | `/api/sentinels` | Bearer | — | `{ sentinels: [...] }` |
| POST | `/api/sentinels/create` | Bearer | `{ name }` | `{ id, name, ... }` |
| PATCH | `/api/sentinels/{id}/policy` | Bearer | `{ persistence, stealth, efficiency, aggression }` | `{ updated }` |
| POST | `/api/sentinels/{id}/toggle` | Bearer | — | `{ active: bool }` |
| GET | `/api/sentinels/{id}/logs` | Bearer | — | `{ logs: [...] }` |

### 16.6 Legacy Endpoints (v3.1, epoch-based)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/world/state` | Bearer | Full node list |
| GET | `/api/epoch/current` | Bearer | Current epoch info |
| POST | `/api/epoch/action` | Bearer | Submit epoch action |
| GET | `/api/faction/{id}` | Bearer | Faction details |
| GET | `/api/news/latest` | Bearer | Generated news feed |
| GET | `/api/leaderboard` | None | Global rankings |
| POST | `/api/players/me/game-over` | Bearer | Submit end-game stats |

---

## 17. Controls & Accessibility

### 17.1 Keyboard Controls

| Key | Action |
|---|---|
| `A` (hold) | Highlight playable nodes |
| `E` (hold) | Highlight enemy targets |
| `` ` `` or `C` | Toggle terminal CLI |
| `Space` | Pause / Resume |
| `Enter` / `Space` | Activate focused element |
| `Escape` | Close modals / menus |
| `1`–`7` | Quick action hotkeys (mapped to action slots) |
| `Tab` | Navigate focus |

### 17.2 Gamepad Support

Full Gamepad API: D-pad navigation, face buttons (A=confirm, B=cancel), triggers, analog sticks for map panning.

### 17.3 Terminal CLI Commands

15 game actions + 4 meta commands. Tab completion for commands and node names. Command history with arrow keys.

### 17.4 Accessibility Features

- ARIA live regions for real-time announcements (`#intel-feed`)
- Focus traps in modals
- Reduced motion mode
- High contrast mode
- UI scaling
- Colorblind mode toggle
- Keyboard-only navigation support

---

## 18. Design System & Theming

### 18.1 Color Palette

| Token | Hex | Usage |
|---|---|---|
| `--color-bg` | `#0a0e17` | Primary background |
| `--color-player` | `#00ffdd` | Player/defender elements, success states |
| `--color-enemy` | `#ff0055` | Attacker/enemy elements, danger states |
| `--color-accent` | `#00ffdd` | Borders, labels, highlights |
| `--color-warning` | `#ffcc00` | Warnings, phase indicators |
| `--color-ally` | `#4488ff` | Allied faction elements |
| `--color-neutral` | `#888888` | Neutral/unclaimed elements |
| `--color-text-muted` | `rgba(255,255,255,0.5)` | Secondary text |

### 18.2 Typography

| Token | Font | Usage |
|---|---|---|
| `--font-display` | System / custom display | Titles, headings |
| `--font-hud` | Rajdhani, sans-serif | HUD labels, stats |
| `--font-mono` | Monospace | Code, terminal, data |

### 18.3 UI Components

| Component | Style |
|---|---|
| `.panel` | Dark glass (`rgba(10,14,23,0.9)`), accent border, 4px radius |
| `.btn` | Transparent bg, accent border, uppercase, letter-spacing |
| `.btn-primary` | Filled accent color, dark text |
| `.btn-danger` | Red border, red text |
| `.progress-track` | Dark track with colored fill bar |
| `.modal-overlay` | Fixed full-screen, dark semi-transparent bg |

### 18.4 Visual Effects

- CRT scanline overlay (toggleable)
- Glitch animations (`glitch-anim-1`)
- Text-shadow glow on key elements
- Backdrop blur on panels (`blur(4px)`)
- Neon border glow via `box-shadow`

---

## 19. Known Issues & Gaps

### 19.1 Functional Issues

| Issue | Severity | Location | Description |
|---|---|---|---|
| BREACH/SCAN targeting | Medium | `ui-manager.js` | Action panel uses `selectedNodeId` from v3.1 engine; needs wiring to v3.2 node selection |
| Diplomacy auth required | Medium | `main.py` | `/api/diplomacy/*` endpoints require Bearer token; chat fails if token expired |
| Phase gating | Medium | `ui-manager.js` | Action panel only shows during `PLANNING` phase check from v3.1 epoch system; not wired to v3.2 turn system |
| Diplomacy modal open trigger | Low | `ui-manager.js` | CONTACT AMBASSADOR button depends on v3.1 `faction_id` on nodes; v3.2 nodes don't carry `faction_id` |
| Canvas resize | Low | `renderer.js` | 2D fallback resize handler calls `renderFallback()` (v3.1) instead of `renderGameState()` |
| Game state field mapping | Low | `turn-controller.js` | Frontend uses camelCase (`currentTurn`), backend sends snake_case (`current_turn`) |

### 19.2 UX Gaps

| Gap | Description |
|---|---|
| No action feedback animation | Actions complete silently; no visual feedback on the node being attacked |
| Missing turn transition animation | Turn switches happen instantly with no dramatic transition |
| No undo/confirmation | Actions are immediately executed with no confirmation dialog |
| Limited mobile support | Layout is desktop-first with no responsive breakpoints for mobile |
| Missing action tooltip | No hover tooltips showing success rate, stealth cost, resource cost before executing |
| No minimap | Large scenarios (20–30 nodes) need a minimap for orientation |
| No sound feedback for actions | `audio.playClick()` used generically; no distinct sounds per action type |
| Intel feed not connected | `#intel-feed` is not wired to the v3.2 `LOG_ADD` event system |

---

## 20. Reengineering Recommendations

### 20.1 Critical Fixes (Priority 1)

1. **Unify v3.1 and v3.2 action systems** — The HUD action panel still uses v3.1 epoch-based logic. All game actions should flow exclusively through the v3.2 event bus (`ACTION_EXECUTE` → `TurnController`).

2. **Wire node selection to v3.2** — Node clicks on the canvas should emit `NODE_SELECT` events through the event bus, and the info panel should listen to `NODE_SELECT` instead of legacy `nodeSelected` DOM events.

3. **Connect Intel Feed to event bus** — `#intel-feed` should subscribe to `LOG_ADD` events from `TurnController` action results.

4. **Fix phase gating** — The action panel visibility should check `TurnController.isMyTurn` instead of v3.1 `currentEpoch.phase`.

5. **Fix diplomacy authentication** — Either make diplomacy endpoints auth-optional for dev mode, or ensure the auth token is always sent correctly.

### 20.2 UX Improvements (Priority 2)

6. **Action preview tooltips** — Show success rate, stealth cost, detection chance, and resource cost on hover before executing.

7. **Turn transition animation** — Dramatic screen flash or border pulse when turns switch.

8. **Action result animations** — Node pulse/glow on successful attack, shake on failed, red flash on detection.

9. **Confirmation dialog for high-cost actions** — EXFILTRATE_DATA, INCIDENT_RESPONSE, RESTORE_BACKUP should prompt "Are you sure?"

10. **Progressive disclosure** — Hide advanced actions until prerequisites are met (e.g., LATERAL_MOVEMENT only available after owning adjacent node).

### 20.3 Architecture Improvements (Priority 3)

11. **Component framework** — Migrate from inline HTML templates in `main.js` to a lightweight component system (Lit, Preact, or Svelte) for maintainability.

12. **State management** — Replace global `window.GameInstance` / `window.V32` with a proper reactive store that components subscribe to.

13. **CSS modularization** — Split the monolithic CSS files into per-component CSS modules or use CSS-in-JS.

14. **Responsive design** — Add breakpoints for tablet (768px) and mobile (480px) layouts.

15. **WebSocket integration for v3.2** — Currently v3.2 uses REST polling. Add WebSocket push for real-time AI turn results and multiplayer readiness.

### 20.4 Content Improvements (Priority 4)

16. **Expanded scenario narratives** — Each scenario should have a multi-paragraph briefing with thematic context.

17. **Dynamic difficulty adjustment** — AI agent difficulty should adapt based on player performance mid-game.

18. **Achievement system** — Track and display accomplishments (first scan, first breach, stealth run, etc.)

19. **Replay system** — Allow replaying completed games to study strategy.

20. **Localization readiness** — Extract all user-facing strings to a translation file.

---

*End of specification. This document should serve as the authoritative reference for all UI/UX reengineering work on Neo-Hack: Gridlock v3.2.*
