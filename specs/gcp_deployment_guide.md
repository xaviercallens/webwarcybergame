# Neo-Hack: Gridlock — GCP Deployment Implementation Guide

**GCP Project:** `webwar-490207` (Project Number: `212120873430`)  
**Version:** 1.0 | **Date:** March 14, 2026

---

## 1. Architecture Overview (Cost-Optimized)

```
                    ┌───────────────────────────────────────┐
                    │        Cloud Run (Fully Managed)      │
                    │   Backend API  +  Static Frontend     │
                    │   Single container, scale-to-zero     │
                    │   0–5 instances | 512 MB | 1 vCPU     │
                    └──────────────┬────────────────────────┘
                                   │
                    ┌──────────────▼────────────────────────┐
                    │        Cloud SQL (PostgreSQL 15)       │
                    │   db-f1-micro  |  Zonal  |  10 GB SSD │
                    │   $7.67/mo (Always Free eligible)     │
                    └──────────────┬────────────────────────┘
                                   │
                    ┌──────────────▼────────────────────────┐
                    │        Secret Manager                  │
                    │   DB_PASSWORD, JWT_SECRET              │
                    │   ~$0.06/mo (6 secret versions)       │
                    └───────────────────────────────────────┘
```

> [!IMPORTANT]
> **Why NOT Cloud CDN + Cloud Storage for the frontend?**  
> For a game with < 10k MAU, the overhead of a Load Balancer ($18/mo minimum) + CDN is unjustified.  
> Instead, we serve the Vite-built static files directly from the Cloud Run container (already in the Dockerfile).  
> This eliminates the LB and CDN costs entirely and keeps the architecture **dead simple**.

---

## 2. Cost Optimization Strategy

### Key Decisions

| Decision | Savings | Trade-off |
|----------|---------|-----------|
| **Scale-to-zero** Cloud Run (`--min-instances=0`) | ~$15/mo | 1–3s cold-start on first request |
| **db-f1-micro** SQL instance (shared vCPU) | ~$20/mo vs db-g1-small | Sufficient for < 1000 concurrent |
| **No CDN / No Load Balancer** | ~$23/mo | Slightly higher latency for distant users |
| **Single-region** deployment | ~$10/mo | No multi-region HA |
| **Cloud Run managed URL** (no custom domain initially) | ~$0.20/mo | Uses `*.run.app` URL |

### 💡 Free Tier Utilization

GCP offers generous free tier resources:

| Service | Free Tier Allowance | Our Usage |
|---------|-------------------|-----------|
| Cloud Run | 2M requests/mo, 180k vCPU-seconds, 360k GiB-seconds | Well within for < 5k users |
| Cloud Build | 120 min/day free | Sufficient for CI/CD |
| Artifact Registry | 500 MB storage free | One Docker image ~150MB |
| Secret Manager | 6 active secret versions free | We use 2 |
| Cloud Logging | 50 GB/mo free | More than enough |

---

## 3. Step-by-Step Deployment

### 3.1 Prerequisites

```bash
# Install the Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Authenticate and set project
gcloud auth login
gcloud config set project webwar-490207
```

### 3.2 Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

### 3.3 Create Artifact Registry Repository

```bash
gcloud artifacts repositories create neohack-repo \
  --repository-format=docker \
  --location=europe-west1 \
  --description="Neo-Hack container images"
```

### 3.4 Create Cloud SQL Instance

```bash
# Create the smallest PostgreSQL instance
gcloud sql instances create neohack-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=europe-west1 \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --availability-type=zonal \
  --project=webwar-490207

# Create the game database
gcloud sql databases create cyberwar_db --instance=neohack-db

# Set database password
DB_PASSWORD=$(openssl rand -base64 24)
gcloud sql users set-password postgres \
  --instance=neohack-db \
  --password=$DB_PASSWORD
echo "Save this password: $DB_PASSWORD"
```

### 3.5 Store Secrets

