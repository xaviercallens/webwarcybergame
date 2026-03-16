import os
import sys

# Ensure we can import from backend
sys.path.append('/app/src')

from sqlmodel import Session, select
from backend.database import get_engine
from backend.models import Faction
from backend.seed import FACTIONS_DATA

def run():
    engine = get_engine()
    with Session(engine) as session:
        existing = session.exec(select(Faction)).all()
        existing_names = [f.name for f in existing]
        added = 0
        for data in FACTIONS_DATA:
            if data.get('is_cnsa') and data['name'] not in existing_names:
                print(f"Adding CNSA Faction: {data['name']}")
                fac = Faction(
                    name=data['name'],
                    color=data['color'],
                    global_influence_pct=data['global_influence_pct'],
                    compute_reserves=50000
                )
                session.add(fac)
                added += 1
        
        if added > 0:
            session.commit()
            print(f"Successfully added {added} CNSA factions.")
        else:
            print("All CNSA factions already present.")

if __name__ == '__main__':
    run()
