from fastapi import FastAPI

from ecom_resolution_agent.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Ecommerce Resolution Agent API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.get("/healthz", tags=["system"])
    def healthz() -> dict[str, str | bool]:
        return {
            "status": "ok",
            "app_env": settings.app_env,
            "simulation_mode": settings.simulation_mode,
        }

    return app


app = create_app()
