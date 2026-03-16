
from sqlmodel import Session, select
from backend.database import get_engine
from backend.models import Faction
from backend.seed import FACTIONS_DATA

engine = get_engine()
with Session(engine) as session:
    existing = len(session.exec(select(Faction)).all())
    if existing < 8:
        for data in FACTIONS_DATA:
            if data.get('is_cnsa'):
                fac = session.exec(select(Faction).where(Faction.name == data['name'])).first()
                if not fac:
                    print(f'Adding {data["name"]}')
                    fac = Faction(
                        name=data['name'],
                        color=data['color'],
                        global_influence_pct=data['global_influence_pct'],
                        compute_reserves=50000
                    )
                    session.add(fac)
        session.commit()
        print('CNSA Factions Added.')
    else:
        print('Factions already present.')

