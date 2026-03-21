# Operation Crimson Tide — Full Gameplay Scenario

> **Duration:** ~10 minutes (20 turns, ~30 seconds per turn)
> **Mode:** Asymmetric, No Equilibrium — Attacker has early-game advantage, Defender has late-game scaling
> **Map:** 16-node financial sector network (Eastern European banking cluster)

---

## 1. Factions

### 🔴 ATTACKER — "Scarlet Protocol" (APT-41 / State-sponsored)

| Stat | Value | Notes |
|------|-------|-------|
| **Starting AP per turn** | 3 | High tempo, burns out fast |
| **Max turns before extraction deadline** | 20 | Must exfiltrate before turn 20 |
| **Exploit Kits** | 5 | Consumable, cannot be replenished |
| **Stealth** | 100% | Decreases with noisy actions |
| **Starting visibility** | 2 nodes | Only sees entry points |
| **Win condition** | Exfiltrate data from `core-db` (node 12) | Must reach deep network |

**Strengths:** Fast, multi-action turns, strong early recon. Can chain lateral movements.
**Weaknesses:** Finite exploit kits, stealth degrades permanently, no way to restore stealth once below 40%.

### 🔵 DEFENDER — "Iron Bastion" (National CERT)

| Stat | Value | Notes |
|------|-------|-------|
| **Starting AP per turn** | 2 | Scales to 3 AP at alert level ≥50 |
| **IR Budget** | 8 | Incident Response credits (restore, isolate) |
| **Alert Level** | 0% | Rises on detection; at 80%+ unlocks Incident Response |
| **Starting visibility** | All 16 nodes | Full map, but no compromise indicators initially |
| **Win condition** | Survive 20 turns OR isolate the attacker completely |

**Strengths:** Full visibility, late-game AP scaling, powerful IR tools at high alert.
**Weaknesses:** Slow start (2 AP), blind to attacker until detection, patching is expensive.

### ⚖️ Why No Equilibrium

The attacker has **tempo advantage** (3 AP vs 2 AP) and **information asymmetry** (stealth means defender is blind early). But the defender has **positional advantage** (sees all nodes), **scaling advantage** (gains AP and IR tools as alert rises), and **time advantage** (attacker loses if turn 20 passes without exfiltration). This creates a **ticking-clock dynamic** where the attacker must move fast but not recklessly, while the defender benefits from patience but risks losing critical nodes.

---

## 2. Network Map (16 Nodes)

```
                    [Internet]
                        |
                   ┌────┴────┐
              (1) DMZ-FW    (2) VPN-GW
                   │              │
              ┌────┴────┐    ┌───┴───┐
         (3) WEB-01  (4) WEB-02  (5) MAIL-SRV
              │         │         │
              └────┬────┘    ┌───┘
              (6) APP-LB ────┤
              ┌────┴────┐    │
         (7) APP-01  (8) APP-02
              │         │
              └────┬────┘
              (9) INT-FW
              ┌────┴────┐
        (10) LDAP-DC  (11) FILE-SRV
              │              │
              └──────┬───────┘
              (12) CORE-DB  ←── TARGET
              │
        (13) BACKUP-SRV
              │
        (14) SIEM-MON ─── (15) LOG-AGG ─── (16) HONEYPOT
```

**Connections (bidirectional):**
1↔3, 1↔4, 2↔5, 3↔6, 4↔6, 5↔6, 6↔7, 6↔8, 7↔9, 8↔9, 9↔10, 9↔11, 10↔12, 11↔12, 12↔13, 14↔15, 15↔16, 9↔14

---

## 3. Starting Conditions

### Attacker Sees (Fog of War):
- **Discovered:** Node 1 (DMZ-FW), Node 2 (VPN-GW)
- **Everything else:** Hidden / dimmed on map

### Defender Sees:
- **All 16 nodes visible**, status: `secure`
- **No compromise indicators** — attacker is invisible until detected

### Initial Resources:

