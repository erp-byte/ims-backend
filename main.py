"""
Main FastAPI application.
"""

import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import api_router

# Filter out "Invalid HTTP request received" warnings
class InvalidHTTPFilter(logging.Filter):
    def filter(self, record):
        return "Invalid HTTP request received" not in record.getMessage()

# Apply filter to uvicorn access logger
logging.getLogger("uvicorn.access").addFilter(InvalidHTTPFilter())
logging.getLogger("uvicorn.error").addFilter(InvalidHTTPFilter())


# Middleware to block invalid/malformed requests
class BlockInvalidRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            # Check if request has valid HTTP method
            valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}
            if request.method not in valid_methods:
                return JSONResponse(
                    status_code=405,
                    content={"detail": "Method not allowed"}
                )
            
            # Check if request has valid headers (at minimum)
            if not request.headers:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid request"}
                )
            
            # Process the request
            response = await call_next(request)
            return response
            
        except Exception as e:
            # Block any malformed requests that cause exceptions
            return JSONResponse(
                status_code=400,
                content={"detail": "Bad request"}
            )


# Import all models so they're registered with Base
from app.models import (
    PurchaseOrder,
    POItem,
    POItemBox,
    PurchaseApproval,
    PurchaseApprovalItem,
    PurchaseApprovalBox,
    CFPLItem,
    CDPLItem,
)
from app.models.auth import (
    IMSUser,
    Module,
    PurchasePermission,
    TransferPermission,
    RTVPermission,
    SalesPermission,
    PrintingPermission,
)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Candor Foods Inventory Management System API",
    debug=settings.debug,
)

# Add middleware to block invalid requests (must be first)
app.add_middleware(BlockInvalidRequestsMiddleware)

# CORS middleware
# Note: When allow_origins=["*"], allow_credentials must be False
allow_credentials = settings.cors_allow_credentials and "*" not in settings.cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers with /api prefix
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )

