# Sovereign Algorithm — Global Multiplayer Architecture & Pricing Model

**Project:** `webwar-490207` | **Date:** March 15, 2026

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GLOBAL PLAYERS (Browser)                         │
│   Login Page → Three.js Globe → HUD → Terminal → Sentinel Lab     │
└───────────┬──────────────────┬──────────────────┬───────────────────┘
            │ HTTPS            │ WSS              │ HTTPS
┌───────────▼──────────────────▼──────────────────▼───────────────────┐
│              Google Cloud Load Balancer (Global L7)                 │
│              + Cloud Armor WAF (DDoS + Rate Limiting)              │
│              + Managed SSL Certificate                              │
└───────┬──────────────────┬──────────────────────┬───────────────────┘
        │                  │                      │
┌───────▼─────────┐ ┌─────▼──────────┐   ┌───────▼────────────┐
│  Cloud Run      │ │  Cloud Run     │   │  Cloud Run         │
│  API Service    │ │  WebSocket     │   │  Epoch Worker      │
│  (auth, game)   │ │  (real-time)   │   │  (resolution job)  │
│  min=1, max=20  │ │  min=1, max=10 │   │  triggered by      │
│                 │ │                │   │  Cloud Scheduler    │
└────┬────────────┘ └────┬───────────┘   └──────┬──────────────┘
     │                   │                      │
┌────▼───────────────────▼──────────────────────▼──────────────────┐
│                        Cloud SQL (PostgreSQL 15)                  │
│              db-g1-small | HA regional | 20 GB SSD               │
│              + Read Replica (for leaderboard/analytics)          │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│  Memorystore (Redis 7.0) — 1 GB Basic                           │
│  Session cache | Rate limiting | Leaderboard cache | Pub/Sub    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Security Architecture

### 2.1 Authentication & Identity

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Login page with JWT token storage | User-facing gate |
| **Identity** | Firebase Authentication (free tier) | OAuth2 (Google, GitHub, email/password) |
| **API Auth** | JWT tokens (HS256, rotated via Secret Manager) | Stateless API authentication |
| **Session** | Redis-backed sessions (30-min TTL) | Prevent token replay, force re-auth |
| **Rate Limiting** | Cloud Armor + slowapi (in-app) | 5 login/min, 30 actions/min |

### 2.2 Network Security

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **WAF** | Cloud Armor (Standard tier) | SQLi, XSS, DDoS protection |
| **TLS** | Managed SSL (free with GLB) | End-to-end encryption |
| **CORS** | Restricted to production + localhost | Prevent cross-origin attacks |
| **Secrets** | Secret Manager (4 secrets) | JWT_SECRET, DB_PASSWORD, GEMINI_API_KEY, REDIS_URL |
| **IAM** | Dedicated service account, least-privilege | cloudsql.client + secretmanager.secretAccessor |

### 2.3 Data Security

- **Password hashing:** bcrypt with per-user salt (already implemented)
- **Input validation:** Pydantic models on all endpoints
- **SQL injection:** SQLModel/SQLAlchemy parameterized queries (already implemented)
- **Audit logging:** All auth events logged to Cloud Logging

---

## 3. Scalability Design

### 3.1 Horizontal Scaling

| Component | Min Instances | Max Instances | Scale Trigger |
|-----------|:---:|:---:|---|
| API Service (Cloud Run) | 1 | 20 | CPU > 60% or concurrency > 80 |
| WebSocket Service | 1 | 10 | Connection count > 200/instance |
| Epoch Worker (Cloud Run Job) | 0 | 5 | Triggered every 15 min |
| Cloud SQL | 1 primary + 1 read replica | — | Vertical scaling |
| Redis | 1 (basic) | 1 (standard HA at scale) | Memory > 80% |

### 3.2 Scaling Tiers

| Users (MAU) | Cloud Run Config | Cloud SQL | Redis | Estimated Monthly |
|:-----------:|:---:|:---:|:---:|:---:|
| **12–50** | min=1, max=5 | db-f1-micro (shared) | 1 GB basic | **~$55/mo** |
| **50–200** | min=1, max=10 | db-g1-small (dedicated) | 1 GB basic | **~$95/mo** |
| **200–500** | min=2, max=20 | db-g1-small + read replica | 1 GB standard | **~$165/mo** |
| **500–1k** | min=2, max=50 | db-custom-2-4096 + replica | 3 GB standard | **~$310/mo** |

---

## 4. Login Page Design

The login page is designed to match the existing cyberpunk "Neo-Hack" aesthetic with:
- **CRT scanline overlay** and **vignette effects** (already in `index.html`)
- **Orbitron / Share Tech Mono** typography (already loaded)
- Neon-green accent color (`#00ffdd`) on a dark background
- Animated title with glitch text-shadow
- Toggle between LOGIN and REGISTER modes
- Error/success toast messages styled consistently

### Login Flow

```
┌──────────────────────────────────────────────────┐
│                  NEO-HACK                        │
│                 GRIDLOCK                         │
│         v2.0.0 // AUTHENTICATION REQUIRED         │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  OPERATIVE_ID: [________________]        │   │
│  │  PASSPHRASE:   [________________]        │   │
│  │                                           │   │
│  │  [ ▶ AUTHENTICATE ]    [ REGISTER ]      │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ── or continue with ──                          │
│  [ ◉ Google ]    [ ◉ GitHub ]                   │
│                                                  │
│  Status: AWAITING CREDENTIALS...                 │
└──────────────────────────────────────────────────┘
```