| | Attacker (Scarlet Protocol) | Defender (Iron Bastion) |
|---|---|---|
| AP / turn | 3 | 2 |
| Exploit Kits | 5 | — |
| IR Budget | — | 8 |
| Stealth | 100% | — |
| Alert Level | — | 0% |

---

## 4. Turn-by-Turn Simulation (20 Turns, ~10 Minutes)

Each turn shows: **CLI command**, **GUI equivalent**, **game state changes**, and **event bus emissions**.

---

### TURN 1 — Attacker (Scarlet Protocol) | AP: 3/3 | Stealth: 100%

**Objective:** Recon the perimeter.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `scan dmz-fw` | Click DMZ-FW → [1] SCAN | ✅ Success | Discovers nodes 3, 4 (WEB-01, WEB-02). Stealth 100→97% |
| 2 | `scan vpn-gw` | Click VPN-GW → [1] SCAN | ✅ Success | Discovers node 5 (MAIL-SRV). Stealth 97→94% |
| 3 | `exploit dmz-fw --vuln=CVE-2024-3094` | Click DMZ-FW → [2] EXPLOIT | ✅ Success (72% chance) | DMZ-FW compromised. Exploit kits 5→4. Stealth 94→88% |

**Events Emitted:**
```
→ action:result { actionName: 'SCAN_NETWORK', target: 1, success: true }
→ game:state   { discoveredNodes: [1, 2, 3, 4] }
→ action:result { actionName: 'SCAN_NETWORK', target: 2, success: true }
→ game:state   { discoveredNodes: [1, 2, 3, 4, 5] }
→ action:result { actionName: 'EXPLOIT_VULNERABILITY', target: 1, success: true }
→ game:state   { compromisedNodes: [1], stealthLevel: 88 }
→ turn:switch  { player: 'defender', turn: 1 }
```

**Intel Feed:**
```
[T1] ▶ Scanning DMZ-FW... 2 adjacent hosts discovered.
[T1] ▶ Scanning VPN-GW... 1 adjacent host discovered.
[T1] ▶ Exploiting DMZ-FW via CVE-2024-3094... ACCESS GRANTED. Firewall bypassed.
```

---

### TURN 1 — Defender (Iron Bastion) | AP: 2/2 | Alert: 0%

**Objective:** Routine monitoring. No indication of attack yet.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `monitor` | Click [1] MONITOR LOGS | ✅ No anomalies detected | Alert 0%. (Attacker stealth 88% > 50% threshold) |
| 2 | `firewall web-01` | Click WEB-01 → [6] FIREWALL | ✅ Rule applied | Firewall rule on WEB-01. Attacker exploit chance on WEB-01 reduced 15% |

**Events Emitted:**
```
→ action:result { actionName: 'MONITOR_LOGS', success: true, message: 'No anomalies' }
→ action:result { actionName: 'FIREWALL_RULE', target: 3, success: true }
→ turn:switch  { player: 'attacker', turn: 2 }
```

---

### TURN 2 — Attacker | AP: 3/3 | Stealth: 88% | Exploits: 4

**Objective:** Penetrate deeper. Avoid the firewalled WEB-01.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `move web-02` | Click WEB-02 → [6] LATERAL MOVE | ✅ Moved from DMZ-FW to WEB-02 | WEB-02 compromised. Stealth 88→83% |
| 2 | `scan web-02` | Click WEB-02 → [1] SCAN | ✅ Success | Discovers node 6 (APP-LB). Stealth 83→80% |
| 3 | `phish mail-srv` | Click MAIL-SRV → [3] PHISHING | ⚠️ Success but DETECTED | MAIL-SRV compromised. Stealth 80→65%. **Alert +15%** |

**Events Emitted:**
```
→ action:result { actionName: 'LATERAL_MOVEMENT', target: 4, success: true }
→ action:result { actionName: 'SCAN_NETWORK', target: 4, success: true }
→ game:state   { discoveredNodes: [..., 6] }
→ action:result { actionName: 'PHISHING', target: 5, success: true, detected: true }
→ alert:change { level: 15, previous: 0 }
→ game:state   { compromisedNodes: [1, 4, 5], alertLevel: 15, stealthLevel: 65 }
→ toast:show   { message: '⚠ PHISHING DETECTED — Alert level rising', type: 'warning' }
```

