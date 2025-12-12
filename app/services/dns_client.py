"""
Google Cloud DNS service factory.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.config import Settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/ndev.clouddns.readwrite"]


@lru_cache()
def _build_service(credentials_path: str):
    logger.debug("Initializing Google Cloud DNS client with credentials %s", credentials_path)
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )
    return build("dns", "v1", credentials=credentials)


def get_dns_service(settings: Settings):
    return _build_service(settings.gcloud_service_account)
