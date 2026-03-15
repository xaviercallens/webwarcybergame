# Neo-Hack: Gridlock — GCP Professional Recommendations

**GCP Project:** `webwar-490207` | **Date:** March 15, 2026

Based on a full review of the deployed architecture, backend codebase, Dockerfile, and Cloud Run configuration.

---

## 🔴 Security — Critical Findings

### 1. Hardcoded JWT Secret Key

> [!CAUTION]
> `auth.py` contains `SECRET_KEY = "SUPER_SECRET_CYBERWAR_KEY"` — a hardcoded secret used to sign **all** authentication tokens. An attacker who reads the source code can forge arbitrary JWTs and impersonate any player.

**Fix:** Read the secret from the `JWT_SECRET` environment variable (already injected by Cloud Run via Secret Manager):

```diff
- SECRET_KEY = "SUPER_SECRET_CYBERWAR_KEY"
+ import os
+ SECRET_KEY = os.environ["JWT_SECRET"]
```

**Effort:** 5 min | **Impact:** Critical

---

### 2. Overly Permissive CORS Policy

> [!WARNING]
> `main.py` sets `allow_origins=["*"]` with `allow_credentials=True`. This combination allows **any website** to make authenticated cross-origin requests and steal player tokens via cookie/header reflection.

**Fix:** Restrict origins to your actual domains:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://neohack-gridlock-212120873430.europe-west1.run.app",
        "http://localhost:5173",   # local dev
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**Effort:** 5 min | **Impact:** High

---

### 3. No Rate Limiting on Auth Endpoints

The `/api/auth/login` and `/api/auth/register` endpoints have no rate limiting, making them vulnerable to brute-force credential attacks and account-enumeration spam.

**Recommended GCP approach:**

| Option | Cost | Complexity |
|--------|------|------------|
| **Cloud Armor** WAF policy (rate limiting rules) | ~$5/mo per policy | Low — attach to Cloud Run via GLB |
| **Application-level** with `slowapi` or `fastapi-limiter` | Free | Medium — add Redis or in-memory store |
| **API Gateway** (Apigee or API Gateway) | Free tier available | Medium |

**Quick win** — add `slowapi` directly to FastAPI:

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
def login_user(...):
```

---

### 4. No Input Validation on `limit` Parameter

`/api/leaderboard?limit=999999` — the `limit` query parameter has no upper bound. An attacker can request the entire player table in one call.

```diff
- def get_leaderboard(limit: int = 10, ...):
+ from fastapi import Query
+ def get_leaderboard(limit: int = Query(default=10, ge=1, le=100), ...):
```

---

### 5. Database Connection Without SSL

The Cloud SQL connection string uses Unix socket via Cloud SQL Proxy (which is encrypted), but the SQLAlchemy engine has no `pool_pre_ping` or SSL enforcement. If you ever switch to TCP connections, traffic would flow unencrypted.

**Fix:** Add connection pooling health checks:

```python
_engine = create_engine(
    config.settings.database_url,
    echo=False,
    pool_pre_ping=True,     # detect stale connections
    pool_size=5,
    max_overflow=10,
)
```

---

## 🟡 Architecture — Recommended Improvements

### 6. Separate Alembic Migrations from Container Startup

> [!IMPORTANT]
> The current `CMD` runs `alembic upgrade head && uvicorn ...` on **every container startup**. With Cloud Run's auto-scaling, this means migrations run concurrently across multiple instances — risking deadlocks and duplicate DDL execution.

**Recommended pattern:**

| Approach | Description |
|----------|-------------|
| **Cloud Build step** | Run `alembic upgrade head` as a dedicated step in `cloudbuild.yaml` before deploying the new revision |
| **Cloud Run Job** | Create a one-off Cloud Run Job that runs migrations, triggered before each deploy |

**Example `cloudbuild.yaml` addition:**

```yaml
# Run migrations BEFORE deploying
- name: "gcr.io/cloud-builders/docker"
  args: ["run", "--rm",
    "--env", "DATABASE_URL=$$DATABASE_URL",
    "$IMAGE_URL",
    "alembic", "upgrade", "head"]
  secretEnv: ["DATABASE_URL"]

availableSecrets:
  secretManager:
    - versionName: projects/webwar-490207/secrets/db-connection-string/versions/latest
      env: DATABASE_URL
```

Then simplify the Dockerfile CMD:

```diff
- CMD ["sh", "-c", "alembic upgrade head && uvicorn ..."]
+ CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

### 7. Add a `.dockerignore` File

The current Docker build sends **783 MB** of context (including `node_modules`, `.git`, screenshots, zip files). This slows every build significantly.

**Create `.dockerignore`:**

```
.git
.godot
node_modules
*.zip
*.png
*.import
promo_frames_tmp
__pycache__
.pytest_cache
.coverage
*.log
*.db
```

