"""
SentinelFlux Dashboard — FastAPI app serving the monitoring UI and JSON API.

Start:
    sentinelflux dashboard
    uvicorn dashboard.app:app --reload   # dev mode

UI pages (HTMX + Tailwind):
    /                   Dashboard home
    /activities         Agent activity log
    /approvals          Human-in-the-loop approval queue
    /docs               Generated test case docs viewer
    /scripts            Generated test scripts viewer
    /agents             Agent registry and status

JSON API:
    /api/activities, /api/approvals, /api/docs, /api/scripts, /api/agents, /api/health
    Interactive docs at /api/docs (FastAPI Swagger UI)
"""
import os
import secrets
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from dashboard.routers import activities, approvals, docs, scripts, agents
from dashboard.routers import pages, partials
from dashboard.routers import kb as kb_router, pipeline as pipeline_router
from dashboard.routers import chat as chat_router, quality as quality_router
from dashboard.routers import config_router, runs as runs_router
from dashboard.routers import auth as auth_router

_STATIC_DIR = Path(__file__).resolve().parent / "static"
# Use a stable secret from env so sessions survive restarts; fall back to a generated one.
_SESSION_SECRET = os.environ.get("SF_SESSION_SECRET") or secrets.token_hex(32)
_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get(
        "SF_ALLOWED_ORIGINS",
        "http://sentinelflux.in,https://sentinelflux.in,http://localhost:8765,http://127.0.0.1:8765"
    ).split(",") if o.strip()
]

app = FastAPI(
    title="SentinelFlux Dashboard",
    description="Monitoring, approvals, and artifact review for the SentinelFlux agent system",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# SessionMiddleware must be added before CORSMiddleware
app.add_middleware(SessionMiddleware, secret_key=_SESSION_SECRET, https_only=False)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static assets
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Auth (login / logout — no prefix, routes are /login and /logout)
app.include_router(auth_router.router)

# HTML UI pages and HTMX partials
app.include_router(pages.router)
app.include_router(partials.router)
app.include_router(config_router.router)

# JSON API
app.include_router(activities.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(docs.router, prefix="/api")
app.include_router(scripts.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(kb_router.router, prefix="/api")
app.include_router(pipeline_router.router, prefix="/api")
app.include_router(chat_router.router, prefix="/api")
app.include_router(quality_router.router, prefix="/api")
app.include_router(runs_router.router, prefix="/api")


@app.on_event("startup")
async def _start_schedule_checker():
    import asyncio
    asyncio.create_task(_schedule_loop())


async def _schedule_loop():
    import asyncio
    from datetime import datetime, timezone
    from utils.run_manager import RunManager
    rm = RunManager()
    while True:
        await asyncio.sleep(60)
        now = datetime.now(timezone.utc)
        for sched in rm.all_schedules():
            if RunManager.is_due(sched, now):
                runs_router.fire_scheduled_run(sched["id"])


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
