"""
Neo-Hack: Gridlock v4.1 — 100-Faction Scenario Seeder
Seeds 100 factions (40 Human, 60 AI) with asymmetric power distribution.
2,500 nodes + 175 contested nodes = 2,675 total.

Usage:
    cd backend && PYTHONPATH=src python3 scripts/seed_v41_scenario.py
"""

import random
import math
from sqlmodel import Session, select, SQLModel

from backend.database import get_engine
from backend.models import Faction, Node, NodeClass, Epoch, EpochPhase, Mission
from backend.auth import get_password_hash

random.seed(41)  # Reproducible for video recording

# ============================================
# FACTION DEFINITIONS
# ============================================

TIER_CONFIG = {
    "T1": {"nodes": 80, "cu": 100_000, "aggression": 0.9},
    "T2": {"nodes": 40, "cu":  50_000, "aggression": 0.7},
    "T3": {"nodes": 25, "cu":  20_000, "aggression": 0.5},
    "T4": {"nodes": 15, "cu":   8_000, "aggression": 0.3},
    "T5": {"nodes": 10, "cu":   3_000, "aggression": 0.8},
}

# Geographic regions for distribution
REGIONS = [
    {"name": "North America", "lat": 39.0, "lng": -98.0},
    {"name": "South America", "lat": -15.0, "lng": -55.0},
    {"name": "Western Europe", "lat": 48.0, "lng": 5.0},
    {"name": "Eastern Europe", "lat": 55.0, "lng": 37.0},
    {"name": "Middle East", "lat": 30.0, "lng": 45.0},
    {"name": "Central Asia", "lat": 45.0, "lng": 68.0},
    {"name": "East Asia", "lat": 35.0, "lng": 115.0},
    {"name": "Southeast Asia", "lat": 5.0, "lng": 110.0},
    {"name": "Africa", "lat": 0.0, "lng": 25.0},
    {"name": "Oceania", "lat": -25.0, "lng": 135.0},
]

FACTIONS = [
    # Tier 1 — Hegemony (5: 3H, 2AI)
    {"name": "Nexus Dominion",   "color": "#00FFDD", "tier": "T1", "type": "H", "region": 0},
    {"name": "Iron Citadel",     "color": "#FF4444", "tier": "T1", "type": "H", "region": 3},
    {"name": "Jade Imperium",    "color": "#FFCC00", "tier": "T1", "type": "H", "region": 6},
    {"name": "Quantum Axis",     "color": "#FF00FF", "tier": "T1", "type": "AI", "region": 2},
    {"name": "Obsidian Crown",   "color": "#FF8800", "tier": "T1", "type": "AI", "region": 4},
    # Tier 2 — Major Powers (15: 8H, 7AI)
    {"name": "Arctic Syndicate", "color": "#88DDFF", "tier": "T2", "type": "H", "region": 0},
    {"name": "Pacific Vanguard", "color": "#AA44FF", "tier": "T2", "type": "H", "region": 9},
    {"name": "Shadow Cartel",    "color": "#880088", "tier": "T2", "type": "H", "region": 1},
    {"name": "Neon Concord",     "color": "#00FF88", "tier": "T2", "type": "H", "region": 2},
    {"name": "Crimson Networks",  "color": "#FF2266", "tier": "T2", "type": "H", "region": 5},
    {"name": "Silk Fiber Group",  "color": "#DDAA00", "tier": "T2", "type": "H", "region": 7},
    {"name": "Titan Assembly",    "color": "#4488FF", "tier": "T2", "type": "H", "region": 8},
    {"name": "Binary Collective", "color": "#44FFAA", "tier": "T2", "type": "H", "region": 0},
    {"name": "Void Protocol",    "color": "#6644CC", "tier": "T2", "type": "AI", "region": 3},
    {"name": "Echo Chamber",     "color": "#CC4466", "tier": "T2", "type": "AI", "region": 1},
    {"name": "DataStream Corp",  "color": "#88AA44", "tier": "T2", "type": "AI", "region": 6},
    {"name": "Null Sector",      "color": "#AA8844", "tier": "T2", "type": "AI", "region": 4},
    {"name": "Cipher Guild",     "color": "#4466AA", "tier": "T2", "type": "AI", "region": 5},
    {"name": "Phantom Fleet",    "color": "#668844", "tier": "T2", "type": "AI", "region": 7},
    {"name": "Grid Wolves",      "color": "#AA4488", "tier": "T2", "type": "AI", "region": 9},
]

