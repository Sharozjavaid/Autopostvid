"""Global error handler to prevent information leakage."""

import logging
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from ..config import get_settings, IS_PRODUCTION

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers on the FastAPI app.
    
    Call this in main.py after creating the app:
        register_error_handlers(app)
    """
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """
        Handle HTTP exceptions with consistent format.
        These are intentional errors (404, 401, 400, etc.)
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
            headers=exc.headers,
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle request validation errors (bad input).
        In production, hide detailed validation errors.
        """
        if IS_PRODUCTION:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid request data"}
            )
        
        # In development, show validation details
        return JSONResponse(
            status_code=400,
            content={
                "error": "Validation error",
                "details": exc.errors()
            }
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        if IS_PRODUCTION:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid request data"}
            )
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "Validation error",
                "details": exc.errors()
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Catch-all handler for unhandled exceptions.
        
        CRITICAL: This prevents stack traces and internal details from
        being exposed to clients in production.
        """
        # Always log the full error internally
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {exc}",
            exc_info=True
        )
        
        if IS_PRODUCTION:
            # Generic message - never expose internal details
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
        
        # In development, show more details for debugging
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc().split("\n")[-5:]
            }
        )
