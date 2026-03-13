a# CyberWar Backend Configuration & Integration Guide

**Last Updated:** March 12, 2026 at 21:24 UTC+01:00

---

## ✅ Backend Status

| Component | Status | Details |
|-----------|--------|---------|
| **FastAPI Server** | 🟢 **RUNNING** | http://localhost:8000 |
| **Health Check** | 🟢 **HEALTHY** | `/api/health` returns 200 OK |
| **Auto-reload** | 🟢 **ENABLED** | Watches for file changes |
| **Database** | ⚠️ **NOT CONFIGURED** | DATABASE_URL set but DB not initialized |
| **Static Files** | 🟢 **READY** | Serving from `build/web/` if available |

---

## 🔌 API Configuration for Frontend

### Base URL

```
http://localhost:8000
```

### Available Endpoints

#### 1. Health Check (Status Monitoring)

**Endpoint:** `GET /api/health`

**Purpose:** Verify backend is running

**Request:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

**Status Code:** `200 OK`

**Frontend Usage:**
```gdscript
# In Godot GDScript
var response = await HTTP.get_request("http://localhost:8000/api/health")
if response.status == 200:
    print("Backend is healthy")
```

#### 2. Static Files (Web Build)

**Endpoint:** `GET /`

**Purpose:** Serve web-based frontend (if built)

**Available Files:**
- `/index.html` - Main SPA entry point
- `/assets/*` - Static assets
- `/styles/*` - CSS files
- `/scripts/*` - JavaScript files

**Configuration:**
```python
# Backend serves from: build/web/
# Falls back to index.html for SPA routing
```

---

## 🎮 Godot Game Client Integration

### Network Manager Configuration

Update your `NetworkManager` or game client to use:

```gdscript
const BACKEND_URL = "http://localhost:8000"
const API_HEALTH_ENDPOINT = BACKEND_URL + "/api/health"

func check_backend_health() -> bool:
    var http = HTTPClient.new()
    var error = http.connect_to_host(BACKEND_URL.split("://")[1].split(":")[0], 8000)
    if error != OK:
        return false
    return true
```

### Future Endpoints (Prepared)

These endpoints are prepared in the backend architecture but not yet implemented:

```
POST   /api/auth/register          - User registration
POST   /api/auth/login             - User authentication
GET    /api/players/{id}           - Get player data
POST   /api/games                  - Create game session
GET    /api/games/{id}             - Get game state
POST   /api/games/{id}/moves       - Submit game move
GET    /api/leaderboard            - Get rankings
POST   /api/alliances              - Request alliance
```

---

## 🗄️ Database Configuration

### Current Status

**Database:** PostgreSQL (not yet initialized)

**Connection String:**
```
postgresql://user:password@localhost:5432/cyberwar_db
```

**Environment Variable:**
```
DATABASE_URL=postgresql://user:password@localhost:5432/cyberwar_db
```

### Setup Instructions (When Ready)

1. **Create PostgreSQL Database:**
```bash
createdb cyberwar_db
```

2. **Run Migrations:**
```bash
cd backend/
alembic upgrade head
```

3. **Verify Connection:**
```bash
psql -U user -d cyberwar_db -c "SELECT 1"
```

### Database Models (Prepared)

Currently empty, ready for:
- Player accounts
- Game sessions
- Leaderboards
- Game statistics
- Alliance records

---

## 🚀 Server Information

### Development Server

**Host:** `0.0.0.0`  
**Port:** `8000`  
**Protocol:** HTTP  
**Auto-reload:** Enabled  

**Access from:**
- Local: `http://localhost:8000`
- Network: `http://<your-ip>:8000`

### Production Deployment

When deploying to production:

```bash
# Use Gunicorn (production ASGI server)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000
```

**Environment Variables for Production:**
```env
DATABASE_URL=postgresql://prod_user:prod_pass@prod-db.example.com:5432/cyberwar
PORT=8000
WEB_BUILD_DIR=/app/build/web
```

---

## 📦 Dependencies

### Core Stack

| Package | Version | Purpose |
|---------|---------|---------|
| FastAPI | 0.128.0+ | Web framework |
| Uvicorn | 0.40.0+ | ASGI server |
| SQLModel | 0.0.31 | ORM & data validation |
| Alembic | 1.18.2+ | Database migrations |
| psycopg2-binary | 2.9.11+ | PostgreSQL driver |
| PyJWT | 2.10.1+ | JWT authentication |
| python-dotenv | 1.2.1+ | Environment management |
| Pydantic | 2.12.5+ | Data validation |