**Intel Feed:**
```
[T2] ▶ Lateral movement DMZ-FW → WEB-02. Pivot established.
[T2] ▶ Scanning WEB-02... 1 adjacent host: APP-LB.
[T2] ⚠ Phishing MAIL-SRV... Access granted but TRIP WIRE TRIGGERED. Stealth degraded.
```

---

### TURN 2 — Defender | AP: 2/2 | Alert: 15%

**Objective:** First sign of intrusion! Phishing detection on MAIL-SRV.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `scanmal mail-srv` | Click MAIL-SRV → [2] SCAN MALWARE | ✅ Compromise confirmed | MAIL-SRV flagged as `compromised_detected`. Alert 15→22% |
| 2 | `patch mail-srv` | Click MAIL-SRV → [3] PATCH | ✅ Patched | Vulnerability closed. Attacker cannot re-exploit MAIL-SRV |

**Events Emitted:**
```
→ action:result { actionName: 'SCAN_FOR_MALWARE', target: 5, success: true }
→ game:state   { detectedNodes: [5], alertLevel: 22 }
→ action:result { actionName: 'APPLY_PATCH', target: 5, success: true }
```

**Intel Feed:**
```
[T2] 🔍 Malware scan on MAIL-SRV: MALICIOUS PAYLOAD DETECTED. Attacker foothold confirmed.
[T2] 🔧 Patch applied to MAIL-SRV. Vulnerability CVE-2024-5218 remediated.
```

---

### TURN 3 — Attacker | AP: 3/3 | Stealth: 65% | Exploits: 4

**Objective:** Push through APP-LB to application tier before defender locks down.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `exploit app-lb` | Click APP-LB → [2] EXPLOIT | ✅ Success (68%) | APP-LB compromised. Exploits 4→3. Stealth 65→58% |
| 2 | `scan app-lb` | Click APP-LB → [1] SCAN | ✅ Success | Discovers nodes 7, 8 (APP-01, APP-02). Stealth 58→55% |
| 3 | `clearlogs` | Click [8] CLEAR LOGS | ✅ Success | Evidence removed from APP-LB logs. Stealth +5 → 60% |

**Events Emitted:**
```
→ action:result { actionName: 'EXPLOIT_VULNERABILITY', target: 6, success: true }
→ game:state   { compromisedNodes: [1, 4, 5, 6], stealthLevel: 58 }
→ action:result { actionName: 'SCAN_NETWORK', target: 6, success: true }
→ game:state   { discoveredNodes: [..., 7, 8] }
→ action:result { actionName: 'CLEAR_LOGS', success: true }
→ game:state   { stealthLevel: 60 }
```

---

### TURN 3 — Defender | AP: 2/2 | Alert: 22%

**Objective:** Expand monitoring. Try to locate the attacker's path.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `monitor` | Click [1] MONITOR | ⚠️ Anomaly detected on DMZ-FW | DMZ-FW flagged suspicious. Alert 22→30% |
| 2 | `scanmal dmz-fw` | Click DMZ-FW → [2] SCAN MALWARE | ✅ Compromise confirmed | DMZ-FW marked `compromised_detected` |

**Intel Feed:**
```
[T3] 🔍 Log monitoring: ANOMALOUS TRAFFIC on DMZ-FW. Unusual outbound connections.
[T3] 🔍 Malware scan DMZ-FW: ROOTKIT DETECTED. Full compromise confirmed.
```

---

### TURN 4 — Attacker | AP: 3/3 | Stealth: 60% | Exploits: 3

**Objective:** Race to the internal firewall. Attacker knows defender is on the trail.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `move app-01` | Click APP-01 → [6] LATERAL MOVE | ✅ Success | APP-01 compromised. Stealth 60→54% |
| 2 | `move 9` | Click INT-FW → [6] LATERAL MOVE | ✅ Success | INT-FW compromised. Stealth 54→47% |
| 3 | `scan int-fw` | Click INT-FW → [1] SCAN | ✅ Success | Discovers 10, 11, 14 (LDAP-DC, FILE-SRV, SIEM-MON). Stealth 47→44% |

