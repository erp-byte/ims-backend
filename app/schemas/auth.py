"""
Pydantic schemas for Authentication and Authorization.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator


# ==================== MODULE SCHEMAS ====================

class ModuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ModuleOut(ModuleBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== PERMISSION SCHEMAS ====================

class PermissionBase(BaseModel):
    can_create: bool = False
    can_edit: bool = False
    can_approve: bool = False
    can_delete: bool = False
    can_view: bool = True


class PurchasePermissionOut(PermissionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransferPermissionOut(PermissionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RTVPermissionOut(PermissionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SalesPermissionOut(PermissionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PrintingPermissionOut(PermissionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AllPermissionsOut(BaseModel):
    """Combined permissions for all modules."""
    purchase: Optional[PurchasePermissionOut] = None
    transfer: Optional[TransferPermissionOut] = None
    rtv: Optional[RTVPermissionOut] = None
    sales: Optional[SalesPermissionOut] = None
    printing: Optional[PrintingPermissionOut] = None


# ==================== USER SCHEMAS ====================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1, max_length=255, description="Plain text password")
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    module_names: List[str] = Field(default_factory=list, description="List of module names: purchase, transfers, rtv, sales, printing")
    
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (with _ and - allowed)')
        return v.lower()


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    module_names: Optional[List[str]] = None


class UserChangePassword(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=255, description="Current plain text password")
    new_password: str = Field(..., min_length=1, max_length=255, description="New plain text password")
    
    @field_validator('new_password')
    @classmethod
    def passwords_different(cls, v: str, info) -> str:
        if 'current_password' in info.data and v == info.data['current_password']:
            raise ValueError('New password must be different from current password')
        return v


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    modules: List[ModuleOut] = []
    
    class Config:
        from_attributes = True


class UserWithPermissions(UserOut):
    """User with all their module permissions."""
    permissions: AllPermissionsOut


# ==================== AUTHENTICATION SCHEMAS ====================

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1, max_length=255, description="Plain text password")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: UserWithPermissions


class TokenData(BaseModel):
    """Data stored in JWT token."""
    user_id: int
    username: str
    is_superuser: bool
    modules: List[str] = []


class SetPermissionsRequest(BaseModel):
    """Request to set permissions for a user in a specific module."""
    user_id: int
    module_name: str = Field(..., description="Module name: purchase, transfers, rtv, sales, printing")
    permissions: PermissionBase
    
    @field_validator('module_name')
    @classmethod
    def validate_module(cls, v: str) -> str:
        valid_modules = ['purchase', 'transfers', 'rtv', 'sales', 'printing']
        if v.lower() not in valid_modules:
            raise ValueError(f'Module must be one of: {", ".join(valid_modules)}')
        return v.lower()


class PermissionCheckRequest(BaseModel):
    """Request to check if user has specific permission."""
    module_name: str
    permission: str = Field(..., description="Permission name: create, edit, approve, delete, view")
    
    @field_validator('permission')
    @classmethod
    def validate_permission(cls, v: str) -> str:
        valid_permissions = ['create', 'edit', 'approve', 'delete', 'view']
        if v.lower() not in valid_permissions:
            raise ValueError(f'Permission must be one of: {", ".join(valid_permissions)}')
        return v.lower()


class PermissionCheckResponse(BaseModel):
    has_permission: bool
    module_name: str
    permission: str
    user_id: int
    username: str
