"""
Database initialization script for authentication system.

Run this script to create the default modules and superuser account.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.services.auth import initialize_modules, create_user
from app.schemas.auth import UserCreate


def init_database():
    """Initialize database with default data."""
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✓ Database tables created successfully")
    
    # Create database session
    db = SessionLocal()
    
    try:
        print("\nInitializing modules...")
        initialize_modules(db)
        print("✓ Modules initialized successfully")
        
        print("\nCreating default superuser...")
        
        # Create default superuser with pre-hashed password
        # Password: admin123 hashed with Bcrypt
        default_admin = UserCreate(
            username="admin",
            password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeUuL.HLtG8a",  # admin123
            email="admin@candorfoods.com",
            full_name="System Administrator",
            is_active=True,
            is_superuser=True,
            module_names=["purchase", "transfers", "rtv", "sales", "printing"]
        )
        
        try:
            admin_user = create_user(db, default_admin)
            print(f"✓ Superuser created: {admin_user.username}")
            print(f"  Email: {admin_user.email}")
            print(f"  Password: admin123 (CHANGE THIS IN PRODUCTION!)")
        except Exception as e:
            print(f"ℹ Superuser already exists or error occurred: {str(e)}")
        
        print("\n" + "=" * 60)
        print("DATABASE INITIALIZATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nDefault Credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\n⚠️  IMPORTANT: Change the default password immediately!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during initialization: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
