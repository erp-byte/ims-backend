"""
Service layer for Purchase Order CRUD operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.models.purchase import PurchaseOrder, POItem, POItemBox
from app.schemas.purchase import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderOut,
    Party,
    PurchaseOrderInfo,
    FinancialSummary,
    ItemCreate,
    ItemUpdate,
    ItemOut,
    BoxCreate,
    BoxUpdate,
    BoxOut,
)


# ==================== Helper Functions ====================

def _db_po_to_schema(db_po: PurchaseOrder) -> PurchaseOrderOut:
    """Convert database PurchaseOrder to PurchaseOrderOut schema."""
    return PurchaseOrderOut(
        id=db_po.id,
        company_name=db_po.company_name,
        purchase_number=db_po.purchase_number,
        purchase_order=PurchaseOrderInfo(
            po_number=db_po.po_number,
            po_date=db_po.po_date,
            po_validity=db_po.po_validity,
            currency=db_po.currency,
        ),
        buyer=Party(
            name=db_po.buyer_name,
            address=db_po.buyer_address,
            gstin=db_po.buyer_gstin,
            state=db_po.buyer_state,
        ),
        supplier=Party(
            name=db_po.supplier_name,
            address=db_po.supplier_address,
            gstin=db_po.supplier_gstin,
            state=db_po.supplier_state,
        ),
        ship_to=Party(
            name=db_po.ship_to_name,
            address=db_po.ship_to_address,
            gstin=None,  # Database doesn't have separate field for ship_to gstin
            state=db_po.ship_to_state,
        ),
        freight_by=db_po.freight_by,
        dispatch_by=db_po.dispatch_by,
        indentor=db_po.indentor,
        financial_summary=FinancialSummary(
            sub_total=db_po.sub_total,
            igst=db_po.igst,
            other_charges_non_gst=db_po.other_charges_non_gst,
            grand_total=db_po.grand_total,
        ),
        created_at=db_po.created_at,
        updated_at=db_po.updated_at,
    )


def _db_item_to_schema(db_item: POItem) -> ItemOut:
    """Convert database POItem to ItemOut schema."""
    return ItemOut(
        id=db_item.id,
        purchase_order_id=db_item.purchase_order_id,
        sr_no=db_item.sr_no,
        material_type=db_item.material_type,
        item_category=db_item.item_category,
        sub_category=db_item.sub_category,
        item_description=db_item.item_description,
        hsn_code=db_item.hsn_code,
        net_weight_kg=db_item.net_weight_kg,
        price_per_kg=db_item.price_per_kg,
        taxable_value=db_item.taxable_value,
        gst_percentage=db_item.gst_percentage,
        created_at=db_item.created_at,
        updated_at=db_item.updated_at,
    )


def _db_box_to_schema(db_box: POItemBox) -> BoxOut:
    """Convert database POItemBox to BoxOut schema."""
    return BoxOut(
        id=db_box.id,
        po_item_id=db_box.po_item_id,
        box_no=db_box.box_no,
        qty_units=db_box.qty_units,
        net_weight_kg=db_box.net_weight_kg,
        gross_weight_kg=db_box.gross_weight_kg,
        remarks=db_box.remarks,
        created_at=db_box.created_at,
    )


# ==================== PURCHASE ORDER (Header) CRUD ====================

def create_purchase_order(db: Session, po_data: PurchaseOrderCreate) -> PurchaseOrderOut:
    """Create a new purchase order."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Creating purchase order with data: {po_data.model_dump()}")

        # Flatten the nested structure for database storage
        db_po = PurchaseOrder(
            company_name=po_data.company_name,
            purchase_number=po_data.purchase_number,
            po_number=po_data.purchase_order.po_number,
            po_date=po_data.purchase_order.po_date,
            po_validity=po_data.purchase_order.po_validity,
            currency=po_data.purchase_order.currency,

            # Buyer
            buyer_name=po_data.buyer.name,
            buyer_address=po_data.buyer.address,
            buyer_gstin=po_data.buyer.gstin,
            buyer_state=po_data.buyer.state,

            # Supplier
            supplier_name=po_data.supplier.name,
            supplier_address=po_data.supplier.address,
            supplier_gstin=po_data.supplier.gstin,
            supplier_state=po_data.supplier.state,

            # Ship-to
            ship_to_name=po_data.ship_to.name,
            ship_to_address=po_data.ship_to.address,
            ship_to_state=po_data.ship_to.state,

            # Additional info
            freight_by=po_data.freight_by,
            dispatch_by=po_data.dispatch_by,
            indentor=po_data.indentor,

            # Financial summary
            sub_total=po_data.financial_summary.sub_total,
            igst=po_data.financial_summary.igst,
            other_charges_non_gst=po_data.financial_summary.other_charges_non_gst,
            grand_total=po_data.financial_summary.grand_total,
        )

        db.add(db_po)
        db.commit()
        db.refresh(db_po)

        logger.info(f"Successfully created purchase order with ID: {db_po.id}")
        return _db_po_to_schema(db_po)

    except Exception as e:
        logger.error(f"Error creating purchase order: {str(e)}", exc_info=True)
        db.rollback()
        raise


