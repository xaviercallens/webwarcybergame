"""
Neo-Hack: Gridlock — IMPROVED Remote Gameplay Simulation v2
=============================================================
Improvements over v1:
  - Staggered registration (13s delay between each player) to avoid 5/min rate limit
  - Asymmetric starting power: factions have different CU budgets & aggression
  - Pre-existing TRADE alliance established between Factions 2 & 3
  - Higher, varied CU attacks (up to 250) to breach node defenses (100+)
  - Coordinated "wolf pack" attacks where multiple players target the same node
  - Smarter heuristics: focus fire on weakest nodes, defend valuable territory
  - Multiple actions per PLANNING phase (up to 5 per player)
"""

import asyncio
import random
import time
import uuid
import json
import os
from datetime import datetime
from pathlib import Path

import requests

# ─── Configuration ──────────────────────────────────────────────────────────
BASE_URL = "https://neohack-gridlock-v2-212120873430.europe-west1.run.app"
API = f"{BASE_URL}/api"
SIMULATION_DURATION_SECONDS = 600  # 10 minutes
NUM_FACTIONS = 5
PLAYERS_PER_FACTION = 2
POLL_INTERVAL = 3  # seconds between action cycles
REG_DELAY = 7      # seconds between each registration (10/min rate limit)

# Faction profiles with asymmetric power levels
# cu_budget: how much CU each action can spend (higher = more powerful)
# aggression: probability of BREACH vs DEFEND
# focus_fire: probability of targeting the weakest enemy node vs random
FACTION_PROFILES = {
    1: {"name": "SiliconValley", "aggression": 0.6,  "cu_min": 120, "cu_max": 350, "focus_fire": 0.7, "color": "🔵"},
    2: {"name": "IronGrid",      "aggression": 0.85, "cu_min": 150, "cu_max": 500, "focus_fire": 0.8, "color": "🔴"},
    3: {"name": "SilkRoad",      "aggression": 0.5,  "cu_min": 100, "cu_max": 300, "focus_fire": 0.6, "color": "🟡"},
    4: {"name": "EuroNexus",     "aggression": 0.25, "cu_min": 80,  "cu_max": 250, "focus_fire": 0.4, "color": "🟢"},
    5: {"name": "PacificVgd",    "aggression": 0.75, "cu_min": 130, "cu_max": 400, "focus_fire": 0.9, "color": "🟣"},
}

# Pre-planned alliances to establish at the start
ALLIANCES = [
    {"faction_a": 2, "faction_b": 3, "type": "TRADE",     "reason": "Iron Grid & Silk Road trade pact"},
    {"faction_a": 1, "faction_b": 4, "type": "CEASEFIRE",  "reason": "Silicon Valley & Euro Nexus non-aggression"},
]

# Coordinated attack targets: factions that will focus on the same enemy
WOLF_PACK_TARGETS = {
    2: 4,  # Iron Grid focuses on Euro Nexus (defensive faction)
    5: 4,  # Pacific Vanguard also targets Euro Nexus
    3: 1,  # Silk Road targets Silicon Valley
}

# ─── Logging ────────────────────────────────────────────────────────────────
LOG_FILE = Path("/tmp") / f"gameplay_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
combat_log = []

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    combat_log.append(line)


