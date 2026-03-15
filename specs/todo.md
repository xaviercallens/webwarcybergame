# Phase 2 — Sovereign Algorithm: Implementation Guide

**Status:** 🟡 Not Started | **Target:** Public Beta ("The Breach")
**Baseline:** Phase 1 complete — FastAPI backend, Player auth, Leaderboard, Static Vite frontend, Cloud Run + Cloud SQL deployed on `webwar-490207`.

---

## 🔴 Sprint 0 — Security Hardening (Week 1)

> [!CAUTION]
> These items block all Phase 2 work. Do NOT ship new features until these are resolved.

- [ ] **Fix hardcoded JWT secret** — `auth.py` line 15: read from `os.environ["JWT_SECRET"]`
- [ ] **Restrict CORS origins** — `main.py` line 31: replace `allow_origins=["*"]` with deployed URL + localhost
- [ ] **Add rate limiting** on `/api/auth/login` and `/api/auth/register` (use `slowapi`)
- [ ] **Cap leaderboard `limit`** — add `Query(default=10, ge=1, le=100)`
- [ ] **Add `.dockerignore`** — exclude `.git`, `node_modules`, `*.zip`, `*.png`, `*.log`, `*.db`
- [ ] **Separate Alembic from CMD** — run migrations in Cloud Build, not on container startup

---

## 🟠 Sprint 1 — World State & Epoch Engine (Weeks 2–3)

### 1.1 Data Model — Nodes, Factions, Epochs

- [ ] Design PostgreSQL schema for `Node`, `Faction`, `Epoch`, `EpochAction`
  - `Node`: id, name, lat, lng, faction_id, defense_level, compute_output, node_class (TIER_1/2/3)
  - `Faction`: id, name, color, compute_reserves, global_influence_pct
  - `Epoch`: id, number, phase (PLANNING/SIM/TRANSITION), started_at, ended_at
  - `EpochAction`: id, epoch_id, player_id, action_type (SCAN/BREACH/DEFEND/TREATY), target_node_id
- [ ] Create Alembic migration for new tables
- [ ] Seed initial world state: 5 factions × ~50 starting nodes each = 250 nodes
  - Silicon Valley Bloc, Iron Grid, Silk Road Coalition, Euro Nexus, Pacific Vanguard

### 1.2 Epoch Loop Backend

- [ ] `POST /api/epoch/action` — submit player action during PLANNING phase
- [ ] `GET /api/epoch/current` — return current epoch number, phase, and time remaining
- [ ] `GET /api/world/state` — return all nodes with faction ownership and stats
- [ ] `GET /api/faction/{id}` — return faction stats, compute reserves, node count
- [ ] Epoch Scheduler — background task (APScheduler or Cloud Scheduler)
  - 10 min PLANNING → 4 min SIM → 1 min TRANSITION → repeat
  - During TRANSITION: resolve all actions, flip nodes, update compute reserves
- [ ] Epoch resolution engine: attack/defense calculations
  - Attacker CU vs Defender defense_level → probability-based outcome
  - Multiple attackers on same node: highest CU wins

### 1.3 Compute Units (CU) Economy

- [ ] Each node generates CU per epoch based on `node_class` tier
- [ ] Faction `compute_reserves` updated during TRANSITION
- [ ] Actions cost CU: SCAN (10), BREACH (50–200), DEFEND (30)
- [ ] `GET /api/faction/{id}/economy` — CU income, expenses, and balance per epoch

---

## 🟡 Sprint 2 — Three.js Globe & Real-Time HUD (Weeks 4–5)

### 2.1 3D Globe Renderer

- [x] Integrate Three.js globe with world-state data from `/api/world/state`
- [x] Nodes rendered as glowing dots, color-coded by faction
- [x] Node size reflects `node_class` tier
- [x] Click-to-select node → show info panel (owner, defense, CU output)
- [ ] Attack arcs: animated curves between nodes during SIM phase (WIP - backend refactor needed for edges)

### 2.2 Combat HUD

- [x] Epoch timer bar — shows current phase + countdown
- [x] Faction scoreboard sidebar — live influence percentages
- [x] Intel Feed panel — scrolling log of recent epoch events ("Node X captured by Iron Grid")
- [x] Action buttons: SCAN, BREACH, DEFEND — disabled outside PLANNING phase
- [ ] Minimap with faction territory heat overlay

### 2.3 Terminal CLI

