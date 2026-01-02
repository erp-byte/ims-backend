"""
Router for inward inventory/receipt endpoints.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/inward", tags=["Inward Receipts"])


@router.get("/{company_name}")
async def get_inward_receipts(company_name: str):
    """
    Get inward receipts for a company.
    TODO: Implement actual inward receipt logic
    """
    return {
        "company_name": company_name,
        "receipts": [],
        "total_count": 0,
        "status": "stub"
    }