# Tier 3: 25 (12H, 13AI)
T3_NAMES = [
    "Byte Horde", "Steel Phoenix", "Chrome Vipers", "Delta Enclave",
    "Neon Jackals", "Rust Covenant", "Flux Dominion", "Pulse Network",
    "Wave Syndicate", "Core Breach", "Zero Division", "Silicon Ghosts",
    "Data Phantoms", "Circuit Nomads", "Hex Council", "Black ICE",
    "Root Authority", "Kernel Panic", "Stack Overflow", "Buffer Zone",
    "Null Pointer", "Deep Link", "Socket Storm", "Ping Lords", "Trace Route"
]
T3_COLORS = [f"#{random.randint(0x222222, 0xDDDDDD):06X}" for _ in range(25)]
for i, name in enumerate(T3_NAMES):
    FACTIONS.append({
        "name": name,
        "color": T3_COLORS[i],
        "tier": "T3",
        "type": "H" if i < 12 else "AI",
        "region": i % len(REGIONS),
    })

# Tier 4: 30 (10H, 20AI)
T4_PREFIXES = ["Bit", "Net", "Code", "Hash", "Port", "Wire", "Log", "Hex", "Sys", "Mem",
               "Bus", "Reg", "Seg", "Pix", "Dot", "Key", "Tag", "Zip", "Tar", "Git",
               "Node", "Link", "Path", "Pipe", "Fork", "Sync", "Lock", "Boot", "Disk", "Ram"]
T4_SUFFIXES = ["Runners", "Crawlers", "Scrapers", "Miners", "Hawks", "Foxes",
               "Wolves", "Snakes", "Hawks", "Falcons", "Drones", "Bots",
               "Agents", "Scouts", "Sentries", "Guards", "Raiders", "Strikers",
               "Breakers", "Hackers", "Phishers", "Spiders", "Swarm", "Hive",
               "Pack", "Cell", "Unit", "Squad", "Corps", "Legion"]
for i in range(30):
    FACTIONS.append({
        "name": f"{T4_PREFIXES[i]} {T4_SUFFIXES[i]}",
        "color": f"#{random.randint(0x333333, 0xBBBBBB):06X}",
        "tier": "T4",
        "type": "H" if i < 10 else "AI",
        "region": i % len(REGIONS),
    })

# Tier 5: 25 (7H, 18AI)
T5_NAMES = [
    "Rust Rats", "Code Plague", "Phantom Virus", "Worm Collective",
    "Trojan Herd", "Rootkit Rising", "Spyware Swarm", "Malware Mob",
    "Ransomware Ring", "Botnet Brood", "Keylog Killers", "Zero Day Zealots",
    "Exploit Express", "Payload Pirates", "Shellcode Saints", "Backdoor Bandits",
    "Cross-Site Clan", "Injection Army", "Buffer Blitz", "Overflow Order",
    "Stack Smashers", "Heap Hunters", "Pointer Pirates", "Format Fiends",
    "Race Condition"
]
for i, name in enumerate(T5_NAMES):
    FACTIONS.append({
        "name": name,
        "color": f"#{random.randint(0x440000, 0xFF4444):06X}",
        "tier": "T5",
        "type": "H" if i < 7 else "AI",
        "region": i % len(REGIONS),
    })

assert len(FACTIONS) == 100, f"Expected 100 factions, got {len(FACTIONS)}"
assert sum(1 for f in FACTIONS if f["type"] == "H") == 40
assert sum(1 for f in FACTIONS if f["type"] == "AI") == 60


# ============================================
# SEED FUNCTIONS
# ============================================

def generate_nodes(faction_db, tier: str, region: dict, count: int):
    """Generate nodes with tier-appropriate stats distributed around region."""
    nodes = []
    tier_cfg = TIER_CONFIG[tier]
    for i in range(count):
        # Tier distribution: 10% T3, 30% T2, 60% T1
        roll = random.random()
        if roll > 0.9:
            nc, defense, compute = NodeClass.TIER_3, random.randint(500, 1000), random.randint(50, 100)
        elif roll > 0.6:
            nc, defense, compute = NodeClass.TIER_2, random.randint(200, 499), random.randint(20, 49)
        else:
            nc, defense, compute = NodeClass.TIER_1, random.randint(50, 199), random.randint(5, 19)

        # Scale defense by faction tier
        if tier in ("T1", "T2"):
            defense = int(defense * 1.5)

        lat = region["lat"] + random.uniform(-12.0, 12.0)
        lng = region["lng"] + random.uniform(-18.0, 18.0)
        lat = max(min(lat, 85.0), -85.0)
        lng = max(min(lng, 180.0), -180.0)

        prefix = faction_db.name[:3].upper().replace(" ", "X")
        nodes.append(Node(
            name=f"{prefix}-N{i:03d}",
            lat=lat, lng=lng,
            faction_id=faction_db.id,
            defense_level=defense,
            compute_output=compute,
            node_class=nc,
        ))
    return nodes


