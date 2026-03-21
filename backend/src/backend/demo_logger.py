"""
Demo API Logger Middleware for Neo-Hack v3.2.
Logs all HTTP requests/responses to a timestamped log file for demo recording.
"""
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from io import BytesIO

DEMO_LOG_DIR = Path(__file__).parent.parent.parent.parent / "specs" / "demo_logs"
DEMO_LOG_DIR.mkdir(parents=True, exist_ok=True)

_log_file = None
_start_time = None


def init_demo_log():
    """Initialize a new demo log file."""
    global _log_file, _start_time
    _start_time = time.time()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    _log_file = DEMO_LOG_DIR / f"demo_api_log_{ts}.txt"
    with open(_log_file, "w") as f:
        f.write(f"{'='*80}\n")
        f.write(f"  NEO-HACK: GRIDLOCK v3.2 — DEMO API CALL LOG\n")
        f.write(f"  Started: {datetime.now().isoformat()}\n")
        f.write(f"{'='*80}\n\n")
    return _log_file


def _elapsed():
    if _start_time is None:
        return "00:00.000"
    e = time.time() - _start_time
    m, s = divmod(e, 60)
    return f"{int(m):02d}:{s:06.3f}"


def log_entry(method, path, status, req_body, res_body, latency_ms):
    """Write a single log entry."""
    if _log_file is None:
        init_demo_log()

    # Truncate large bodies
    req_str = _format_body(req_body, max_len=500)
    res_str = _format_body(res_body, max_len=1000)

    entry = (
        f"[{_elapsed()}] {method} {path} → {status} ({latency_ms:.0f}ms)\n"
        f"  REQUEST:  {req_str}\n"
        f"  RESPONSE: {res_str}\n"
        f"{'─'*80}\n"
    )

    with open(_log_file, "a") as f:
        f.write(entry)


def _format_body(body, max_len=500):
    if body is None:
        return "—"
    s = str(body)
    if len(s) > max_len:
        return s[:max_len] + f"... [truncated, {len(s)} chars total]"
    return s


class DemoLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all API calls to a file for demo documentation."""

    async def dispatch(self, request: Request, call_next):
        # Only log /api/ routes
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""
        if query:
            path = f"{path}?{query}"

        # Read request body
        req_body = None
        if method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                req_body = json.loads(body_bytes) if body_bytes else None
                # Mask passwords
                if isinstance(req_body, dict) and "password" in req_body:
                    req_body = {**req_body, "password": "***"}
            except Exception:
                req_body = "<binary or unreadable>"

        # Execute request and measure time
        start = time.time()
        response = await call_next(request)
        latency_ms = (time.time() - start) * 1000

        # Read response body (requires capturing it)
        res_body = None
        try:
            body_chunks = []
            async for chunk in response.body_iterator:
                body_chunks.append(chunk if isinstance(chunk, bytes) else chunk.encode())
            raw = b"".join(body_chunks)
            try:
                res_body = json.loads(raw)
            except Exception:
                res_body = raw.decode("utf-8", errors="replace")[:500]

            # Rebuild the response with the consumed body
            from starlette.responses import Response as StarletteResponse
            response = StarletteResponse(
                content=raw,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        except Exception:
            res_body = "<could not capture>"

        log_entry(method, path, response.status_code, req_body, res_body, latency_ms)
        return response
