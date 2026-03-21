"""
Database Reset Script for Game Balance v3
==========================================
Resets node defenses, redistributes territory asymmetrically,
sets varied faction CU reserves, and resets player XP.
"""
import os
import sys

# Try to connect to the GCP database via the Cloud SQL Proxy
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Default: use the same DB string used by the app
    # Assumes cloud_sql_proxy is running locally on port 5432
    DATABASE_URL = "postgresql://neohack_user:neohack_pass@localhost:5432/neohack_db"

print(f"Connecting to: {DATABASE_URL[:40]}...")

from sqlalchemy import create_engine, text
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # 1. Reset ALL node defenses to 50-100 range
    print("\n1. Resetting node defense levels to 50-100...")
    conn.execute(text("""
        UPDATE node SET defense_level = 50 + (RANDOM() * 50)::int
    """))
    
    # 2. Asymmetric node distribution:
    # F1=15 nodes (30%), F2=12 (24%), F3=8 (16%), F4=5 (10%), F5=10 (20%)
    print("2. Redistributing nodes asymmetrically...")
    
    # Get all node IDs
    result = conn.execute(text("SELECT id FROM node ORDER BY id"))
    all_ids = [row[0] for row in result]
    total = len(all_ids)
    print(f"   Total nodes: {total}")
    
    # Distribution ranges
    distributions = [
        (1, 15),  # F1 gets 15 nodes (30%)
        (2, 12),  # F2 gets 12 nodes (24%)
        (3, 8),   # F3 gets 8 nodes (16%)
        (4, 5),   # F4 gets 5 nodes (10%)
        (5, 10),  # F5 gets 10 nodes (20%)
    ]
    
    idx = 0
    for faction_id, count in distributions:
        node_ids = all_ids[idx:idx+count]
        if node_ids:
            ids_str = ",".join(str(i) for i in node_ids)
            conn.execute(text(f"UPDATE node SET faction_id = {faction_id} WHERE id IN ({ids_str})"))
            print(f"   F{faction_id}: assigned {len(node_ids)} nodes")
        idx += count
    
    # 3. Set varied CU reserves
    print("3. Setting asymmetric faction CU reserves...")
    reserves = [(1, 2000), (2, 3000), (3, 1500), (4, 800), (5, 2500)]
    for fid, cu in reserves:
        conn.execute(text(f"UPDATE faction SET compute_reserves = {cu} WHERE id = {fid}"))
        print(f"   F{fid}: {cu} CU")
    
    # 4. Reset player XP
    print("4. Resetting all player XP and ranks...")
    conn.execute(text("""
        UPDATE player SET xp = 0, rank = 'SCRIPT_KIDDIE', wins = 0, losses = 0, win_streak = 0, best_streak = 0
    """))
    
    # 5. Clear old epoch actions to start fresh
    print("5. Clearing old epoch actions...")
    conn.execute(text("DELETE FROM epochaction"))
    
    conn.commit()
    
    # Verify
    print("\n✅ Database reset complete! New state:")
    result = conn.execute(text("""
        SELECT faction_id, COUNT(*) as nodes, 
               ROUND(AVG(defense_level)) as avg_def,
               MIN(defense_level) as min_def,
               MAX(defense_level) as max_def
        FROM node 
        GROUP BY faction_id 
        ORDER BY faction_id
    """))
    for row in result:
        print(f"   F{row[0]}: {row[1]} nodes, defense avg={row[2]} (min={row[3]}, max={row[4]})")
    
    result = conn.execute(text("SELECT id, name, compute_reserves FROM faction ORDER BY id"))
    for row in result:
        print(f"   F{row[0]} ({row[1]}): {row[2]} CU")

print("\n🏁 Ready for v3 simulation!")
