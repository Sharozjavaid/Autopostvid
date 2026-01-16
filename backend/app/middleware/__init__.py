"""Security middleware for the Philosophy Video Generator API."""

from .auth import verify_api_key, optional_api_key, API_KEY_HEADER
from .rate_limiter import limiter, rate_limit_exceeded_handler
from .error_handler import register_error_handlers
from .security_headers import SecurityHeadersMiddleware

__all__ = [
    "verify_api_key",
    "optional_api_key", 
    "API_KEY_HEADER",
    "limiter",
    "rate_limit_exceeded_handler",
    "register_error_handlers",
    "SecurityHeadersMiddleware",
]
