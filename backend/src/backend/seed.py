import asyncio
import os
import random
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import create_async_engine

from backend.database import get_engine
from backend.models import Faction, Node, NodeClass

FACTIONS_DATA = [
    {
        "name": "Silicon Valley Bloc",
        "color": "#00FFDD",
        "global_influence_pct": 20.0,
        "base_lat": 37.3875,
        "base_lng": -122.0575,
    },
    {
        "name": "Iron Grid",
        "color": "#FF4444",
        "global_influence_pct": 20.0,
        "base_lat": 55.7558,
        "base_lng": 37.6173,
    },
    {
        "name": "Silk Road Coalition",
        "color": "#FFCC00",
        "global_influence_pct": 20.0,
        "base_lat": 39.9042,
        "base_lng": 116.4074,
    },
    {
        "name": "Euro Nexus",
        "color": "#4488FF",
        "global_influence_pct": 20.0,
        "base_lat": 50.8503,
        "base_lng": 4.3517,
    },
    {
        "name": "Pacific Vanguard",
        "color": "#AA44FF",
        "global_influence_pct": 20.0,
        "base_lat": 35.6762,
        "base_lng": 139.6503,
    },
    {
        "name": "Cyber Mercenaries",
        "color": "#AAAAAA",
        "global_influence_pct": 0.0,
        "base_lat": 0.0,
        "base_lng": 0.0,
        "is_cnsa": True
    },
    {
        "name": "Sentinel Vanguard",
        "color": "#FFFFFF",
        "global_influence_pct": 0.0,
        "base_lat": 0.0,
        "base_lng": 0.0,
        "is_cnsa": True
    },
    {
        "name": "Shadow Cartels",
        "color": "#880088",
        "global_influence_pct": 0.0,
        "base_lat": 0.0,
        "base_lng": 0.0,
        "is_cnsa": True
    }
]

def generate_nodes_for_faction(faction: Faction, base_lat: float, base_lng: float, count: int = 45):
    nodes = []
    for i in range(count):
        # Determine class and stats
        tier_roll = random.random()
        if tier_roll > 0.9:
            node_class = NodeClass.TIER_3
            defense = random.randint(500, 1000)
            compute = random.randint(50, 100)
        elif tier_roll > 0.6:
            node_class = NodeClass.TIER_2
            defense = random.randint(200, 499)
            compute = random.randint(20, 49)
        else:
            node_class = NodeClass.TIER_1
            defense = random.randint(50, 199)
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

def seed_database(total_nodes: int = 30):
    print(f"Seeding database with {total_nodes} nodes...")
    engine = get_engine()
    
    with Session(engine) as session:
        # Check if factions already exist
        existing_factions = session.exec(select(Faction)).all()
        
        if not existing_factions:
            # Create factions on first run
            for data in FACTIONS_DATA:
                faction = Faction(
                    name=data["name"],
                    color=data["color"],
                    global_influence_pct=data["global_influence_pct"],
                    compute_reserves=50000 if data.get("is_cnsa") else 5000
                )
                session.add(faction)
            session.commit()
            existing_factions = session.exec(select(Faction)).all()

        # Build playable faction list (non-CNSA)
        cnsa_names = {d["name"] for d in FACTIONS_DATA if d.get("is_cnsa")}
        factions_for_nodes = []
        for faction in existing_factions:
            if faction.name not in cnsa_names:
                match = next((d for d in FACTIONS_DATA if d["name"] == faction.name), None)
                if match:
                    factions_for_nodes.append((faction, match["base_lat"], match["base_lng"]))

        if not factions_for_nodes:
            print("No playable factions found. Aborting seed.")
            return

        # Delete existing nodes to allow re-seeding with new count
        session.exec(select(Node)).all()  # load
        from sqlalchemy import delete
        session.exec(delete(Node))
        session.commit()

        # Create nodes distributed across factions
        nodes_per_faction = max(1, total_nodes // len(factions_for_nodes))
        extra_nodes = total_nodes % len(factions_for_nodes)
        
        for i, (faction, base_lat, base_lng) in enumerate(factions_for_nodes):
            count = nodes_per_faction + (1 if i < extra_nodes else 0)
            nodes = generate_nodes_for_faction(faction, base_lat, base_lng, count)
            session.add_all(nodes)
            
        session.commit()
        print(f"Database seeded successfully with {total_nodes} nodes across {len(factions_for_nodes)} factions.")

if __name__ == "__main__":
    seed_database()
