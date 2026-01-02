"""
API routers for the application.
"""

from fastapi import APIRouter
from app.routers import purchase, purchase_approval, item_catalog, pdf_extraction, whatsapp, auth, inward, ims_auth

api_router = APIRouter()

# Include routers
api_router.include_router(ims_auth.router)  # Authentication system
api_router.include_router(purchase.router)
api_router.include_router(purchase_approval.router)
api_router.include_router(item_catalog.router)
api_router.include_router(pdf_extraction.router)
api_router.include_router(whatsapp.router)
api_router.include_router(auth.router)
api_router.include_router(inward.router)

__all__ = ["api_router", "purchase", "purchase_approval", "item_catalog", "pdf_extraction", "whatsapp", "auth", "inward", "ims_auth"]

