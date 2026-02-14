"""
Google Cloud DNS service factory.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import google_auth_httplib2
import httplib2
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.config import Settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/ndev.clouddns.readwrite"]


@lru_cache()
def _build_service(credentials_path: str, timeout_seconds: int):
    logger.debug(
        "Initializing Google Cloud DNS client with credentials %s (timeout=%ss)",
        credentials_path,
        timeout_seconds,
    )
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )
    base_http = httplib2.Http(timeout=timeout_seconds)
    authed_http = google_auth_httplib2.AuthorizedHttp(credentials, http=base_http)
    return build("dns", "v1", http=authed_http, cache_discovery=False)


def get_dns_service(settings: Settings):
    return _build_service(settings.gcloud_service_account, settings.dns_api_timeout_seconds)
