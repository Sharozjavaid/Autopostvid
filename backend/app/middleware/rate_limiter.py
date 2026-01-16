"""Rate limiting middleware using slowapi."""

import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Create limiter instance using client IP as the key
limiter = Limiter(key_func=get_remote_address)

# Rate limit decorators to use on routes:
# 
# @limiter.limit("100/minute")  - General API endpoints
# @limiter.limit("10/minute")   - Auth-sensitive endpoints
# @limiter.limit("5/minute")    - Heavy operations (image generation)
# @limiter.limit("20/minute")   - Agent/chat endpoints
# @limiter.limit("30/minute")   - CRUD operations


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.
    Returns a clean JSON response instead of the default HTML.
    """
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}: {exc.detail}")
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too many requests",
            "detail": "Rate limit exceeded. Please slow down.",
            "retry_after": exc.detail.split("per")[0].strip() if exc.detail else "1 minute"
        },
        headers={"Retry-After": "60"}
    )


# Common rate limit strings for consistency
RATE_LIMITS = {
    "general": "100/minute",
    "auth": "10/minute",
    "heavy": "5/minute",
    "agent": "20/minute",
    "crud": "60/minute",
    "automations": "30/minute",
    "tiktok": "10/minute",
}
