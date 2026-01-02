"""
Database models for Authentication and Authorization.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Table, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import BIGINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


# Association table for user-module many-to-many relationship
user_modules = Table(
    'user_modules',
    Base.metadata,
    Column('user_id', BIGINT, ForeignKey('ims_users.id', ondelete="CASCADE"), primary_key=True),
    Column('module_id', Integer, ForeignKey('modules.id', ondelete="CASCADE"), primary_key=True),
    Column('created_at', DateTime(timezone=True), nullable=False, server_default=func.now())
)


class IMSUser(Base):
    """IMS User model for authentication."""
    __tablename__ = "ims_users"
    
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # Bcrypt hash
    email = Column(String(255), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    modules = relationship("Module", secondary=user_modules, back_populates="users")
    purchase_permissions = relationship("PurchasePermission", back_populates="user", cascade="all, delete-orphan")
    transfer_permissions = relationship("TransferPermission", back_populates="user", cascade="all, delete-orphan")
    rtv_permissions = relationship("RTVPermission", back_populates="user", cascade="all, delete-orphan")
    sales_permissions = relationship("SalesPermission", back_populates="user", cascade="all, delete-orphan")
    printing_permissions = relationship("PrintingPermission", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_email", "email"),
        Index("idx_user_active", "is_active"),
    )


class Module(Base):
    """Module model representing different system modules."""
    __tablename__ = "modules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)  # purchase, transfers, rtv, sales, printing
    display_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("IMSUser", secondary=user_modules, back_populates="modules")
    
    # Indexes
    __table_args__ = (
        Index("idx_module_name", "name"),
    )


class PurchasePermission(Base):
    """Purchase module permissions."""
    __tablename__ = "purchase_permissions"
    
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey('ims_users.id', ondelete="CASCADE"), nullable=False)
    
    # Permissions
    can_create = Column(Boolean, default=False, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_approve = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)
    can_view = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("IMSUser", back_populates="purchase_permissions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_purchase_permission_user'),
        Index("idx_purchase_perm_user", "user_id"),
    )


class TransferPermission(Base):
    """Transfer module permissions."""
    __tablename__ = "transfer_permissions"
    
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey('ims_users.id', ondelete="CASCADE"), nullable=False)
    
    # Permissions
    can_create = Column(Boolean, default=False, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_approve = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)
    can_view = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("IMSUser", back_populates="transfer_permissions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_transfer_permission_user'),
        Index("idx_transfer_perm_user", "user_id"),
    )


class RTVPermission(Base):
    """RTV (Return to Vendor) module permissions."""
    __tablename__ = "rtv_permissions"
    
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey('ims_users.id', ondelete="CASCADE"), nullable=False)
    
    # Permissions
    can_create = Column(Boolean, default=False, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_approve = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)
    can_view = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("IMSUser", back_populates="rtv_permissions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_rtv_permission_user'),
        Index("idx_rtv_perm_user", "user_id"),
    )


class SalesPermission(Base):
    """Sales module permissions."""
    __tablename__ = "sales_permissions"
    
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey('ims_users.id', ondelete="CASCADE"), nullable=False)
    
    # Permissions
    can_create = Column(Boolean, default=False, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_approve = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)
    can_view = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("IMSUser", back_populates="sales_permissions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_sales_permission_user'),
        Index("idx_sales_perm_user", "user_id"),
    )


class PrintingPermission(Base):
    """Printing module permissions."""
    __tablename__ = "printing_permissions"
    
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey('ims_users.id', ondelete="CASCADE"), nullable=False)
    
    # Permissions
    can_create = Column(Boolean, default=False, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_approve = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)
    can_view = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("IMSUser", back_populates="printing_permissions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_printing_permission_user'),
        Index("idx_printing_perm_user", "user_id"),
    )
