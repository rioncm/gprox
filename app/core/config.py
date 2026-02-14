"""
Configuration loading for the GPROX FastAPI application.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "/etc/gprox/config.yaml"


class Settings(BaseModel):
    log_level: str = Field(default="INFO", description="Application log level.")
    gcloud_service_account: str = Field(..., description="Path to Google Cloud service account JSON.")
    gcloud_project: str = Field(..., description="Google Cloud project ID.")
    managed_zones: Dict[str, str] = Field(default_factory=dict, description="Allowed managed zones.")
    api_keys: List[str] = Field(default_factory=list, description="Valid API keys.")
    ttl: int = Field(default=300, description="Default TTL for DNS records.")
    dns_api_num_retries: int = Field(
        default=3,
        ge=0,
        description="Number of retries for Google DNS API requests.",
    )
    dns_api_timeout_seconds: int = Field(
        default=10,
        ge=1,
        description="HTTP timeout in seconds for Google DNS API requests.",
    )


def _config_path() -> Path:
    return Path(os.environ.get("GPROX_CONFIG_PATH", DEFAULT_CONFIG_PATH))


def _load_raw_config(path: Path) -> Dict:
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_settings() -> Settings:
    path = _config_path()
    logger.debug("Loading configuration from %s", path)
    try:
        raw = _load_raw_config(path)
        settings = Settings(**raw)
        logger.debug("Configuration loaded successfully")
        return settings
    except FileNotFoundError:
        logger.exception("Configuration file missing")
        raise
    except ValidationError:
        logger.exception("Configuration validation failed")
        raise
    except yaml.YAMLError:
        logger.exception("Failed to parse YAML configuration")
        raise


@lru_cache()
def get_settings() -> Settings:
    return load_settings()
