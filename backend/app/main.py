"""SMIT FastAPI application entry point.

Run:  uvicorn app.main:app --port 8000   (from the backend/ directory)
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from . import __version__
from .db import init_db, session_factory
from .services.configs import ensure_default_config
from .settings import get_settings

log = logging.getLogger("smit")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    with session_factory()() as db:
        ensure_default_config(db)
    s = get_settings()
    if s.using_default_password:
        log.warning("SMIT_ADMIN_PASSWORD is the default value. Set it in .env before collecting real data.")
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="SMIT — Spatial Memory Interference Task", version=__version__, lifespan=lifespan)
    s = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in s.cors_origins.split(",") if o.strip()],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Session-Token"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    from .api import admin, analysis, imports, participant, reports

    app.include_router(participant.router)
    app.include_router(admin.router)
    app.include_router(imports.router)
    app.include_router(analysis.router)
    app.include_router(reports.router)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    dist: Path = s.frontend_dist
    if dist.exists():
        @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
        def spa(full_path: str):
            if full_path.startswith("api/"):
                return JSONResponse({"detail": "Not found"}, status_code=404)
            target = (dist / full_path).resolve()
            if full_path and target.is_file() and dist.resolve() in target.parents:
                # Hashed build assets never change → cache for a long time.
                cache = ("public, max-age=31536000, immutable" if full_path.startswith("assets/")
                         else "no-cache")
                return FileResponse(target, headers={"Cache-Control": cache})
            if full_path.startswith("assets/"):
                # A missing asset must NOT fall back to index.html (wrong MIME type → blank page).
                return JSONResponse({"detail": "Not found"}, status_code=404)
            # The HTML shell must always be revalidated so browsers pick up new builds.
            return FileResponse(dist / "index.html", headers={"Cache-Control": "no-cache, must-revalidate"})

    return app


app = create_app()
