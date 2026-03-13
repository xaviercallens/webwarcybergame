# Neo-Hack: Gridlock — Deployment Specification

**Phase 2 — Infrastructure & Deployment**  
**Version:** 1.0 | **Date:** March 13, 2026

---

## 1. Deployment Overview

```
                        ┌──────────────────────────────────────────┐
                        │            DEPLOYMENT TARGETS            │
                        ├────────────────────┬─────────────────────┤
                        │   LOCAL DEV        │   GCP PRODUCTION    │
                        │                    │                     │
                        │   Docker Compose   │   Cloud Run         │
                        │   SQLite / PgSQL   │   Cloud SQL (Pg15)  │
                        │   localhost:8000   │   HTTPS (custom)    │
                        │   Hot-reload       │   Auto-scaling      │
                        └────────────────────┴─────────────────────┘
```

| Environment | Backend | Database | Frontend | CDN |
|-------------|---------|----------|----------|-----|
| **Local** | Uvicorn (hot-reload) | SQLite or Docker PostgreSQL 15 | Vite dev server `:5173` | N/A |
| **Staging** | Cloud Run (1 instance) | Cloud SQL PostgreSQL 15 (shared) | Cloud Run static | N/A |
| **Production** | Cloud Run (auto-scale 1–10) | Cloud SQL PostgreSQL 15 (HA) | Cloud CDN + Cloud Run | Cloud CDN |

---

## 2. Local Deployment

### 2.1 Prerequisites

```bash
# Required tools
python >= 3.11       # Runtime
uv                   # Python dependency manager (fast pip alternative)
node >= 20           # Web frontend build
docker               # Optional: for PostgreSQL container
docker-compose       # Optional: full-stack orchestration
```

### 2.2 Quick Start (No Docker)

```bash
# 1. Clone and enter project
cd /home/kalxav/xdev/webwargame/CascadeProjects/windsurf-project

# 2. Backend setup
cd backend/
cp .env.example .env          # Configure DATABASE_URL
uv sync                       # Install Python dependencies
uv run alembic upgrade head   # Run database migrations (uses SQLite by default)
uv run python main.py         # Start backend at http://localhost:8000

# 3. Web frontend setup (in a second terminal)
cd build/web/                 # Or wherever Vite project lives
npm install
npm run dev                   # Start Vite dev server at http://localhost:5173
```

### 2.3 Quick Start (Docker Compose — Recommended)

#### `docker-compose.yml`

```yaml
version: "3.9"

services:
  # ─── PostgreSQL Database ──────────────────────────────────
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: cyberwar
      POSTGRES_PASSWORD: ${DB_PASSWORD:-cyberwar_dev}
      POSTGRES_DB: cyberwar_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cyberwar -d cyberwar_db"]
      interval: 5s
      timeout: 3s
      retries: 5

  # ─── FastAPI Backend ──────────────────────────────────────
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://cyberwar:${DB_PASSWORD:-cyberwar_dev}@db:5432/cyberwar_db
      PORT: 8000
      WEB_BUILD_DIR: /app/static
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend/src:/app/src:ro    # Hot-reload in dev
      - ./build/web:/app/static:ro   # Serve frontend

  # ─── Web Frontend (Dev Only) ──────────────────────────────
  frontend:
    image: node:20-alpine
    working_dir: /app
    command: sh -c "npm install && npm run dev -- --host 0.0.0.0"
    ports:
      - "5173:5173"
    volumes:
      - ./build/web:/app
    profiles:
      - dev   # Only starts with: docker compose --profile dev up

volumes:
  pgdata:
```

#### `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/
COPY main.py ./
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Run migrations then start server
EXPOSE 8000
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

#### Usage

```bash
# Full stack (backend + database)
docker compose up -d

# Full stack + frontend dev server
docker compose --profile dev up -d

# View logs
docker compose logs -f backend

# Tear down
docker compose down

# Tear down (including database volume)
docker compose down -v
```

### 2.4 Environment Variables (Local)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///cyberwar.db` | PostgreSQL or SQLite connection string |
| `PORT` | `8000` | Backend listen port |
| `WEB_BUILD_DIR` | `../build/web` | Path to compiled web frontend |
| `JWT_SECRET` | `dev-secret-change-me` | JWT signing key |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins (comma-separated) |

### 2.5 Local Verification Checklist

```bash
# 1. Health check
curl http://localhost:8000/api/health
# Expected: {"status":"healthy"}

# 2. Database connection
docker exec -it windsurf-project-db-1 psql -U cyberwar -d cyberwar_db -c "SELECT 1"

# 3. Frontend accessible
curl -s http://localhost:5173 | head -5
# Expected: <!DOCTYPE html> ...

# 4. API → DB roundtrip
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
# Expected: 201 Created
```

---

## 3. GCP Cloud Deployment

