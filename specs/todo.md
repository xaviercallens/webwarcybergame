# Phase 2 — Sovereign Algorithm: Implementation Guide

**Status:** 🟡 Not Started | **Target:** Public Beta ("The Breach")
**Baseline:** Phase 1 complete — FastAPI backend, Player auth, Leaderboard, Static Vite frontend, Cloud Run + Cloud SQL deployed on `webwar-490207`.

---

## 🔴 Sprint 0 — Security Hardening (Week 1)

> [!CAUTION]
> These items block all Phase 2 work. Do NOT ship new features until these are resolved.

- [x] **Fix hardcoded JWT secret** — `auth.py` line 15: read from `os.environ["JWT_SECRET"]`
- [x] **Restrict CORS origins** — `main.py` line 31: replace `allow_origins=["*"]` with deployed URL + localhost
- [x] **Add rate limiting** on `/api/auth/login` and `/api/auth/register` (use `slowapi`)
- [x] **Cap leaderboard `limit`** — add `Query(default=10, ge=1, le=100)`
- [x] **Add `.dockerignore`** — exclude `.git`, `node_modules`, `*.zip`, `*.png`, `*.log`, `*.db`
- [x] **Separate Alembic from CMD** — run migrations in Cloud Build, not on container startup

---

## 🟠 Sprint 1 — World State & Epoch Engine (Weeks 2–3)

### 1.1 Data Model — Nodes, Factions, Epochs

- [x] Design PostgreSQL schema for `Node`, `Faction`, `Epoch`, `EpochAction`
  - `Node`: id, name, lat, lng, faction_id, defense_level, compute_output, node_class (TIER_1/2/3)
  - `Faction`: id, name, color, compute_reserves, global_influence_pct
  - `Epoch`: id, number, phase (PLANNING/SIM/TRANSITION), started_at, ended_at
  - `EpochAction`: id, epoch_id, player_id, action_type (SCAN/BREACH/DEFEND/TREATY), target_node_id
- [x] Create Alembic migration for new tables
- [x] Seed initial world state: 5 factions × ~50 starting nodes each = 250 nodes
  - Silicon Valley Bloc, Iron Grid, Silk Road Coalition, Euro Nexus, Pacific Vanguard

### 1.2 Epoch Loop Backend

- [x] `POST /api/epoch/action` — submit player action during PLANNING phase
- [x] `GET /api/epoch/current` — return current epoch number, phase, and time remaining
- [x] `GET /api/world/state` — return all nodes with faction ownership and stats
- [x] `GET /api/faction/{id}` — return faction stats, compute reserves, node count
- [x] Epoch Scheduler — background task (APScheduler or Cloud Scheduler)
  - 10 min PLANNING → 4 min SIM → 1 min TRANSITION → repeat
  - During TRANSITION: resolve all actions, flip nodes, update compute reserves
- [x] Epoch resolution engine: attack/defense calculations
  - Attacker CU vs Defender defense_level → probability-based outcome
  - Multiple attackers on same node: highest CU wins

### 1.3 Compute Units (CU) Economy

- [x] Each node generates CU per epoch based on `node_class` tier
- [x] Faction `compute_reserves` updated during TRANSITION
- [x] Actions cost CU: SCAN (10), BREACH (50–200), DEFEND (30)
- [x] `GET /api/faction/{id}/economy` — CU income, expenses, and balance per epoch

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

- [x] In-game terminal overlay activated with backtick `` ` ``
- [x] Commands:
  - [x] `/scan [node_id]` — reveal node stats and defenses
  - [x] `/breach [node_id]` — launch attack (costs CU)
  - [x] `/defend [node_id]` — reinforce owned node
  - [x] `/status` — show own faction stats
  - [x] `/epoch` — show current epoch info
- [x] Terminal output styled as green-on-black monospace


---

## 🟢 Sprint 3 — Gemini LLM Diplomacy Engine (Weeks 6–7)

### 3.1 Faction AI Ambassadors

- [x] Enable Gemini API (`aiplatform.googleapis.com`)
- [x] Create `DiplomacyService` using Gemini 2.5 Flash
- [x] System prompt per faction ambassador with personality + current game state injection
  - Silicon Valley: cautious, privacy-focused, values data sovereignty
  - Iron Grid: aggressive, transactional, respects strength
  - Silk Road: opportunistic, trade-focused, values mutual benefit
- [x] `POST /api/diplomacy/chat` — player sends message to faction ambassador
- [x] Context injection: inject current epoch stats, recent battles, treaty history into LLM context

### 3.2 Treaty (Accords) System

- [x] `POST /api/diplomacy/propose` — player drafts a treaty (alliance, ceasefire, trade)
- [x] LLM evaluates proposal against game state → accept/reject/counter
- [x] `GET /api/diplomacy/accords` — list active treaties
- [x] Active treaties automate CU sharing between factions per epoch
- [x] Treaty violations detected: attacking an ally's node breaks the accord
- [x] `POST /api/diplomacy/break` — manually break an accord (reputation penalty)

### 3.3 AI-Generated News & Briefings

- [x] After each TRANSITION, Gemini generates 2–3 sentences summarizing epoch outcomes
- [x] `GET /api/news/latest` — returns last 10 news items
- [x] News displayed in Intel Feed panel on the HUD

---

## 🟢 Sprint 3.5 — Cyber Non-State Actors & UI Restoration

- [x] Enhance backend data seeder to create Cyber Mercenaries, Sentinel Vanguard, and Shadow Cartels
- [x] Add Persona configurations for the new CNSA factions
- [x] Implement `<EMOTION>` tag accessibility parsers in frontend
- [x] Restore Diplomacy UI and map to all 8 factions
- [x] Apply specific Accord mechanics (Buffs/Debuffs) for CNSA treaties

---

## 🟢 Sprint 4 — Sentinel Lab (Completed)

> [!NOTE]
> Autonomous AI units configured by the player to fight on their behalf.

- [x] **Data Model**
  - Add `Sentinel` (id, player_id, name, status=`IDLE|DEPLOYED`)
  - Add `SentinelPolicy` (persistance, stealth, efficiency, aggression) [Floats 0.0-1.0]
- [x] **API Endpoints**
  - `POST /api/sentinels/create`: Initialize new AI agent
  - `PATCH /api/sentinels/policy`: Update AI heuristics (sliders)
  - `POST /api/sentinels/toggle`: Deploy/Recall
- [x] **Frontend UI (`#modal-sentinel-lab`)**
  - Render a visual readout of the Policy Weights using `Chart.js` Radar graph.
  - 4 Sliders to adjust weights.
  - Render an Action Log box pulling from `SentinelActionLog`.
- [x] **Epoch Engine Injection**
  - During `TRANSITION`, deployed Sentinels autonomously act. High aggression = attack, High defense = fortify, etc.

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
