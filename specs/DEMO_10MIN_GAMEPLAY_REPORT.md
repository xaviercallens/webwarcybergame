# Neo-Hack: Gridlock — 10-Minute Demo Gameplay Simulation Report

**Version:** 3.2.0 | **Date:** March 21, 2026  
**Scenario:** Operation Crimson Tide (16-node Financial Network)  
**Duration:** 10 minutes (20 turns, ~30s/turn) | **Mode:** Human Attacker vs PPO AI Defender

---

## 1. Scenario Setup & Faction Roster

### 1.1 Scenario Parameters

| Param | Value |
|---|---|
| Nodes | 16 | Max Turns | 20 | Attacker AP | 2/turn | Defender AP | 1 (scales to 2 at alert≥50) |
| Type | capture_flag | Difficulty | Normal (PPO) |

### 1.2 Five Factions — Non-Equilibrium

| # | Faction | Size | Nodes | Leader | Role | Power |
|---|---|---|---|---|---|---|
| 1 | **Silicon Valley** (Player) | Small | 2 (N-00,01) | The Architect | Human Attacker | ★★☆☆☆ |
| 2 | **Iron Grid** | Large | 5 (N-02..06) | General Volkov | AI Defender (PPO) | ★★★★★ |
| 3 | **Silk Road Coalition** | Medium | 4 (N-07..10) | Chairman Wei | NPC Diplomacy | ★★★☆☆ |
| 4 | **Shadow Cartels** | Small | 2 (N-11,12) | Cipher | NPC Hostile | ★★☆☆☆ |
| 5 | **Sentinel Vanguard** | Medium | 3 (N-13..15) | Oracle | NPC Potential Ally | ★★★☆☆ |

### 1.3 Starting Resources

| Resource | Attacker | Defender |
|---|---|---|
| AP/turn | 2 | 1→2 |
| Exploit Kits | 10 | — |
| Malware Payloads | 3 | — |
| IR Budget | — | 100 |
| Patches | — | 5 |
| Scan Bandwidth | — | 2 |

### 1.4 Victory Conditions

- **Attacker wins:** Exfiltrate ≥100 data units OR own ≥8/16 nodes
- **Defender wins:** Alert reaches 100 OR survive 20 turns with <8 compromised

---

## 2. Network Topology

```
  SILICON VALLEY          IRON GRID                    SILK ROAD
  ┌─────┐  ┌─────┐    ┌─────┐┌─────┐┌─────┐      ┌─────┐┌─────┐
  │N-00 │──│N-01 │────│N-02 ││N-03 ││N-04 │──────│N-07 ││N-08 │
  │ GW  │  │ DNS │    │ FW  ││CORE ││ DB  │      │SILK ││ MKT │
  └─────┘  └──┬──┘    └──┬──┘└──┬──┘└──┬──┘      └──┬──┘└──┬──┘
              │          │     │     │              │     │
              │       ┌──┴──┐  │  ┌──┴──┐       ┌──┴──┐┌──┴──┐
              │       │N-05 │  │  │N-06 │       │N-09 ││N-10 │
              │       │ LOG │  │  │BKUP │       │ TRD ││VAULT│
              │       └─────┘  │  └─────┘       └─────┘└─────┘
              │                │
      SHADOW CARTELS           │      SENTINEL VANGUARD
     ┌─────┐┌─────┐           │    ┌─────┐┌─────┐┌─────┐
     │N-11 ││N-12 │───────────┘    │N-13 ││N-14 ││N-15 │
     │DARK ││CRYPT│                │ SOC ││CERT ││HIVE │
     └─────┘└─────┘                └─────┘└─────┘└─────┘
```

---

## 3. Turn-by-Turn Gameplay Simulation

### Pre-Game (0:00–0:45)

**Backend start:**
```bash
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload
npx vite --port 5173
```

**Login → POST `/api/auth/login`**
```json
{ "username": "GHOST_4X1", "password": "d3m0pa55" }
→ { "access_token": "eyJ...", "player": { "username": "GHOST_4X1", "rank": "SCRIPT_KIDDIE", "xp": 245 } }
```

**Create Game → POST `/api/game/create`**
```json
{ "role": "attacker", "difficulty": "normal", "scenario": "crimson_tide" }
→ { "session_id": "gs-47291", "game_state": { "current_turn": 1, "nodes": [...16 nodes...], "alert_level": 0, "stealth_level": 100 } }
```

