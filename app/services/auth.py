"""
API key validation helpers.
"""

from fastapi import HTTPException, status

from app.core.config import Settings


def require_api_key(api_key: str, settings: Settings) -> None:
    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