def get_purchase_order(db: Session, po_id: int) -> Optional[PurchaseOrderOut]:
    """Get a purchase order by ID."""
    db_po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not db_po:
        return None
    return _db_po_to_schema(db_po)


def get_purchase_order_by_po_number(db: Session, po_number: str) -> Optional[PurchaseOrderOut]:
    """Get a purchase order by PO number."""
    import logging
    import urllib.parse
    
    logger = logging.getLogger(__name__)
    
    # URL decode the PO number to handle special characters like '/'
    decoded_po_number = urllib.parse.unquote(po_number)
    
    logger.info(f"Looking up purchase order for PO number: {decoded_po_number} (original: {po_number})")
    
    db_po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == decoded_po_number).first()
    if not db_po:
        logger.warning(f"No purchase order found for PO number: {decoded_po_number}")
        return None
    
    logger.info(f"Found purchase order ID {db_po.id} for PO number {decoded_po_number}")
    return _db_po_to_schema(db_po)


def get_purchase_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    company_name: Optional[str] = None
) -> List[PurchaseOrderOut]:
    """Get all purchase orders with optional filtering."""
    query = db.query(PurchaseOrder)
    
    if company_name:
        query = query.filter(PurchaseOrder.company_name == company_name)
    
    db_pos = query.order_by(desc(PurchaseOrder.created_at)).offset(skip).limit(limit).all()
    return [_db_po_to_schema(db_po) for db_po in db_pos]


def update_purchase_order(
    db: Session,
    po_id: int,
    po_update: PurchaseOrderUpdate
) -> Optional[PurchaseOrderOut]:
    """Update a purchase order."""
    db_po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not db_po:
        return None
    
    # Handle nested updates
    if po_update.purchase_order:
        po_info = po_update.purchase_order
        if po_info.po_number:
            db_po.po_number = po_info.po_number
        if po_info.po_date:
            db_po.po_date = po_info.po_date
        if po_info.po_validity is not None:
            db_po.po_validity = po_info.po_validity
        if po_info.currency:
            db_po.currency = po_info.currency
    
    if po_update.buyer:
        buyer = po_update.buyer
        if buyer.name:
            db_po.buyer_name = buyer.name
        if buyer.address is not None:
            db_po.buyer_address = buyer.address
        if buyer.gstin is not None:
            db_po.buyer_gstin = buyer.gstin
        if buyer.state is not None:
            db_po.buyer_state = buyer.state
    
    if po_update.supplier:
        supplier = po_update.supplier
        if supplier.name:
            db_po.supplier_name = supplier.name
        if supplier.address is not None:
            db_po.supplier_address = supplier.address
        if supplier.gstin is not None:
            db_po.supplier_gstin = supplier.gstin
        if supplier.state is not None:
            db_po.supplier_state = supplier.state
    
    if po_update.ship_to:
        ship_to = po_update.ship_to
        if ship_to.name:
            db_po.ship_to_name = ship_to.name
        if ship_to.address is not None:
            db_po.ship_to_address = ship_to.address
        if ship_to.state is not None:
            db_po.ship_to_state = ship_to.state
        # Note: ship_to.gstin is not stored in database (no ship_to_gstin field)
    
    # Update financial summary
    if po_update.financial_summary:
        fs = po_update.financial_summary
        if fs.sub_total:
            db_po.sub_total = fs.sub_total
        if fs.igst is not None:
            db_po.igst = fs.igst
        if fs.other_charges_non_gst is not None:
            db_po.other_charges_non_gst = fs.other_charges_non_gst
        if fs.grand_total:
            db_po.grand_total = fs.grand_total
    
    # Handle simple fields
    if po_update.freight_by is not None:
        db_po.freight_by = po_update.freight_by
    if po_update.dispatch_by is not None:
        db_po.dispatch_by = po_update.dispatch_by
    if po_update.indentor is not None:
        db_po.indentor = po_update.indentor
    
    db_po.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_po)
    return _db_po_to_schema(db_po)


