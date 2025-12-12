"""
FastAPI dependencies for injecting configuration and services.
"""

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.dns_client import get_dns_service
from app.services.dns_manager import DNSManager


def get_app_settings() -> Settings:
    return get_settings()


def get_dns_manager(settings: Settings = Depends(get_app_settings)) -> DNSManager:
    service = get_dns_service(settings)
    return DNSManager(settings=settings, dns_service=service)
