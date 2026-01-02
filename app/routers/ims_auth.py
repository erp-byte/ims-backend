"""
Router for Authentication and Authorization endpoints.
"""

from typing import List
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import (
    get_current_user, get_current_active_user, get_current_superuser,
    create_access_token, check_permission
)
from app.core.config import settings
from app.models.auth import IMSUser
from app.schemas.auth import (
    LoginRequest, LoginResponse, UserCreate, UserUpdate, UserOut, UserWithPermissions,
    UserChangePassword, SetPermissionsRequest, PermissionCheckRequest, PermissionCheckResponse,
    ModuleOut, AllPermissionsOut
)
from app.services import auth as auth_service


router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


# ==================== AUTHENTICATION ENDPOINTS ====================

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    **User Login**

    Authenticate user with username and password.
    Returns JWT access token and user information with permissions.

    **Encryption Algorithm:**
    - Password Hashing: **Bcrypt** (applied on backend)
    - Token Encryption: **HS256** (HMAC with SHA-256)

    **Request Payload:**
    ```json
    {
        "username": "john_doe",
        "password": "plain_password_here"
    }
    ```
    
    **Response Payload:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 108000,
        "user": {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "is_active": true,
            "is_superuser": false,
            "created_at": "2025-11-18T10:30:00Z",
            "updated_at": "2025-11-18T10:30:00Z",
            "last_login": "2025-11-18T10:35:00Z",
            "modules": [
                {
                    "id": 1,
                    "name": "purchase",
                    "display_name": "Purchase",
                    "is_active": true,
                    "created_at": "2025-11-18T10:00:00Z"
                }
            ],
            "permissions": {
                "purchase": {
                    "id": 1,
                    "user_id": 1,
                    "can_create": true,
                    "can_edit": true,
                    "can_approve": false,
                    "can_delete": false,
                    "can_view": true,
                    "created_at": "2025-11-18T10:30:00Z",
                    "updated_at": "2025-11-18T10:30:00Z"
                },
                "transfer": null,
                "rtv": null,
                "sales": null,
                "printing": null
            }
        }
    }
    ```
    """
    user = auth_service.authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    module_names = [m.name for m in user.modules]
    
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "username": user.username,
            "is_superuser": user.is_superuser,
            "modules": module_names
        },
        expires_delta=access_token_expires
    )
    
    # Get user permissions
    permissions = auth_service.get_user_permissions(db, user.id)
    
    # Build response
    user_response = UserWithPermissions(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        modules=[ModuleOut.model_validate(m) for m in user.modules],
        permissions=permissions
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        user=user_response
    )


@router.get("/me", response_model=UserWithPermissions)
async def get_current_user_info(
    current_user: IMSUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    **Get Current User Information**
    
    Get the authenticated user's information including modules and permissions.
    Requires valid JWT token in Authorization header.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Response Payload:**
    ```json
    {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "is_active": true,
        "is_superuser": false,
        "created_at": "2025-11-18T10:30:00Z",
        "updated_at": "2025-11-18T10:30:00Z",
        "last_login": "2025-11-18T10:35:00Z",
        "modules": [...],
        "permissions": {...}
    }
    ```
    """
    permissions = auth_service.get_user_permissions(db, current_user.id)
    
    return UserWithPermissions(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login,
        modules=[ModuleOut.model_validate(m) for m in current_user.modules],
        permissions=permissions
    )


@router.post("/change-password", status_code=200)
async def change_password(
    password_data: UserChangePassword,
    current_user: IMSUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    **Change User Password**

    Change the current user's password. Requires current password for verification.

    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```

    **Request Payload:**
    ```json
    {
        "current_password": "current_plain_password",
        "new_password": "new_plain_password"
    }
    ```
    
    **Response Payload:**
    ```json
    {
        "message": "Password changed successfully"
    }
    ```
    """
    success = auth_service.change_user_password(
        db, current_user, password_data.current_password, password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}


# ==================== USER MANAGEMENT ENDPOINTS (Admin Only) ====================

@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    user_data: UserCreate,
    current_user: IMSUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    **Create New User (Admin Only)**

    Create a new user account with modules. Only superusers can create users.

    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```

    **Request Payload:**
    ```json
    {
        "username": "jane_smith",
        "password": "plain_password_here",
        "email": "jane@example.com",
        "full_name": "Jane Smith",
        "is_active": true,
        "is_superuser": false,
        "module_names": ["purchase", "transfers"]
    }
    ```
    
    **Response Payload:**
    ```json
    {
        "id": 2,
        "username": "jane_smith",
        "email": "jane@example.com",
        "full_name": "Jane Smith",
        "is_active": true,
        "is_superuser": false,
        "created_at": "2025-11-18T11:00:00Z",
        "updated_at": "2025-11-18T11:00:00Z",
        "last_login": null,
        "modules": [...]
    }
    ```
    """
    return auth_service.create_user(db, user_data)


