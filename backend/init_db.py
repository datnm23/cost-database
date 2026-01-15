#!/usr/bin/env python3
"""
Initialize database with admin user and seed data.
Run this script to create the admin user if it doesn't exist.
"""

from app.core.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from passlib.context import CryptContext
import sys

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_admin_user():
    """Create admin user if it doesn't exist."""
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            print("✓ Admin user already exists")
            print(f"  Username: {admin.username}")
            print(f"  Email: {admin.email}")
            print(f"  Role: {admin.role}")
            print(f"  Active: {admin.is_active}")
            return True
        else:
            # Create admin user
            print("Creating admin user...")
            hashed_password = pwd_context.hash("admin123")
            admin = User(
                username="admin",
                email="admin@boqsystem.com",
                full_name="System Administrator",
                hashed_password=hashed_password,
                role=UserRole.super_admin,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
            print("✓ Admin user created successfully!")
            print(f"  Username: admin")
            print(f"  Password: admin123")
            print(f"  Email: {admin.email}")
            print(f"  Role: {admin.role}")
            return True
            
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False


def main():
    """Main initialization function."""
    print("=" * 60)
    print("BOQ System - Database Initialization")
    print("=" * 60)
    print()
    
    # Create tables
    if not create_tables():
        sys.exit(1)
    
    print()
    
    # Create admin user
    if not init_admin_user():
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✓ Database initialization complete!")
    print("=" * 60)
    print()
    print("You can now login with:")
    print("  Username: admin")
    print("  Password: admin123")
    print()


if __name__ == "__main__":
    main()
