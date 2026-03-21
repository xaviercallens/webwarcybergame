"""
Database Seeding Script.

This module provides utilities to initialize the database with factions
and a starting distribution of controllable nodes. It supports generating
nodes with asymmetric properties based on v3 balance configuration.
"""
import random
from sqlmodel import Session, select

from backend.database import get_engine
from backend.models import Faction, Node, NodeClass

# Asymmetric faction configuration (v3 game balance)
# node_share: fraction of total nodes this faction starts with
# compute_reserves: starting CU budget (higher = more powerful)
FACTIONS_DATA = [
    {
        "name": "Silicon Valley Bloc",
        "color": "#00FFDD",
        "global_influence_pct": 30.0,
        "base_lat": 37.3875,
        "base_lng": -122.0575,
        "node_share": 0.30,          # 30% of nodes  (dominant start)
        "compute_reserves": 2000,
    },
    {
        "name": "Iron Grid",
        "color": "#FF4444",
        "global_influence_pct": 24.0,
        "base_lat": 55.7558,
        "base_lng": 37.6173,
        "node_share": 0.24,          # 24% of nodes  (aggressive)
        "compute_reserves": 3000,
    },
    {
        "name": "Silk Road Coalition",
        "color": "#FFCC00",
        "global_influence_pct": 16.0,
        "base_lat": 39.9042,
        "base_lng": 116.4074,
        "node_share": 0.16,          # 16% of nodes  (underdog)
        "compute_reserves": 1500,
    },
    {
        "name": "Euro Nexus",
        "color": "#4488FF",
        "global_influence_pct": 10.0,
        "base_lat": 50.8503,
        "base_lng": 4.3517,
        "node_share": 0.10,          # 10% of nodes  (weakest start)
        "compute_reserves": 800,
    },
    {
        "name": "Pacific Vanguard",
        "color": "#AA44FF",
        "global_influence_pct": 20.0,
        "base_lat": 35.6762,
        "base_lng": 139.6503,
        "node_share": 0.20,          # 20% of nodes  (balanced)
        "compute_reserves": 2500,
    },
    {
        "name": "Cyber Mercenaries",
        "color": "#AAAAAA",
        "global_influence_pct": 0.0,
        "base_lat": 0.0,
        "base_lng": 0.0,
        "is_cnsa": True,
        "compute_reserves": 50000,
    },
    {
        "name": "Sentinel Vanguard",
        "color": "#FFFFFF",
        "global_influence_pct": 0.0,
        "base_lat": 0.0,
        "base_lng": 0.0,
        "is_cnsa": True,
        "compute_reserves": 50000,
    },
    {
        "name": "Shadow Cartels",
        "color": "#880088",
        "global_influence_pct": 0.0,
        "base_lat": 0.0,
        "base_lng": 0.0,
        "is_cnsa": True,
        "compute_reserves": 50000,
    }
]

def generate_nodes_for_faction(faction: Faction, base_lat: float, base_lng: float, count: int = 45):
    """
    Generate nodes with balanced defense levels (50-100) to allow dynamic gameplay.
    Nodes are assigned a Tier 1, 2, or 3 classification probabilistically and distributed
    globally around the faction's base coordinates.
    
    Args:
        faction (Faction): The faction object to which these nodes will belong.
        base_lat (float): The base latitude around which to cluster the generated nodes.
        base_lng (float): The base longitude around which to cluster the generated nodes.
        count (int): The number of nodes to generate. Defaults to 45.
        
    Returns:
        list[Node]: A list of unpersisted Node model instances.
    """
    nodes = []
    for i in range(count):
        # Determine class and stats — defense kept low (50-100) for viable captures
        tier_roll = random.random()
        if tier_roll > 0.9:
            node_class = NodeClass.TIER_3
            defense = random.randint(80, 100)
            compute = random.randint(50, 100)
        elif tier_roll > 0.6:
            node_class = NodeClass.TIER_2
            defense = random.randint(60, 85)
            compute = random.randint(20, 49)
        else:
            node_class = NodeClass.TIER_1
            defense = random.randint(50, 70)
            compute = random.randint(5, 19)

        # Distribute geographically around the base
        lat = base_lat + random.uniform(-10.0, 10.0)
        lng = base_lng + random.uniform(-15.0, 15.0)

        # Keep clamped
        lat = max(min(lat, 90.0), -90.0)
        lng = max(min(lng, 180.0), -180.0)

        node = Node(
            name=f"{faction.name[:3].upper()}-N{i:03d}",
            lat=lat,
            lng=lng,
            faction_id=faction.id,
            defense_level=defense,
            compute_output=compute,
            node_class=node_class
        )
        nodes.append(node)
    return nodes

