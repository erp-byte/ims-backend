"""
Router for Purchase Approval CRUD operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.purchase_approval import (
    PurchaseApprovalCreate,
    PurchaseApprovalUpdate,
    PurchaseApprovalOut,
    PurchaseApprovalWithItemsOut,
)
from app.services import purchase_approval as approval_service

router = APIRouter(prefix="/v1/purchase-approval", tags=["Purchase Approval"])


@router.post("/debug", status_code=200)
async def debug_purchase_approval(request: Request):
    """Debug endpoint to capture raw request data and identify validation issues."""
    import logging
    import json
    from pydantic import ValidationError
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get raw request body
        body = await request.body()
        raw_data = json.loads(body.decode('utf-8'))
        
        logger.info(f"=== RAW REQUEST DEBUG ===")
        logger.info(f"Raw JSON: {json.dumps(raw_data, indent=2)}")
        
        # Try to validate with Pydantic
        try:
            approval_data = PurchaseApprovalCreate(**raw_data)
            return {
                "success": True,
                "message": "Validation successful",
                "data_structure": {
                    "purchase_order_id": raw_data.get("purchase_order_id"),
                    "has_transporter_info": bool(raw_data.get("transporter_information")),
                    "has_customer_info": bool(raw_data.get("customer_information")),
                    "items_count": len(raw_data.get("items", []))
                }
            }
        except ValidationError as ve:
            logger.error(f"Validation errors: {ve.errors()}")
            return {
                "success": False,
                "message": "Validation failed",
                "validation_errors": ve.errors(),
                "raw_data_keys": list(raw_data.keys()),
                "transporter_info": raw_data.get("transporter_information"),
                "items_structure": [
                    {
                        "index": i,
                        "keys": list(item.keys()) if isinstance(item, dict) else "not_dict",
                        "hsn_code_type": type(item.get("hsn_code", None)).__name__ if isinstance(item, dict) else None
                    } for i, item in enumerate(raw_data.get("items", []))
                ]
            }
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        return {
            "success": False,
            "message": "Failed to parse request",
            "error": str(e)
        }


@router.post("/", response_model=PurchaseApprovalWithItemsOut, status_code=201)
async def create_purchase_approval(
    approval_data: PurchaseApprovalCreate,
    db: Session = Depends(get_db)
):
    """Create a new purchase approval with items and boxes."""
    import logging
    from pydantic import ValidationError
    
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Creating purchase approval for PO: {approval_data.purchase_order_id}")
        logger.info(f"Number of items in request: {len(approval_data.items)}")
        
        # Log each item for debugging
        for idx, item in enumerate(approval_data.items):
            logger.info(f"Item {idx}: {item.item_description}, HSN: {item.hsn_code}, Price: {item.price_per_kg}")

        result = approval_service.create_purchase_approval(db, approval_data)

        logger.info(f"Successfully created purchase approval with ID: {result.id}")
        logger.info(f"Number of items saved: {len(result.items)}")

        return result
        
    except ValidationError as ve:
        logger.error(f"Validation error: {ve}")
        logger.error(f"Validation details: {ve.errors()}")
        raise HTTPException(
            status_code=422, 
            detail={
                "message": "Validation failed", 
                "errors": ve.errors(),
                "error_count": len(ve.errors())
            }
        )
    except ValueError as ve:
        logger.error(f"Value error: {str(ve)}")
        raise HTTPException(status_code=400, detail={"message": "Invalid data", "error": str(ve)})
    except Exception as e:
        logger.error(f"Failed to create purchase approval: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"message": "Internal server error", "error": str(e)})


@router.post("/validate", status_code=200)
async def validate_purchase_approval_data(approval_data: dict):
    """Validate purchase approval data structure and identify issues."""
    import logging
    from pydantic import ValidationError
    
    logger = logging.getLogger(__name__)
    
    try:
        # Try to parse with Pydantic model
        parsed_data = PurchaseApprovalCreate(**approval_data)
        
        return {
            "valid": True,
            "message": "Data is valid",
            "purchase_order_id": parsed_data.purchase_order_id,
            "items_count": len(parsed_data.items),
            "parsed_successfully": True
        }
        
    except ValidationError as ve:
        logger.error(f"Validation errors: {ve.errors()}")
        
        return {
            "valid": False,
            "message": "Validation failed",
            "errors": ve.errors(),
            "error_count": len(ve.errors()),
            "raw_data_keys": list(approval_data.keys()) if isinstance(approval_data, dict) else "Not a dict"
        }
    except Exception as e:
        logger.error(f"Unexpected error in validation: {str(e)}")
        
        return {
            "valid": False,
            "message": "Unexpected error during validation",
            "error": str(e),
            "data_type": type(approval_data).__name__
        }


@router.get("/", response_model=List[PurchaseApprovalOut])
async def get_purchase_approvals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    purchase_order_id: Optional[str] = Query(None, description="Filter by purchase order ID"),
    db: Session = Depends(get_db)
):
    """Get all purchase approvals with optional filtering."""
    return approval_service.get_purchase_approvals(db, skip, limit, purchase_order_id)


@router.get("/by-po/{po_id:path}", response_model=List[PurchaseApprovalWithItemsOut])
async def get_approvals_by_po(
    po_id: str,
    db: Session = Depends(get_db)
):
    """Get all purchase approvals by purchase order ID with complete details.

    Note: The po_id parameter supports URL encoding and special characters like '/'.
    Example: CF/PO/2025-26/01477 should be URL encoded as CF%2FPO%2F2025-26%2F01477
    """
    import logging
    import urllib.parse

    logger = logging.getLogger(__name__)

    # URL decode the PO ID to handle special characters like '/'
    decoded_po_id = urllib.parse.unquote(po_id)

    logger.info(f"Looking up purchase approvals for PO: {decoded_po_id} (original: {po_id})")

    approvals = approval_service.get_approvals_by_po_id(db, decoded_po_id)

    logger.info(f"Found {len(approvals)} approval(s) for PO: {decoded_po_id}")
    return approvals


@router.get("/by-purchase-number/{purchase_number:path}", response_model=PurchaseApprovalWithItemsOut)
async def get_purchase_approval_by_number(
    purchase_number: str,
    db: Session = Depends(get_db)
):
    """Get a purchase approval by purchase number with all items and boxes.
    
    Note: The purchase_number parameter supports URL encoding and special characters like '/'.
    Example: CF/PO/2025-26/01478 should be URL encoded as CF%2FPO%2F2025-26%2F01478
    """
    import logging
    import urllib.parse
    
    logger = logging.getLogger(__name__)
    
    # URL decode the purchase number to handle special characters like '/'
    decoded_purchase_number = urllib.parse.unquote(purchase_number)
    
    logger.info(f"Looking up purchase approval for purchase number: {decoded_purchase_number} (original: {purchase_number})")
    
    approval = approval_service.get_purchase_approval_by_purchase_number(db, decoded_purchase_number)
    if not approval:
        logger.warning(f"No purchase approval found for purchase number: {decoded_purchase_number}")
        raise HTTPException(status_code=404, detail=f"Purchase approval not found for purchase number: {decoded_purchase_number}")
    
    logger.info(f"Found purchase approval ID {approval.id} for purchase number {decoded_purchase_number}")
    return approval


@router.get("/{approval_id}", response_model=PurchaseApprovalWithItemsOut)
async def get_purchase_approval(
    approval_id: int,
    db: Session = Depends(get_db)
):
    """Get a purchase approval by ID with all items and boxes."""
    import logging
    import json

    logger = logging.getLogger(__name__)

    approval = approval_service.get_purchase_approval(db, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Purchase approval not found")

    # Log the response for debugging
    logger.info(f"========== APPROVAL {approval_id} RESPONSE ==========")
    logger.info(f"Items count: {len(approval.items)}")

    for idx, item in enumerate(approval.items):
        logger.info(f"Item {idx + 1}:")
        logger.info(f"  - Description: {item.item_description}")
        logger.info(f"  - quantity_units: {item.quantity_units} (type: {type(item.quantity_units).__name__})")
        logger.info(f"  - pack_size: {item.pack_size}")
        logger.info(f"  - net_weight: {item.net_weight}")
        logger.info(f"  - gross_weight: {item.gross_weight}")

    logger.info("====================================================")

    return approval


@router.put("/{approval_id}", response_model=PurchaseApprovalWithItemsOut)
async def update_purchase_approval(
    approval_id: int,
    approval_update: PurchaseApprovalUpdate,
    db: Session = Depends(get_db)
):
    """Update a purchase approval."""
    approval = approval_service.update_purchase_approval(db, approval_id, approval_update)
    if not approval:
        raise HTTPException(status_code=404, detail="Purchase approval not found")
    return approval


@router.get("/box/{box_id}")
async def get_purchase_approval_box(
    box_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific purchase approval box by ID with related item and approval info."""
    box_data = approval_service.get_purchase_approval_box(db, box_id)
    if not box_data:
        raise HTTPException(status_code=404, detail="Purchase approval box not found")
    return box_data