```bash
# Database password
echo -n "$DB_PASSWORD" | gcloud secrets create db-password \
  --data-file=- --replication-policy=automatic

# JWT secret for authentication
JWT_SECRET=$(openssl rand -base64 32)
echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret \
  --data-file=- --replication-policy=automatic

# Full connection string for Cloud Run → Cloud SQL
CONNECTION_STRING="postgresql://postgres:${DB_PASSWORD}@/cyberwar_db?host=/cloudsql/webwar-490207:europe-west1:neohack-db"
echo -n "$CONNECTION_STRING" | gcloud secrets create db-connection-string \
  --data-file=- --replication-policy=automatic
```

### 3.6 Create Service Account with Least Privilege

```bash
# Create a dedicated service account
gcloud iam service-accounts create neohack-backend \
  --display-name="Neo-Hack Backend"

SA="neohack-backend@webwar-490207.iam.gserviceaccount.com"

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding webwar-490207 \
  --member="serviceAccount:${SA}" \
  --role="roles/cloudsql.client"

# Grant Secret Manager access
for SECRET in db-password jwt-secret db-connection-string; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:${SA}" \
    --role="roles/secretmanager.secretAccessor"
done
```

### 3.7 Build and Push Docker Image

```bash
# Configure Docker to use Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev

# Build the production image (from project root)
docker build -t europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:v1.0.1 .

# Push to Artifact Registry
docker push europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:v1.0.1
```

### 3.8 Deploy to Cloud Run

```bash
gcloud run deploy neohack-gridlock \
  --image=europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:v1.0.1 \
  --region=europe-west1 \
  --platform=managed \
  --project=webwar-490207 \
  --service-account=neohack-backend@webwar-490207.iam.gserviceaccount.com \
  --add-cloudsql-instances=webwar-490207:europe-west1:neohack-db \
  --set-env-vars="WEB_BUILD_DIR=/app/static" \
  --set-secrets="DATABASE_URL=db-connection-string:latest,JWT_SECRET=jwt-secret:latest" \
  --min-instances=0 \
  --max-instances=5 \
  --memory=512Mi \
  --cpu=1 \
  --concurrency=80 \
  --timeout=300 \
  --allow-unauthenticated
```

> After deployment, Cloud Run provides a URL like:  
> `https://neohack-gridlock-XXXXX-ew.a.run.app`

### 3.9 Verify Deployment

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe neohack-gridlock \
  --region=europe-west1 --format="value(status.url)")

# Health check
curl "$SERVICE_URL/api/health"
# Expected: {"status":"healthy"}

# Open in browser
xdg-open "$SERVICE_URL"
```

---

## 4. CI/CD with Cloud Build

### `cloudbuild.yaml` (place in project root)

```yaml
steps:
  # Build Docker image
  - name: "gcr.io/cloud-builders/docker"
    args: ["build", "-t",
      "europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:$SHORT_SHA",
      "-t",
      "europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:latest",
      "."]

  # Push image
  - name: "gcr.io/cloud-builders/docker"
    args: ["push", "--all-tags",
      "europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend"]

  # Deploy to Cloud Run
  - name: "gcr.io/cloud-builders/gcloud"
    args:
      - "run"
      - "deploy"
      - "neohack-gridlock"
      - "--image=europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:$SHORT_SHA"
      - "--region=europe-west1"
      - "--platform=managed"
      - "--service-account=neohack-backend@webwar-490207.iam.gserviceaccount.com"
      - "--add-cloudsql-instances=webwar-490207:europe-west1:neohack-db"
      - "--set-env-vars=WEB_BUILD_DIR=/app/static"
      - "--set-secrets=DATABASE_URL=db-connection-string:latest,JWT_SECRET=jwt-secret:latest"
      - "--min-instances=0"
      - "--max-instances=5"
      - "--memory=512Mi"
      - "--cpu=1"
      - "--allow-unauthenticated"

options:
  logging: CLOUD_LOGGING_ONLY
```

### Connect GitHub Trigger

```bash
gcloud builds triggers create github \
  --repo-name="webwarcybergame" \
  --repo-owner="xaviercallens" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml" \
  --description="Auto-deploy Neo-Hack to Cloud Run on push to main"
```

---

## 5. Rollback

```bash
# List all revisions
gcloud run revisions list --service=neohack-gridlock --region=europe-west1