# ─── Player Agent ───────────────────────────────────────────────────────────
class PlayerAgent:
    def __init__(self, username: str, password: str, faction_id: int, profile: dict):
        self.username = username
        self.password = password
        self.faction_id = faction_id
        self.profile = profile
        self.token = None
        self.headers = {}
        self.stats = {"breaches": 0, "defenses": 0, "chats": 0, "captures_attempted": 0}

    def register_and_login(self) -> bool:
        payload = {"username": self.username, "password": self.password}
        try:
            r = requests.post(f"{API}/auth/register", json=payload, timeout=10)
            if r.status_code == 200:
                self.token = r.json()["access_token"]
                log(f"  ✅ {self.username} registered (Faction {self.faction_id} {self.profile['color']})")
            elif r.status_code == 400:
                r = requests.post(f"{API}/auth/login", json=payload, timeout=10)
                if r.status_code == 200:
                    self.token = r.json()["access_token"]
                    log(f"  🔑 {self.username} logged in (Faction {self.faction_id})")
                else:
                    log(f"  ❌ {self.username} login FAILED: {r.status_code}")
                    return False
            else:
                log(f"  ❌ {self.username} register FAILED: {r.status_code} {r.text[:80]}")
                return False
        except Exception as e:
            log(f"  ❌ {self.username} connection error: {e}")
            return False

        self.headers = {"Authorization": f"Bearer {self.token}"}
        return True

    def get_epoch(self) -> dict | None:
        try:
            r = requests.get(f"{API}/epoch/current", headers=self.headers, timeout=5)
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    def get_world_state(self) -> list:
        try:
            r = requests.get(f"{API}/world/state", headers=self.headers, timeout=5)
            return r.json().get("nodes", []) if r.status_code == 200 else []
        except Exception:
            return []

    def submit_action(self, action_type: str, target_node_id: int, cu: int) -> bool:
        try:
            r = requests.post(f"{API}/epoch/action", json={
                "action_type": action_type, "target_node_id": target_node_id, "cu_committed": cu
            }, headers=self.headers, timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def chat_with_faction(self, target_faction_id: int, message: str) -> str | None:
        try:
            r = requests.post(f"{API}/diplomacy/chat", json={
                "faction_id": target_faction_id, "message": message
            }, headers=self.headers, timeout=15)
            return r.json().get("reply", "") if r.status_code == 200 else None
        except Exception:
            return None

    def propose_treaty(self, target_faction_id: int, treaty_type: str, text: str) -> dict | None:
        try:
            r = requests.post(f"{API}/diplomacy/propose", json={
                "target_faction_id": target_faction_id, "type": treaty_type, "proposal_text": text
            }, headers=self.headers, timeout=10)
            return r.json() if r.status_code in (200, 400) else None
        except Exception:
            return None

    def choose_actions(self, nodes: list) -> list:
        """
        Advanced AI: returns a LIST of (action_type, target_node_id, cu) tuples.
        Can submit multiple actions per planning phase.
        """
        own_nodes = [n for n in nodes if n.get("faction_id") == self.faction_id]
        enemy_nodes = [n for n in nodes if n.get("faction_id") != self.faction_id and n.get("faction_id") is not None]
        
        actions = []
        num_actions = random.randint(2, 5)  # Submit 2-5 actions per phase
        
        for _ in range(num_actions):
            if random.random() < self.profile["aggression"] and enemy_nodes:
                # BREACH: pick target based on focus_fire strategy
                if random.random() < self.profile["focus_fire"]:
                    # Focus fire: pick the weakest defended enemy node
                    enemy_nodes.sort(key=lambda n: n.get("defense_level", 100))
                    target = enemy_nodes[0]
                else:
                    # Wolf pack: if faction has a wolf pack target, prefer those nodes
                    wolf_target_faction = WOLF_PACK_TARGETS.get(self.faction_id)
                    if wolf_target_faction:
                        wolf_nodes = [n for n in enemy_nodes if n.get("faction_id") == wolf_target_faction]
                        if wolf_nodes:
                            wolf_nodes.sort(key=lambda n: n.get("defense_level", 100))
                            target = wolf_nodes[0]
                        else:
                            target = random.choice(enemy_nodes)
                    else:
                        target = random.choice(enemy_nodes)
                
                cu = random.randint(self.profile["cu_min"], self.profile["cu_max"])
                actions.append(("BREACH", target["id"], cu))
            elif own_nodes:
                # DEFEND: boost a vulnerable owned node
                own_nodes.sort(key=lambda n: n.get("defense_level", 100))
                target = own_nodes[0] if random.random() < 0.7 else random.choice(own_nodes)
                cu = random.randint(self.profile["cu_min"] // 2, self.profile["cu_max"] // 2)
                actions.append(("DEFEND", target["id"], cu))
            elif enemy_nodes:
                target = random.choice(enemy_nodes)
                actions.append(("BREACH", target["id"], random.randint(80, 150)))
        
        return actions


# ─── Main Simulation ───────────────────────────────────────────────────────
async def run_player_loop(agent: PlayerAgent, start_time: float):
    last_chat_time = 0
    last_epoch_num = -1
    actions_this_epoch = 0

    while (time.time() - start_time) < SIMULATION_DURATION_SECONDS:
        epoch = agent.get_epoch()
        if not epoch:
            await asyncio.sleep(POLL_INTERVAL)
            continue

        epoch_num = epoch.get("number", 0)
        phase = epoch.get("phase", "")

        if epoch_num != last_epoch_num:
            actions_this_epoch = 0
            last_epoch_num = epoch_num

        if phase == "PLANNING" and actions_this_epoch < 5:
            nodes = agent.get_world_state()
            if nodes:
                planned = agent.choose_actions(nodes)
                for action_type, target_id, cu in planned:
                    if actions_this_epoch >= 5:
                        break
                    ok = agent.submit_action(action_type, target_id, cu)
                    if ok:
                        actions_this_epoch += 1
                        if action_type == "BREACH":
                            agent.stats["breaches"] += 1
                            target_node = next((n for n in nodes if n["id"] == target_id), {})
                            owner_id = target_node.get("faction_id", "?")
                            defense = target_node.get("defense_level", "?")
                            log(f"  ⚔️  [{agent.username}] BREACH → Node {target_id} (owned by F{owner_id}, def={defense}) with {cu} CU")
                        else:
                            agent.stats["defenses"] += 1
                            log(f"  🛡️  [{agent.username}] DEFEND → Node {target_id} ({cu} CU)")
                    # Tiny delay between action submissions
                    await asyncio.sleep(0.3)

        # Diplomacy chat every ~120 seconds
        now = time.time()
        if now - last_chat_time > 120:
            rival_factions = [f for f in range(1, NUM_FACTIONS + 1) if f != agent.faction_id]
            target_f = random.choice(rival_factions)
            messages = [
                "We should form an alliance against our common enemies. What are your terms?",
                "Your territory is surrounded. Consider a trade deal before we breach your defenses.",
                "I propose a ceasefire — we both have bigger threats to deal with.",
                "Your weakest nodes are exposed. Surrender them or face coordinated assault.",
                "Our faction is willing to negotiate. What do you want in exchange for peace?",
                "We've been watching your expansion. Impressive. But can you hold what you've taken?",
                "The grid is shifting. Choose your allies wisely — or stand alone.",
            ]
            reply = agent.chat_with_faction(target_f, random.choice(messages))
            if reply:
                agent.stats["chats"] += 1
                log(f"  💬 [{agent.username}] → F{target_f}: {reply[:90]}...")
            last_chat_time = now

        await asyncio.sleep(POLL_INTERVAL + random.uniform(-0.5, 1.5))


async def world_state_reporter(start_time: float):
    while (time.time() - start_time) < SIMULATION_DURATION_SECONDS:
        try:
            r = requests.get(f"{API}/world/state", timeout=5)
            if r.status_code == 200:
                nodes = r.json().get("nodes", [])
                faction_counts = {}
                faction_defense = {}
                for n in nodes:
                    fid = n.get("faction_id", 0)
                    faction_counts[fid] = faction_counts.get(fid, 0) + 1
                    faction_defense[fid] = faction_defense.get(fid, 0) + n.get("defense_level", 0)

                total = len(nodes)
                elapsed = int(time.time() - start_time)
                m, s = elapsed // 60, elapsed % 60

                lines = [f"📊 WORLD STATE [{m:02d}:{s:02d}] — {total} nodes"]
                for fid in sorted(faction_counts.keys()):
                    cnt = faction_counts[fid]
                    pct = (cnt / max(1, total)) * 100
                    avg_def = faction_defense[fid] // max(1, cnt)
                    bar = "█" * int(pct / 2.5) + "░" * (40 - int(pct / 2.5))
                    p = FACTION_PROFILES.get(fid, {})
                    fname = p.get("name", f"Unk-{fid}")
                    color = p.get("color", "⚪")
                    lines.append(f"   {color} F{fid} {fname:14s}: {cnt:3d} ({pct:5.1f}%) {bar} avg_def={avg_def}")
                log("\n".join(lines))
        except Exception:
            pass
        await asyncio.sleep(20)


async def news_reporter(start_time: float):
    last_news_id = 0
    while (time.time() - start_time) < SIMULATION_DURATION_SECONDS:
        try:
            r = requests.get(f"{API}/news/latest?limit=1", timeout=5)
            if r.status_code == 200:
                items = r.json()
                if items and len(items) > 0:
                    latest = items[0]
                    if latest.get("id", 0) != last_news_id:
                        last_news_id = latest["id"]
                        log(f"  📰 NEWS: {latest.get('content', '')[:140]}")
        except Exception:
            pass
        await asyncio.sleep(15)


async def main():
    log("=" * 72)
    log("🎮 NEO-HACK: GRIDLOCK — IMPROVED GAMEPLAY SIMULATION v2")
    log(f"   Target: {BASE_URL}")
    log(f"   Duration: {SIMULATION_DURATION_SECONDS // 60} minutes")
    log(f"   Factions: {NUM_FACTIONS} | Players per faction: {PLAYERS_PER_FACTION}")
    log(f"   Registration delay: {REG_DELAY}s per player (rate limit bypass)")
    log("=" * 72)

    # ─── Phase 1: Register all players with staggered delays ────────────
    log("\n🔐 Phase 1: Registering players (staggered to avoid rate limits)...")
    agents = []
    run_id = str(uuid.uuid4())[:6]

    for faction_id in range(1, NUM_FACTIONS + 1):
        profile = FACTION_PROFILES[faction_id]
        for p_idx in range(PLAYERS_PER_FACTION):
            username = f"sim2_{profile['name']}_{p_idx}_{run_id}"
            agent = PlayerAgent(username, f"SecurePass_{run_id}!", faction_id, profile)
            if agent.register_and_login():
                agents.append(agent)
            # Stagger registrations: wait 13s between each to stay under 5/min
            if len(agents) < NUM_FACTIONS * PLAYERS_PER_FACTION:
                log(f"     ⏳ Waiting {REG_DELAY}s before next registration...")
                await asyncio.sleep(REG_DELAY)

    log(f"\n✅ {len(agents)} players ready across {NUM_FACTIONS} factions.\n")

    # ─── Phase 1b: Establish pre-existing alliances ─────────────────────
    log("🤝 Phase 1b: Establishing pre-existing alliances...")
    for alliance in ALLIANCES:
        # Find an agent from faction_a
        agent_a = next((a for a in agents if a.faction_id == alliance["faction_a"]), None)
        if agent_a:
            result = agent_a.propose_treaty(
                alliance["faction_b"],
                alliance["type"],
                f"Formal {alliance['type']} agreement between our factions."
            )
            if result:
                log(f"  🤝 {alliance['reason']}: {result.get('status', 'unknown')} — {result.get('message', '')[:60]}")
            else:
                log(f"  ⚠️ Treaty proposal failed for {alliance['reason']}")
            await asyncio.sleep(2)

    # ─── Phase 2: Fetch initial state ───────────────────────────────────
    log("\n🌍 Phase 2: Initial world state...")
    r = requests.get(f"{API}/world/state", timeout=5)
    if r.status_code == 200:
        nodes = r.json().get("nodes", [])
        faction_counts = {}
        for n in nodes:
            fid = n.get("faction_id", 0)
            faction_counts[fid] = faction_counts.get(fid, 0) + 1
        log(f"   Total nodes: {len(nodes)}")
        for fid in sorted(faction_counts.keys()):
            p = FACTION_PROFILES.get(fid, {})
            log(f"   {p.get('color','⚪')} F{fid} ({p.get('name','?'):14s}): {faction_counts[fid]:3d} nodes | aggression={p.get('aggression',0):.0%} | CU range={p.get('cu_min',0)}-{p.get('cu_max',0)}")

    # Fetch active accords
    try:
        r = requests.get(f"{API}/diplomacy/accords", timeout=5)
        if r.status_code == 200:
            accords = r.json()
            if accords:
                log(f"\n   📜 Active Accords: {len(accords)}")
                for a in accords:
                    log(f"      {a.get('type','?')} between F{a.get('faction_a_id','?')} ↔ F{a.get('faction_b_id','?')} ({a.get('status','?')})")
    except Exception:
        pass

    # ─── Phase 3: Combat simulation ─────────────────────────────────────
    log(f"\n⚔️  Phase 3: Starting {SIMULATION_DURATION_SECONDS // 60}-minute combat simulation...")
    log("   Strategies:")
    for fid, p in FACTION_PROFILES.items():
        wt = WOLF_PACK_TARGETS.get(fid)
        wolf = f" → Wolf pack target: F{wt}" if wt else ""
        log(f"   {p['color']} F{fid} {p['name']:14s}: {p['aggression']:.0%} aggression, CU {p['cu_min']}-{p['cu_max']}, focus={p['focus_fire']:.0%}{wolf}")
    log("=" * 72)

    start_time = time.time()

    tasks = []
    for agent in agents:
        tasks.append(asyncio.create_task(run_player_loop(agent, start_time)))
    tasks.append(asyncio.create_task(world_state_reporter(start_time)))
    tasks.append(asyncio.create_task(news_reporter(start_time)))

    await asyncio.gather(*tasks)

    # ─── Phase 4: Final Report ──────────────────────────────────────────
    log("\n" + "=" * 72)
    log("📋 SIMULATION COMPLETE — FINAL REPORT")
    log("=" * 72)

    try:
        r = requests.get(f"{API}/world/state", timeout=5)
        if r.status_code == 200:
            nodes = r.json().get("nodes", [])
            faction_counts = {}
            for n in nodes:
                fid = n.get("faction_id", 0)
                faction_counts[fid] = faction_counts.get(fid, 0) + 1

            log("\n🏆 FINAL TERRITORY CONTROL:")
            sorted_factions = sorted(faction_counts.items(), key=lambda x: -x[1])
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
            for rank, (fid, cnt) in enumerate(sorted_factions, 1):
                pct = (cnt / max(1, len(nodes))) * 100
                p = FACTION_PROFILES.get(fid, {})
                medal = medals[min(rank - 1, len(medals) - 1)]
                bar = "█" * int(pct / 2.5) + "░" * (40 - int(pct / 2.5))
                log(f"   {medal} #{rank} {p.get('color','⚪')} F{fid} {p.get('name','?'):14s}: {cnt:3d} nodes ({pct:5.1f}%) {bar}")
    except Exception as e:
        log(f"   ⚠️ Could not fetch final state: {e}")

    log("\n📊 PLAYER STATISTICS:")
    log(f"   {'Player':35s} | {'⚔️ Breach':>9s} | {'🛡️ Defend':>9s} | {'💬 Chat':>7s} | {'Total':>5s}")
    log(f"   {'-'*35}-+-{'-'*9}-+-{'-'*9}-+-{'-'*7}-+-{'-'*5}")
    for agent in agents:
        total = agent.stats["breaches"] + agent.stats["defenses"]
        log(f"   {agent.username:35s} | {agent.stats['breaches']:>9d} | {agent.stats['defenses']:>9d} | {agent.stats['chats']:>7d} | {total:>5d}")

    log(f"\n   Total breaches: {sum(a.stats['breaches'] for a in agents)}")
    log(f"   Total defenses: {sum(a.stats['defenses'] for a in agents)}")
    log(f"   Total chats:    {sum(a.stats['chats'] for a in agents)}")

    # Leaderboard
    log("\n🏅 LEADERBOARD:")
    try:
        r = requests.get(f"{API}/leaderboard?limit=10", timeout=5)
        if r.status_code == 200:
            for entry in r.json().get("rankings", []):
                log(f"   #{entry['rank']} {entry['username']:25s} XP:{entry['xp']:6d} W:{entry['wins']} L:{entry['losses']}")
    except Exception:
        pass

    # Save log
    with open(LOG_FILE, "w") as f:
        f.write("\n".join(combat_log))
    log(f"\n💾 Full combat log saved to: {LOG_FILE}")
    log("=" * 72)


if __name__ == "__main__":
    asyncio.run(main())