**RL Agent loaded:** `ppo_defender_latest.zip` (SB3 PPO, CPU, obs_space=(176,), action_space=Discrete(7))

---

### TURN 1 — Reconnaissance (0:45–1:15)

**Action 1: SCAN_NETWORK** — CLI: `scan NODE-01`

```
POST /api/game/action → { session_id: "gs-47291", player_role: "attacker", action_id: 0, target_node: 1 }
```
RL env: discovers N-02, N-11 from N-01 adjacency. Stealth cost +5. Alert: 0→5. Not detected.
```
→ { success: true, detected: false, details: { discovered_nodes: 2 }, alert: 5, stealth: 95 }
```

**Action 2: SCAN_NETWORK** — discovers N-03, N-05, N-12 from N-02/N-11 adjacency.
Alert: 5→10. AP exhausted → turn switches to defender.

**AI Defender (PPO):**
```
Observation: [alert=10, compromised=2/16, detected=0]
PPO logits: [-0.42, 0.89, -0.15, -1.23, -0.67, 0.34, -0.91]
Sampled: action=0 (MONITOR_LOGS) → FAILED (alert<30, can't detect)
```
Turn → T2, back to attacker.

---

### TURN 2 — First Breach (1:15–1:45)

**Action 1: EXPLOIT_VULNERABILITY on N-02** — CLI: `exploit NODE-02`
```
POST /api/game/action → { action_id: 1, target_node: 2 }
```
RL: base_success=0.70, roll=0.38 → **SUCCESS**. N-02 owned. Exploit kits: 10→9. Stealth +30. Alert: 10→40. Not detected.

**Action 2: LATERAL_MOVEMENT N-02→N-03** — CLI: `lateral NODE-03`
RL: success=0.80, roll=0.22 → **SUCCESS**. N-03 owned. **DETECTED** (roll 0.31 < 0.45). Alert +20 → 60.

**AI Defender (PPO, now 1 AP since alert<50 at start of AI turn... actually alert=60 now, gets 2 AP next turn):**
```
Obs: [alert=60, comp=4, det=2]
PPO: action=1 (SCAN_FOR_MALWARE) → detects N-02, N-03. scan_bandwidth: 2→1.
```

Intel: `⚠ Lateral movement DETECTED. Iron Grid scanning for malware...`

---

### TURN 3 — Expanding South (1:45–2:15)

**Action 1: CLEAR_LOGS** — CLI: `clearlogs` — Success. Stealth +10. Alert: 60→70.

**Action 2: EXPLOIT N-11 (Shadow Cartels)** — defense=0, easy target.
RL: roll=0.15 < 0.70 → **SUCCESS**. N-11 owned. **DETECTED** (+20). Alert: 70→90.

**AI Defender (2 AP, alert≥50):**
```
PPO Action 1: APPLY_PATCH on N-04 (patches: 5→4)
PPO Action 2: ISOLATE_HOST on N-03 → N-03 severed from network! ★ Critical defensive move
```

Intel: `★ NODE-03 ISOLATED! Core router quarantined. Lateral path severed.`

**State: Attacker owns [0,1,2,3(isolated),11] = 5 nodes. Alert: 90.**

---

### TURN 4 — Diplomacy Phase (2:15–3:00)

Player opens Diplomacy Modal → clicks Silk Road Coalition.

**Chat #1 → POST `/api/diplomacy/chat`**
```json
{ "faction_id": 3, "message": "Chairman Wei, I propose a trade agreement. The Iron Grid grows too powerful." }
```

**Gemini LLM call:**
```
Model: gemini-2.5-flash | Temp: 0.7
System: "You are ambassador for Silk Road Coalition, known as Chairman Wei. Personality: Opportunistic, trade-focused..."
Prompt: "GAME STATE: T4/20, SV owns 5 nodes, alert 90%...\nPLAYER: 'Chairman Wei, I propose...'"
```
**Gemini response:** `[Intrigued] The Iron Grid's ambitions concern us too. A trade corridor between our networks could be... mutually enriching. What do you offer?`

**Chat #2:** Player offers NODE-02 access for safe passage through N-07.
**Gemini:** `[Calculating] A firewall node with Iron Grid access — considerable value. Propose formally.`

