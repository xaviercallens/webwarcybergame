# Sovereign Algorithm: Phase 2 Development Guide

Welcome to the **Phase 2** local development environment. This setup utilizes Docker Compose to provide a fully containerized, hot-reloading environment for both the backend (FastAPI) and frontend (Vite).

## 🚀 Starting the Environment

To start the full development stack (Database, Backend via Uvicorn reload, Frontend via Vite HMR), run:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

### Services Included:
1. **PostgreSQL Database** (`db`)
   - Port: `5432`
   - Access: `postgresql://cyberwar:cyberwar_dev@localhost:5432/cyberwar_db`

2. **FastAPI Backend** (`backend`)
   - Port: `8000`
   - Access: `http://localhost:8000`
   - Hot-reloading is **ENABLED** for the `/backend/src` and `main.py` files.
   - Swagger Documentation: `http://localhost:8000/docs`
   - Automatically runs `alembic upgrade head` before starting.

3. **Vite Frontend** (`frontend`)
   - Port: `5173`
   - Access: `http://localhost:5173`
   - Hot Moduel Replacement (HMR) is **ENABLED** for `/build/web` files.

## 🛠 Developing within Sprint 0 (Security Hardening)

As per `specs/todo.md`, Sprint 0 revolves around security.
When you make changes to `backend/src/backend/auth.py` or `main.py`, the backend container will auto-restart.

Wait for the containers to initialize, then navigate to `http://localhost:5173` to see your local instance!
