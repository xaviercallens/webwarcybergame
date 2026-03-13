# CyberWar Backend Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup & Installation](#setup--installation)
4. [Configuration](#configuration)
5. [Database](#database)
6. [API Endpoints](#api-endpoints)
7. [Project Structure](#project-structure)
8. [Development](#development)
9. [Deployment](#deployment)

---

## Overview

The CyberWar backend is a **FastAPI-based REST API** that serves the Godot game client. It provides infrastructure for:

- **Game state management** (future multiplayer support)
- **Player authentication & authorization** (prepared)
- **Database persistence** (PostgreSQL with SQLModel ORM)
- **Static file serving** (web build distribution)
- **Health monitoring** (API health checks)

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | FastAPI | 0.128.0+ |
| **Server** | Uvicorn | 0.40.0+ |
| **ORM** | SQLModel | 0.0.31 |
| **Database** | PostgreSQL | 9.6+ |
| **Migrations** | Alembic | 1.18.2+ |
| **Auth** | PyJWT | 2.10.1+ |
| **Python** | Python | 3.11+ |

---

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                   Godot Game Client                      │
│                   (Websocket/HTTP)                       │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI Application                     │
├──────────────────────────────────────────────────────────┤
│  • REST API Endpoints                                    │
│  • Request/Response Validation (Pydantic)               │
│  • Static File Serving                                   │
│  • Health Checks                                         │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              SQLModel ORM Layer                          │
├──────────────────────────────────────────────────────────┤
│  • Model Definitions                                     │
│  • Database Session Management                          │
│  • Query Building                                        │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              PostgreSQL Database                         │
├──────────────────────────────────────────────────────────┤
│  • Schema Management (Alembic)                          │
│  • Data Persistence                                      │
│  • Transaction Management                               │
└──────────────────────────────────────────────────────────┘
```

### Module Structure

```
backend/
├── src/backend/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI app & routes
│   ├── config.py             # Configuration management
│   ├── database.py           # Database engine & sessions
│   └── models.py             # SQLModel data models
├── migrations/
│   ├── env.py                # Alembic environment config
│   ├── script.py.mako        # Migration template
│   └── versions/             # Migration files (auto-generated)
├── alembic.ini               # Alembic configuration
├── pyproject.toml            # Project metadata & dependencies
├── main.py                   # Entry point
├── .env.example              # Environment template
└── uv.lock                   # Dependency lock file
```

---

## Setup & Installation

### Prerequisites

- **Python 3.11+** installed
- **PostgreSQL 9.6+** running and accessible
- **uv** package manager (or pip)

### Installation Steps

#### 1. Clone & Navigate

```bash
cd backend/
```

#### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/cyberwar_db
PORT=8000
```

#### 3. Install Dependencies

Using **uv** (recommended):

```bash
uv sync
```

Or using **pip**:

```bash
pip install -r requirements.txt
```

#### 4. Initialize Database

```bash
alembic upgrade head
```

This creates all tables defined in `backend/models.py`.

#### 5. Run Development Server

```bash
python main.py
```

Server starts at: `http://localhost:8000`

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Empty | ✅ Yes |
| `PORT` | Server port | 8000 | ❌ No |

### Settings Class

Located in `backend/config.py`:

```python
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "")
```

**Usage in code:**

```python
from backend.config import settings

db_url = settings.database_url
```

### Environment Setup

**Development:**

```env
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/cyberwar_dev
PORT=8000
```

**Production:**

```env
DATABASE_URL=postgresql://prod_user:prod_pass@prod-db.example.com:5432/cyberwar
PORT=8000
```

---

## Database

### Connection Management

#### Engine Creation

`backend/database.py` manages the SQLAlchemy engine:

```python
def get_engine():
    global _engine
    if _engine is None:
        if not config.settings.database_url:
            logger.warning("Database not configured")
            return None
        _engine = create_engine(config.settings.database_url, echo=False)
    return _engine
```

**Features:**
- Lazy initialization (engine created on first use)
- Singleton pattern (single engine instance)
- Graceful degradation (returns None if not configured)

#### Session Management

```python
def get_session():
    engine = get_engine()
    if engine is None:
        yield None
        return
    with Session(engine) as session:
        yield session
```

**Usage in FastAPI routes:**

```python
from backend.database import get_session

@app.get("/api/data")
def get_data(session: Session = Depends(get_session)):
    # Use session for queries
    pass
```

### Database Initialization

```python
def init_db():
    engine = get_engine()
    if engine is not None:
        SQLModel.metadata.create_all(engine)
```

Called automatically on app startup via lifespan context manager.

### Models

Located in `backend/models.py`. Currently empty (prepared for future features).

**Example model structure:**

```python
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Migrations

#### Alembic Setup

Alembic manages schema changes:

```bash
# Create a new migration
alembic revision --autogenerate -m "Add player table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

#### Migration Files

Located in `backend/migrations/versions/`:

```python
# Example: 001_initial_schema.py
def upgrade():
    op.create_table(
        'player',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('player')
```

#### Environment Configuration

`backend/migrations/env.py` handles:

- **Database URL override** from `DATABASE_URL` env var
- **SQLModel type rendering** (AutoString → sa.String)
- **Offline & online migration modes**

---

## API Endpoints

### Health Check

**Endpoint:** `GET /api/health`

**Description:** Verify API is running

**Response:**

```json
{
  "status": "healthy"
}
```

**Status Codes:**
- `200 OK` - API is healthy
- `500 Internal Server Error` - Database connection failed

**Example:**

```bash
curl http://localhost:8000/api/health
```

### Static Files

**Endpoint:** `GET /`

**Description:** Serve web build (if available)

**Behavior:**
- Serves files from `WEB_BUILD_DIR` (default: `build/web/`)
- Falls back to `index.html` for SPA routing
- Only mounted if directory exists

**Configuration:**

```python
WEB_BUILD_DIR = Path(os.getenv(
    "WEB_BUILD_DIR", 
    Path(__file__).parent.parent.parent.parent / "build" / "web"
))

if WEB_BUILD_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_BUILD_DIR, html=True), name="static")
```

### Future Endpoints (Prepared)

These are prepared in the architecture but not yet implemented:

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User authentication
- `GET /api/players/{id}` - Get player data
- `POST /api/games` - Create game session
- `GET /api/games/{id}` - Get game state
- `POST /api/games/{id}/moves` - Submit game move

---

## Project Structure

### File Descriptions

#### `main.py` (Entry Point)

```python
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
```

**Purpose:** Starts the development server with auto-reload

**Usage:**

```bash
python main.py
```

#### `src/backend/main.py` (FastAPI App)

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend import database

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield

app = FastAPI(
    title="Backend",
    description="Backend API",
    version="0.1.0",
    lifespan=lifespan,
)

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
```

**Features:**
- Lifespan context manager for startup/shutdown
- Health check endpoint
- Static file mounting

#### `src/backend/config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    database_url: str = os.getenv("DATABASE_URL", "")

settings = Settings()
```

**Purpose:** Centralized configuration management

#### `src/backend/database.py`

```python
from sqlmodel import Session, SQLModel, create_engine
from backend import config

_engine = None

def get_engine():
    # Engine creation logic
    pass

def init_db():
    # Database initialization
    pass

def get_session():
    # Session generator for FastAPI dependency injection
    pass
```

**Purpose:** Database connection and session management

#### `src/backend/models.py`

```python
# Define SQLModel models here
# Example:
# class Player(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     username: str
```

**Purpose:** Data model definitions (currently empty, ready for expansion)

#### `pyproject.toml`

```toml
[project]
name = "backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "alembic>=1.18.2",
    "fastapi>=0.128.0",
    "psycopg2-binary>=2.9.11",
    "pydantic>=2.12.5",
    "pyjwt>=2.10.1",
    "python-dotenv>=1.2.1",
    "sqlmodel>=0.0.31",
    "uvicorn[standard]>=0.40.0",
]
```

**Purpose:** Project metadata and dependency management

#### `alembic.ini`

Configuration for Alembic migrations:

```ini
[alembic]
script_location = %(here)s/migrations
sqlalchemy.url = driver://user:password@localhost/dbname
```

**Key Settings:**
- `script_location` - Path to migrations directory
- `sqlalchemy.url` - Database URL (overridden by env var)

#### `migrations/env.py`

Alembic environment configuration:

```python
# Handles:
# - DATABASE_URL environment variable override
# - SQLModel type rendering
# - Offline/online migration modes
```

---

## Development

### Adding a New Model

1. **Define in `models.py`:**

```python
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class GameSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

2. **Create migration:**

```bash
alembic revision --autogenerate -m "Add game_session table"
```

3. **Apply migration:**

```bash
alembic upgrade head
```

### Adding a New Endpoint

1. **Add to `main.py`:**

```python
from fastapi import Depends
from backend.database import get_session
from sqlmodel import Session

@app.post("/api/games")
def create_game(session: Session = Depends(get_session)):
    # Implementation
    pass
```

2. **Test endpoint:**

```bash
curl -X POST http://localhost:8000/api/games
```

### Running Tests

Currently no test suite configured. To add:

```bash
# Install pytest
pip install pytest pytest-asyncio

# Create tests/test_api.py
# Run tests
pytest
```

### Debugging

**Enable SQL logging:**

```python
# In database.py
_engine = create_engine(config.settings.database_url, echo=True)  # Log all SQL
```

**Check database connection:**

```python
from backend.database import get_engine
engine = get_engine()
with engine.connect() as conn:
    result = conn.execute("SELECT 1")
    print(result.fetchone())
```

---

## Deployment

### Production Checklist

- [ ] Set `DATABASE_URL` environment variable
- [ ] Configure `PORT` for production (e.g., 8000)
- [ ] Set `WEB_BUILD_DIR` if serving web build
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Use production ASGI server (Gunicorn, etc.)
- [ ] Enable HTTPS/TLS
- [ ] Set up monitoring & logging
- [ ] Configure CORS if needed

### Deployment Options

#### Option 1: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

COPY . .

ENV DATABASE_URL=postgresql://...
ENV PORT=8000

CMD ["python", "main.py"]
```

#### Option 2: Gunicorn (Production Server)

```bash
# Install
pip install gunicorn

# Run
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000
```

#### Option 3: Cloud Platforms

**Heroku:**

```bash
git push heroku main
```

**Railway/Render:**

- Connect GitHub repo
- Set `DATABASE_URL` environment variable
- Deploy

### Environment Variables for Production

```env
DATABASE_URL=postgresql://user:password@prod-db.example.com:5432/cyberwar
PORT=8000
WEB_BUILD_DIR=/app/build/web
```

### Monitoring

**Health check endpoint:**

```bash
curl https://api.example.com/api/health
```

**Database connection test:**

```python
# Add to monitoring script
from backend.database import get_engine
engine = get_engine()
with engine.connect() as conn:
    conn.execute("SELECT 1")
```

---

## Troubleshooting

### Issue: Database Connection Failed

**Error:** `sqlalchemy.exc.OperationalError: could not connect to server`

**Solutions:**
1. Verify PostgreSQL is running: `psql -U postgres`
2. Check `DATABASE_URL` format: `postgresql://user:password@host:port/dbname`
3. Verify credentials and database exists
4. Check firewall/network connectivity

### Issue: Alembic Migration Fails

**Error:** `sqlalchemy.exc.ProgrammingError: relation already exists`

**Solutions:**
1. Check if table already exists: `\dt` in psql
2. Drop and recreate database if needed
3. Ensure `alembic upgrade head` runs before app start

### Issue: Port Already in Use

**Error:** `Address already in use`

**Solutions:**
1. Change port: `PORT=8001 python main.py`
2. Kill existing process: `lsof -i :8000` then `kill -9 <PID>`

### Issue: Static Files Not Serving

**Error:** `404 Not Found` on `/`

**Solutions:**
1. Verify `WEB_BUILD_DIR` exists
2. Check path in `main.py`: `Path(__file__).parent.parent.parent.parent / "build" / "web"`
3. Build web app first: `npm run build` (if applicable)

---

## Future Enhancements

### Planned Features

1. **Authentication System**
   - JWT token generation
   - User registration/login endpoints
   - Role-based access control

2. **Multiplayer Support**
   - Game session management
   - Real-time updates (WebSocket)
   - Player matchmaking

3. **Leaderboards & Stats**
   - Player rankings
   - Game statistics
   - Achievement tracking

4. **Admin Dashboard**
   - User management
   - Game monitoring
   - Database administration

### Recommended Libraries

```toml
# WebSocket support
websockets = "^12.0"

# Real-time updates
fastapi-socketio = "^0.0.10"

# Advanced authentication
python-jose = "^3.3.0"
passlib = "^1.7.4"

# Database migrations (already included)
alembic = "^1.18.2"

# Testing
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
httpx = "^0.24.0"

# Monitoring
prometheus-client = "^0.17.0"
```

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

---

## Support

For issues or questions:

1. Check this documentation
2. Review code comments in `backend/` directory
3. Check FastAPI/SQLModel official docs
4. Open an issue in the project repository

---

**Last Updated:** March 2026  
**Backend Version:** 0.1.0  
**Python Version:** 3.11+
