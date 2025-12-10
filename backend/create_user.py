#!/usr/bin/env python3
"""
Script to create a user (with optional admin role)
Usage: 
    python create_user.py <email> <password> [--name "Name"] [--admin] [--client-id <uuid>]
    python create_user.py test@example.com password123 --name "Test User" --admin
"""
import sys
import asyncio
import argparse
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import User, UserRole, Client
from models.database import get_async_session_local
from auth import get_password_hash


async def create_user_with_role(
    email: str,
    password: str,
    name: str | None = None,
    role: str = UserRole.USER.value,
    client_id: str | None = None
):
    """Create a user with specified role"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        result = await db.execute(select(User).filter(User.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"Error: User with email '{email}' already exists")
            return False
        
        # Get or use default client
        if client_id:
            client_uuid = uuid.UUID(client_id)
        else:
            # Get first active client or create default
            result = await db.execute(
                select(Client).where(Client.is_active == True).limit(1)
            )
            client = result.scalar_one_or_none()
            
            if not client:
                print("Error: No active client found. Please create a client first or specify --client-id")
                return False
            
            client_uuid = client.client_id
        
        # Validate role
        if role not in [UserRole.ADMIN.value, UserRole.USER.value]:
            print(f"Error: Invalid role '{role}'. Must be 'admin' or 'user'")
            return False
        
        # Create user
        hashed_password = get_password_hash(password)
        new_user = User(
            email=email,
            name=name,
            hashed_password=hashed_password,
            client_id=client_uuid,
            role=role,
            is_active=True
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        role_display = "admin" if role == UserRole.ADMIN.value else "user"
        print(f"Successfully created {role_display} user '{email}'")
        print(f"  ID: {new_user.id}")
        print(f"  Name: {new_user.name or 'N/A'}")
        print(f"  Role: {new_user.role}")
        print(f"  Client ID: {new_user.client_id}")
        
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a user with optional admin role")
    parser.add_argument("email", help="User email address")
    parser.add_argument("password", help="User password")
    parser.add_argument("--name", help="User name (optional)")
    parser.add_argument("--admin", action="store_true", help="Create user as admin")
    parser.add_argument("--client-id", help="Client ID (UUID). If not provided, uses first active client")
    
    args = parser.parse_args()
    
    role = UserRole.ADMIN.value if args.admin else UserRole.USER.value
    
    asyncio.run(create_user_with_role(
        email=args.email,
        password=args.password,
        name=args.name,
        role=role,
        client_id=args.client_id
    ))

