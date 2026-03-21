#!/bin/bash
set -e

IMAGE="europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:v20260319-103131"
REGION="europe-west1"
SERVICE_ACCOUNT="neohack-backend@webwar-490207.iam.gserviceaccount.com"
DB_INSTANCE="webwar-490207:europe-west1:neohack-db"

cat << 'EOF' > seed_script.py
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
EOF

SCRIPT=$(cat seed_script.py)

echo "Updating job to use inline python..."
gcloud run jobs update neohack-seed \
    --image=$IMAGE \
    --region=$REGION \
    --command="python" \
    --args="-c,$SCRIPT" || \
gcloud run jobs create neohack-seed \
    --image=$IMAGE \
    --region=$REGION \
    --service-account=$SERVICE_ACCOUNT \
    --set-cloudsql-instances=$DB_INSTANCE \
    --set-secrets="DATABASE_URL=db-connection-string:latest" \
    --command="python" \
    --args="-c,$SCRIPT"

gcloud run jobs execute neohack-seed --region=$REGION --wait
