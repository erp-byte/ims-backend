"""
Main FastAPI application.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import httpx

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

# Health check URL for Render service
RENDER_HEALTH_URL = "https://ims-backend-ts4y.onrender.com/health"
HEALTH_CHECK_INTERVAL = 300  # 5 minutes in seconds

logger = logging.getLogger(__name__)


async def health_check_task():
    """Background task to ping health endpoint every 5 minutes to keep Render service alive."""
    # Wait 30 seconds after startup before first check (give service time to fully start)
    await asyncio.sleep(30)
    
    # Create HTTP client with appropriate timeout and SSL settings
    timeout = httpx.Timeout(30.0, connect=10.0)  # 30s total, 10s connect
    async with httpx.AsyncClient(
        timeout=timeout,
        verify=True,  # SSL verification
        follow_redirects=True
    ) as client:
        while True:
            try:
                logger.debug(f"Sending health check to: {RENDER_HEALTH_URL}")
                response = await client.get(RENDER_HEALTH_URL)
                
                if response.status_code == 200:
                    logger.info(f"✓ Health check successful: {RENDER_HEALTH_URL} (Status: {response.status_code})")
                else:
                    logger.warning(
                        f"⚠ Health check returned non-200 status: {RENDER_HEALTH_URL} "
                        f"(Status: {response.status_code}, Response: {response.text[:200]})"
                    )
                    
            except httpx.TimeoutException as e:
                logger.error(
                    f"✗ Health check timeout: {RENDER_HEALTH_URL} - "
                    f"Request timed out after {timeout.read} seconds. Error: {str(e)}"
                )
            except httpx.ConnectError as e:
                logger.error(
                    f"✗ Health check connection error: {RENDER_HEALTH_URL} - "
                    f"Could not connect to server. Error: {str(e)}"
                )
            except httpx.HTTPError as e:
                logger.error(
                    f"✗ Health check HTTP error: {RENDER_HEALTH_URL} - "
                    f"HTTP error occurred. Error: {str(e)}"
                )
            except Exception as e:
                logger.error(
                    f"✗ Health check failed: {RENDER_HEALTH_URL} - "
                    f"Unexpected error: {type(e).__name__}: {str(e)}"
                )
                import traceback
                logger.debug(f"Traceback: {traceback.format_exc()}")
            
            # Wait 5 minutes before next check
            await asyncio.sleep(HEALTH_CHECK_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Start background health check task
    logger.info("Starting health check background task...")
    health_task = asyncio.create_task(health_check_task())
    
    yield
    
    # Shutdown: Cancel background task
    logger.info("Stopping health check background task...")
    health_task.cancel()
    try:
        await health_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Candor Foods Inventory Management System API",
    debug=settings.debug,
    lifespan=lifespan,
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