@router.delete("/by-purchase-number/{purchase_number:path}", status_code=204)
async def delete_purchase_approval_by_number(
    purchase_number: str,
    db: Session = Depends(get_db)
):
    """Delete a purchase approval by purchase number."""
    import logging
    import urllib.parse
    
    logger = logging.getLogger(__name__)
    
    # URL decode the purchase number to handle special characters like '/'
    decoded_purchase_number = urllib.parse.unquote(purchase_number)
    
    logger.info(f"Attempting to delete purchase approval for purchase number: {decoded_purchase_number}")
    
    success = approval_service.delete_purchase_approval_by_purchase_number(db, decoded_purchase_number)
    if not success:
        logger.warning(f"No purchase approval found for deletion with purchase number: {decoded_purchase_number}")
        raise HTTPException(status_code=404, detail=f"Purchase approval not found for purchase number: {decoded_purchase_number}")
    
    logger.info(f"Successfully deleted purchase approval for purchase number: {decoded_purchase_number}")
    return None


@router.delete("/by-po/{po_number:path}", status_code=204)
async def delete_purchase_approval_by_po(
    po_number: str,
    db: Session = Depends(get_db)
):
    """Delete a purchase approval by PO number."""
    import logging
    import urllib.parse

    logger = logging.getLogger(__name__)

    # URL decode the PO number to handle special characters like '/'
    decoded_po_number = urllib.parse.unquote(po_number)

    logger.info(f"Attempting to delete purchase approval for PO number: {decoded_po_number}")

    success = approval_service.delete_purchase_approval_by_purchase_number(db, decoded_po_number)
    if not success:
        logger.warning(f"No purchase approval found for deletion with PO number: {decoded_po_number}")
        raise HTTPException(status_code=404, detail=f"Purchase approval not found for PO number: {decoded_po_number}")

    logger.info(f"Successfully deleted purchase approval for PO number: {decoded_po_number}")
    return None


