"""
Pydantic models for API requests and responses.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class DNSChangeRequest(BaseModel):
    api_key: str = Field(..., description="API key for authentication.")
    fqdn: str = Field(..., description="Fully qualified domain name.")
    value: str = Field(..., description="TXT record value.")


class DNSChangeResponse(BaseModel):
    fqdn: Optional[str]
    status: Literal["success", "error"]
    message: str
    response: Optional[Any] = None
