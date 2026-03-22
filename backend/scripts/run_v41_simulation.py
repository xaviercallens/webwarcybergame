"""
Neo-Hack: Gridlock v4.1 — 12-Epoch Simulation Runner
Runs the 100-faction scenario with AI agent decisions, diplomacy,
ghost node deployments, phantom presences, and React Phase events.

Usage:
    cd backend && PYTHONPATH=src python3 scripts/run_v41_simulation.py --epochs 12
"""

import argparse
import random
import time
import json
from datetime import datetime
from sqlmodel import Session, select

from backend.database import get_engine
from backend.models import (
    Faction, Node, Epoch, EpochPhase, EpochAction, ActionType,
    GhostNode, GhostNodeStatus, PhantomPresence, ReactPhaseEvent,
    Accord, NewsItem,
)

random.seed(41)

# AI personality configs
AI_STYLES = {
    "aggressive":  {"scan": 0.1, "breach": 0.7, "defend": 0.2, "ghost": 0.3, "phantom": 0.4},
    "defensive":   {"scan": 0.2, "breach": 0.2, "defend": 0.5, "ghost": 0.5, "phantom": 0.1},
    "balanced":    {"scan": 0.2, "breach": 0.4, "defend": 0.3, "ghost": 0.3, "phantom": 0.2},
    "guerrilla":   {"scan": 0.3, "breach": 0.5, "defend": 0.1, "ghost": 0.1, "phantom": 0.6},
    "economic":    {"scan": 0.4, "breach": 0.2, "defend": 0.3, "ghost": 0.4, "phantom": 0.1},
}

DIPLOMACY_SCRIPTS = [
    {
        "epoch": 4,
        "type": "CEASEFIRE",
        "factions": ["Nexus Dominion", "Jade Imperium"],
        "dialogue": [
            {"from": "Nexus Dominion", "msg": "Commander Jade, the Iron Citadel moves against our eastern flank. We propose a NON-AGGRESSION PACT covering sectors 7-12. TERMS: 4-epoch ceasefire, mutual SCAN sharing."},
            {"from": "Jade Imperium", "msg": "ANALYSIS: Nexus proposal aligns with expansion vector. COUNTER: Extend to 6 epochs. Include trade route protection. CONDITION: Nexus withdraws from zone C."},
            {"from": "Nexus Dominion", "msg": "Acceptable if Jade commits 2,000 CU to joint defense of Sector 9."},
            {"from": "Jade Imperium", "msg": "ACCEPTED. ACCORD ACTIVE."},
        ],
    },
    {
        "epoch": 4,
        "type": "THREAT",
        "factions": ["Rust Rats", "Nexus Dominion"],
        "dialogue": [
            {"from": "Rust Rats", "msg": "We know your ghost nodes at NXS-N065 and NXS-N071 are DECOYS. Our phantom on NXS-N044 says hello. DEMAND: Release 5 contested nodes or we activate all phantoms."},
            {"from": "Nexus Dominion", "msg": "Threats from insurgents holding 10 nodes are amusing. Expect a PURGE next epoch."},
            {"from": "Rust Rats", "msg": "Then war it is. VOID_NULL sends regards."},
        ],
    },
    {
        "epoch": 4,
        "type": "ALLIANCE",
        "factions": ["Byte Horde", "Delta Enclave", "Flux Dominion", "Core Breach"],
        "dialogue": [
            {"from": "Byte Horde", "msg": "Fellow regionals: T1 factions consumed 60% of contested zones. PROPOSAL: Regional Defense Alliance (RDA). Pool 20% CU."},
            {"from": "Delta Enclave", "msg": "Agreed. Iron Citadel already probing our borders."},
            {"from": "Flux Dominion", "msg": "IN. Rotate leadership per epoch."},
            {"from": "Core Breach", "msg": "AYE. ALLIANCE FORMED: RDA-001."},
        ],
    },
    {
        "epoch": 7,
        "type": "BETRAYAL",
        "factions": ["Jade Imperium", "Nexus Dominion"],
        "dialogue": [
            {"from": "Jade Imperium", "msg": "Treaty ACC-0041 TERMINATED. Nexus placed ghost nodes in the neutral zone — violation of Article 2. All Jade forces consider Nexus HOSTILE."},
            {"from": "Nexus Dominion", "msg": "Those were DEFENSIVE ghost nodes. You're making a mistake."},
            {"from": "Jade Imperium", "msg": "The accord is broken. Prepare your firewalls."},
        ],
    },
    {
        "epoch": 8,
        "type": "ABSORPTION",
        "factions": ["Rust Rats", "Bit Runners"],
        "dialogue": [
            {"from": "Rust Rats", "msg": "Your defenses are pathetic. OPTION A: Join insurgency. OPTION B: We take everything."},
            {"from": "Bit Runners", "msg": "...We accept Option A. Merging command structure."},
        ],
    },
    {
        "epoch": 11,
        "type": "EMERGENCY_COALITION",
        "factions": ["Nexus Dominion", "Byte Horde", "Arctic Syndicate", "Pacific Vanguard"],
        "dialogue": [
            {"from": "Nexus Dominion", "msg": "EMERGENCY BROADCAST: Nexus lost 18 nodes. Iron+Jade will control 50% by E12. PROPOSAL: Emergency Defense Coalition. ALL non-T1 pool 30% CU."},
            {"from": "Byte Horde", "msg": "RDA commits 12,000 CU. Deploying 8 ghost nodes as screen."},
            {"from": "Arctic Syndicate", "msg": "Arctic in. 10,000 CU to counter-offensive."},
            {"from": "Pacific Vanguard", "msg": "Pacific commits 8,000 CU. Launching phantom infiltration on Jade rear."},
        ],
    },
]