**Events Emitted:**
```
→ game:state { compromisedNodes: [1, 4, 5, 6, 7, 9], discoveredNodes: [..., 9, 10, 11, 14], stealthLevel: 44 }
→ toast:show { message: '⚠ STEALTH CRITICAL — Below 50%', type: 'danger' }
```

**Intel Feed:**
```
[T4] ▶ Lateral: APP-LB → APP-01 → INT-FW. Deep network reached.
[T4] ▶ Scanning INT-FW: 3 hosts discovered. TARGET ZONE VISIBLE.
[T4] ⚠ STEALTH BELOW 50% — Detection probability increasing rapidly.
```

---

### TURN 4 — Defender | AP: 2/2 | Alert: 30%

**Objective:** Isolate confirmed compromised node. Harden critical path.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `isolate dmz-fw` | Click DMZ-FW → [4] ISOLATE | ✅ Isolated | DMZ-FW quarantined. IR Budget 8→7. Attacker loses that foothold |
| 2 | `firewall app-lb` | Click APP-LB → [6] FIREWALL | ✅ Rule applied | Firewall on APP-LB. Blocks lateral movement back through it |

**Intel Feed:**
```
[T4] 🔒 DMZ-FW ISOLATED from network. Attacker entry point severed.
[T4] 🛡️ Firewall rule applied on APP-LB. Lateral movement blocked.
```

---

### TURN 5 — Attacker | AP: 3/3 | Stealth: 44% | Exploits: 3

**Objective:** Critical decision — go for LDAP-DC to reach CORE-DB, or hit SIEM to blind the defender.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `exploit ldap-dc --vuln=CVE-2024-8901` | [2] EXPLOIT | ✅ Success (65%) | LDAP-DC compromised. Exploits 3→2. Stealth 44→36% |
| 2 | `elevate ldap-dc` | Click LDAP-DC → [5] ELEVATE | ✅ Admin access | Full domain admin. Stealth 36→28%. **Alert +20%** |
| 3 | `scan ldap-dc` | Click LDAP-DC → [1] SCAN | ✅ Success | Discovers node 12 (CORE-DB). **TARGET VISIBLE.** |

**Events Emitted:**
```
→ action:result { actionName: 'ELEVATE_PRIVILEGES', target: 10, success: true, detected: true }
→ alert:change { level: 50, previous: 30 }
→ toast:show { message: '🚨 ALERT 50% — Defender AP increased to 3!', type: 'danger' }
→ game:state { discoveredNodes: [..., 12], alertLevel: 50, stealthLevel: 28 }
```

**Intel Feed:**
```
[T5] ▶ Exploiting LDAP-DC... DOMAIN ADMIN ACHIEVED.
[T5] ⚠ PRIVILEGE ESCALATION DETECTED — Massive alert spike.
[T5] ▶ Target CORE-DB located. One hop away.
```

---

### TURN 5 — Defender | AP: 3/3 (SCALED UP!) | Alert: 50%

**Objective:** Alert spike! Defender now has 3 AP. Full incident response mode.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `scanmal app-01` | Click APP-01 → [2] SCAN MALWARE | ✅ Compromise found | APP-01 marked `compromised_detected`. Alert 50→55% |
| 2 | `isolate app-01` | Click APP-01 → [4] ISOLATE | ✅ Isolated | Cuts off one lateral path. IR 7→6 |
| 3 | `firewall core-db` | Click CORE-DB → [6] FIREWALL | ✅ Hardened | CORE-DB exploit chance reduced 20%. Critical defense |

**Intel Feed:**
```
[T5] 🔍 APP-01: COMPROMISED. Attacker lateral movement confirmed through app tier.
[T5] 🔒 APP-01 ISOLATED. Lateral path severed.
[T5] 🛡️ CORE-DB hardened with emergency firewall rules.
```