### 3.1 Architecture

```
                    ┌─────────────────────────────────┐
                    │          Cloud DNS               │
                    │     neohack-gridlock.com         │
                    └───────────┬─────────────────────┘
                                │
                    ┌───────────▼─────────────────────┐
                    │      Cloud Load Balancer         │
                    │   (HTTPS termination, CDN)       │
                    └───────┬───────────┬─────────────┘
                            │           │
              ┌─────────────▼──┐  ┌─────▼──────────────┐
              │  Cloud Run     │  │  Cloud CDN          │
              │  (Backend API) │  │  (Static Frontend)  │
              │  auto-scale    │  │  Global edge cache  │
              │  1–10 inst.    │  │                     │
              └───────┬────────┘  └─────────────────────┘
                      │
              ┌───────▼────────┐
              │  Cloud SQL     │
              │  PostgreSQL 15 │
              │  HA replica    │
              └────────────────┘
                      │
              ┌───────▼────────┐
              │  Secret Mgr    │
              │  DB_PASS, JWT  │
              └────────────────┘
```

### 3.2 GCP Services Used

| Service | Purpose | Tier/Sizing |
|---------|---------|-------------|
| **Cloud Run** | Backend API container | min 1, max 10, 1 vCPU / 512MB |
| **Cloud SQL** | PostgreSQL 15 | `db-f1-micro` (staging), `db-g1-small` (prod) |
| **Cloud Build** | CI/CD pipeline | Triggered on `git push` |
| **Artifact Registry** | Docker image storage | `us-central1-docker.pkg.dev` |
| **Cloud CDN** | Frontend static assets | Global edge caching |
| **Cloud Storage** | Frontend bundle hosting | Single bucket, public |
| **Secret Manager** | Database passwords, JWT keys | Versioned secrets |
| **Cloud DNS** | Custom domain | `neohack-gridlock.com` |
| **Cloud Monitoring** | Dashboards, alerts | Free tier |

### 3.3 Initial GCP Setup

```bash
# ─── 1. Project Setup ──────────────────────────────────────
export PROJECT_ID="neohack-gridlock"
export REGION="europe-west1"

gcloud projects create $PROJECT_ID --name="Neo-Hack Gridlock"
gcloud config set project $PROJECT_ID
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com \
  dns.googleapis.com

# ─── 2. Artifact Registry ──────────────────────────────────
gcloud artifacts repositories create neohack-repo \
  --repository-format=docker \
  --location=$REGION \
  --description="Neo-Hack container images"

# ─── 3. Cloud SQL Instance ─────────────────────────────────
gcloud sql instances create neohack-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --availability-type=zonal     # 'regional' for prod HA

gcloud sql databases create cyberwar_db --instance=neohack-db

# Generate and store credentials
DB_PASSWORD=$(openssl rand -base64 24)
gcloud sql users set-password postgres \
  --instance=neohack-db \
  --password=$DB_PASSWORD

# ─── 4. Secret Manager ─────────────────────────────────────
echo -n $DB_PASSWORD | gcloud secrets create db-password \
  --data-file=- --replication-policy=automatic

JWT_SECRET=$(openssl rand -base64 32)
echo -n $JWT_SECRET | gcloud secrets create jwt-secret \
  --data-file=- --replication-policy=automatic

# ─── 5. IAM — Grant Cloud Run access to secrets + SQL ──────
export SA="neohack-backend@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts create neohack-backend \
  --display-name="Neo-Hack Backend Service Account"

gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:${SA}" --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding jwt-secret \
  --member="serviceAccount:${SA}" --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" --role="roles/cloudsql.client"
```

### 3.4 Backend Deployment (Cloud Run)

#### `cloudbuild.yaml`

```yaml
steps:
  # Build the Docker image
  - name: "gcr.io/cloud-builders/docker"
    args:
      - "build"
      - "-t"
      - "${_REGION}-docker.pkg.dev/${PROJECT_ID}/neohack-repo/backend:${SHORT_SHA}"
      - "-t"
      - "${_REGION}-docker.pkg.dev/${PROJECT_ID}/neohack-repo/backend:latest"
      - "-f"
      - "backend/Dockerfile"
      - "backend/"

  # Push to Artifact Registry
  - name: "gcr.io/cloud-builders/docker"
    args:
      - "push"
      - "--all-tags"
      - "${_REGION}-docker.pkg.dev/${PROJECT_ID}/neohack-repo/backend"

  # Deploy to Cloud Run
  - name: "gcr.io/cloud-builders/gcloud"
    args:
      - "run"
      - "deploy"
      - "neohack-backend"
      - "--image=${_REGION}-docker.pkg.dev/${PROJECT_ID}/neohack-repo/backend:${SHORT_SHA}"
      - "--region=${_REGION}"
      - "--platform=managed"
      - "--service-account=neohack-backend@${PROJECT_ID}.iam.gserviceaccount.com"
      - "--add-cloudsql-instances=${PROJECT_ID}:${_REGION}:neohack-db"
      - "--set-env-vars=PORT=8080"
      - "--set-secrets=DATABASE_URL=db-connection-string:latest,JWT_SECRET=jwt-secret:latest"
      - "--min-instances=1"
      - "--max-instances=10"
      - "--memory=512Mi"
      - "--cpu=1"
      - "--allow-unauthenticated"

substitutions:
  _REGION: europe-west1

options:
  logging: CLOUD_LOGGING_ONLY
```