**Treaty → POST `/api/diplomacy/propose`**
```json
{ "target_faction_id": 3, "type": "TRADE", "proposal_text": "NODE-02 access for N-07 transit" }
```
**Gemini (temp=0.2):** `ACCEPT`
**Mock mode fallback:** faction=3, rate=0.80, roll=0.42 → ACCEPTED ✓

Toast: `✓ Trade Agreement with Silk Road ACCEPTED!`

---

### TURN 5 — Exploit & Counter (3:00–3:30)

**Action 1: EXPLOIT N-12** (Shadow Cartels Crypto) — SUCCESS. Exploit kits: 9→8.
**Action 2: PHISHING N-05** (Iron Grid Logs) — roll=0.41 < 0.60 → SUCCESS.

**AI Defender (2 AP):**
```
PPO: INCIDENT_RESPONSE on N-02 → RECLAIMED! (ir_budget: 100→90)
PPO: FIREWALL_RULE on N-06 → connections hardened
```

---

### TURN 6 — Failed Alliance (3:30–4:00)

**Diplomacy with Sentinel Vanguard (faction=7):**
Player: `"Oracle, the Shadow Cartels are neutralized. Let us ally."`

**Gemini:** `[Skeptical] Your 80% alert level suggests reckless methods, not responsible custody. Patch your nodes first.`

**Treaty proposal (Alliance):** **REJECTED** (Gemini: "REJECT" | Mock: rate=0.70, roll=0.85 → rejected)

**Combat: INSTALL_MALWARE on N-05** — SUCCESS. malware_payloads: 3→2. DETECTED. Alert→95.
**CLEAR_LOGS** — reduces evidence trail.

**AI Defender:** INCIDENT_RESPONSE on N-11 → reclaimed. APPLY_PATCH on N-08.

---

### TURNS 7–8 — Silk Road Corridor (4:00–5:00)

**T7-A1:** LATERAL to N-04 (patched) — FAILED (0.80×0.30=0.24, roll=0.67).
**T7-A2:** EXPLOIT N-07 via treaty — SUCCESS (treaty bonus: 0.95 success, no detection). Exploit kits: 8→7.

**AI T7:** INCIDENT_RESPONSE on N-05 (cleaned, ir: 90→80). ISOLATE N-12 (severed).

**T8-A1:** LATERAL N-07→N-08 — SUCCESS (barely, roll=0.18<0.24).
**T8-A2:** EXFILTRATE_DATA — 6 nodes × 5 = **30 data units**. Total: 30/100. DETECTED.

**AI T8:** INCIDENT_RESPONSE on N-03 (cleaned, ir: 80→70). SCAN_FOR_MALWARE → all detected.

---

### TURNS 9–10 — Final Exfiltration (5:00–6:30)

**T9-A1:** EXPLOIT N-09 (Trading) — SUCCESS via Silk Road corridor.
**T9-A2:** EXFILTRATE — 7 nodes × 5 = **35 units**. Total: 65/100.

**AI T9:** INCIDENT_RESPONSE on N-08 (ir: 70→60). Desperate defense.

**T10-A1:** EXFILTRATE — 6 nodes × 5 = **30 units**. Total: 95/100.
**T10-A2:** EXFILTRATE — **+25 units**. Total: **120/100 ★ OBJECTIVE MET!**

```
★★★ ATTACKER WINS — EXFILTRATION COMPLETE (120/100 data units) ★★★
```

---

## 4. Diplomacy & Gemini LLM Call Log

| # | Time | Endpoint | Faction | Type | Model | Temp | Response |
|---|---|---|---|---|---|---|---|
| 1 | 2:30 | `/diplomacy/chat` | Silk Road | Chat | gemini-2.5-flash | 0.7 | "[Intrigued] The Iron Grid's ambitions concern us..." |
| 2 | 2:45 | `/diplomacy/chat` | Silk Road | Chat | gemini-2.5-flash | 0.7 | "[Calculating] A firewall node... propose formally." |
| 3 | 2:55 | `/diplomacy/propose` | Silk Road | Treaty | gemini-2.5-flash | 0.2 | "ACCEPT" |
| 4 | 3:35 | `/diplomacy/chat` | Sentinel | Chat | gemini-2.5-flash | 0.7 | "[Skeptical] Your alert level suggests reckless methods..." |
| 5 | 3:50 | `/diplomacy/propose` | Sentinel | Treaty | gemini-2.5-flash | 0.2 | "REJECT" |