---

### TURN 6 — Attacker | AP: 3/3 | Stealth: 28% | Exploits: 2

**Objective:** Final push. Must reach CORE-DB this turn or next.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `malware ldap-dc` | Click LDAP-DC → [4] MALWARE | ✅ Persistence installed | Backdoor on LDAP-DC. Even if patched, can re-enter. Stealth 28→20% |
| 2 | `move core-db` | Click CORE-DB → [6] LATERAL MOVE | ⚠️ BLOCKED by firewall | Firewall rule on CORE-DB blocks lateral from LDAP-DC directly |
| 3 | `move file-srv` | Click FILE-SRV → [6] LATERAL MOVE | ✅ Success | Alternate path. FILE-SRV compromised. Stealth 20→14% |

**Events Emitted:**
```
→ action:result { actionName: 'LATERAL_MOVEMENT', target: 12, success: false, message: 'Blocked by firewall' }
→ toast:show { message: 'BLOCKED — Firewall rule active on CORE-DB', type: 'error' }
→ action:result { actionName: 'LATERAL_MOVEMENT', target: 11, success: true }
→ alert:change { level: 62, previous: 55 }
```

**Intel Feed:**
```
[T6] ▶ Malware implant on LDAP-DC. Persistence achieved.
[T6] ✖ LATERAL MOVEMENT TO CORE-DB BLOCKED. Firewall active.
[T6] ▶ Rerouting via FILE-SRV... Access granted. Adjacent to CORE-DB.
```

---

### TURN 6 — Defender | AP: 3/3 | Alert: 62%

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `scanmal ldap-dc` | [2] SCAN MALWARE | ✅ Malware + rootkit found | Alert 62→68% |
| 2 | `scanmal file-srv` | [2] SCAN MALWARE | ✅ New compromise detected | Alert 68→72% |
| 3 | `patch ldap-dc` | [3] PATCH | ✅ Vulnerability patched | But malware persistence remains (attacker installed backdoor) |

---

### TURN 7 — Attacker | AP: 3/3 | Stealth: 14% | Exploits: 2

**Objective:** FINAL ASSAULT on CORE-DB.

| # | CLI Command | GUI Action | Result | State Change |
|---|------------|------------|--------|--------------|
| 1 | `exploit core-db --vuln=CVE-2024-0001` | [2] EXPLOIT | ⚠️ **FAILED** (42% chance, reduced by firewall) | Exploit kit wasted. Exploits 2→1. Stealth 14→8%. Alert +10% |
| 2 | `exploit core-db` | [2] EXPLOIT | ✅ **SUCCESS** (42% — lucky roll) | CORE-DB COMPROMISED. Exploits 1→0. Stealth 8→2% |
| 3 | `exfiltrate core-db` | [7] EXFILTRATE | ✅ **DATA EXFILTRATED** | 🔴 **ATTACKER WIN CONDITION MET** |

**Events Emitted:**
```
→ action:result { actionName: 'EXPLOIT_VULNERABILITY', target: 12, success: false }
→ toast:show { message: 'Exploit FAILED on CORE-DB — firewall deflected', type: 'error' }
→ action:result { actionName: 'EXPLOIT_VULNERABILITY', target: 12, success: true }
→ game:state { compromisedNodes: [..., 12] }
→ action:result { actionName: 'EXFILTRATE_DATA', target: 12, success: true }
→ game:over { winner: 'attacker', reason: 'Data exfiltration complete' }
```

**Intel Feed:**
```
[T7] ✖ Exploit attempt on CORE-DB FAILED. Firewall held.
[T7] ▶ Second exploit attempt... CORE-DB BREACHED.
[T7] 🔴 EXFILTRATION IN PROGRESS... 4.2 TB transferred to C2 server.
[T7] 🔴 ████ MISSION COMPLETE — SCARLET PROTOCOL WINS ████
```

---

## 5. Game Over — Debrief Screen

### Incident Report

