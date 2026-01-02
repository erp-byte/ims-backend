"""
Service layer for Authentication and Authorization operations.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.auth import (
    IMSUser, Module, PurchasePermission, TransferPermission,
    RTVPermission, SalesPermission, PrintingPermission
)
from app.schemas.auth import (
    UserCreate, UserUpdate, UserOut, UserWithPermissions,
    PermissionBase, AllPermissionsOut, TokenData
)
from app.core.auth import get_password_hash, verify_password, create_access_token
from app.core.config import settings


def create_user(db: Session, user_data: UserCreate) -> IMSUser:
    """
    Create a new user with hashed password.
    
    Args:
        db: Database session
        user_data: User creation data
        
    Returns:
        Created IMSUser object
        
    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username exists
    existing_user = db.query(IMSUser).filter(IMSUser.username == user_data.username.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' already exists"
        )
    
    # Check if email exists (if provided)
    if user_data.email:
        existing_email = db.query(IMSUser).filter(IMSUser.email == user_data.email.lower()).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_data.email}' already exists"
            )
    
    # Hash the password
    password_hash = get_password_hash(user_data.password)
    
    # Create user
    db_user = IMSUser(
        username=user_data.username.lower(),
        password_hash=password_hash,
        email=user_data.email.lower() if user_data.email else None,
        full_name=user_data.full_name,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser,
    )
    
    # Assign modules
    if user_data.module_names:
        for module_name in user_data.module_names:
            module = db.query(Module).filter(Module.name == module_name.lower()).first()
            if module:
                db_user.modules.append(module)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def authenticate_user(db: Session, username: str, plain_password: str) -> Optional[IMSUser]:
    """
    Authenticate a user with username and plain password.

    Args:
        db: Database session
        username: Username
        plain_password: Plain text password from frontend

    Returns:
        IMSUser object if authentication successful, None otherwise
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Login attempt - Username: '{username}', Password length: {len(plain_password)}")

    user = db.query(IMSUser).filter(IMSUser.username == username.lower()).first()

    if not user:
        logger.warning(f"User not found: '{username}'")
        return None

    logger.info(f"User found: {user.username}, checking password...")
    logger.info(f"Stored hash: {user.password_hash}")
    password_match = verify_password(plain_password, user.password_hash)
    logger.info(f"Password verification result: {password_match}")

    if not password_match:
        return None

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[IMSUser]:
    """Get user by ID."""
    return db.query(IMSUser).filter(IMSUser.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[IMSUser]:
    """Get user by username."""
    return db.query(IMSUser).filter(IMSUser.username == username.lower()).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[IMSUser]:
    """Get all users with pagination."""
    return db.query(IMSUser).offset(skip).limit(limit).all()


def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[IMSUser]:
    """
    Update user information.
    
    Args:
        db: Database session
        user_id: User ID
        user_data: User update data
        
    Returns:
        Updated IMSUser object or None if not found
    """
    user = db.query(IMSUser).filter(IMSUser.id == user_id).first()
    
    if not user:
        return None
    
    # Update fields
    if user_data.email is not None:
        user.email = user_data.email.lower()
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.is_superuser is not None:
        user.is_superuser = user_data.is_superuser
    
    # Update modules
    if user_data.module_names is not None:
        user.modules.clear()
        for module_name in user_data.module_names:
            module = db.query(Module).filter(Module.name == module_name.lower()).first()
            if module:
                user.modules.append(module)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """
    Delete a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        True if deleted, False if not found
    """
    user = db.query(IMSUser).filter(IMSUser.id == user_id).first()
    
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    
    return True


def change_user_password(db: Session, user: IMSUser, current_password: str, new_password: str) -> bool:
    """
    Change user password.

    Args:
        db: Database session
        user: IMSUser object
        current_password: Current plain text password for verification
        new_password: New plain text password to set

    Returns:
        True if password changed, False if current password is incorrect
    """
    if not verify_password(current_password, user.password_hash):
        return False

    user.password_hash = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    return True


# ==================== MODULE OPERATIONS ====================

def get_all_modules(db: Session) -> List[Module]:
    """Get all modules."""
    return db.query(Module).filter(Module.is_active == True).all()


def get_module_by_name(db: Session, module_name: str) -> Optional[Module]:
    """Get module by name."""
    return db.query(Module).filter(Module.name == module_name.lower()).first()


def initialize_modules(db: Session):
    """Initialize default modules if they don't exist."""
    default_modules = [
        {"name": "purchase", "display_name": "Purchase", "description": "Purchase Order Management"},
        {"name": "transfers", "display_name": "Transfers", "description": "Inventory Transfer Management"},
        {"name": "rtv", "display_name": "RTV", "description": "Return to Vendor Management"},
        {"name": "sales", "display_name": "Sales", "description": "Sales Order Management"},
        {"name": "printing", "display_name": "Printing", "description": "Label and Document Printing"},
    ]
    
    for mod_data in default_modules:
        existing = db.query(Module).filter(Module.name == mod_data["name"]).first()
        if not existing:
            module = Module(**mod_data)
            db.add(module)
    
    db.commit()


# ==================== PERMISSION OPERATIONS ====================