#### Manual Deploy (Without Cloud Build)

```bash
# Build + push image
cd backend/
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/neohack-repo/backend:v1 .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/neohack-repo/backend:v1

# Deploy to Cloud Run
gcloud run deploy neohack-backend \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/neohack-repo/backend:v1 \
  --region=$REGION \
  --platform=managed \
  --service-account=${SA} \
  --add-cloudsql-instances=${PROJECT_ID}:${REGION}:neohack-db \
  --set-env-vars="PORT=8080" \
  --set-secrets="DATABASE_URL=db-connection-string:latest,JWT_SECRET=jwt-secret:latest" \
  --min-instances=1 \
  --max-instances=10 \
  --allow-unauthenticated
```

### 3.5 Frontend Deployment (Cloud Storage + CDN)

```bash
# ─── 1. Build the web frontend ─────────────────────────────
cd build/web/
npm run build    # Produces dist/ folder

# ─── 2. Create Cloud Storage bucket ────────────────────────
gsutil mb -p $PROJECT_ID -l $REGION gs://neohack-frontend/
gsutil web set -m index.html -e index.html gs://neohack-frontend/

# ─── 3. Upload built assets ────────────────────────────────
gsutil -m rsync -r -d dist/ gs://neohack-frontend/

# ─── 4. Make publicly readable ─────────────────────────────
gsutil iam ch allUsers:objectViewer gs://neohack-frontend/

# ─── 5. Set cache headers ──────────────────────────────────
gsutil -m setmeta \
  -h "Cache-Control:public, max-age=31536000, immutable" \
  "gs://neohack-frontend/assets/**"

gsutil setmeta \
  -h "Cache-Control:no-cache, must-revalidate" \
  "gs://neohack-frontend/index.html"

# ─── 6. Enable Cloud CDN (via Load Balancer) ───────────────
gcloud compute backend-buckets create neohack-frontend-bucket \
  --gcs-bucket-name=neohack-frontend \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC

gcloud compute url-maps create neohack-lb \
  --default-backend-bucket=neohack-frontend-bucket

gcloud compute target-https-proxies create neohack-https-proxy \
  --ssl-certificates=neohack-cert \
  --url-map=neohack-lb

gcloud compute forwarding-rules create neohack-https-rule \
  --target-https-proxy=neohack-https-proxy \
  --ports=443 \
  --global
```

### 3.6 Database Connection String (Cloud SQL)

Create a secret for the full connection string:

```bash
# Format: postgresql+asyncpg://USER:PASS@/DB?host=/cloudsql/PROJECT:REGION:INSTANCE
CONNECTION_STRING="postgresql://postgres:${DB_PASSWORD}@/cyberwar_db?host=/cloudsql/${PROJECT_ID}:${REGION}:neohack-db"

echo -n "$CONNECTION_STRING" | gcloud secrets create db-connection-string \
  --data-file=- --replication-policy=automatic

gcloud secrets add-iam-policy-binding db-connection-string \
  --member="serviceAccount:${SA}" --role="roles/secretmanager.secretAccessor"
```

### 3.7 Custom Domain Setup

```bash
# ─── 1. Register domain with Cloud DNS ─────────────────────
gcloud dns managed-zones create neohack-zone \
  --dns-name="neohack-gridlock.com." \
  --description="Neo-Hack game domain"

# ─── 2. Create a managed SSL certificate ───────────────────
gcloud compute ssl-certificates create neohack-cert \
  --domains="neohack-gridlock.com,www.neohack-gridlock.com" \
  --global

# ─── 3. Point DNS A record to the Load Balancer IP ─────────
LB_IP=$(gcloud compute forwarding-rules describe neohack-https-rule --global --format="value(IPAddress)")

gcloud dns record-sets create neohack-gridlock.com. \
  --zone=neohack-zone --type=A --ttl=300 --rrdatas=$LB_IP

gcloud dns record-sets create www.neohack-gridlock.com. \
  --zone=neohack-zone --type=CNAME --ttl=300 \
  --rrdatas="neohack-gridlock.com."
```

---

## 4. CI/CD Pipeline

### 4.1 Trigger Configuration