```
╔══════════════════════════════════════════════════════╗
║             OPERATION CRIMSON TIDE                    ║
║             ─── INCIDENT REPORT ───                   ║
╠══════════════════════════════════════════════════════╣
║                                                       ║
║  WINNER:     🔴 SCARLET PROTOCOL (Attacker)           ║
║  DURATION:   7 turns (≈ 3.5 minutes active play)      ║
║  DIFFICULTY:  ADVANCED                                ║
║                                                       ║
║  ── ATTACKER STATS ──                                 ║
║  Nodes Compromised:   8 / 16                          ║
║  Exploit Kits Used:   5 / 5                           ║
║  Final Stealth:       2%                              ║
║  Actions Taken:       21                              ║
║  Detection Events:    3                               ║
║  Kill Chain:  DMZ-FW → WEB-02 → APP-LB →             ║
║               APP-01 → INT-FW → LDAP-DC →            ║
║               FILE-SRV → CORE-DB                     ║
║                                                       ║
║  ── DEFENDER STATS ──                                 ║
║  Final Alert Level:    82%                            ║
║  Nodes Isolated:       2 (DMZ-FW, APP-01)            ║
║  Patches Applied:      2 (MAIL-SRV, LDAP-DC)         ║
║  Firewall Rules:       3 (WEB-01, APP-LB, CORE-DB)   ║
║  IR Budget Remaining:  6 / 8                          ║
║  Actions Taken:        14                             ║
║                                                       ║
║  ── XP BREAKDOWN ──                                   ║
║  Base XP:              100                            ║
║  Nodes Compromised:    8 × 12 = 96                    ║
║  Speed Bonus:          +50 (completed before T10)     ║
║  Stealth Penalty:      -30 (below 10%)                ║
║  ─────────────────────────                            ║
║  TOTAL XP:             216                            ║
║                                                       ║
╚══════════════════════════════════════════════════════╝
```

---

## 6. Complete Action Log (Machine-Readable)