def seed_database(total_nodes: int = 50):
    """
    Seed the game database with an asymmetric faction distribution.
    
    Deletes existing game nodes and recreates them according to configured shares.
    If factions don't exist, they are created with specific compute reserves. If they do, 
    their compute reserves are updated to match the latest balance configuration.
    
    Args:
        total_nodes (int): The total global initial node count to distribute. Defaults to 50 nodes.
        
    Distribution (default setup):
      - Silicon Valley Bloc (30%): Dominant start
      - Iron Grid (24%): Aggressive high-CU
      - Pacific Vanguard (20%): Balanced
      - Silk Road Coalition (16%): Underdog
      - Euro Nexus (10%): Weakest start, defensive
    """
    print(f"Seeding database with {total_nodes} nodes (asymmetric distribution)...")
    engine = get_engine()
    
    with Session(engine) as session:
        # Check if factions already exist
        existing_factions = session.exec(select(Faction)).all()
        
        if not existing_factions:
            # Create factions on first run with varied CU reserves
            for data in FACTIONS_DATA:
                faction = Faction(
                    name=data["name"],
                    color=data["color"],
                    global_influence_pct=data["global_influence_pct"],
                    compute_reserves=data.get("compute_reserves", 5000)
                )
                session.add(faction)
            session.commit()
            existing_factions = session.exec(select(Faction)).all()
        else:
            # Update existing faction CU reserves to match config
            for faction in existing_factions:
                match = next((d for d in FACTIONS_DATA if d["name"] == faction.name), None)
                if match and "compute_reserves" in match:
                    faction.compute_reserves = match["compute_reserves"]
                    faction.global_influence_pct = match.get("global_influence_pct", faction.global_influence_pct)
                    session.add(faction)
            session.commit()

        # Build playable faction list (non-CNSA)
        cnsa_names = {d["name"] for d in FACTIONS_DATA if d.get("is_cnsa")}
        factions_for_nodes = []
        for faction in existing_factions:
            if faction.name not in cnsa_names:
                match = next((d for d in FACTIONS_DATA if d["name"] == faction.name), None)
                if match:
                    factions_for_nodes.append((faction, match))

        if not factions_for_nodes:
            print("No playable factions found. Aborting seed.")
            return

        # Delete existing nodes to allow re-seeding with new count
        session.exec(select(Node)).all()  # load
        from sqlalchemy import delete
        session.exec(delete(Node))
        session.commit()

        # Create nodes with ASYMMETRIC distribution based on node_share
        total_assigned = 0
        for i, (faction, data) in enumerate(factions_for_nodes):
            share = data.get("node_share", 1.0 / len(factions_for_nodes))
            count = max(1, round(total_nodes * share))
            # Ensure we don't exceed total
            if i == len(factions_for_nodes) - 1:
                count = total_nodes - total_assigned
            total_assigned += count
            
            nodes = generate_nodes_for_faction(
                faction, data["base_lat"], data["base_lng"], count
            )
            session.add_all(nodes)
            print(f"  {faction.name:25s}: {count:3d} nodes ({share:.0%}) | CU: {faction.compute_reserves}")
            
        session.commit()
        print(f"\nDatabase seeded: {total_nodes} nodes across {len(factions_for_nodes)} factions (asymmetric).")

if __name__ == "__main__":
    seed_database()
