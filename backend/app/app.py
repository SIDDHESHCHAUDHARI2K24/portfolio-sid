"""FastAPI application factory."""

from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.features.auth.router import admin_router, limiter
from app.features.auth.router import router as auth_router
from app.features.auth.service import AuthError

api_v1 = APIRouter(prefix="/api/v1")


@api_v1.get("/health")
async def api_v1_health() -> dict[str, str]:
    return {"status": "ok"}


def register_routers(app: FastAPI) -> None:
    app.include_router(api_v1)
    # Feature routers append below, one include_router per feature, alphabetical.
    app.include_router(auth_router)
    app.include_router(admin_router)


async def _auth_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AuthError)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def _rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RateLimitExceeded)
    return JSONResponse(status_code=429, content={"detail": f"Rate limit exceeded: {exc.detail}"})


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="portfolio-sid API")

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_exception_handler(AuthError, _auth_error_handler)

    # Empty allow_origins = no cross-origin access (same-origin only).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    register_routers(app)

    static_dir = Path(settings.admin_static_dir)
    if static_dir.is_dir():
        static_root = static_dir.resolve()

        # Registered AFTER all routers so explicit /api/* routes win. Serves the
        # built admin SPA: real files as-is, everything else falls back to
        # index.html so client-side routing survives a hard refresh.
        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa_catchall(full_path: str) -> FileResponse:
            if full_path == "api" or full_path.startswith("api/"):
                raise HTTPException(status_code=404)
            candidate = (static_root / full_path).resolve()
            if candidate.is_file() and candidate.is_relative_to(static_root):
                return FileResponse(candidate)
            return FileResponse(static_root / "index.html")

    return app
