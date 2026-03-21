import sys
from datetime import datetime
sys.path.append('/app/src')
from sqlmodel import Session, select
from backend.database import get_engine
from backend.models import Node, Faction, NewsItem, Epoch

engine = get_engine()
with Session(engine) as session:
    epoch = session.exec(select(Epoch)).first()
    if not epoch:
        epoch = Epoch(number=999)
        session.add(epoch)
        session.commit()
    nodes = session.exec(select(Node)).all()
    factions = session.exec(select(Faction)).all()
    
    content = f"DEBUG: Total Nodes = {len(nodes)}, Total Factions = {len(factions)}"
    news = NewsItem(epoch_id=epoch.id, content=content, created_at=datetime.utcnow())
    session.add(news)
    session.commit()
    print("Report written!")