def delete_purchase_order(db: Session, po_id: int) -> bool:
    """Delete a purchase order."""
    db_po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not db_po:
        return False
    
    db.delete(db_po)
    db.commit()
    return True


def get_complete_purchase_data(db: Session, purchase_number: str, box_id: Optional[int] = None) -> Optional[dict]:
    """
    Get complete purchase data including order, approval, items, and boxes in one call.
    
    Args:
        db: Database session
        purchase_number: Purchase number (like "PR-20251105155654")
        box_id: Optional box ID to filter boxes and related items to specific box only
        
    Returns:
        Dictionary containing all purchase-related data or None if purchase not found
    """
    import logging
    from sqlalchemy.exc import OperationalError
    import time
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"Getting complete purchase data for purchase number: {purchase_number}")
    
    # Step 1: Get Purchase Order by purchase_number with retry logic
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            db_po = db.query(PurchaseOrder).filter(PurchaseOrder.purchase_number == purchase_number).first()
            break  # Success, exit retry loop
        except OperationalError as e:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Database connection failed after {max_retries} attempts")
                raise
    if not db_po:
        logger.warning(f"Purchase order not found for purchase number: {purchase_number}")
        return None
    
    purchase_order = _db_po_to_schema(db_po)
    logger.info(f"Found purchase order ID {db_po.id} with PO number: {db_po.po_number}")
    
    # Step 2: Get Purchase Approval using the PO number (may not exist)
    approval_data = None
    items_count = 0
    boxes_count = 0
    
    try:
        # Import here to avoid circular imports
        from app.services import purchase_approval as approval_service
        
        # Use the PO number to find approval (approval table stores po_number in purchase_order_id field)
        approval_data = approval_service.get_purchase_approval_by_purchase_number(db, db_po.po_number)
        
        if approval_data:
            # If box_id is specified, filter approval data to only include that box and its related item
            if box_id is not None:
                logger.info(f"Filtering approval data for box_id: {box_id}")
                logger.info(f"Total items in approval: {len(approval_data.items) if approval_data.items else 0}")
                
                # Debug: Log all available box IDs
                all_box_ids = []
                for item_idx, item in enumerate(approval_data.items or []):
                    logger.info(f"Item index: {item_idx}, boxes count: {len(item.boxes) if item.boxes else 0}")
                    for box in item.boxes or []:
                        all_box_ids.append(box.box_id)
                        logger.info(f"  Box ID: {box.box_id}, box_number: {getattr(box, 'box_number', 'N/A')}")
                
                logger.info(f"All available box IDs: {all_box_ids}")
                logger.info(f"Looking for box_id: {box_id} (type: {type(box_id)})")
                
                # Find the box and its parent item
                target_box = None
                target_item = None
                target_item_idx = None
                
                for item_idx, item in enumerate(approval_data.items or []):
                    for box in item.boxes or []:
                        logger.info(f"Comparing box.box_id={box.box_id} (type: {type(box.box_id)}) with box_id={box_id} (type: {type(box_id)})")
                        if box.box_id == box_id:
                            target_box = box
                            target_item = item
                            target_item_idx = item_idx
                            logger.info(f"FOUND matching box! Box ID: {box.box_id}, Item index: {item_idx}")
                            break
                    if target_box:
                        break
                
                if target_box and target_item and target_item_idx is not None:
                    logger.info(f"Successfully found target box {target_box.box_id} in item index {target_item_idx}")
                    # Create filtered approval data with only the target item and box
                    filtered_item = type(target_item)(
                        **{**target_item.dict(), 'boxes': [target_box]}
                    )
                    
                    approval_data = type(approval_data)(
                        **{**approval_data.dict(), 'items': [filtered_item]}
                    )
                    
                    items_count = 1
                    boxes_count = 1
                    logger.info(f"Filtered to specific box {box_id}: 1 item, 1 box")
                else:
                    logger.warning(f"Box with ID {box_id} not found in approval data. Available box IDs: {all_box_ids}")
                    # Keep original approval data but note the box wasn't found
                    items_count = len(approval_data.items) if approval_data.items else 0
                    boxes_count = sum(len(item.boxes) for item in approval_data.items) if approval_data.items else 0
            else:
                # Normal case - show all items and boxes
                items_count = len(approval_data.items) if approval_data.items else 0
                boxes_count = sum(len(item.boxes) for item in approval_data.items) if approval_data.items else 0
                logger.info(f"Found approval with {items_count} items and {boxes_count} boxes")
        else:
            logger.info(f"No approval found for PO: {db_po.po_number}")
            
    except Exception as e:
        logger.error(f"Error fetching approval data: {str(e)}")
        approval_data = None
    
    # Step 3: Build complete response
    complete_data = {
        "purchase_order": purchase_order.dict() if hasattr(purchase_order, 'dict') else purchase_order,
        "approval": approval_data.dict() if approval_data and hasattr(approval_data, 'dict') else approval_data,
        "has_approval": approval_data is not None,
        "items_count": items_count,
        "boxes_count": boxes_count,
        "summary": {
            "purchase_number": purchase_number,
            "po_number": db_po.po_number,
            "po_id": purchase_order.id if purchase_order else None,
            "approval_id": approval_data.id if approval_data else None,
            "company_name": purchase_order.company_name if purchase_order else None,
            "supplier_name": purchase_order.supplier.name if purchase_order and purchase_order.supplier else None,
            "buyer_name": purchase_order.buyer.name if purchase_order and purchase_order.buyer else None,
            "grn_number": approval_data.customer_information.grn_number if approval_data and approval_data.customer_information else None,
            "total_items": items_count,
            "total_boxes": boxes_count,
            "filtered_by_box_id": box_id,
            "is_filtered": box_id is not None,
        }
    }
    
    filter_msg = f" (filtered by box_id: {box_id})" if box_id else ""
    logger.info(f"Returning complete purchase data for purchase number: {purchase_number}{filter_msg}")
    return complete_data


