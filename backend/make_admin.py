#!/usr/bin/env python3
"""
Script to make a user an admin
Usage: python make_admin.py <email>
"""
import sys
from sqlalchemy.orm import Session
from models import get_db, User, UserRole

def make_admin(email: str):
    """Make a user an admin by email"""
    db: Session = next(get_db())
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        print(f"Error: User with email '{email}' not found")
        return False
    
    if user.role == UserRole.ADMIN.value:
        print(f"User '{email}' is already an admin")
        return True
    
    user.role = UserRole.ADMIN.value
    db.commit()
    db.refresh(user)
    
    print(f"Successfully updated user '{email}' to admin role")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <email>")
        print("Example: python make_admin.py test@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    make_admin(email)