def get_ai_style(faction_name: str, tier: str) -> str:
    if tier == "T5":
        return "guerrilla"
    if "Jade" in faction_name or "Silk" in faction_name:
        return "economic"
    if "Iron" in faction_name or "Crimson" in faction_name:
        return "aggressive"
    if "Quantum" in faction_name or "Sentinel" in faction_name:
        return "defensive"
    return "balanced"


def simulate_epoch(session: Session, epoch_num: int, factions: list, all_nodes: list):
    """Run one epoch of AI decisions."""
    print(f"\n{'='*60}")
    print(f"  EPOCH {epoch_num:02d}")
    print(f"{'='*60}")

    epoch = Epoch(number=epoch_num, phase=EpochPhase.PLANNING)
    session.add(epoch)
    session.flush()

    actions_taken = 0
    ghost_deployed = 0
    phantoms_placed = 0
    react_phases = 0
    nodes_changed = 0

    for faction in factions:
        faction_nodes = [n for n in all_nodes if n.faction_id == faction.id]
        enemy_nodes = [n for n in all_nodes if n.faction_id and n.faction_id != faction.id]
        neutral_nodes = [n for n in all_nodes if n.faction_id is None]

        if not faction_nodes:
            continue

        tier = "T1" if faction.compute_reserves >= 80000 else \
               "T2" if faction.compute_reserves >= 40000 else \
               "T3" if faction.compute_reserves >= 15000 else \
               "T4" if faction.compute_reserves >= 5000 else "T5"

        style = get_ai_style(faction.name, tier)
        probs = AI_STYLES[style]

        # Decide action count based on tier
        action_count = {"T1": 5, "T2": 3, "T3": 2, "T4": 1, "T5": 2}[tier]

        for _ in range(action_count):
            roll = random.random()

            if roll < probs["scan"] and (neutral_nodes or enemy_nodes):
                # SCAN
                target = random.choice(neutral_nodes or enemy_nodes)
                cu = random.randint(50, 300)
                if cu <= faction.compute_reserves:
                    session.add(EpochAction(epoch_id=epoch.id, player_id=1, action_type=ActionType.SCAN, target_node_id=target.id, cu_committed=cu))
                    faction.compute_reserves -= cu
                    actions_taken += 1

            elif roll < probs["scan"] + probs["breach"] and enemy_nodes:
                # BREACH
                target = random.choice(enemy_nodes)
                cu = random.randint(200, 3000) if tier in ("T1", "T2") else random.randint(100, 500)
                if cu <= faction.compute_reserves:
                    session.add(EpochAction(epoch_id=epoch.id, player_id=1, action_type=ActionType.BREACH, target_node_id=target.id, cu_committed=cu))
                    faction.compute_reserves -= cu
                    actions_taken += 1

                    # Resolve breach
                    if cu > target.defense_level * 0.7:
                        # Trigger React Phase (30% chance for high-value targets)
                        if target.defense_level > 300 and random.random() < 0.3:
                            defender_wins = random.random() < 0.4
                            rp = ReactPhaseEvent(
                                attacker_id=1, defender_id=1,
                                node_id=target.id, epoch_id=epoch.id,
                                attacker_success_pct=random.uniform(20, 95),
                                defender_inputs="w,a,s,d" if defender_wins else "w,a",
                                time_remaining=random.randint(0, 12),
                                defender_won=defender_wins,
                            )
                            session.add(rp)
                            react_phases += 1
                            if defender_wins:
                                continue  # Node defended

                        # Capture node
                        target.faction_id = faction.id
                        nodes_changed += 1

            elif roll < probs["scan"] + probs["breach"] + probs["defend"]:
                # DEFEND
                target = random.choice(faction_nodes)
                cu = random.randint(100, 500)
                if cu <= faction.compute_reserves:
                    target.defense_level += cu // 5
                    session.add(EpochAction(epoch_id=epoch.id, player_id=1, action_type=ActionType.DEFEND, target_node_id=target.id, cu_committed=cu))
                    faction.compute_reserves -= cu
                    actions_taken += 1

            # Ghost node deployment
            if random.random() < probs["ghost"] and enemy_nodes:
                target = random.choice(enemy_nodes)
                ghost = GhostNode(
                    player_id=1, target_node_id=target.id,
                    epoch_id=epoch.id, bait_telemetry=f"bait_{faction.name[:3]}",
                )
                session.add(ghost)
                ghost_deployed += 1

            # Phantom presence
            if random.random() < probs["phantom"] and enemy_nodes:
                target = random.choice(enemy_nodes)
                phantom = PhantomPresence(
                    attacker_id=1, node_id=target.id,
                    epoch_id=epoch.id,
                    encryption_level=random.randint(1, 5),
                    turns_remaining=random.randint(2, 6),
                    detection_risk=random.uniform(0.05, 0.35),
                )
                session.add(phantom)
                phantoms_placed += 1

        session.add(faction)

    # Process diplomacy for this epoch
    for script in DIPLOMACY_SCRIPTS:
        if script["epoch"] == epoch_num:
            print(f"\n  📜 DIPLOMACY: {script['type']}")
            for line in script["dialogue"]:
                print(f"     [{line['from']}]: {line['msg'][:80]}...")
            if script["type"] in ("CEASEFIRE", "ALLIANCE"):
                f_names = script["factions"]
                f_objs = [f for f in factions if f.name in f_names]
                if len(f_objs) >= 2:
                    accord = Accord(
                        faction_a_id=f_objs[0].id,
                        faction_b_id=f_objs[1].id,
                        type=script["type"],
                        status="ACTIVE",
                    )
                    session.add(accord)

    # Create news
    news = NewsItem(epoch_id=epoch.id, content=f"Epoch {epoch_num}: {actions_taken} actions, {nodes_changed} nodes changed, {react_phases} React Phases, {ghost_deployed} ghosts deployed")
    session.add(news)

    # End epoch
    epoch.phase = EpochPhase.TRANSITION
    epoch.ended_at = datetime.utcnow()
    session.add(epoch)
    session.commit()

    # Refresh nodes
    all_nodes = list(session.exec(select(Node)).all())

    print(f"  Actions: {actions_taken} | Nodes changed: {nodes_changed}")
    print(f"  Ghost nodes: {ghost_deployed} | Phantoms: {phantoms_placed} | React Phases: {react_phases}")

    return all_nodes


