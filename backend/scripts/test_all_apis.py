#!/usr/bin/env python3
"""
Comprehensive API Test Script

Tests all inventory management APIs created in Phases 1-4:
- Phase 1 & 2: Inventory APIs (Products, Dashboard)
- Phase 3: Order Planning & Purchase Orders
- Phase 4: Settings

Usage:
    uv run python scripts/test_all_apis.py [--client-id <uuid>]
"""
import asyncio
import sys
import json
from pathlib import Path
from typing import Optional
from uuid import UUID
import httpx

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from models.database import get_async_session_local
from models.client import Client
from models.user import User
from auth.security import get_password_hash


BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"
TEST_USER_NAME = "Test User"


async def create_test_user(client_id: UUID) -> Optional[str]:
    """Create a test user and return auth token"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        # Check if user exists
        result = await session.execute(
            select(User).filter(User.email == TEST_EMAIL)
        )
        user = result.scalar_one_or_none()

        # Ensure user has client_id and correct password
        if user:
            if user.client_id != client_id:
                user.client_id = client_id
            hashed_password = get_password_hash(TEST_PASSWORD)
            user.hashed_password = hashed_password
            user.is_active = True
            await session.commit()
            print(f"✅ Updated user with client_id: {TEST_EMAIL}")

        # Try to register/login via API
        async with httpx.AsyncClient() as client:
            # Try registration first (in case user doesn't exist)
            register_response = await client.post(
                f"{BASE_URL}/api/v1/auth/register",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "full_name": TEST_USER_NAME,
                    "client_id": str(client_id)
                }
            )
            if register_response.status_code in [200, 201]:
                print(f"✅ Registered test user: {TEST_EMAIL}")
            # Ignore if user already exists

            # Login using form data (OAuth2PasswordRequestForm)
            login_response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                data={
                    "username": TEST_EMAIL,  # OAuth2 uses 'username' for email
                    "password": TEST_PASSWORD
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if login_response.status_code == 200:
                data = login_response.json()
                return data.get("access_token")
            else:
                print(f"❌ Failed to login: {login_response.status_code} - {login_response.text}")
                return None


async def get_client_id() -> Optional[UUID]:
    """Get the first active client ID"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Client).filter(Client.is_active == True).limit(1)
        )
        client = result.scalar_one_or_none()
        if client:
            return client.client_id
        return None


