#!/usr/bin/env python3
"""
Script to list all users in the database
Usage: python list_users.py [--test-only]
"""
import asyncio
import argparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from models import User, UserRole
from models.database import get_async_session_local


async def list_users(test_only: bool = False):
    """List all users in the database"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as db:
        if test_only:
            # Filter for test users (emails containing 'test' or 'example.com')
            result = await db.execute(
                select(User).filter(
                    or_(
                        User.email.contains('test'),
                        User.email.contains('example.com')
                    )
                ).order_by(User.email)
            )
        else:
            result = await db.execute(select(User).order_by(User.email))

        users = result.scalars().all()

        if not users:
            print("No users found" + (" matching test criteria" if test_only else ""))
            return

        print(f"\nFound {len(users)} user(s):\n")
        print(f"{'Email':<40} {'Name':<30} {'Role':<10} {'Active':<8} {'Client ID':<40}")
        print("-" * 130)

        for user in users:
            print(f"{user.email:<40} {str(user.name or 'N/A'):<30} {user.role:<10} {str(user.is_active):<8} {str(user.client_id):<40}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List users in the database")
    parser.add_argument("--test-only", action="store_true", help="Only show test users (emails with 'test' or 'example.com')")

    args = parser.parse_args()
    asyncio.run(list_users(test_only=args.test_only))

