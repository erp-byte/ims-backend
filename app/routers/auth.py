"""
Router for authentication and company-related endpoints.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/company/{company_name}/dashboard-info")
async def get_company_dashboard_info(company_name: str):
    """
    Get dashboard information for a company.
    TODO: Implement actual dashboard logic
    """
    return {
        "company_name": company_name,
        "total_purchase_orders": 0,
        "total_approvals": 0,
        "pending_approvals": 0,
        "total_items": 0,
        "status": "stub"
    }
