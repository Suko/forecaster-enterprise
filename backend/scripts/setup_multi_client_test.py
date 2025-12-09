"""
Setup Multi-Client Testing Environment

Creates a second client and test data for multi-client isolation testing.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from models.client import Client
from models.user import User
from config import settings


async def main():
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Check existing clients
        result = await db.execute(select(Client))
        existing_clients = result.scalars().all()
        
        print("=" * 80)
        print("MULTI-CLIENT TEST SETUP")
        print("=" * 80)
        print(f"\nExisting clients: {len(existing_clients)}")
        
        if len(existing_clients) >= 2:
            print("✅ Already have 2+ clients")
            for i, client in enumerate(existing_clients[:2], 1):
                print(f"   Client {i}: {client.client_id} ({client.name or 'Unnamed'})")
            return
        
        # Create second client if needed
        if len(existing_clients) == 1:
            print("\n📦 Creating second client for testing...")
            
            client1 = existing_clients[0]
            
            # Create client 2
            client2 = Client(
                name="Test Client 2",
                is_active=True
            )
            db.add(client2)
            await db.commit()
            await db.refresh(client2)
            
            print(f"✅ Created Client 2: {client2.client_id}")
            
            # Create a test user for client 2
            import uuid
            from models.user import UserRole
            
            user2 = User(
                id=str(uuid.uuid4()),
                email=f"test_user2_{datetime.now().strftime('%Y%m%d')}@test.com",
                name="Test User 2",
                hashed_password="hashed_test_password",  # In real scenario, properly hash this
                client_id=client2.client_id,
                is_active=True,
                role=UserRole.USER.value
            )
            db.add(user2)
            await db.commit()
            
            print(f"✅ Created User 2: {user2.email} (Client: {client2.client_id})")
            
            # Check if we need to import some test data for client 2
            # Check if client 2 has any SKUs
            result = await db.execute(
                text("""
                    SELECT COUNT(*) as count
                    FROM sku_classifications
                    WHERE client_id = :client_id
                """),
                {"client_id": str(client2.client_id)}
            )
            row = result.fetchone()
            sku_count = row.count if row else 0
            
            if sku_count == 0:
                print("\n⚠️  Client 2 has no SKUs")
                print("   To test multi-client isolation, you may want to:")
                print("   1. Import some test data for Client 2")
                print("   2. Or use existing Client 1 data to verify isolation")
            else:
                print(f"\n✅ Client 2 has {sku_count} SKUs")
            
            print("\n" + "=" * 80)
            print("SETUP COMPLETE")
            print("=" * 80)
            print("\nYou can now run multi-client isolation tests:")
            print("   python scripts/test_production_readiness.py")
            print("=" * 80)
        
        elif len(existing_clients) == 0:
            print("❌ No clients found in database")
            print("   Please create at least one client first")
            return


if __name__ == "__main__":
    asyncio.run(main())