def generate_contested_nodes(count: int = 175):
    """Generate unclaimed contested nodes scattered globally."""
    nodes = []
    for i in range(count):
        lat = random.uniform(-70.0, 70.0)
        lng = random.uniform(-170.0, 170.0)
        nodes.append(Node(
            name=f"CTX-N{i:03d}",
            lat=lat, lng=lng,
            faction_id=None,
            defense_level=random.randint(30, 100),
            compute_output=random.randint(3, 15),
            node_class=NodeClass.TIER_1,
        ))
    return nodes


def seed_missions(session):
    """Seed campaign missions."""
    missions = [
        Mission(order=1, title="CORE SYSTEMS TUTORIAL", briefing="Learn neural hacking basics.", difficulty="TUTORIAL", required_level=1, xp_reward=1500, reward_description="Basic Data Tap"),
        Mission(order=2, title="THE BERYLIA BANK RUN", briefing="Breach Berylia Corporation vault.", difficulty="NORMAL", required_level=2, xp_reward=4500, reward_description="Encryption Bypass, Decoy Signal"),
        Mission(order=3, title="SILICON SILK ROAD HEIST", briefing="Intercept data convoy.", difficulty="HARD", required_level=5, xp_reward=6000, reward_description="Advanced Network Scanner, Virus Injector"),
        Mission(order=4, title="OPERATION BLACKOUT", briefing="Coordinate city power grid strike.", difficulty="HARD", required_level=8, xp_reward=8500, reward_description="EMP Disruptor, Stealth Protocol"),
        Mission(order=5, title="OPERATION CRIMSON TIDE", briefing="Infiltrate Neo-Tokyo Corporate Tower.", difficulty="EXTREME", required_level=12, xp_reward=12000, reward_description="Master Key, AI Override"),
    ]
    for m in missions:
        session.add(m)


def seed_scenario():
    print("=" * 60)
    print("Neo-Hack: Gridlock v4.1 — 100-Faction Scenario Seeder")
    print("=" * 60)

    engine = get_engine()
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        existing = session.exec(select(Faction)).first()
        if existing:
            print("⚠ Database already seeded. Drop tables first to re-seed.")
            return

        # Create factions
        faction_db_map = {}
        for i, f in enumerate(FACTIONS):
            tier_cfg = TIER_CONFIG[f["tier"]]
            faction = Faction(
                name=f["name"],
                color=f["color"],
                compute_reserves=tier_cfg["cu"],
                global_influence_pct=round(tier_cfg["nodes"] / 25.0, 1),
            )
            session.add(faction)
            session.flush()
            faction_db_map[i] = (faction, f)
            print(f"  [{f['tier']}] [{f['type']}] {f['name']:<25s} CU={tier_cfg['cu']:>7,} Nodes={tier_cfg['nodes']}")

        session.commit()
        print(f"\n✓ {len(FACTIONS)} factions created")

        # Create nodes per faction
        total_nodes = 0
        for i, (faction, f) in faction_db_map.items():
            tier_cfg = TIER_CONFIG[f["tier"]]
            region = REGIONS[f["region"]]
            nodes = generate_nodes(faction, f["tier"], region, tier_cfg["nodes"])
            session.add_all(nodes)
            total_nodes += len(nodes)

        # Contested nodes
        contested = generate_contested_nodes(175)
        session.add_all(contested)
        total_nodes += len(contested)
        session.commit()
        print(f"✓ {total_nodes} nodes created (175 contested)")

        # Create initial epoch
        epoch = Epoch(number=1, phase=EpochPhase.PLANNING)
        session.add(epoch)

        # Seed missions
        seed_missions(session)
        session.commit()
        print("✓ 5 campaign missions seeded")
        print("✓ Epoch 1 (PLANNING) created")

    print(f"\n{'=' * 60}")
    print(f"SCENARIO READY — 100 factions, {total_nodes} nodes")
    print(f"  Human:  40 factions")
    print(f"  AI:     60 factions")
    print(f"  Power:  Asymmetric (T1=100K CU, T5=3K CU)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    seed_scenario()