---

## 5. GCP Cost Model (Detailed)

### 5.1 Infrastructure Cost Breakdown — 50 MAU Tier

| Service | Configuration | Monthly Cost |
|---------|--------------|:---:|
| **Cloud Run** (API) | min=1, max=5, 512Mi, 1 vCPU | $12.00 |
| **Cloud Run** (WebSocket) | min=1, max=3, 512Mi, 1 vCPU | $8.00 |
| **Cloud SQL** | db-f1-micro, zonal, 10 GB SSD, backups | $9.50 |
| **Memorystore Redis** | 1 GB Basic (M1) | $12.00 |
| **Load Balancer** (GLB) | Forwarding rules + data processing | $5.00 |
| **Cloud Armor** | Standard tier, 2 policies | $5.00 |
| **Secret Manager** | 4 secrets, ~100 accesses/day | $0.00 |
| **Cloud Scheduler** | 96 invocations/day (every 15 min) | $0.00 |
| **Artifact Registry** | ~200 MB storage | $0.00 |
| **Cloud Logging** | < 50 GB/mo | $0.00 |
| **Network Egress** | ~5 GB/mo (static assets + API) | $0.60 |
| **Managed SSL** | Included with GLB | $0.00 |
| | | |
| **Total (50 MAU)** | | **~$52/mo** |

### 5.2 Cost Scaling by MAU

| MAU | Cloud Run | SQL | Redis | GLB + Armor | Misc | **Total** |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **12** | $15 | $9.50 | $12 | $10 | $1 | **$48** |
| **50** | $20 | $9.50 | $12 | $10 | $1 | **$52** |
| **100** | $30 | $26 | $12 | $10 | $2 | **$80** |
| **200** | $45 | $26 | $12 | $12 | $3 | **$98** |
| **500** | $70 | $52 | $35 | $15 | $5 | **$177** |

### 5.3 Assumptions

- Each user averages **3 sessions/month**, each ~30 min
- Each session generates **~50 API calls** + **1 WebSocket connection**
- Epoch transitions every 15 min = **2,880 Cloud Run Job executions/mo**
- Static assets (~5 MB) served via Cloud Run (or CDN at scale)
- Cloud Run free tier covers ~40% of compute for the 12-user tier

---

## 6. Subscription Pricing (60% Margin)

### Formula

```
Subscription Revenue = Cloud Cost / (1 - Target Margin)
Subscription Revenue = Cloud Cost / 0.40
Price Per User = Subscription Revenue / Number of Users
```

### 6.1 Pricing Table

| MAU | GCP Cost/mo | Revenue Needed (60% margin) | **Price/User/mo** | **Suggested Tier** |
|:---:|:---:|:---:|:---:|:---|
| **12** | $48 | $120 | **$10.00** | 🏴 Operator (Early Access) |
| **50** | $52 | $130 | **$2.60** | 🔵 Sentinel |
| **100** | $80 | $200 | **$2.00** | 🔵 Sentinel |
| **200** | $98 | $245 | **$1.23** | 🟢 Agent |
| **500** | $177 | $443 | **$0.89** | 🟢 Agent |

### 6.2 Recommended Subscription Tiers

| Tier | Monthly Price | Includes | Target Audience |
|------|:---:|---|---|
| **🆓 Recon (Free)** | $0 | 3 games/day, no Sentinel training, no diplomacy | Trial users |
| **🔵 Sentinel** | $2.99/mo | Unlimited games, 1 Sentinel, basic diplomacy | Casual players |
| **🟡 Zero-Day** | $6.99/mo | Unlimited games, 3 Sentinels, full diplomacy, priority matchmaking | Competitive players |
| **🔴 Architect** | $14.99/mo | Everything + custom faction creation, early access to features | Power users, streamers |

### 6.3 Break-Even Analysis

| Tier | Price | Users to Break Even (at $52/mo base cost) |
|------|:---:|:---:|
| Sentinel ($2.99) | $2.99 | **18 users** |
| Zero-Day ($6.99) | $6.99 | **8 users** |
| Architect ($14.99) | $14.99 | **4 users** |

### 6.4 Revenue Projections (Mixed Tier)

Assuming user distribution: 60% Free, 25% Sentinel, 10% Zero-Day, 5% Architect:

| Total Users | Paying Users | Monthly Revenue | GCP Cost | **Net Profit** | **Margin** |
|:-----------:|:---:|:---:|:---:|:---:|:---:|
| **50** | 20 | $96 | $52 | **$44** | 46% |
| **100** | 40 | $192 | $80 | **$112** | 58% |
| **200** | 80 | $384 | $98 | **$286** | 74% |
| **500** | 200 | $960 | $177 | **$783** | 82% |

> [!TIP]
> At 100+ users with the mixed-tier model, you exceed the 60% margin target. 
> Low user counts (< 50) will operate at ~46% margin until the user base grows.

---

## 7. Implementation Priority

| # | Task | Effort | Sprint |
|---|------|--------|--------|
| 1 | Login/Register page (frontend) | 1 day | Now |
| 2 | JWT auth flow integration with existing API | 1 day | Now |
| 3 | Redis session cache (Memorystore) | 2 days | S1 |
| 4 | WebSocket real-time layer | 3 days | S5 |
| 5 | Cloud Armor WAF policies | 1 day | S6 |
| 6 | Subscription/payment integration (Stripe) | 3 days | S6+ |
| 7 | Usage quota enforcement (free tier limits) | 2 days | S6+ |