**Expected improvement:** Build context drops from ~784 MB → ~50 MB, saving ~30s per build.

---

### 8. Add Health Check with Database Dependency

The current `/api/health` endpoint only returns `{"status": "healthy"}` — it doesn't verify the database connection. Cloud Run will mark the service as healthy even if PostgreSQL is unreachable.

```python
@app.get("/api/health")
def health_check(session: Session = Depends(database.get_session)):
    try:
        session.exec(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unreachable")
```

---

### 9. Use Cloud Run Startup Probe Instead of Liveness

Cloud Run currently uses a default TCP startup probe. Configure a proper HTTP startup probe pointing to `/api/health`:

```bash
gcloud run services update neohack-gridlock \
  --region=europe-west1 \
  --startup-probe-http-path=/api/health \
  --startup-probe-initial-delay=5 \
  --startup-probe-period=10 \
  --startup-probe-failure-threshold=3
```

---

## 🟢 Scalability — Growth Path

### 10. Scaling Tier Plan

| MAU | Cloud SQL Tier | Cloud Run Config | Estimated Cost |
|-----|---------------|-----------------|---------------|
| **< 1k** (current) | `db-f1-micro` | min=0, max=5 | ~$8/mo |
| **1k–5k** | `db-f1-micro` | min=1, max=10 | ~$25/mo |
| **5k–10k** | `db-g1-small` | min=1, max=20 | ~$55/mo |
| **10k–50k** | `db-custom-2-4096` | min=2, max=50 + Cloud Armor | ~$150/mo |
| **50k+** | Cloud SQL HA + Read Replicas | Multi-region Cloud Run + CDN + GLB | ~$400/mo |

---

### 11. Add Memorystore (Redis) for Session/Leaderboard Caching

The leaderboard query hits PostgreSQL on every request. At scale, this becomes a bottleneck.

**Recommendation:** Add **Memorystore for Redis** (Basic tier, 1 GB = ~$35/mo) to cache:
- Leaderboard rankings (TTL: 30s)
- Player session data
- Rate limiting counters

**GCP setup:**

```bash
gcloud redis instances create neohack-cache \
  --size=1 \
  --region=europe-west1 \
  --tier=basic \
  --redis-version=redis_7_0
```

> [!NOTE]
> This is only needed at 5k+ MAU. At current scale, PostgreSQL handles the load comfortably.

---

### 12. Implement Cloud CDN When Crossing 10k MAU

At 10k+ MAU, serve static frontend assets from **Cloud Storage + Cloud CDN** behind a **Global External Application Load Balancer**:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
│  Cloud CDN  │───▶│ Cloud       │───▶│  Static assets   │
│  (global)   │    │ Storage     │    │  (Vite build)    │
└─────────────┘    └─────────────┘    └─────────────────┘
       │
       ▼
┌─────────────┐    ┌─────────────────┐
│  GLB /api/* │───▶│  Cloud Run      │
│  routing    │    │  (API only)     │
└─────────────┘    └─────────────────┘
```

This offloads static file serving from Cloud Run and gives you global edge caching. Cost justified only at scale (~$23/mo for GLB).

---

### 13. Enable Cloud SQL Automated Backups with PITR

Currently backups are enabled but Point-in-Time Recovery (PITR) is not.

```bash
gcloud sql instances patch neohack-db \
  --enable-point-in-time-recovery \
  --retained-transaction-log-days=7
```

Cost: ~$0.08/GB/mo for transaction logs. Essential for disaster recovery.

---

## 📋 Implementation Priority Matrix

| # | Recommendation | Priority | Effort | Impact |
|---|---------------|----------|--------|--------|
| 1 | Fix hardcoded JWT secret | 🔴 **P0** | 5 min | Critical security |
| 2 | Restrict CORS origins | 🔴 **P0** | 5 min | High security |
| 3 | Add rate limiting | 🟠 **P1** | 30 min | Medium security |
| 4 | Validate query params | 🟠 **P1** | 5 min | Low security |
| 5 | DB connection pooling | 🟡 **P2** | 10 min | Reliability |
| 6 | Separate migrations from startup | 🟠 **P1** | 1 hr | Architecture |
| 7 | Add `.dockerignore` | 🟢 **P2** | 5 min | Build speed |
| 8 | Health check with DB | 🟠 **P1** | 10 min | Reliability |
| 9 | HTTP startup probe | 🟡 **P2** | 5 min | Reliability |
| 10 | Scaling tier plan | 🟡 **P3** | — | Planning |
| 11 | Redis caching | 🟡 **P3** | 2 hrs | Performance |
| 12 | CDN + GLB separation | 🟡 **P3** | 4 hrs | Scalability |
| 13 | Enable PITR backups | 🟡 **P2** | 5 min | Disaster recovery |

---

> **Recommendation:** Address items 1–4 immediately (combined ~45 minutes of work). These are security fundamentals that should be deployed before any real users access the platform.
