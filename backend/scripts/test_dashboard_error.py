#!/usr/bin/env python3
"""Quick test to see dashboard error"""
import asyncio
import sys
import httpx
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_async_session_local
from models.client import Client
from sqlalchemy import select

BASE_URL = "http://localhost:8000"

async def test_dashboard():
    # Get client
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Client).filter(Client.is_active == True).limit(1))
        client = result.scalar_one_or_none()
        if not client:
            print("No client found")
            return
    
    # Login
    async with httpx.AsyncClient() as http_client:
        login_resp = await http_client.post(
            f"{BASE_URL}/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if login_resp.status_code != 200:
            print(f"Login failed: {login_resp.status_code} - {login_resp.text}")
            return
        
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test dashboard
        resp = await http_client.get(f"{BASE_URL}/api/v1/dashboard", headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test_dashboard())