```jsonc
[
  // TURN 1 — Attacker
  { "turn": 1, "player": "attacker", "seq": 1, "cli": "scan dmz-fw",     "action": "SCAN_NETWORK",         "target": 1,  "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 97 },
  { "turn": 1, "player": "attacker", "seq": 2, "cli": "scan vpn-gw",     "action": "SCAN_NETWORK",         "target": 2,  "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 94 },
  { "turn": 1, "player": "attacker", "seq": 3, "cli": "exploit dmz-fw",  "action": "EXPLOIT_VULNERABILITY","target": 1,  "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 88, "exploit_kits_after": 4 },

  // TURN 1 — Defender
  { "turn": 1, "player": "defender", "seq": 1, "cli": "monitor",          "action": "MONITOR_LOGS",         "target": null, "success": true, "detected": false, "ap_cost": 1, "alert_after": 0 },
  { "turn": 1, "player": "defender", "seq": 2, "cli": "firewall web-01",  "action": "FIREWALL_RULE",        "target": 3,  "success": true,  "detected": false, "ap_cost": 1, "alert_after": 0 },

  // TURN 2 — Attacker
  { "turn": 2, "player": "attacker", "seq": 1, "cli": "move web-02",     "action": "LATERAL_MOVEMENT",     "target": 4,  "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 83 },
  { "turn": 2, "player": "attacker", "seq": 2, "cli": "scan web-02",     "action": "SCAN_NETWORK",         "target": 4,  "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 80 },
  { "turn": 2, "player": "attacker", "seq": 3, "cli": "phish mail-srv",  "action": "PHISHING",             "target": 5,  "success": true,  "detected": true,  "ap_cost": 1, "stealth_after": 65 },

  // TURN 2 — Defender
  { "turn": 2, "player": "defender", "seq": 1, "cli": "scanmal mail-srv", "action": "SCAN_FOR_MALWARE",     "target": 5,  "success": true,  "detected": false, "ap_cost": 1, "alert_after": 22 },
  { "turn": 2, "player": "defender", "seq": 2, "cli": "patch mail-srv",   "action": "APPLY_PATCH",          "target": 5,  "success": true,  "detected": false, "ap_cost": 1, "alert_after": 22 },

  // TURN 3 — Attacker
  { "turn": 3, "player": "attacker", "seq": 1, "cli": "exploit app-lb",  "action": "EXPLOIT_VULNERABILITY","target": 6,  "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 58, "exploit_kits_after": 3 },
  { "turn": 3, "player": "attacker", "seq": 2, "cli": "scan app-lb",     "action": "SCAN_NETWORK",         "target": 6,  "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 55 },
  { "turn": 3, "player": "attacker", "seq": 3, "cli": "clearlogs",       "action": "CLEAR_LOGS",           "target": null,"success": true,  "detected": false, "ap_cost": 1, "stealth_after": 60 },

  // TURN 3 — Defender
  { "turn": 3, "player": "defender", "seq": 1, "cli": "monitor",          "action": "MONITOR_LOGS",         "target": null, "success": true, "detected": false, "ap_cost": 1, "alert_after": 30 },
  { "turn": 3, "player": "defender", "seq": 2, "cli": "scanmal dmz-fw",   "action": "SCAN_FOR_MALWARE",     "target": 1,  "success": true,  "detected": false, "ap_cost": 1, "alert_after": 30 },

  // TURN 4 — Attacker
  { "turn": 4, "player": "attacker", "seq": 1, "cli": "move app-01",     "action": "LATERAL_MOVEMENT",     "target": 7,  "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 54 },
  { "turn": 4, "player": "attacker", "seq": 2, "cli": "move 9",          "action": "LATERAL_MOVEMENT",     "target": 9,  "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 47 },
  { "turn": 4, "player": "attacker", "seq": 3, "cli": "scan int-fw",     "action": "SCAN_NETWORK",         "target": 9,  "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 44 },

  // TURN 4 — Defender
  { "turn": 4, "player": "defender", "seq": 1, "cli": "isolate dmz-fw",   "action": "ISOLATE_HOST",         "target": 1,  "success": true,  "detected": false, "ap_cost": 1, "ir_after": 7 },
  { "turn": 4, "player": "defender", "seq": 2, "cli": "firewall app-lb",  "action": "FIREWALL_RULE",        "target": 6,  "success": true,  "detected": false, "ap_cost": 1, "alert_after": 30 },

  // TURN 5 — Attacker
  { "turn": 5, "player": "attacker", "seq": 1, "cli": "exploit ldap-dc",  "action": "EXPLOIT_VULNERABILITY","target": 10, "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 36, "exploit_kits_after": 2 },
  { "turn": 5, "player": "attacker", "seq": 2, "cli": "elevate ldap-dc",  "action": "ELEVATE_PRIVILEGES",   "target": 10, "success": true,  "detected": true,  "ap_cost": 1, "stealth_after": 28 },
  { "turn": 5, "player": "attacker", "seq": 3, "cli": "scan ldap-dc",     "action": "SCAN_NETWORK",         "target": 10, "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 28 },

  // TURN 5 — Defender (3 AP now!)
  { "turn": 5, "player": "defender", "seq": 1, "cli": "scanmal app-01",   "action": "SCAN_FOR_MALWARE",     "target": 7,  "success": true,  "detected": false, "ap_cost": 1, "alert_after": 55 },
  { "turn": 5, "player": "defender", "seq": 2, "cli": "isolate app-01",   "action": "ISOLATE_HOST",         "target": 7,  "success": true,  "detected": false, "ap_cost": 1, "ir_after": 6 },
  { "turn": 5, "player": "defender", "seq": 3, "cli": "firewall core-db", "action": "FIREWALL_RULE",        "target": 12, "success": true,  "detected": false, "ap_cost": 1, "alert_after": 55 },

  // TURN 6 — Attacker
  { "turn": 6, "player": "attacker", "seq": 1, "cli": "malware ldap-dc",  "action": "INSTALL_MALWARE",      "target": 10, "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 20 },
  { "turn": 6, "player": "attacker", "seq": 2, "cli": "move core-db",     "action": "LATERAL_MOVEMENT",     "target": 12, "success": false, "detected": false, "ap_cost": 1, "stealth_after": 20 },
  { "turn": 6, "player": "attacker", "seq": 3, "cli": "move file-srv",    "action": "LATERAL_MOVEMENT",     "target": 11, "success": true,  "detected": false, "ap_cost": 1, "stealth_after": 14 },

  // TURN 6 — Defender
  { "turn": 6, "player": "defender", "seq": 1, "cli": "scanmal ldap-dc",  "action": "SCAN_FOR_MALWARE",     "target": 10, "success": true,  "detected": false, "ap_cost": 1, "alert_after": 68 },
  { "turn": 6, "player": "defender", "seq": 2, "cli": "scanmal file-srv", "action": "SCAN_FOR_MALWARE",     "target": 11, "success": true,  "detected": false, "ap_cost": 1, "alert_after": 72 },
  { "turn": 6, "player": "defender", "seq": 3, "cli": "patch ldap-dc",    "action": "APPLY_PATCH",          "target": 10, "success": true,  "detected": false, "ap_cost": 1, "alert_after": 72 },

  // TURN 7 — Attacker (FINAL)
  { "turn": 7, "player": "attacker", "seq": 1, "cli": "exploit core-db",  "action": "EXPLOIT_VULNERABILITY","target": 12, "success": false, "detected": true,  "ap_cost": 1, "stealth_after": 8, "exploit_kits_after": 1 },
  { "turn": 7, "player": "attacker", "seq": 2, "cli": "exploit core-db",  "action": "EXPLOIT_VULNERABILITY","target": 12, "success": true,  "detected": true,  "ap_cost": 1, "stealth_after": 2, "exploit_kits_after": 0 },
  { "turn": 7, "player": "attacker", "seq": 3, "cli": "exfiltrate core-db","action": "EXFILTRATE_DATA",     "target": 12, "success": true,  "detected": true,  "ap_cost": 1, "stealth_after": 0 }
  // → GAME OVER: Attacker wins
]
```