class APITester:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.results = {
            "passed": [],
            "failed": [],
            "skipped": []
        }

    async def test(self, method: str, endpoint: str, data: Optional[dict] = None,
                   expected_status: int = 200, description: str = ""):
        """Test an API endpoint"""
        url = f"{BASE_URL}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=self.headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unknown method: {method}")

                status_ok = response.status_code == expected_status
                status_icon = "✅" if status_ok else "❌"

                print(f"{status_icon} {method} {endpoint}")
                if description:
                    print(f"   {description}")

                if status_ok:
                    self.results["passed"].append(f"{method} {endpoint}")
                    if response.status_code == 200 and response.content:
                        try:
                            result = response.json()
                            if isinstance(result, dict) and len(result) > 0:
                                print(f"   Response keys: {list(result.keys())[:5]}")
                        except:
                            pass
                else:
                    self.results["failed"].append(f"{method} {endpoint}")
                    print(f"   Expected {expected_status}, got {response.status_code}")
                    if response.text:
                        print(f"   Error: {response.text[:200]}")

                return response
            except Exception as e:
                print(f"❌ {method} {endpoint} - Exception: {str(e)}")
                self.results["failed"].append(f"{method} {endpoint}")
                return None

    async def test_products(self):
        """Test Products API"""
        print("\n" + "="*60)
        print("TESTING: Products API")
        print("="*60)

        # List products
        response = await self.test("GET", "/api/v1/products",
                                  description="List all products")
        products_data = None
        if response and response.status_code == 200:
            products_data = response.json()
            if "items" in products_data and len(products_data["items"]) > 0:
                item_id = products_data["items"][0]["item_id"]

                # Get product details
                await self.test("GET", f"/api/v1/products/{item_id}",
                               description="Get product details")

                # Get product metrics
                await self.test("GET", f"/api/v1/products/{item_id}/metrics",
                               description="Get product metrics")

                # Get product suppliers
                suppliers_response = await self.test("GET",
                    f"/api/v1/products/{item_id}/suppliers",
                    description="Get product suppliers")

                # If we have suppliers, test update/delete
                if suppliers_response and suppliers_response.status_code == 200:
                    suppliers_data = suppliers_response.json()
                    if "suppliers" in suppliers_data and len(suppliers_data["suppliers"]) > 0:
                        supplier_id = suppliers_data["suppliers"][0]["supplier_id"]

                        # Update supplier
                        await self.test("PUT",
                            f"/api/v1/products/{item_id}/suppliers/{supplier_id}",
                            data={"moq": 100, "lead_time_days": 5},
                            description="Update supplier conditions")

        return products_data

    async def test_dashboard(self):
        """Test Dashboard API"""
        print("\n" + "="*60)
        print("TESTING: Dashboard API")
        print("="*60)

        await self.test("GET", "/api/v1/dashboard",
                       description="Get dashboard KPIs and top products")

    async def test_cart(self):
        """Test Cart API"""
        print("\n" + "="*60)
        print("TESTING: Cart API")
        print("="*60)

        # Get products first to get an item_id
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/products",
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                if "items" in data and len(data["items"]) > 0:
                    item_id = data["items"][0]["item_id"]
                    supplier_id = None

                    # Get suppliers for this product
                    suppliers_resp = await client.get(
                        f"{BASE_URL}/api/v1/products/{item_id}/suppliers",
                        headers=self.headers
                    )
                    if suppliers_resp.status_code == 200:
                        suppliers_data = suppliers_resp.json()
                        if "suppliers" in suppliers_data and len(suppliers_data["suppliers"]) > 0:
                            supplier_id = suppliers_data["suppliers"][0]["supplier_id"]

                    # Add to cart
                    cart_data = {
                        "item_id": item_id,
                        "quantity": 50,
                        "supplier_id": supplier_id
                    }
                    await self.test("POST", "/api/v1/order-planning/cart/add",
                                   data=cart_data,
                                   description="Add item to cart")

                    # Get cart
                    await self.test("GET", "/api/v1/order-planning/cart",
                                   description="Get cart items")

                    # Update cart item
                    await self.test("PUT", f"/api/v1/order-planning/cart/{item_id}",
                                   data={"quantity": 75},
                                   description="Update cart item quantity")

                    # Remove from cart
                    await self.test("DELETE", f"/api/v1/order-planning/cart/{item_id}",
                                   description="Remove item from cart")

    async def test_suggestions(self):
        """Test Order Suggestions API"""
        print("\n" + "="*60)
        print("TESTING: Order Suggestions API")
        print("="*60)

        await self.test("GET", "/api/v1/order-planning/suggestions",
                       description="Get order suggestions")

    async def test_recommendations(self):
        """Test Recommendations API"""
        print("\n" + "="*60)
        print("TESTING: Recommendations API")
        print("="*60)

        # Get all recommendations
        response = await self.test("GET", "/api/v1/recommendations",
                                   description="Get all recommendations")

        # Get filtered recommendations
        await self.test("GET", "/api/v1/recommendations?type=REORDER",
                       description="Get REORDER recommendations")

        await self.test("GET", "/api/v1/recommendations?role=PROCUREMENT",
                       description="Get PROCUREMENT role recommendations")

        # If we have recommendations, test dismiss
        if response and response.status_code == 200:
            data = response.json()
            if "recommendations" in data and len(data["recommendations"]) > 0:
                rec_id = data["recommendations"][0]["id"]
                await self.test("POST", f"/api/v1/recommendations/{rec_id}/dismiss",
                               description="Dismiss recommendation")

    async def test_purchase_orders(self):
        """Test Purchase Orders API"""
        print("\n" + "="*60)
        print("TESTING: Purchase Orders API")
        print("="*60)

        # Get products and suppliers first
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/products",
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                if "items" in data and len(data["items"]) > 0:
                    item_id = data["items"][0]["item_id"]
                    supplier_id = None

                    # Get suppliers
                    suppliers_resp = await client.get(
                        f"{BASE_URL}/api/v1/products/{item_id}/suppliers",
                        headers=self.headers
                    )
                    if suppliers_resp.status_code == 200:
                        suppliers_data = suppliers_resp.json()
                        if "suppliers" in suppliers_data and len(suppliers_data["suppliers"]) > 0:
                            supplier_id = suppliers_data["suppliers"][0]["supplier_id"]

                    if supplier_id:
                        # Create PO from items
                        po_data = {
                            "items": [
                                {
                                    "item_id": item_id,
                                    "quantity": 100,
                                    "supplier_id": supplier_id
                                }
                            ],
                            "notes": "Test purchase order"
                        }
                        po_response = await self.test("POST", "/api/v1/purchase-orders",
                                                     data=po_data,
                                                     description="Create purchase order")

                        # List purchase orders
                        await self.test("GET", "/api/v1/purchase-orders",
                                       description="List purchase orders")

                        # If PO was created, get details and update status
                        if po_response and po_response.status_code == 201:
                            po_data_resp = po_response.json()
                            if "id" in po_data_resp:
                                po_id = po_data_resp["id"]

                                # Get PO details
                                await self.test("GET", f"/api/v1/purchase-orders/{po_id}",
                                               description="Get purchase order details")

                                # Update PO status
                                await self.test("PUT", f"/api/v1/purchase-orders/{po_id}/status",
                                               data={"status": "confirmed"},
                                               description="Update PO status to confirmed")

    async def test_settings(self):
        """Test Settings API"""
        print("\n" + "="*60)
        print("TESTING: Settings API")
        print("="*60)

        # Get settings
        await self.test("GET", "/api/v1/settings",
                       description="Get client settings")

        # Update settings
        update_data = {
            "dir_threshold_days": 30,
            "stockout_risk_threshold": 0.3,
            "overstock_threshold_multiplier": 2.0
        }
        await self.test("PUT", "/api/v1/settings",
                       data=update_data,
                       description="Update client settings")

        # Get recommendation rules
        await self.test("GET", "/api/v1/settings/recommendation-rules",
                       description="Get recommendation rules")

        # Update recommendation rules
        rules_data = {
            "show_dead_stock": True,
            "show_stockout_risks": True,
            "show_overstocked": True
        }
        await self.test("PUT", "/api/v1/settings/recommendation-rules",
                       data=rules_data,
                       description="Update recommendation rules")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✅ Passed: {len(self.results['passed'])}")
        print(f"❌ Failed: {len(self.results['failed'])}")
        print(f"⏭️  Skipped: {len(self.results['skipped'])}")

        if self.results['failed']:
            print("\nFailed tests:")
            for test in self.results['failed']:
                print(f"  - {test}")


async def main():
    """Main test function"""
    print("="*60)
    print("COMPREHENSIVE API TEST SUITE")
    print("="*60)

    # Get client ID
    client_id = await get_client_id()
    if not client_id:
        print("❌ No active client found. Please run setup_test_data.py first.")
        return

    print(f"✅ Using client ID: {client_id}")

    # Create test user and get token
    token = await create_test_user(client_id)
    if not token:
        print("❌ Failed to create/get auth token")
        return

    print(f"✅ Auth token obtained")

    # Run tests
    tester = APITester(token)

    await tester.test_products()
    await tester.test_dashboard()
    await tester.test_cart()
    await tester.test_suggestions()
    await tester.test_recommendations()
    await tester.test_purchase_orders()
    await tester.test_settings()

    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