@router.get("/users", response_model=List[UserOut])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: IMSUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    **List All Users (Admin Only)**
    
    Get a list of all users. Only superusers can access this endpoint.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Response Payload:**
    ```json
    [
        {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "is_active": true,
            "is_superuser": false,
            "created_at": "2025-11-18T10:30:00Z",
            "updated_at": "2025-11-18T10:30:00Z",
            "last_login": "2025-11-18T10:35:00Z",
            "modules": [...]
        }
    ]
    ```
    """
    users = auth_service.get_all_users(db, skip, limit)
    return [UserOut.model_validate(u) for u in users]


@router.get("/users/{user_id}", response_model=UserWithPermissions)
async def get_user(
    user_id: int,
    current_user: IMSUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    **Get User by ID (Admin Only)**
    
    Get detailed information about a specific user including permissions.
    Only superusers can access this endpoint.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Response Payload:**
    ```json
    {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "is_active": true,
        "is_superuser": false,
        "created_at": "2025-11-18T10:30:00Z",
        "updated_at": "2025-11-18T10:30:00Z",
        "last_login": "2025-11-18T10:35:00Z",
        "modules": [...],
        "permissions": {...}
    }
    ```
    """
    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    permissions = auth_service.get_user_permissions(db, user.id)
    
    return UserWithPermissions(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        modules=[ModuleOut.model_validate(m) for m in user.modules],
        permissions=permissions
    )


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: IMSUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    **Update User (Admin Only)**
    
    Update user information. Only superusers can update users.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Request Payload:**
    ```json
    {
        "email": "newemail@example.com",
        "full_name": "John Updated Doe",
        "is_active": true,
        "is_superuser": false,
        "module_names": ["purchase", "sales", "printing"]
    }
    ```
    
    **Response Payload:**
    ```json
    {
        "id": 1,
        "username": "john_doe",
        "email": "newemail@example.com",
        "full_name": "John Updated Doe",
        "is_active": true,
        "is_superuser": false,
        "created_at": "2025-11-18T10:30:00Z",
        "updated_at": "2025-11-18T11:45:00Z",
        "last_login": "2025-11-18T10:35:00Z",
        "modules": [...]
    }
    ```
    """
    user = auth_service.update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return UserOut.model_validate(user)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    current_user: IMSUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    **Delete User (Admin Only)**
    
    Delete a user account. Only superusers can delete users.
    Cannot delete yourself.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Response:**
    - 204 No Content on success
    - 404 Not Found if user doesn't exist
    - 400 Bad Request if trying to delete yourself
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    success = auth_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    return None


# ==================== MODULE ENDPOINTS ====================

@router.get("/modules", response_model=List[ModuleOut])
async def list_modules(
    current_user: IMSUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    **List All Modules**
    
    Get a list of all available system modules.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Response Payload:**
    ```json
    [
        {
            "id": 1,
            "name": "purchase",
            "display_name": "Purchase",
            "description": "Purchase Order Management",
            "is_active": true,
            "created_at": "2025-11-18T10:00:00Z"
        },
        {
            "id": 2,
            "name": "transfers",
            "display_name": "Transfers",
            "description": "Inventory Transfer Management",
            "is_active": true,
            "created_at": "2025-11-18T10:00:00Z"
        }
    ]
    ```
    """
    modules = auth_service.get_all_modules(db)
    return [ModuleOut.model_validate(m) for m in modules]


# ==================== PERMISSION MANAGEMENT ENDPOINTS ====================

@router.post("/permissions", status_code=200)
async def set_permissions(
    permission_data: SetPermissionsRequest,
    current_user: IMSUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    **Set User Permissions (Admin Only)**
    
    Set permissions for a user in a specific module. Only superusers can manage permissions.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Request Payload:**
    ```json
    {
        "user_id": 1,
        "module_name": "purchase",
        "permissions": {
            "can_create": true,
            "can_edit": true,
            "can_approve": false,
            "can_delete": false,
            "can_view": true
        }
    }
    ```
    
    **Response Payload:**
    ```json
    {
        "message": "Permissions set successfully for user 1 in module purchase",
        "permissions": {
            "id": 1,
            "user_id": 1,
            "can_create": true,
            "can_edit": true,
            "can_approve": false,
            "can_delete": false,
            "can_view": true,
            "created_at": "2025-11-18T10:30:00Z",
            "updated_at": "2025-11-18T12:00:00Z"
        }
    }
    ```
    """
    # Verify user exists
    user = auth_service.get_user_by_id(db, permission_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {permission_data.user_id} not found"
        )
    
    # Set permissions
    perm = auth_service.set_module_permissions(
        db, permission_data.user_id, permission_data.module_name, permission_data.permissions
    )
    
    return {
        "message": f"Permissions set successfully for user {permission_data.user_id} in module {permission_data.module_name}",
        "permissions": perm
    }


@router.get("/permissions/{user_id}", response_model=AllPermissionsOut)
async def get_user_permissions(
    user_id: int,
    current_user: IMSUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    **Get User Permissions (Admin Only)**
    
    Get all permissions for a specific user across all modules.
    Only superusers can access this endpoint.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Response Payload:**
    ```json
    {
        "purchase": {
            "id": 1,
            "user_id": 1,
            "can_create": true,
            "can_edit": true,
            "can_approve": false,
            "can_delete": false,
            "can_view": true,
            "created_at": "2025-11-18T10:30:00Z",
            "updated_at": "2025-11-18T10:30:00Z"
        },
        "transfer": null,
        "rtv": null,
        "sales": null,
        "printing": null
    }
    ```
    """
    return auth_service.get_user_permissions(db, user_id)


@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_user_permission(
    check_data: PermissionCheckRequest,
    current_user: IMSUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    **Check User Permission**
    
    Check if the current user has a specific permission in a module.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Request Payload:**
    ```json
    {
        "module_name": "purchase",
        "permission": "create"
    }
    ```
    
    **Response Payload:**
    ```json
    {
        "has_permission": true,
        "module_name": "purchase",
        "permission": "create",
        "user_id": 1,
        "username": "john_doe"
    }
    ```
    """
    has_perm = check_permission(current_user, check_data.module_name, check_data.permission)
    
    return PermissionCheckResponse(
        has_permission=has_perm,
        module_name=check_data.module_name,
        permission=check_data.permission,
        user_id=current_user.id,
        username=current_user.username
    )
