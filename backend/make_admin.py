#!/usr/bin/env python3
"""
Script to make a user an admin
Usage: python make_admin.py <email>
"""
import sys
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import AsyncSessionLocal, User, UserRole


async def make_admin(email: str):
    """Make a user an admin by email"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"Error: User with email '{email}' not found")
            return False
        
        if user.role == UserRole.ADMIN.value:
            print(f"User '{email}' is already an admin")
            return True
        
        user.role = UserRole.ADMIN.value
        await db.commit()
        await db.refresh(user)
        
        print(f"Successfully updated user '{email}' to admin role")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <email>")
        print("Example: python make_admin.py test@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    asyncio.run(make_admin(email))
