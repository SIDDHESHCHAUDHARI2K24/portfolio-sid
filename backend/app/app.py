"""FastAPI application factory."""

from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.features.auth.endpoints.router import admin_router, limiter
from app.features.auth.endpoints.router import router as auth_router
from app.features.auth.service import AuthError
from app.features.certifications.endpoints.router import admin_router as certs_admin_router
from app.features.certifications.endpoints.router import public_router as certs_public_router
from app.features.collections.endpoints.router import admin_router as collections_admin_router
from app.features.collections.endpoints.router import public_router as collections_public_router
from app.features.forms.endpoints.router import admin_router as forms_admin_router
from app.features.forms.endpoints.router import public_router as forms_public_router
from app.features.overview.endpoints.router import admin_router as overview_admin_router
from app.features.overview.endpoints.router import public_router as overview_public_router
from app.features.posts.endpoints.router import admin_router as posts_admin_router
from app.features.posts.endpoints.router import public_router as posts_public_router
from app.features.projects.endpoints.router import admin_router as projects_admin_router
from app.features.projects.endpoints.router import public_router as projects_public_router
from app.features.prose.endpoints.router import admin_router as prose_admin_router
from app.features.prose.endpoints.router import public_router as prose_public_router
from app.features.relevance.endpoints.router import admin_router as relevance_admin_router
from app.features.relevance.endpoints.router import public_router as relevance_public_router
from app.features.relevance.endpoints.router import tag_admin_router
from app.features.resumes.endpoints.router import admin_router as resumes_admin_router
from app.features.resumes.endpoints.router import public_router as resumes_public_router
from app.features.skills.endpoints.router import admin_router as skills_admin_router
from app.features.skills.endpoints.router import public_router as skills_public_router
from app.features.thesis.endpoints.router import admin_router as thesis_admin_router
from app.features.thesis.endpoints.router import public_router as thesis_public_router
from app.features.timeline.endpoints.router import admin_router as timeline_admin_router
from app.features.timeline.endpoints.router import public_router as timeline_public_router

api_v1 = APIRouter(prefix="/api/v1")


@api_v1.get("/health")
async def api_v1_health() -> dict[str, str]:
    return {"status": "ok"}


def register_routers(app: FastAPI) -> None:
    app.include_router(api_v1)
    # === APPEND-ZONE-START: feature router registration ===
    # Add new feature routers below, in alphabetical feature-name order, never reorder
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(certs_public_router)
    app.include_router(certs_admin_router)
    app.include_router(collections_public_router)
    app.include_router(collections_admin_router)
    app.include_router(forms_public_router)
    app.include_router(forms_admin_router)
    app.include_router(overview_public_router)
    app.include_router(overview_admin_router)
    app.include_router(posts_public_router)
    app.include_router(posts_admin_router)
    app.include_router(projects_public_router)
    app.include_router(projects_admin_router)
    app.include_router(prose_public_router)
    app.include_router(prose_admin_router)
    app.include_router(relevance_public_router)
    app.include_router(relevance_admin_router)
    app.include_router(resumes_public_router)
    app.include_router(resumes_admin_router)
    app.include_router(skills_public_router)
    app.include_router(skills_admin_router)
    app.include_router(thesis_public_router)
    app.include_router(thesis_admin_router)
    app.include_router(timeline_public_router)
    app.include_router(timeline_admin_router)
    app.include_router(tag_admin_router)
    # === APPEND-ZONE-END: feature router registration ===


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
