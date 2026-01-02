"""
Authentication and Authorization utilities.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.auth import IMSUser
from app.schemas.auth import TokenData


# HTTP Bearer token security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password_in_db: str) -> bool:
    """
    Verify plain password against stored bcrypt hash in database.

    Args:
        plain_password: Plain text password from frontend
        hashed_password_in_db: Bcrypt hash stored in database

    Returns:
        True if password matches hash, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password_in_db.encode('utf-8')
    )


def get_password_hash(plain_password: str) -> str:
    """
    Hash a plain password using Bcrypt.

    Bcrypt Algorithm Details:
    - Uses Blowfish cipher
    - Includes salt (automatically generated and stored in hash)
    - Cost factor (rounds): 12 by default (2^12 = 4096 iterations)
    - Format: $2b$[cost]$[22 character salt][31 character hash]

    Args:
        plain_password: Plain text password to hash

    Returns:
        Bcrypt hash of the password
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    JWT Algorithm: HS256 (HMAC with SHA-256)
    - Symmetric encryption using a secret key
    - Payload is JSON-encoded and base64url-encoded
    - Signature is created using: HMACSHA256(base64UrlEncode(header) + "." + base64UrlEncode(payload), secret)
    
    Args:
        data: Dictionary containing token data (user_id, username, etc.)
        expires_delta: Optional expiration time delta
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData object with decoded information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: int = payload.get("user_id")
        username: str = payload.get("username")
        is_superuser: bool = payload.get("is_superuser", False)
        modules: list = payload.get("modules", [])
        
        if user_id is None or username is None:
            raise credentials_exception
        
        token_data = TokenData(
            user_id=user_id,
            username=username,
            is_superuser=is_superuser,
            modules=modules
        )
        return token_data
        
    except JWTError:
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> IMSUser:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials (Bearer token)
        db: Database session
        
    Returns:
        IMSUser object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    user = db.query(IMSUser).filter(IMSUser.id == token_data.user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: IMSUser = Depends(get_current_user)
) -> IMSUser:
    """
    Get the current active user (non-disabled).
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active IMSUser object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: IMSUser = Depends(get_current_user)
) -> IMSUser:
    """
    Get the current user and verify they are a superuser.
    
    Args:
        current_user: Current user from token
        
    Returns:
        IMSUser object if superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges. Superuser access required."
        )
    return current_user


def has_module_access(user: IMSUser, module_name: str) -> bool:
    """
    Check if user has access to a specific module.
    
    Args:
        user: IMSUser object
        module_name: Name of the module (purchase, transfers, rtv, sales, printing)
        
    Returns:
        True if user has access to the module, False otherwise
    """
    if user.is_superuser:
        return True
    
    return any(module.name.lower() == module_name.lower() for module in user.modules)


def check_permission(user: IMSUser, module_name: str, permission: str) -> bool:
    """
    Check if user has a specific permission in a module.
    
    Args:
        user: IMSUser object
        module_name: Name of the module
        permission: Permission name (create, edit, approve, delete, view)
        
    Returns:
        True if user has the permission, False otherwise
    """
    if user.is_superuser:
        return True
    
    # Map module names to permission attributes
    permission_map = {
        'purchase': user.purchase_permissions,
        'transfers': user.transfer_permissions,
        'rtv': user.rtv_permissions,
        'sales': user.sales_permissions,
        'printing': user.printing_permissions,
    }
    
    module_permissions = permission_map.get(module_name.lower())
    
    if not module_permissions or len(module_permissions) == 0:
        return False
    
    # Get the first permission record (should only be one per user per module)
    perm_obj = module_permissions[0]
    
    # Map permission names to object attributes
    perm_attr = f"can_{permission.lower()}"
    
    return getattr(perm_obj, perm_attr, False)