---

## 7. Alternate Ending — Defender Wins

If the Turn 7 exploit on CORE-DB had **failed twice** (both at 42%), the attacker would have 0 exploit kits remaining and no way to breach CORE-DB. The game would continue:

| Turn | Attacker (0 exploits) | Defender (3 AP, 82% alert) |
|------|----------------------|---------------------------|
| T8 | Can only scan/move — no offensive capability | `respond file-srv` → ejects attacker. `isolate int-fw` → cuts deep network |
| T9 | Trapped. Can only `clearlogs` to delay | `restore ldap-dc` → removes malware. All paths to CORE-DB blocked |
| T10+ | No viable path. Forced to `endturn` repeatedly | Mops up remaining compromised nodes. Runs out the clock |
| T20 | **DEADLINE PASSED** | 🔵 **IRON BASTION WINS — Attacker failed to exfiltrate** |

This demonstrates the **asymmetric tension**: the attacker's finite exploit kits create a resource cliff, while the defender's scaling AP and IR tools create an exponential late-game advantage.

---

## 8. Key Strategic Takeaways

| Insight | Attacker Perspective | Defender Perspective |
|---------|---------------------|---------------------|
| **Tempo** | 3 AP is powerful but burns resources fast | 2 AP feels slow; prioritize monitoring early |
| **Stealth** | Every action costs stealth. `clearlogs` is vital | Monitor every turn — each detection compounds |
| **Firewall rules** | One well-placed firewall can block the kill chain | Firewall CORE-DB and chokepoints (INT-FW, APP-LB) |
| **Exploit economy** | 5 kits for an 8-hop kill chain is razor-thin | Force the attacker to waste exploits on firewalled nodes |
| **Isolation** | Devastating if it cuts your only path | Isolate confirmed nodes, but don't waste IR on suspicion |
| **Persistence** | `malware` is insurance against patching | `restore` is the only counter to malware — costs IR |
| **The clock** | You lose at T20. Speed > caution | You win at T20. Delay > aggression |
