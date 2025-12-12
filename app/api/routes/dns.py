"""
DNS management endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, status

from app.api.deps import get_app_settings, get_dns_manager
from app.api.models import DNSChangeRequest, DNSChangeResponse
from app.core.config import Settings
from app.services.auth import require_api_key
from app.services.dns_manager import DNSManager

router = APIRouter(prefix="/v1/dns", tags=["dns"])


@router.post(
    "/add",
    response_model=List[DNSChangeResponse],
    status_code=status.HTTP_207_MULTI_STATUS,
)
def add_txt_record(
    payload: DNSChangeRequest,
    settings: Settings = Depends(get_app_settings),
    manager: DNSManager = Depends(get_dns_manager),
):
    require_api_key(payload.api_key, settings)
    return manager.add_txt_record(payload.fqdn, payload.value)


@router.post(
    "/remove",
    response_model=List[DNSChangeResponse],
    status_code=status.HTTP_207_MULTI_STATUS,
)
def remove_txt_record(
    payload: DNSChangeRequest,
    settings: Settings = Depends(get_app_settings),
    manager: DNSManager = Depends(get_dns_manager),
):
    require_api_key(payload.api_key, settings)
    return manager.remove_txt_record(payload.fqdn, payload.value)