**System prompt pattern:**
```
Chat: "You are ambassador for {name}, known as {leader}. Personality: {desc}. 
       Respond in character, under 3 sentences. Start with [Emotion Subtitle]."
Treaty: "You are {leader} of {name}. Output exactly ONE WORD: ACCEPT or REJECT."
```

---

## 5. RL Execution Log (PPO AI Defender)

**Model:** `models/normal/ppo_defender_latest.zip` | SB3 PPO | CPU | Stochastic

| Turn | Alert | Compromised | PPO Action | Result | Reward | Resources Used |
|---|---|---|---|---|---|---|
| T1 | 10 | 2 | MONITOR_LOGS | Failed (alert<30) | -1 | — |
| T2 | 60 | 4 | SCAN_FOR_MALWARE | Detected N-02,03 | +10 | scan_bw: 2→1 |
| T3a | 90 | 5 | APPLY_PATCH (N-04) | Patched | +3 | patches: 5→4 |
| T3b | 90 | 5 | ISOLATE_HOST (N-03) | **★ Core severed** | +10 | — |
| T5a | 95 | 7 | INCIDENT_RESPONSE (N-02) | Reclaimed! | +15 | ir: 100→90 |
| T5b | 95 | 6 | FIREWALL_RULE (N-06) | Blocked | +3 | — |
| T6a | 95 | 6 | INCIDENT_RESPONSE (N-11) | Reclaimed! | +15 | ir: 90→80 |
| T6b | 95 | 5 | APPLY_PATCH (N-08) | Patched | +3 | patches: 4→3 |
| T7a | 95 | 7 | INCIDENT_RESPONSE (N-05) | Reclaimed! | +15 | ir: 80→70 |
| T7b | 95 | 6 | ISOLATE_HOST (N-12) | Severed | +10 | — |
| T8a | 100 | 7 | INCIDENT_RESPONSE (N-03) | Reclaimed! | +15 | ir: 70→60 |
| T8b | 100 | 6 | SCAN_FOR_MALWARE | Full detection | +10 | scan_bw: 1→0 |
| T9a | 100 | 7 | INCIDENT_RESPONSE (N-08) | Reclaimed! | +15 | ir: 60→50 |

**PPO Behavioral Pattern:** Early game — passive monitoring. Mid game (alert>50) — defensive patching + isolation. Late game (alert=100) — all-in INCIDENT_RESPONSE to reclaim nodes. Total IR budget spent: 50/100.

**Rule-based fallback priority** (if PPO unavailable): `[MONITOR, SCAN, PATCH, FIREWALL, IR]` cycling.

---

## 6. CLI Command Reference

| Command | Action ID | Example | Description |
|---|---|---|---|
| `scan <node>` | 0 | `scan NODE-01` | Discover adjacent nodes |
| `exploit <node>` | 1 | `exploit NODE-02` | Compromise via vulnerability |
| `phish <node>` | 2 | `phish NODE-05` | Social engineering attack |
| `malware <node>` | 3 | `malware NODE-05` | Install persistent backdoor |
| `elevate <node>` | 4 | `elevate NODE-03` | Escalate privileges |
| `lateral <node>` | 5 | `lateral NODE-03` | Move to adjacent node |
| `exfil` | 6 | `exfil` | Steal data from all owned nodes |
| `clearlogs` | 7 | `clearlogs` | Wipe forensic traces |
| `/help` | — | `/help` | Show all commands |
| `/status` | — | `/status` | Current game state |
| `/map` | — | `/map` | Show network topology |
| `/endturn` | — | `/endturn` | Skip remaining AP |

---

## 7. Alert Level Timeline

```
100│                                              ████████ ← DETECTED (T10)
 90│                          ██████████████████████
 80│                         █
 70│                    █████
 60│               █████
 50│              █
 40│         █████
 30│        █
 20│       █
 10│  █████
  0│██
   └──┬──┬──┬──┬──┬──┬──┬──┬──┬──
     T1  T2  T3  T4  T5  T6  T7  T8  T9  T10
```

---

## 8. Final Scoring & Leaderboard

### 8.1 Score Breakdown

| Metric | Value | Points |
|---|---|---|
| Nodes compromised (peak: 7) | 7 × 10 | +70 |
| Data exfiltrated | 120 × 2 | +240 |
| Victory bonus | — | +500 |
| Speed bonus (T10/T20) | 50% time remaining | +200 |
| Diplomacy (1 treaty) | — | +100 |
| Stealth penalty (0% final) | — | -200 |
| Detection penalty (5 detected) | 5 × -20 | -100 |
| **TOTAL** | | **+810 XP** |