def set_purchase_permissions(db: Session, user_id: int, permissions: PermissionBase) -> PurchasePermission:
    """Set purchase permissions for a user."""
    # Check if permissions already exist
    existing = db.query(PurchasePermission).filter(PurchasePermission.user_id == user_id).first()
    
    if existing:
        # Update existing permissions
        existing.can_create = permissions.can_create
        existing.can_edit = permissions.can_edit
        existing.can_approve = permissions.can_approve
        existing.can_delete = permissions.can_delete
        existing.can_view = permissions.can_view
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new permissions
        perm = PurchasePermission(
            user_id=user_id,
            can_create=permissions.can_create,
            can_edit=permissions.can_edit,
            can_approve=permissions.can_approve,
            can_delete=permissions.can_delete,
            can_view=permissions.can_view,
        )
        db.add(perm)
        db.commit()
        db.refresh(perm)
        return perm


def set_transfer_permissions(db: Session, user_id: int, permissions: PermissionBase) -> TransferPermission:
    """Set transfer permissions for a user."""
    existing = db.query(TransferPermission).filter(TransferPermission.user_id == user_id).first()
    
    if existing:
        existing.can_create = permissions.can_create
        existing.can_edit = permissions.can_edit
        existing.can_approve = permissions.can_approve
        existing.can_delete = permissions.can_delete
        existing.can_view = permissions.can_view
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        perm = TransferPermission(
            user_id=user_id,
            can_create=permissions.can_create,
            can_edit=permissions.can_edit,
            can_approve=permissions.can_approve,
            can_delete=permissions.can_delete,
            can_view=permissions.can_view,
        )
        db.add(perm)
        db.commit()
        db.refresh(perm)
        return perm


def set_rtv_permissions(db: Session, user_id: int, permissions: PermissionBase) -> RTVPermission:
    """Set RTV permissions for a user."""
    existing = db.query(RTVPermission).filter(RTVPermission.user_id == user_id).first()
    
    if existing:
        existing.can_create = permissions.can_create
        existing.can_edit = permissions.can_edit
        existing.can_approve = permissions.can_approve
        existing.can_delete = permissions.can_delete
        existing.can_view = permissions.can_view
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        perm = RTVPermission(
            user_id=user_id,
            can_create=permissions.can_create,
            can_edit=permissions.can_edit,
            can_approve=permissions.can_approve,
            can_delete=permissions.can_delete,
            can_view=permissions.can_view,
        )
        db.add(perm)
        db.commit()
        db.refresh(perm)
        return perm


def set_sales_permissions(db: Session, user_id: int, permissions: PermissionBase) -> SalesPermission:
    """Set sales permissions for a user."""
    existing = db.query(SalesPermission).filter(SalesPermission.user_id == user_id).first()
    
    if existing:
        existing.can_create = permissions.can_create
        existing.can_edit = permissions.can_edit
        existing.can_approve = permissions.can_approve
        existing.can_delete = permissions.can_delete
        existing.can_view = permissions.can_view
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        perm = SalesPermission(
            user_id=user_id,
            can_create=permissions.can_create,
            can_edit=permissions.can_edit,
            can_approve=permissions.can_approve,
            can_delete=permissions.can_delete,
            can_view=permissions.can_view,
        )
        db.add(perm)
        db.commit()
        db.refresh(perm)
        return perm


def set_printing_permissions(db: Session, user_id: int, permissions: PermissionBase) -> PrintingPermission:
    """Set printing permissions for a user."""
    existing = db.query(PrintingPermission).filter(PrintingPermission.user_id == user_id).first()
    
    if existing:
        existing.can_create = permissions.can_create
        existing.can_edit = permissions.can_edit
        existing.can_approve = permissions.can_approve
        existing.can_delete = permissions.can_delete
        existing.can_view = permissions.can_view
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        perm = PrintingPermission(
            user_id=user_id,
            can_create=permissions.can_create,
            can_edit=permissions.can_edit,
            can_approve=permissions.can_approve,
            can_delete=permissions.can_delete,
            can_view=permissions.can_view,
        )
        db.add(perm)
        db.commit()
        db.refresh(perm)
        return perm


def set_module_permissions(db: Session, user_id: int, module_name: str, permissions: PermissionBase):
    """Set permissions for a user in a specific module."""
    module_permission_map = {
        'purchase': set_purchase_permissions,
        'transfers': set_transfer_permissions,
        'rtv': set_rtv_permissions,
        'sales': set_sales_permissions,
        'printing': set_printing_permissions,
    }
    
    setter_func = module_permission_map.get(module_name.lower())
    if not setter_func:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid module name: {module_name}"
        )
    
    return setter_func(db, user_id, permissions)


def get_user_permissions(db: Session, user_id: int) -> AllPermissionsOut:
    """Get all permissions for a user."""
    user = db.query(IMSUser).filter(IMSUser.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    return AllPermissionsOut(
        purchase=user.purchase_permissions[0] if user.purchase_permissions else None,
        transfer=user.transfer_permissions[0] if user.transfer_permissions else None,
        rtv=user.rtv_permissions[0] if user.rtv_permissions else None,
        sales=user.sales_permissions[0] if user.sales_permissions else None,
        printing=user.printing_permissions[0] if user.printing_permissions else None,
    )