@router.get("/debug/{approval_id}")
async def debug_approval_data(
    approval_id: int,
    db: Session = Depends(get_db)
):
    """Debug endpoint to check raw database values for quantity_units."""
    import logging
    from sqlalchemy import text
    from app.models.purchase_approval import PurchaseApproval, PurchaseApprovalItem

    logger = logging.getLogger(__name__)

    # Get the approval
    db_approval = db.query(PurchaseApproval).filter(PurchaseApproval.id == approval_id).first()
    if not db_approval:
        raise HTTPException(status_code=404, detail="Purchase approval not found")

    # Get items with raw data using ORM
    db_items = db.query(PurchaseApprovalItem).filter(
        PurchaseApprovalItem.approval_id == approval_id
    ).all()

    # Also get raw SQL data to compare
    raw_sql_result = db.execute(
        text("SELECT id, item_description, quantity_units, pack_size, net_weight, gross_weight, uom FROM purchase_approval_items WHERE approval_id = :approval_id"),
        {"approval_id": approval_id}
    ).fetchall()

    debug_info = {
        "approval_id": approval_id,
        "purchase_order_id": db_approval.purchase_order_id,
        "items_count": len(db_items),
        "orm_items": [],
        "raw_sql_items": []
    }

    # ORM data
    for idx, item in enumerate(db_items):
        debug_info["orm_items"].append({
            "index": idx,
            "item_id": item.id,
            "material_type": item.material_type,
            "item_description": item.item_description,
            "quantity_units_raw": str(item.quantity_units) if item.quantity_units is not None else "NULL",
            "quantity_units_type": type(item.quantity_units).__name__,
            "quantity_units_is_none": item.quantity_units is None,
            "quantity_units_value": float(item.quantity_units) if item.quantity_units is not None else None,
            "pack_size": str(item.pack_size) if item.pack_size is not None else "NULL",
            "uom": item.uom,
            "net_weight": str(item.net_weight) if item.net_weight is not None else "NULL",
            "gross_weight": str(item.gross_weight) if item.gross_weight is not None else "NULL",
        })

    # Raw SQL data
    for row in raw_sql_result:
        debug_info["raw_sql_items"].append({
            "id": row[0],
            "item_description": row[1],
            "quantity_units": str(row[2]) if row[2] is not None else "NULL",
            "pack_size": str(row[3]) if row[3] is not None else "NULL",
            "net_weight": str(row[4]) if row[4] is not None else "NULL",
            "gross_weight": str(row[5]) if row[5] is not None else "NULL",
            "uom": row[6]
        })

    logger.info(f"Debug info for approval {approval_id}: {debug_info}")
    return debug_info


@router.post("/fix-null-quantities", status_code=200)
async def fix_null_quantity_units(
    db: Session = Depends(get_db)
):
    """Fix NULL quantity_units in existing purchase approval items by setting them to 0."""
    import logging
    from decimal import Decimal
    from app.models.purchase_approval import PurchaseApprovalItem

    logger = logging.getLogger(__name__)

    # Find all items with NULL quantity_units
    items_with_null = db.query(PurchaseApprovalItem).filter(
        PurchaseApprovalItem.quantity_units == None
    ).all()

    if not items_with_null:
        return {
            "success": True,
            "message": "No items with NULL quantity_units found",
            "updated_count": 0
        }

    updated_count = 0
    updated_items = []

    for item in items_with_null:
        item.quantity_units = Decimal('0.000')
        updated_count += 1
        updated_items.append({
            "item_id": item.id,
            "approval_id": item.approval_id,
            "item_description": item.item_description,
            "old_value": "NULL",
            "new_value": "0.000"
        })

    db.commit()

    logger.info(f"Fixed {updated_count} items with NULL quantity_units")

    return {
        "success": True,
        "message": f"Successfully updated {updated_count} items",
        "updated_count": updated_count,
        "updated_items": updated_items
    }


