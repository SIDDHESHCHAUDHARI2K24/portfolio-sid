"""FastAPI application factory."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

api_v1 = APIRouter(prefix="/api/v1")


@api_v1.get("/health")
async def api_v1_health() -> dict[str, str]:
    return {"status": "ok"}


def register_routers(app: FastAPI) -> None:
    app.include_router(api_v1)
    # Feature routers append below, one include_router per feature, alphabetical.


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="portfolio-sid API")

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
    return app
