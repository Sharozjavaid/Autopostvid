"""API Key authentication middleware."""

import logging
from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from ..config import get_settings

logger = logging.getLogger(__name__)

# API Key header - auto_error=False allows us to handle missing keys gracefully
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Verify the API key is valid.
    
    Use this as a dependency on protected routes:
        @router.get("/protected", dependencies=[Depends(verify_api_key)])
    
    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    settings = get_settings()
    
    # If no API key is configured, allow all requests (development mode)
    if not settings.api_key:
        logger.warning("No API_KEY configured - authentication disabled")
        return "dev-mode"
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != settings.api_key:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


async def optional_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> Optional[str]:
    """
    Optional API key verification - doesn't raise if missing.
    
    Use for routes that work differently for authenticated vs anonymous users.
    Returns the API key if valid, None otherwise.
    """
    settings = get_settings()
    
    if not settings.api_key or not api_key:
        return None
    
    if api_key == settings.api_key:
        return api_key
    
    return None
