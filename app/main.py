"""
FastAPI application entrypoint.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import dns, health
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.dns_client import get_dns_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    get_dns_service(settings)  # Warm up the Google DNS client
    yield


def create_application() -> FastAPI:
    application = FastAPI(
        title="GPROX",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.include_router(health.router)
    application.include_router(dns.router)
    return application


app = create_application()