### 8.2 Final Leaderboard

| Rank | Faction | Nodes (End) | Peak Nodes | Data Stolen | Score | Status |
|---|---|---|---|---|---|---|
| 🥇 1st | **Silicon Valley** (Player) | 5 | 7 | 120 units | **2,450** | ★ WINNER |
| 🥈 2nd | **Iron Grid** (AI) | 8 | 11 | 0 | **1,890** | Defender |
| 🥉 3rd | **Silk Road Coalition** | 4 | 4 | 0 | **1,200** | Allied (Trade) |
| 4th | **Sentinel Vanguard** | 3 | 3 | 0 | **980** | Neutral |
| 5th | **Shadow Cartels** | 0 | 2 | 0 | **120** | Eliminated |

### 8.3 Player Stats Update

```
Before: GHOST_4X1 | Rank: SCRIPT_KIDDIE | XP: 245/500
After:  GHOST_4X1 | Rank: HACKER         | XP: 1055/1500  ★ RANK UP!
```

---

## 9. Rules Summary (Quick Reference)

**Turn order:** Attacker (2 AP) → Defender (1-2 AP) → repeat. Turn increments after both play.

**Attacker actions:** SCAN (discover), EXPLOIT (capture, uses exploit kit), PHISHING (social eng), MALWARE (persist, uses payload), ELEVATE (admin), LATERAL (move), EXFILTRATE (steal data), CLEAR_LOGS (reduce evidence).

**Defender actions:** MONITOR (detect if alert>30), SCAN_MALWARE (find compromises), PATCH (block exploits), ISOLATE (sever node), RESTORE (clean from backup, 5 IR), FIREWALL (block connections), INCIDENT_RESPONSE (reclaim node, 10 IR).

**Alert/Stealth:** Each attacker action adds stealth cost (5–50). Detection adds +20. At alert≥50 defender gets 2 AP. At alert=100, defender wins.

**Fog of War:** Attacker sees only discovered nodes. Defender sees all.

**Diplomacy:** Chat with faction ambassadors (Gemini LLM). Propose treaties (Ceasefire/Trade/Alliance). AI evaluates based on personality + game state.

---

## 10. Technical Appendix

### API Endpoints Used in Demo

| # | Method | Endpoint | Auth | Calls |
|---|---|---|---|---|
| 1 | POST | `/api/auth/login` | None | 1 |
| 2 | POST | `/api/game/create` | Bearer | 1 |
| 3 | POST | `/api/game/action` | Bearer | 20 (2 AP × 10 turns) |
| 4 | GET | `/api/game/state/{id}` | Bearer | ~10 (polling) |
| 5 | POST | `/api/diplomacy/chat` | Bearer | 2 |
| 6 | POST | `/api/diplomacy/propose` | Bearer | 2 |

### Events Emitted (Sample)

```
game:start → { sessionId, role: "attacker", gameState }
action:execute → { actionId: 0, actionName: "SCAN_NETWORK", targetNode: 1 }
game:state:update → { gameState, sessionId, role }
action:result → { success: true, detected: false, message: "..." }
turn:switch → { from: "attacker", to: "defender" }
toast:show → { message: "NODE-02 compromised!", type: "capture" }
game:over → { winner: "attacker", reason: "Exfiltration (120/100)" }
```

### Key Files Referenced

| File | Purpose |
|---|---|
| `backend/src/backend/game_routes.py` | Game session API, LiveSession, PPO agent loading |
| `backend/src/rl/neohack_env.py` | Gymnasium environment, action execution |
| `backend/src/rl/train_agents.py` | RuleBasedAttacker/Defender, PPO training |
| `backend/src/rl/action_space.py` | Action definitions, costs, success rates |
| `backend/src/backend/services/diplomacy.py` | Gemini LLM chat + treaty evaluation |
| `backend/src/game/turn_manager.py` | Turn scheduling, AP management |
| `backend/src/game/detection_engine.py` | Stealth/alert system |
| `build/web/scripts/turn-controller.js` | Frontend turn controller |
| `build/web/scripts/game-events.js` | Event bus (22 event types) |
| `build/web/scripts/ui-manager.js` | UI initialization, action buttons, diplomacy modal |

---

*End of 10-minute demo simulation report.*