```bash
# Auto-deploy on push to main branch
gcloud builds triggers create github \
  --repo-name="webwargame" \
  --repo-owner="YOUR_GITHUB_ORG" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml" \
  --description="Deploy backend to Cloud Run on push to main"
```

### 4.2 Pipeline Flow

```
  git push main
      │
      ▼
  Cloud Build Trigger
      │
      ├──► Step 1: docker build (backend)
      ├──► Step 2: docker push → Artifact Registry
      ├──► Step 3: gcloud run deploy → Cloud Run
      ├──► Step 4: npm run build (frontend)
      └──► Step 5: gsutil rsync → Cloud Storage → CDN invalidation
```

### 4.3 Rollback

```bash
# List recent revisions
gcloud run revisions list --service=neohack-backend --region=$REGION

# Route 100% traffic to a previous revision
gcloud run services update-traffic neohack-backend \
  --region=$REGION \
  --to-revisions=neohack-backend-00003-abc=100
```

---

## 5. Monitoring & Observability

### 5.1 Cloud Monitoring Dashboard

```bash
# Create a custom dashboard
gcloud monitoring dashboards create \
  --config-from-file=monitoring/dashboard.json
```

**Key Metrics:**

| Metric | Alert Threshold | Channel |
|--------|----------------|---------|
| Cloud Run request latency (p99) | > 2000ms | Email + Slack |
| Cloud Run error rate (5xx) | > 5% over 5 min | PagerDuty |
| Cloud SQL CPU utilization | > 80% for 10 min | Email |
| Cloud SQL connections | > 90% of max | Email |
| CDN cache hit ratio | < 80% | Email (weekly) |

### 5.2 Structured Logging

```python
# backend/src/backend/logging_config.py
import logging
import json

class GCPJsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record),
            "module": record.module,
        }
        if record.exc_info:
            log_entry["stack_trace"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)
```

---

## 6. Cost Estimate (Monthly)

| Service | Staging | Production |
|---------|---------|------------|
| Cloud Run (backend) | ~$5 (1 inst, minimal) | ~$25 (avg 3 instances) |
| Cloud SQL (PostgreSQL) | ~$8 (db-f1-micro) | ~$26 (db-g1-small + HA) |
| Cloud Storage (frontend) | ~$0.50 (< 1GB) | ~$1 |
| Cloud CDN | ~$0 (free tier) | ~$5 (moderate traffic) |
| Secret Manager | ~$0.06 | ~$0.06 |
| Cloud Build | ~$0 (free 120 min/day) | ~$0 |
| Cloud DNS | ~$0.20/zone | ~$0.20/zone |
| **Total** | **~$14/mo** | **~$57/mo** |

---

## 7. Security Checklist

| Item | Local | GCP |
|------|-------|-----|
| HTTPS | ❌ (localhost HTTP) | ✅ Managed SSL cert |
| Secrets in env vars | ⚠️ `.env` file | ✅ Secret Manager |
| CORS | Permissive (dev) | Strict origin whitelist |
| Rate limiting | None | Cloud Armor WAF rules |
| DB access | Local socket / Docker | Cloud SQL Auth Proxy |
| Authentication | JWT (dev key) | JWT (Secret Manager key) |
| Image scanning | None | Artifact Registry vulnerability scanning |
| WAF | None | Cloud Armor (DDoS, OWASP rules) |

---

## 8. Deployment Commands Cheat Sheet

```bash
# ════════════════════════════════════════════
#  LOCAL
# ════════════════════════════════════════════
docker compose up -d                     # Start everything
docker compose logs -f backend           # Watch backend logs
docker compose down                      # Stop everything

# ════════════════════════════════════════════
#  GCP — BACKEND
# ════════════════════════════════════════════
gcloud builds submit --config cloudbuild.yaml    # Build + deploy
gcloud run services describe neohack-backend     # Check status
gcloud run services logs read neohack-backend    # Read logs

# ════════════════════════════════════════════
#  GCP — FRONTEND
# ════════════════════════════════════════════
npm run build && gsutil -m rsync -r -d dist/ gs://neohack-frontend/
gcloud compute url-maps invalidate-cdn-cache neohack-lb --path="/*"

# ════════════════════════════════════════════
#  GCP — DATABASE
# ════════════════════════════════════════════
gcloud sql connect neohack-db --user=postgres    # Interactive psql
gcloud sql operations list --instance=neohack-db # Check ops

# ════════════════════════════════════════════
#  GCP — ROLLBACK
# ════════════════════════════════════════════
gcloud run revisions list --service=neohack-backend --region=$REGION
gcloud run services update-traffic neohack-backend \
  --to-revisions=REVISION_NAME=100 --region=$REGION
```

---

*This specification is designed to be applied incrementally — start with local Docker Compose, then graduate to GCP when ready for public access.*