### Installation

```bash
cd backend/
uv sync  # Install all dependencies
```

---

## 🔐 Security Considerations

### Current Implementation

- ✅ Health check endpoint (public)
- ✅ Static file serving (public)
- ⚠️ No authentication yet (prepared)
- ⚠️ No CORS configured (add if needed)
- ⚠️ No rate limiting (add for production)

### Recommended for Production

```python
# Add CORS support
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

---

## 🧪 Testing the Backend

### 1. Health Check

```bash
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{"status":"healthy"}
```

### 2. Check Server is Listening

```bash
netstat -tuln | grep 8000
# or
lsof -i :8000
```

### 3. Test from Godot

```gdscript
extends Node

func _ready():
    var http = HTTPClient.new()
    var error = http.connect_to_host("localhost", 8000)
    
    if error == OK:
        print("✅ Backend is reachable")
    else:
        print("❌ Backend connection failed")
```

---

## 📋 Frontend Integration Checklist

- [ ] Backend running on `http://localhost:8000`
- [ ] Health check endpoint responding with `{"status":"healthy"}`
- [ ] Frontend can reach backend from game client
- [ ] CORS configured (if frontend on different domain)
- [ ] Error handling implemented for backend failures
- [ ] Fallback UI for offline mode
- [ ] API response validation in frontend
- [ ] Loading states during API calls
- [ ] Error messages for failed requests

---

## 🔄 API Response Format

All API responses follow this format:

### Success Response (200 OK)

```json
{
  "status": "healthy"
}
```

### Error Response (5xx)

```json
{
  "detail": "Error message"
}
```

### Future Responses (Prepared)

```json
{
  "data": {
    "id": 1,
    "username": "player",
    "score": 1000
  },
  "status": "success"
}
```

---

## 🛠️ Troubleshooting

### Backend Not Responding

**Check if server is running:**
```bash
curl http://localhost:8000/api/health
```

**Check port is open:**
```bash
lsof -i :8000
```

**Restart backend:**
```bash
# Kill existing process
pkill -f "uvicorn"

# Start new instance
cd backend/
uv run python main.py
```

### Database Connection Issues

**Verify PostgreSQL is running:**
```bash
psql -U postgres -c "SELECT 1"
```

**Check DATABASE_URL:**
```bash
cat backend/.env
```

**Test connection:**
```bash
psql postgresql://user:password@localhost:5432/cyberwar_db -c "SELECT 1"
```

### CORS Issues (Frontend on Different Port)

**Add to backend `main.py`:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📞 Support & Documentation

### Backend Documentation
- Full backend docs: `BACKEND.md`
- API reference: `BACKEND.md` → API Endpoints section
- Database setup: `BACKEND.md` → Database section

### External Resources
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLModel Docs](https://sqlmodel.tiangolo.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

## 📊 System Architecture

```
┌─────────────────────────────────────────┐
│      Godot Game Client (Frontend)       │
│   - Game Logic                          │
│   - UI Rendering                        │
│   - User Input Handling                 │
└────────────────┬────────────────────────┘
                 │
        HTTP/REST API Calls
                 │
┌────────────────▼────────────────────────┐
│   FastAPI Backend (http://localhost:8000)│
│   - REST Endpoints                      │
│   - Business Logic                      │
│   - Data Validation                     │
└────────────────┬────────────────────────┘
                 │
        SQL Queries & Transactions
                 │
┌────────────────▼────────────────────────┐
│    PostgreSQL Database                  │
│    - Data Persistence                   │
│    - Schema Management                  │
│    - Transaction Support                │
└─────────────────────────────────────────┘
```

---

## 🎯 Next Steps

1. **Frontend Development**
   - Implement API client in Godot
   - Add error handling for backend failures
   - Create loading states

2. **Backend Enhancement**
   - Implement authentication endpoints
   - Add game session management
   - Create leaderboard endpoints

3. **Database Setup**
   - Initialize PostgreSQL
   - Run migrations
   - Create initial data

4. **Testing**
   - Unit tests for API endpoints
   - Integration tests with database
   - Load testing for multiplayer

---

**Backend Version:** 0.1.0  
**Python Version:** 3.12.13  
**FastAPI Version:** 0.128.0  
**Status:** ✅ Ready for Frontend Integration