# Route 100% traffic to a stable previous revision
gcloud run services update-traffic neohack-gridlock \
  --region=europe-west1 \
  --to-revisions=PREVIOUS_REVISION_NAME=100
```

---

## 6. Monthly Cost Estimation

### Baseline (Scale-to-Zero, No Traffic)

| Service | Cost/mo |
|---------|---------|
| Cloud SQL (db-f1-micro, zonal) | **$7.67** |
| Cloud Run (0 instances when idle) | **$0.00** |
| Artifact Registry (~150 MB image) | **$0.00** (free tier) |
| Secret Manager (3 secrets) | **$0.00** (free tier) |
| Cloud Build (CI/CD) | **$0.00** (free 120 min/day) |
| **Total (idle)** | **~$8/mo** |

### Per-User Tier Cost Breakdown

| Users (MAU) | Cloud Run | Cloud SQL | Storage | **Total/mo** | **Cost/User** |
|-------------|-----------|-----------|---------|-------------|---------------|
| **100** | $0.50 | $7.67 | $0.00 | **~$8** | **$0.08** |
| **500** | $2.00 | $7.67 | $0.00 | **~$10** | **$0.02** |
| **1,000** | $4.00 | $7.67 | $0.10 | **~$12** | **$0.012** |
| **5,000** | $12.00 | $7.67 | $0.50 | **~$20** | **$0.004** |
| **10,000** | $25.00 | $26.00¹ | $1.00 | **~$52** | **$0.005** |
| **50,000** | $80.00 | $26.00¹ | $3.00 | **~$109** | **$0.002** |

> ¹ At 10k+ MAU, upgrade Cloud SQL to `db-g1-small` ($25.55/mo) for dedicated vCPU.

### Cost Assumptions

- **Cloud Run**: $0.00002400/vCPU-second, $0.00000250/GiB-second. Average request takes 100ms with 256 MB.
- **Cloud SQL**: db-f1-micro = $7.67/mo (shared vCPU, 614 MB RAM). db-g1-small = $25.55/mo (1 vCPU, 1.7 GB RAM).
- Each game session averages ~50 API calls (auth, state saves, leaderboard).
- Average user plays 3 sessions/month.

---

## 7. Optional: Custom Domain (Add When Ready)

```bash
# Map your domain to Cloud Run (no Load Balancer needed!)
gcloud beta run domain-mappings create \
  --service=neohack-gridlock \
  --domain=play.neohack-gridlock.com \
  --region=europe-west1

# Follow the DNS verification instructions printed by gcloud
# (Add CNAME record pointing to ghs.googlehosted.com)
```

> [!TIP]
> Cloud Run domain mapping provides **free managed SSL** and avoids the $18/mo Load Balancer cost entirely.

---

## 8. Monitoring & Alerts

```bash
# View live logs
gcloud run services logs read neohack-gridlock --region=europe-west1 --limit=50

# Set up an alert for high error rates
gcloud alpha monitoring policies create \
  --notification-channels="YOUR_EMAIL_CHANNEL_ID" \
  --condition-display-name="High 5xx Error Rate" \
  --condition-filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count" AND metric.labels.response_code_class="5xx"' \
  --condition-threshold-value=10 \
  --condition-threshold-duration=300s
```

---

## 9. Quick Reference Cheat Sheet

```bash
# ═══════ BUILD & DEPLOY ═══════
docker build -t europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:latest .
docker push europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:latest
gcloud run deploy neohack-gridlock --image=europe-west1-docker.pkg.dev/webwar-490207/neohack-repo/backend:latest --region=europe-west1

# ═══════ MONITOR ═══════
gcloud run services describe neohack-gridlock --region=europe-west1
gcloud run services logs read neohack-gridlock --region=europe-west1

# ═══════ DATABASE ═══════
gcloud sql connect neohack-db --user=postgres

# ═══════ SECRETS ═══════
gcloud secrets versions access latest --secret=db-password
```

---

*This guide is designed for the `webwar-490207` GCP project. Start with zero-cost scale-to-zero deployment, then adjust `--min-instances` and Cloud SQL tier as your player base grows.*
