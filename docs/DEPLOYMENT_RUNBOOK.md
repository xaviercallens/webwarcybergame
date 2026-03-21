# Neo-Hack v3.1 — GCP Deployment Runbook

## Prerequisites

- GCP project: `webwar-490207`
- Region: `europe-west1`
- Service account: `neohack-backend@webwar-490207.iam.gserviceaccount.com`
- `gcloud` CLI authenticated and configured
- Docker installed locally

## Services

| Service | Cloud Run Name | Port | Min Instances |
|---------|---------------|------|---------------|
| Backend | `neohack-gridlock` | 8000 | 0 |
| RL Agent | `neohack-rl-agent` | 8001 | 1 |

## 1. Build & Push Images

### Backend
```bash
cd backend/
docker build -t europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:latest .
docker push europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:latest
```

### RL Agent
```bash
cd backend/
docker build -f Dockerfile.rl_agent \
  -t europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/rl-agent:latest .
docker push europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/rl-agent:latest
```

## 2. Deploy to Cloud Run

### Backend
```bash
gcloud run deploy neohack-gridlock \
  --image europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:latest \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars "DATABASE_URL=postgresql://...,JWT_SECRET=...,RL_AGENT_URL=https://neohack-rl-agent-xxx.run.app"
```

### RL Agent
```bash
gcloud run deploy neohack-rl-agent \
  --image europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/rl-agent:latest \
  --region europe-west1 \
  --platform managed \
  --min-instances 1 \
  --max-instances 5 \
  --memory 1Gi \
  --cpu 1 \
  --no-allow-unauthenticated \
  --service-account neohack-backend@webwar-490207.iam.gserviceaccount.com
```

## 3. CI/CD (Cloud Build)

### Single Service
```bash
gcloud builds submit --config infrastructure/cloudbuild-rl-agent.yaml --project webwar-490207
```

### Multi-Service
```bash
gcloud builds submit --config infrastructure/cloudbuild-multi-service.yaml --project webwar-490207
```

Trigger on push to `develop/v3.1` branch.

## 4. Firestore Setup

```bash
# Enable Firestore
gcloud firestore databases create --region=europe-west1

# Collections are auto-created:
# - game_sessions: active multiplayer sessions
# - match_replays: completed match replays
```

## 5. Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Backend | PostgreSQL connection string |
| `JWT_SECRET` | Backend | JWT signing secret |
| `RL_AGENT_URL` | Backend | Internal URL of RL agent service |
| `GOOGLE_CLOUD_PROJECT` | Both | GCP project ID |
| `GOOGLE_API_KEY` | Backend | Google Gemini API key for Diplomacy AI features |
| `WEB_BUILD_DIR` | Backend | (Optional) Path to static frontend build directory |

## 6. Monitoring

### Health Checks
```bash
# Backend
curl https://neohack-gridlock-xxx.run.app/health

# RL Agent
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://neohack-rl-agent-xxx.run.app/health
```

### Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=neohack-rl-agent" --limit 50
```

## 7. Rollback

```bash
# List revisions
gcloud run revisions list --service neohack-gridlock --region europe-west1

# Route traffic to previous revision
gcloud run services update-traffic neohack-gridlock \
  --to-revisions PREVIOUS_REVISION=100 \
  --region europe-west1
```

## 8. Cost Targets

| Service | Monthly Target |
|---------|---------------|
| Cloud Run (backend) | ~$3 |
| Cloud Run (RL agent) | ~$8 |
| Cloud SQL | ~$8 |
| Firestore | ~$2 |
| Cloud Storage | ~$1 |
| **Total** | **~$22/mo** |

## 9. Performance Targets

| Metric | Target | Verified |
|--------|--------|----------|
| Turn processing latency | <100ms | ✅ (benchmark_suite.py) |
| RL inference | <500ms | ✅ (benchmark_suite.py) |
| Firestore sync | <200ms | ✅ (benchmark_suite.py) |
| Concurrent sessions | 50 | Pending load test |
