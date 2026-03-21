"""
Neo-Hack: Gridlock — Full Remote Gameplay Simulation
=====================================================
Simulates 5 factions (10 players, 2 per faction) battling over 50 nodes
on the live GCP deployment for 10 minutes.

Each player independently:
  1. Registers & logs in
  2. Polls the epoch phase every few seconds
  3. During PLANNING: submits BREACH or DEFEND actions to strategic nodes
  4. During SIM/TRANSITION: waits & watches the world state
  5. Periodically attempts diplomacy chats with rival factions

A live combat log is printed to stdout and simultaneously written to a
timestamped log file in the artifacts directory for review.
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
POLL_INTERVAL = 4  # seconds between action cycles

# Faction profiles: (name_prefix, strategy)
# strategy: "aggressive" = mostly breach, "defensive" = mostly defend, "balanced" = mix
FACTION_PROFILES = {
    1: {"name": "SiliconValley", "strategy": "balanced"},
    2: {"name": "IronGrid",      "strategy": "aggressive"},
    3: {"name": "SilkRoad",      "strategy": "balanced"},
    4: {"name": "EuroNexus",     "strategy": "defensive"},
    5: {"name": "PacificVgd",    "strategy": "aggressive"},
}

# ─── Log Setup ──────────────────────────────────────────────────────────────
LOG_DIR = Path(os.getenv(
    "LOG_DIR",
    Path(__file__).parent.parent.parent / ".gemini" / "antigravity" / "brain"
))
LOG_FILE = Path("/tmp") / f"gameplay_sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

combat_log = []

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    combat_log.append(line)


# ─── Player Agent ───────────────────────────────────────────────────────────
class PlayerAgent:
    def __init__(self, username: str, password: str, faction_id: int, strategy: str):
        self.username = username
        self.password = password
        self.faction_id = faction_id
        self.strategy = strategy
        self.token = None
        self.headers = {}
        self.stats = {"breaches": 0, "defenses": 0, "chats": 0, "captures": 0}

    def register_and_login(self):
        """Register and obtain JWT token."""
        payload = {"username": self.username, "password": self.password}
        r = requests.post(f"{API}/auth/register", json=payload, timeout=10)
        if r.status_code == 200:
            self.token = r.json()["access_token"]
            log(f"  ✅ {self.username} registered (Faction {self.faction_id})")
        elif r.status_code == 400:
            # Already registered, try login
            r = requests.post(f"{API}/auth/login", json=payload, timeout=10)
            if r.status_code == 200:
                self.token = r.json()["access_token"]
                log(f"  🔑 {self.username} logged in (Faction {self.faction_id})")
            else:
                log(f"  ❌ {self.username} login FAILED: {r.status_code}")
                return False
        else:
            log(f"  ❌ {self.username} register FAILED: {r.status_code} {r.text[:100]}")
            return False

        self.headers = {"Authorization": f"Bearer {self.token}"}
        return True

    def get_epoch(self) -> dict | None:
        try:
            r = requests.get(f"{API}/epoch/current", headers=self.headers, timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def get_world_state(self) -> list:
        try:
            r = requests.get(f"{API}/world/state", headers=self.headers, timeout=5)
            if r.status_code == 200:
                return r.json().get("nodes", [])
        except Exception:
            pass
        return []

    def submit_action(self, action_type: str, target_node_id: int, cu: int) -> bool:
        payload = {
            "action_type": action_type,
            "target_node_id": target_node_id,
            "cu_committed": cu
        }
        try:
            r = requests.post(f"{API}/epoch/action", json=payload, headers=self.headers, timeout=5)
            if r.status_code == 200:
                return True
            else:
                return False
        except Exception:
            return False

    def chat_with_faction(self, target_faction_id: int, message: str) -> str | None:
        try:
            r = requests.post(
                f"{API}/diplomacy/chat",
                json={"faction_id": target_faction_id, "message": message},
                headers=self.headers, timeout=15
            )
            if r.status_code == 200:
                return r.json().get("reply", "")
        except Exception:
            pass
        return None

    def choose_action(self, nodes: list) -> tuple:
        """
        AI strategy: pick an action based on faction profile.
        Returns (action_type, target_node_id, cu_committed)
        """
        own_nodes = [n for n in nodes if n.get("faction_id") == self.faction_id]
        enemy_nodes = [n for n in nodes if n.get("faction_id") != self.faction_id and n.get("faction_id") is not None]

        if self.strategy == "aggressive":
            breach_chance = 0.75
        elif self.strategy == "defensive":
            breach_chance = 0.30
        else:
            breach_chance = 0.50

        if random.random() < breach_chance and enemy_nodes:
            # Prioritize weakly-defended enemy nodes
            enemy_nodes.sort(key=lambda n: n.get("defense_level", 100))
            target = enemy_nodes[0] if random.random() < 0.6 else random.choice(enemy_nodes[:5] if len(enemy_nodes) >= 5 else enemy_nodes)
            cu = random.randint(30, 120)
            return ("BREACH", target["id"], cu)
        elif own_nodes:
            # Defend a random owned node
            target = random.choice(own_nodes)
            cu = random.randint(20, 80)
            return ("DEFEND", target["id"], cu)
        elif enemy_nodes:
            # Fallback: attack something
            target = random.choice(enemy_nodes)
            return ("BREACH", target["id"], random.randint(30, 80))
        else:
            return (None, None, None)


# ─── Main Simulation Loop ──────────────────────────────────────────────────
async def run_player_loop(agent: PlayerAgent, start_time: float):
    """Run the game loop for a single player agent."""
    last_chat_time = 0
    actions_this_epoch = 0
    last_epoch_num = -1

    while (time.time() - start_time) < SIMULATION_DURATION_SECONDS:
        epoch = agent.get_epoch()
        if not epoch:
            await asyncio.sleep(POLL_INTERVAL)
            continue

        epoch_num = epoch.get("number", 0)
        phase = epoch.get("phase", "")

        # Reset per-epoch counter
        if epoch_num != last_epoch_num:
            actions_this_epoch = 0
            last_epoch_num = epoch_num

        if phase == "PLANNING" and actions_this_epoch < 3:
            nodes = agent.get_world_state()
            if nodes:
                action_type, target_id, cu = agent.choose_action(nodes)
                if action_type and target_id:
                    ok = agent.submit_action(action_type, target_id, cu)
                    if ok:
                        actions_this_epoch += 1
                        if action_type == "BREACH":
                            agent.stats["breaches"] += 1
                            log(f"  ⚔️  [{agent.username}] BREACH → Node {target_id} ({cu} CU)")
                        else:
                            agent.stats["defenses"] += 1
                            log(f"  🛡️  [{agent.username}] DEFEND → Node {target_id} ({cu} CU)")

        # Diplomacy chat every ~90 seconds (avoid rate limits)
        now = time.time()
        if now - last_chat_time > 90:
            rival_factions = [f for f in range(1, NUM_FACTIONS + 1) if f != agent.faction_id]
            target_f = random.choice(rival_factions)
            messages = [
                "We should form an alliance against the eastern factions.",
                "Your territory is surrounded. Stand down or face annihilation.",
                "Let's negotiate a trade deal for mutual CU benefit.",
                "I propose a ceasefire so we can focus on bigger threats.",
                "Your nodes are weak. Surrender now or pay the price.",
            ]
            reply = agent.chat_with_faction(target_f, random.choice(messages))
            if reply:
                agent.stats["chats"] += 1
                log(f"  💬 [{agent.username}] → Faction {target_f}: {reply[:80]}...")
            last_chat_time = now

        # Jitter the polling interval slightly to avoid thundering herd
        await asyncio.sleep(POLL_INTERVAL + random.uniform(-1, 2))


async def world_state_reporter(start_time: float):
    """Periodically report the global world state summary."""
    while (time.time() - start_time) < SIMULATION_DURATION_SECONDS:
        try:
            r = requests.get(f"{API}/world/state", timeout=5)
            if r.status_code == 200:
                nodes = r.json().get("nodes", [])
                faction_counts = {}
                for n in nodes:
                    fid = n.get("faction_id", "Neutral")
                    faction_counts[fid] = faction_counts.get(fid, 0) + 1

                total_nodes = len(nodes)
                elapsed = int(time.time() - start_time)
                minutes = elapsed // 60
                seconds = elapsed % 60

                report_lines = [f"📊 WORLD STATE [{minutes:02d}:{seconds:02d}] — {total_nodes} nodes"]
                for fid in sorted(faction_counts.keys(), key=lambda x: str(x)):
                    count = faction_counts[fid]
                    pct = (count / max(1, total_nodes)) * 100
                    bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                    profile = FACTION_PROFILES.get(fid, {})
                    fname = profile.get("name", f"ID-{fid}")
                    report_lines.append(f"   F{fid} ({fname:12s}): {count:3d} nodes ({pct:5.1f}%) {bar}")
                log("\n".join(report_lines))
        except Exception:
            pass

        # Report every 30 seconds
        await asyncio.sleep(30)


async def news_reporter(start_time: float):
    """Periodically fetch and display AI-generated news."""
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
                        log(f"  📰 NEWS: {latest.get('content', '')[:120]}")
        except Exception:
            pass
        await asyncio.sleep(20)


async def main():
    log("=" * 70)
    log("🎮 NEO-HACK: GRIDLOCK — FULL REMOTE GAMEPLAY SIMULATION")
    log(f"   Target: {BASE_URL}")
    log(f"   Duration: {SIMULATION_DURATION_SECONDS // 60} minutes")
    log(f"   Factions: {NUM_FACTIONS} | Players: {NUM_FACTIONS * PLAYERS_PER_FACTION}")
    log("=" * 70)

    # Phase 1: Register all players
    log("\n🔐 Phase 1: Registering players...")
    agents = []
    run_id = str(uuid.uuid4())[:6]
    for faction_id in range(1, NUM_FACTIONS + 1):
        profile = FACTION_PROFILES[faction_id]
        for p_idx in range(PLAYERS_PER_FACTION):
            username = f"sim_{profile['name']}_{p_idx}_{run_id}"
            agent = PlayerAgent(
                username=username,
                password=f"SecurePass_{run_id}!",
                faction_id=faction_id,
                strategy=profile["strategy"]
            )
            if agent.register_and_login():
                agents.append(agent)

    log(f"\n✅ {len(agents)} players ready across {NUM_FACTIONS} factions.\n")

    # Phase 2: Fetch initial state
    log("🌍 Phase 2: Initial world state...")
    r = requests.get(f"{API}/world/state", timeout=5)
    if r.status_code == 200:
        nodes = r.json().get("nodes", [])
        faction_counts = {}
        for n in nodes:
            fid = n.get("faction_id", "Neutral")
            faction_counts[fid] = faction_counts.get(fid, 0) + 1
        log(f"   Total nodes: {len(nodes)}")
        for fid, cnt in sorted(faction_counts.items(), key=lambda x: str(x)):
            fname = FACTION_PROFILES.get(fid, {}).get("name", f"ID-{fid}")
            log(f"   Faction {fid} ({fname}): {cnt} nodes")

    # Phase 3: Start gameplay simulation
    log(f"\n⚔️  Phase 3: Starting {SIMULATION_DURATION_SECONDS // 60}-minute combat simulation...")
    log("=" * 70)

    start_time = time.time()

    tasks = []
    # Player agent loops
    for agent in agents:
        tasks.append(asyncio.create_task(run_player_loop(agent, start_time)))

    # Background reporters
    tasks.append(asyncio.create_task(world_state_reporter(start_time)))
    tasks.append(asyncio.create_task(news_reporter(start_time)))

    # Wait for all tasks to complete (they self-terminate after SIMULATION_DURATION_SECONDS)
    await asyncio.gather(*tasks)

    # Phase 4: Final Report
    log("\n" + "=" * 70)
    log("📋 SIMULATION COMPLETE — FINAL REPORT")
    log("=" * 70)

    # Final world state
    try:
        r = requests.get(f"{API}/world/state", timeout=5)
        if r.status_code == 200:
            nodes = r.json().get("nodes", [])
            faction_counts = {}
            for n in nodes:
                fid = n.get("faction_id", "Neutral")
                faction_counts[fid] = faction_counts.get(fid, 0) + 1

            log("\n🏆 FINAL TERRITORY CONTROL:")
            sorted_factions = sorted(faction_counts.items(), key=lambda x: -x[1])
            for rank, (fid, cnt) in enumerate(sorted_factions, 1):
                pct = (cnt / max(1, len(nodes))) * 100
                fname = FACTION_PROFILES.get(fid, {}).get("name", f"Unknown-{fid}")
                medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"][min(rank - 1, 7)]
                log(f"   {medal} #{rank} Faction {fid} ({fname}): {cnt} nodes ({pct:.1f}%)")
    except Exception as e:
        log(f"   ⚠️ Could not fetch final state: {e}")

    # Player stats
    log("\n📊 PLAYER STATISTICS:")
    for agent in agents:
        total_actions = agent.stats["breaches"] + agent.stats["defenses"]
        log(
            f"   {agent.username:30s} | "
            f"⚔️ {agent.stats['breaches']:3d} | "
            f"🛡️ {agent.stats['defenses']:3d} | "
            f"💬{agent.stats['chats']:2d} | "
            f"Total: {total_actions}"
        )

    # Leaderboard
    log("\n🏅 LEADERBOARD:")
    try:
        r = requests.get(f"{API}/leaderboard?limit=10", timeout=5)
        if r.status_code == 200:
            rankings = r.json().get("rankings", [])
            for entry in rankings:
                log(f"   #{entry['rank']} {entry['username']:25s} XP:{entry['xp']:6d} W:{entry['wins']} L:{entry['losses']}")
    except Exception:
        pass

    # Save log to file
    with open(LOG_FILE, "w") as f:
        f.write("\n".join(combat_log))
    log(f"\n💾 Full combat log saved to: {LOG_FILE}")
    log("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