# ==================== PURCHASE ORDER ITEMS CRUD ====================

def create_po_item(db: Session, item_data: ItemCreate) -> ItemOut:
    """Create a new purchase order item."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Creating PO item with data: {item_data.model_dump()}")

        # Verify purchase order exists
        po_exists = db.query(PurchaseOrder).filter(PurchaseOrder.id == item_data.purchase_order_id).first()
        if not po_exists:
            logger.error(f"Purchase order with ID {item_data.purchase_order_id} not found")
            raise ValueError(f"Purchase order with ID {item_data.purchase_order_id} does not exist")

        db_item = POItem(
            purchase_order_id=item_data.purchase_order_id,
            sr_no=item_data.sr_no,
            material_type=item_data.material_type,
            item_category=item_data.item_category,
            sub_category=item_data.sub_category,
            item_description=item_data.item_description,
            hsn_code=item_data.hsn_code,
            net_weight_kg=item_data.net_weight_kg,
            price_per_kg=item_data.price_per_kg,
            taxable_value=item_data.taxable_value,
            gst_percentage=item_data.gst_percentage,
        )

        db.add(db_item)
        db.commit()
        db.refresh(db_item)

        logger.info(f"Successfully created PO item with ID: {db_item.id}")
        return _db_item_to_schema(db_item)

    except Exception as e:
        logger.error(f"Error creating PO item: {str(e)}", exc_info=True)
        db.rollback()
        raise


def get_po_item(db: Session, item_id: int) -> Optional[ItemOut]:
    """Get a purchase order item by ID."""
    db_item = db.query(POItem).filter(POItem.id == item_id).first()
    if not db_item:
        return None
    return _db_item_to_schema(db_item)


def get_po_items_by_po(
    db: Session,
    purchase_order_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[ItemOut]:
    """Get all items for a purchase order."""
    db_items = (
        db.query(POItem)
        .filter(POItem.purchase_order_id == purchase_order_id)
        .order_by(POItem.sr_no)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_db_item_to_schema(db_item) for db_item in db_items]


def update_po_item(
    db: Session,
    item_id: int,
    item_update: ItemUpdate
) -> Optional[ItemOut]:
    """Update a purchase order item."""
    db_item = db.query(POItem).filter(POItem.id == item_id).first()
    if not db_item:
        return None
    
    update_data = item_update.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_item, field, value)
    
    db_item.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_item)
    return _db_item_to_schema(db_item)


def delete_po_item(db: Session, item_id: int) -> bool:
    """Delete a purchase order item."""
    db_item = db.query(POItem).filter(POItem.id == item_id).first()
    if not db_item:
        return False
    
    db.delete(db_item)
    db.commit()
    return True


# ==================== BOX MANAGEMENT CRUD ====================

def create_box(db: Session, box_data: BoxCreate) -> BoxOut:
    """Create a new box."""
    db_box = POItemBox(
        po_item_id=box_data.po_item_id,
        box_no=box_data.box_no,
        qty_units=box_data.qty_units,
        net_weight_kg=box_data.net_weight_kg,
        gross_weight_kg=box_data.gross_weight_kg,
        remarks=box_data.remarks,
    )
    
    db.add(db_box)
    db.commit()
    db.refresh(db_box)
    return _db_box_to_schema(db_box)


def get_box(db: Session, box_id: int) -> Optional[BoxOut]:
    """Get a box by ID."""
    db_box = db.query(POItemBox).filter(POItemBox.id == box_id).first()
    if not db_box:
        return None
    return _db_box_to_schema(db_box)


def get_boxes_by_item(
    db: Session,
    po_item_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[BoxOut]:
    """Get all boxes for a purchase order item."""
    db_boxes = (
        db.query(POItemBox)
        .filter(POItemBox.po_item_id == po_item_id)
        .order_by(POItemBox.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_db_box_to_schema(db_box) for db_box in db_boxes]


def update_box(
    db: Session,
    box_id: int,
    box_update: BoxUpdate
) -> Optional[BoxOut]:
    """Update a box."""
    db_box = db.query(POItemBox).filter(POItemBox.id == box_id).first()
    if not db_box:
        return None
    
    update_data = box_update.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_box, field, value)
    
    db.commit()
    db.refresh(db_box)
    return _db_box_to_schema(db_box)


def delete_box(db: Session, box_id: int) -> bool:
    """Delete a box."""
    db_box = db.query(POItemBox).filter(POItemBox.id == box_id).first()
    if not db_box:
        return False
    
    db.delete(db_box)
    db.commit()
    return True


# ==================== SEARCH FUNCTIONALITY ====================

def _parse_flexible_date(date_str: str) -> Optional[str]:
    """
    Parse date string in various formats and return database-compatible format (YYYY-MM-DD).
    
    Supports formats:
    - 2/9/25, 2-9-25, 2/9/2025, 2-9-2025
    - 09/02/2025, 09-02-2025
    - 2025-09-02, 2025/09/02
    - And many other common formats
    """
    import re
    from datetime import datetime
    
    if not date_str:
        return None
    
    # Try common date patterns manually with regex
    patterns = [
        # MM/DD/YY or M/D/YY
        (r'^(\d{1,2})/(\d{1,2})/(\d{2})$', lambda m: f"20{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),
        # MM-DD-YY or M-D-YY
        (r'^(\d{1,2})-(\d{1,2})-(\d{2})$', lambda m: f"20{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),
        # MM/DD/YYYY or M/D/YYYY
        (r'^(\d{1,2})/(\d{1,2})/(\d{4})$', lambda m: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),
        # MM-DD-YYYY or M-D-YYYY
        (r'^(\d{1,2})-(\d{1,2})-(\d{4})$', lambda m: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),
        # YYYY/MM/DD
        (r'^(\d{4})/(\d{1,2})/(\d{1,2})$', lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"),
        # YYYY-MM-DD (already correct format)
        (r'^(\d{4})-(\d{1,2})-(\d{1,2})$', lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"),
        # DD/MM/YY or D/M/YY (European format)
        (r'^(\d{1,2})/(\d{1,2})/(\d{2})$', lambda m: f"20{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"),
        # DD-MM-YYYY or D-M-YYYY (European format)
        (r'^(\d{1,2})-(\d{1,2})-(\d{4})$', lambda m: f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"),
    ]
    
    for pattern, formatter in patterns:
        match = re.match(pattern, date_str.strip())
        if match:
            try:
                formatted = formatter(match)
                # Validate it's a real date
                datetime.strptime(formatted, "%Y-%m-%d")
                return formatted
            except:
                continue
    
    return None


def search_purchases(
    db: Session,
    keyword: str,
    skip: int = 0
) -> dict:
    """
    Search across all purchase-related tables with case-insensitive matching.
    
    Searches in:
    - purchase_orders
    - purchase_approvals (via purchase_order_id/po_number)
    - purchase_approval_items
    - purchase_approval_boxes
    
    Returns:
        Dictionary with search results including:
        - results: List of matching purchase orders with relevance info
        - total_results: Total number of matches
        - search_keyword: The keyword searched
        - parsed_date: If keyword was interpreted as date
    """
    import logging
    from sqlalchemy import or_, and_, func, cast, String
    from sqlalchemy.orm import joinedload
    
    logger = logging.getLogger(__name__)
    
    # Import approval models
    from app.models.purchase_approval import (
        PurchaseApproval,
        PurchaseApprovalItem,
        PurchaseApprovalBox
    )
    
    # Parse potential date from keyword
    parsed_date = _parse_flexible_date(keyword)
    
    # Case-insensitive search pattern
    search_pattern = f"%{keyword.lower()}%"
    
    logger.info(f"Search keyword: {keyword}, Pattern: {search_pattern}, Parsed date: {parsed_date}")
    
    # Collect all matching PO IDs from different sources
    matching_po_ids = set()
    match_details = {}  # po_id -> list of match reasons
    
    # 1. Search in purchase_orders table
    po_conditions = [
        func.lower(PurchaseOrder.po_number).like(search_pattern),
        func.lower(PurchaseOrder.purchase_number).like(search_pattern),
        func.lower(PurchaseOrder.buyer_name).like(search_pattern),
        func.lower(PurchaseOrder.supplier_name).like(search_pattern),
        func.lower(PurchaseOrder.company_name).like(search_pattern),
        func.lower(PurchaseOrder.ship_to_name).like(search_pattern),
        func.lower(cast(PurchaseOrder.buyer_gstin, String)).like(search_pattern),
        func.lower(cast(PurchaseOrder.supplier_gstin, String)).like(search_pattern),
        func.lower(cast(PurchaseOrder.freight_by, String)).like(search_pattern),
        func.lower(cast(PurchaseOrder.dispatch_by, String)).like(search_pattern),
        func.lower(cast(PurchaseOrder.indentor, String)).like(search_pattern),
    ]
    
    # Add date searches if date was parsed
    if parsed_date:
        po_conditions.extend([
            cast(PurchaseOrder.po_date, String) == parsed_date,
            cast(PurchaseOrder.po_validity, String) == parsed_date,
        ])
    
    pos_from_orders = db.query(PurchaseOrder.id, PurchaseOrder.po_number).filter(
        or_(*po_conditions)
    ).all()
    
    for po_id, po_number in pos_from_orders:
        matching_po_ids.add(po_id)
        if po_id not in match_details:
            match_details[po_id] = []
        match_details[po_id].append({"table": "purchase_orders", "po_number": po_number})
    
    logger.info(f"Found {len(pos_from_orders)} matches in purchase_orders")
    
    # 2. Search in purchase_approvals table
    approval_conditions = [
        func.lower(cast(PurchaseApproval.vehicle_number, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.transporter_name, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.lr_number, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.destination_location, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.customer_name, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.authority, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.challan_number, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.invoice_number, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.grn_number, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.grn_quantity, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.delivery_note_number, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.service_po_number, String)).like(search_pattern),
        func.lower(cast(PurchaseApproval.purchase_order_id, String)).like(search_pattern),
    ]
    
    approvals = db.query(PurchaseApproval.purchase_order_id).filter(
        or_(*approval_conditions)
    ).all()
    
    # Map po_number to po_id
    for (po_number,) in approvals:
        po = db.query(PurchaseOrder.id, PurchaseOrder.po_number).filter(
            PurchaseOrder.po_number == po_number
        ).first()
        if po:
            po_id, po_num = po
            matching_po_ids.add(po_id)
            if po_id not in match_details:
                match_details[po_id] = []
            match_details[po_id].append({"table": "purchase_approvals", "po_number": po_num})
    
    logger.info(f"Found {len(approvals)} matches in purchase_approvals")
    
    # 3. Search in purchase_approval_items table
    item_conditions = [
        func.lower(cast(PurchaseApprovalItem.material_type, String)).like(search_pattern),
        func.lower(cast(PurchaseApprovalItem.item_category, String)).like(search_pattern),
        func.lower(cast(PurchaseApprovalItem.sub_category, String)).like(search_pattern),
        func.lower(cast(PurchaseApprovalItem.item_description, String)).like(search_pattern),
        func.lower(cast(PurchaseApprovalItem.lot_number, String)).like(search_pattern),
        func.lower(cast(PurchaseApprovalItem.uom, String)).like(search_pattern),
    ]
    
    # Add date searches for items
    if parsed_date:
        item_conditions.extend([
            cast(PurchaseApprovalItem.mfg_date, String) == parsed_date,
            cast(PurchaseApprovalItem.exp_date, String) == parsed_date,
        ])
    
    items = db.query(PurchaseApprovalItem.approval_id).filter(
        or_(*item_conditions)
    ).all()
    
    # Get approval IDs, then map to PO numbers
    for (approval_id,) in items:
        approval = db.query(PurchaseApproval.purchase_order_id).filter(
            PurchaseApproval.id == approval_id
        ).first()
        if approval:
            po_number = approval[0]
            po = db.query(PurchaseOrder.id, PurchaseOrder.po_number).filter(
                PurchaseOrder.po_number == po_number
            ).first()
            if po:
                po_id, po_num = po
                matching_po_ids.add(po_id)
                if po_id not in match_details:
                    match_details[po_id] = []
                match_details[po_id].append({"table": "purchase_approval_items", "po_number": po_num})
    
    logger.info(f"Found {len(items)} matches in purchase_approval_items")
    
    # 4. Search in purchase_approval_boxes table
    box_conditions = [
        func.lower(cast(PurchaseApprovalBox.box_number, String)).like(search_pattern),
        func.lower(cast(PurchaseApprovalBox.article_name, String)).like(search_pattern),
        func.lower(cast(PurchaseApprovalBox.lot_number, String)).like(search_pattern),
    ]
    
    boxes = db.query(PurchaseApprovalBox.item_id).filter(
        or_(*box_conditions)
    ).all()
    
    # Get item IDs, then approval IDs, then PO numbers
    for (item_id,) in boxes:
        item = db.query(PurchaseApprovalItem.approval_id).filter(
            PurchaseApprovalItem.id == item_id
        ).first()
        if item:
            approval_id = item[0]
            approval = db.query(PurchaseApproval.purchase_order_id).filter(
                PurchaseApproval.id == approval_id
            ).first()
            if approval:
                po_number = approval[0]
                po = db.query(PurchaseOrder.id, PurchaseOrder.po_number).filter(
                    PurchaseOrder.po_number == po_number
                ).first()
                if po:
                    po_id, po_num = po
                    matching_po_ids.add(po_id)
                    if po_id not in match_details:
                        match_details[po_id] = []
                    match_details[po_id].append({"table": "purchase_approval_boxes", "po_number": po_num})
    
    logger.info(f"Found {len(boxes)} matches in purchase_approval_boxes")
    
    # Get total count
    total_results = len(matching_po_ids)
    
    # Fetch only unique purchase numbers (all results, no pagination)
    if matching_po_ids:
        po_ids_list = sorted(list(matching_po_ids), reverse=True)  # Most recent first
        
        purchase_numbers = db.query(PurchaseOrder.purchase_number).filter(
            PurchaseOrder.id.in_(po_ids_list)
        ).order_by(PurchaseOrder.id.desc()).all()
        
        # Extract unique purchase numbers
        results = list(set([pn[0] for pn in purchase_numbers]))
        # Sort to maintain consistent order (most recent would be based on ID, but we just have the numbers now)
        results.sort(reverse=True)
    else:
        results = []
    
    return {
        "results": results,
        "total_results": total_results,
        "search_keyword": keyword,
        "parsed_date": parsed_date,
    }


def search_by_date_range(
    db: Session,
    start_date: str,
    end_date: str,
    skip: int = 0
) -> dict:
    """
    Search purchase approvals by created_at date range.
    
    Args:
        db: Database session
        start_date: Start date in flexible format (e.g., "2/9/25", "2025-09-02")
        end_date: End date in flexible format (e.g., "2/9/25", "2025-09-02")
        skip: Number of results to skip (for pagination)
    
    Returns:
        Dictionary with search results including:
        - results: List of unique purchase numbers
        - total_results: Total number of matches
        - start_date: Parsed start date
        - end_date: Parsed end date
    """
    import logging
    from datetime import datetime, timedelta
    from sqlalchemy import and_
    
    logger = logging.getLogger(__name__)
    
    # Import approval models
    from app.models.purchase_approval import PurchaseApproval
    
    # Parse dates
    parsed_start = _parse_flexible_date(start_date)
    parsed_end = _parse_flexible_date(end_date)
    
    if not parsed_start:
        raise ValueError(f"Invalid start_date format: {start_date}. Please use formats like 2/9/25, 2025-09-02, etc.")
    
    if not parsed_end:
        raise ValueError(f"Invalid end_date format: {end_date}. Please use formats like 2/9/25, 2025-09-02, etc.")
    
    logger.info(f"Searching approvals from {parsed_start} to {parsed_end}")
    
    # Convert to datetime objects for comparison
    # Start date at 00:00:00
    start_datetime = datetime.strptime(parsed_start, "%Y-%m-%d")
    # End date at 23:59:59.999999 to include the entire day
    end_datetime = datetime.strptime(parsed_end, "%Y-%m-%d") + timedelta(days=1, microseconds=-1)
    
    # Query purchase_approvals by created_at date range
    approvals = db.query(PurchaseApproval.purchase_order_id).filter(
        and_(
            PurchaseApproval.created_at >= start_datetime,
            PurchaseApproval.created_at <= end_datetime
        )
    ).all()
    
    logger.info(f"Found {len(approvals)} approvals in date range")
    
    # Get unique PO numbers from approvals
    po_numbers = list(set([approval[0] for approval in approvals]))
    
    # Map PO numbers to purchase numbers
    unique_purchase_numbers = set()
    
    for po_number in po_numbers:
        po = db.query(PurchaseOrder.purchase_number).filter(
            PurchaseOrder.po_number == po_number
        ).first()
        if po:
            unique_purchase_numbers.add(po[0])
    
    # Convert to sorted list
    results = sorted(list(unique_purchase_numbers), reverse=True)
    
    logger.info(f"Found {len(results)} unique purchase numbers")
    
    return {
        "results": results,
        "total_results": len(results),
        "start_date": parsed_start,
        "end_date": parsed_end,
        "date_range": f"{parsed_start} to {parsed_end}",
    }