- [ ] In-game terminal overlay activated with backtick `` ` ``
- [ ] Commands:
  - `/scan [node_id]` — reveal node stats and defenses
  - `/breach [node_id]` — launch attack (costs CU)
  - `/defend [node_id]` — reinforce owned node
  - `/status` — show own faction stats
  - `/epoch` — show current epoch info
- [ ] Terminal output styled as green-on-black monospace

---

## 🟢 Sprint 3 — Gemini LLM Diplomacy Engine (Weeks 6–7)

### 3.1 Faction AI Ambassadors

- [ ] Enable Gemini API (`aiplatform.googleapis.com`)
- [ ] Create `DiplomacyService` using Gemini 2.5 Flash
- [ ] System prompt per faction ambassador with personality + current game state injection
  - Silicon Valley: cautious, privacy-focused, values data sovereignty
  - Iron Grid: aggressive, transactional, respects strength
  - Silk Road: opportunistic, trade-focused, values mutual benefit
- [ ] `POST /api/diplomacy/chat` — player sends message to faction ambassador
- [ ] Context injection: inject current epoch stats, recent battles, treaty history into LLM context

### 3.2 Treaty (Accords) System

- [ ] `POST /api/diplomacy/propose` — player drafts a treaty (alliance, ceasefire, trade)
- [ ] LLM evaluates proposal against game state → accept/reject/counter
- [ ] `GET /api/diplomacy/accords` — list active treaties
- [ ] Active treaties automate CU sharing between factions per epoch
- [ ] Treaty violations detected: attacking an ally's node breaks the accord
- [ ] `POST /api/diplomacy/break` — manually break an accord (reputation penalty)

### 3.3 AI-Generated News & Briefings

- [ ] After each TRANSITION, Gemini generates 2–3 sentences summarizing epoch outcomes
- [ ] `GET /api/news/latest` — returns last 10 news items
- [ ] News displayed in Intel Feed panel on the HUD

---

## 🔵 Sprint 4 — Sentinel RL Training Suite (Weeks 8–10)

### 4.1 Sentinel Data Model

- [ ] `Sentinel` model: id, player_id, name, status (TRAINING/DEPLOYED/IDLE)
- [ ] `SentinelPolicy` model: persistence_weight, stealth_weight, efficiency_weight, aggression_weight
- [ ] `POST /api/sentinels/create` — create new sentinel with default weights
- [ ] `PATCH /api/sentinels/{id}/policy` — update reward weights

### 4.2 Sentinel Lab UI

- [ ] "Sentinel Lab" panel accessible from HUD
- [ ] Sliders for reward function weights:
  - Persistence (maintain foothold vs retreat)
  - Stealth (penalty for detection)
  - Efficiency (minimize CU per breach)
  - Aggression (favor attack over defense)
- [ ] Radar chart showing current policy shape (Chart.js)
- [ ] Deploy/Recall buttons

### 4.3 Sentinel Behavior Engine

- [ ] During SIM phase, deployed sentinels execute autonomous actions based on weighted policy
- [ ] Simple rule-based engine first (no ML), weights determine action probabilities:
  - High aggression → more BREACH actions
  - High stealth → target weaker nodes, avoid heavily defended ones
  - High persistence → defend owned nodes first
- [ ] Sentinel action log: `GET /api/sentinels/{id}/log`
- [ ] *Future:* Vertex AI PPO training pipeline (Phase 3)

---

## 🟣 Sprint 5 — Real-Time Sync & WebSockets (Week 11)

### 5.1 WebSocket Event Bus

- [ ] Add WebSocket support to FastAPI (`/ws/game`)
- [ ] Broadcast epoch phase changes to all connected clients
- [ ] Broadcast node ownership changes during TRANSITION
- [ ] Broadcast diplomacy events (new treaty, broken accord)
- [ ] Client reconnection handling with state catchup

### 5.2 Notification System

- [ ] Push notifications for:
  - Your node was attacked
  - Treaty proposed to your faction
  - Epoch transition results summary
  - Sentinel completed an action
- [ ] `GET /api/notifications` — unread notifications for current player

---

## ⬛ Sprint 6 — GCP Infrastructure Scaling (Week 12)

### 6.1 Cloud Scheduler for Epochs

- [ ] Create Cloud Scheduler job → triggers epoch transitions via Pub/Sub or HTTP
- [ ] Cloud Run Job for epoch resolution (separate from API service)
- [ ] Pub/Sub topic: `epoch-transition` — triggers resolution worker

### 6.2 Firestore Integration (Optional — at 5k+ MAU)

- [ ] Migrate world-state reads to Firestore for real-time listener support
- [ ] Keep PostgreSQL as system of record, Firestore as read-optimized cache
- [ ] Firestore schema: `factions/{id}`, `nodes/{id}`, `epochs/{id}`

### 6.3 Cloud Armor & API Gateway

- [ ] Enable Cloud Armor WAF on Cloud Run
- [ ] Rate limit: 100 req/min per IP on `/api/auth/*`
- [ ] Rate limit: 30 req/min per authenticated user on `/api/epoch/action`
- [ ] Geographic allow rules (optional — block known bot regions)

### 6.4 Monitoring & Observability

- [ ] Cloud Monitoring dashboard: request latency, error rate, DB connections
- [ ] Cloud Trace for end-to-end request tracing
- [ ] Alert policy: > 5% error rate over 5 minutes → email notification
- [ ] Structured JSON logging from FastAPI

---

## 📊 Milestone Summary

| Sprint | Deliverable | Duration | Dependencies |
|--------|------------|----------|-------------|
| **S0** | Security hardening | 1 week | None |
| **S1** | Epoch engine + world state | 2 weeks | S0 |
| **S2** | Three.js globe + HUD | 2 weeks | S1 |
| **S3** | Gemini diplomacy | 2 weeks | S1 |
| **S4** | Sentinel RL suite | 3 weeks | S1, S2 |
| **S5** | WebSocket real-time sync | 1 week | S1, S2 |
| **S6** | GCP scaling infrastructure | 1 week | S1–S5 |

**Total estimated duration: 12 weeks**

---

## 🏗️ Architecture Target (Phase 2)

```
┌────────────────────────────────────────────────┐
│              Three.js Globe + HUD              │
│        Terminal CLI  |  Sentinel Lab            │
│            (Vite + WebSocket client)            │
└────────────────┬───────────────────────────────┘
                 │ HTTPS / WSS
┌────────────────▼───────────────────────────────┐
│           Cloud Run (FastAPI + uvicorn)         │
│  /api/*  |  /ws/game  |  /api/diplomacy/*      │
│  Epoch actions  |  World state  |  Auth         │
└──────┬─────────────┬──────────────┬────────────┘
       │             │              │
  ┌────▼────┐   ┌────▼────┐   ┌────▼─────┐
  │Cloud SQL│   │ Gemini  │   │  Pub/Sub │
  │ (PG 15) │   │  2.5    │   │  + Cloud │
  │ World   │   │  Flash  │   │ Scheduler│
  │ State   │   │ Diploma │   │  Epochs  │
  └─────────┘   └─────────┘   └──────────┘
```