def print_leaderboard(session: Session, factions: list, all_nodes: list):
    """Print final faction rankings."""
    print(f"\n{'='*60}")
    print("  FINAL LEADERBOARD")
    print(f"{'='*60}")
    print(f"{'Rank':<5} {'Faction':<25} {'Nodes':>6} {'CU':>8} {'Tier':>5}")
    print("-" * 55)

    results = []
    for f in factions:
        node_count = sum(1 for n in all_nodes if n.faction_id == f.id)
        results.append((f, node_count))

    results.sort(key=lambda x: (-x[1], -x[0].compute_reserves))
    for i, (f, nc) in enumerate(results[:20], 1):
        tier = "T1" if f.compute_reserves >= 50000 else "T2" if f.compute_reserves >= 20000 else "T3" if f.compute_reserves >= 8000 else "T4" if f.compute_reserves >= 3000 else "T5"
        print(f"{i:<5} {f.name:<25} {nc:>6} {f.compute_reserves:>8,} {tier:>5}")

    eliminated = sum(1 for f, nc in results if nc == 0)
    print(f"\n  Eliminated factions: {eliminated}/100")


def main():
    parser = argparse.ArgumentParser(description="v4.1 100-Faction Simulation")
    parser.add_argument("--epochs", type=int, default=12, help="Number of epochs to simulate")
    args = parser.parse_args()

    print("=" * 60)
    print("  Neo-Hack: Gridlock v4.1 — 100-Faction Simulation")
    print(f"  Epochs: {args.epochs}")
    print("=" * 60)

    engine = get_engine()
    with Session(engine) as session:
        factions = list(session.exec(select(Faction)).all())
        if not factions:
            print("ERROR: No factions found. Run seed_v41_scenario.py first.")
            return

        all_nodes = list(session.exec(select(Node)).all())
        print(f"\nLoaded {len(factions)} factions, {len(all_nodes)} nodes")

        for epoch_num in range(1, args.epochs + 1):
            all_nodes = simulate_epoch(session, epoch_num, factions, all_nodes)
            # Re-fetch factions with updated CU
            factions = list(session.exec(select(Faction)).all())
            time.sleep(0.1)  # Brief pause for dramatic effect

        print_leaderboard(session, factions, all_nodes)

    print(f"\n{'='*60}")
    print("  SIMULATION COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
