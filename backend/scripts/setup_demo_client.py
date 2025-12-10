#!/usr/bin/env python3
"""
Setup Demo Client with Test Data

One-command script to create a demo client and import test data.
Perfect for development and demo environments.

Usage:
    uv run python backend/scripts/setup_demo_client.py \
        [--name "Demo Client"] \
        [--csv data/synthetic_data/synthetic_ecom_chronos2_demo.csv]
"""
import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional
import uuid

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_async_session_local
from models.client import Client
from sqlalchemy import select
import importlib.util

# Import the import function from the other script
spec = importlib.util.spec_from_file_location(
    "import_csv",
    Path(__file__).parent / "import_csv_to_ts_demand_daily.py"
)
import_csv_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(import_csv_module)
import_csv_to_ts_demand_daily = import_csv_module.import_csv_to_ts_demand_daily


async def create_demo_client(name: str = "Demo Client") -> str:
    """
    Create a demo client in the database
    
    Returns:
        client_id (UUID string)
    """
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        # Check if client with this name already exists
        result = await session.execute(
            select(Client).where(Client.name == name)
        )
        existing_client = result.scalar_one_or_none()
        
        if existing_client:
            print(f"Client '{name}' already exists with ID: {existing_client.client_id}")
            return str(existing_client.client_id)
        
        # Create new client
        new_client = Client(
            name=name,
            timezone="UTC",
            currency="EUR",
            is_active=True
        )
        session.add(new_client)
        await session.commit()
        await session.refresh(new_client)
        
        print(f"Created client '{name}' with ID: {new_client.client_id}")
        return str(new_client.client_id)


async def setup_demo(
    client_name: str = "Demo Client",
    csv_path: Optional[Path] = None,
    clear_existing: bool = False
) -> dict:
    """
    Complete demo setup: create client + import test data
    
    Returns:
        dict with setup results
    """
    # Default CSV path
    if csv_path is None:
        base_path = Path(__file__).parent.parent.parent
        csv_path = base_path / "data" / "synthetic_data" / "synthetic_ecom_chronos2_demo.csv"
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    print("="*60)
    print("Setting up Demo Client")
    print("="*60)
    
    # Step 1: Create client
    print(f"\n1. Creating client: {client_name}")
    client_id = await create_demo_client(client_name)
    
    # Step 2: Import test data
    print(f"\n2. Importing test data from: {csv_path}")
    import_result = await import_csv_to_ts_demand_daily(
        csv_path=csv_path,
        client_id=client_id,
        clear_existing=clear_existing
    )
    
    return {
        'client_id': client_id,
        'client_name': client_name,
        'import_result': import_result
    }


async def main():
    parser = argparse.ArgumentParser(
        description='Setup demo client with test data (development use only)'
    )
    parser.add_argument(
        '--name',
        type=str,
        default='Demo Client',
        help='Client name (default: "Demo Client")'
    )
    parser.add_argument(
        '--csv',
        type=str,
        help='Path to CSV file (default: data/sintetic_data/synthetic_ecom_chronos2_demo.csv)'
    )
    parser.add_argument(
        '--clear-existing',
        action='store_true',
        help='Clear existing data if client already exists'
    )
    
    args = parser.parse_args()
    
    csv_path = Path(args.csv) if args.csv else None
    
    try:
        result = await setup_demo(
            client_name=args.name,
            csv_path=csv_path,
            clear_existing=args.clear_existing
        )
        
        print("\n" + "="*60)
        print("Demo Setup Complete!")
        print("="*60)
        print(f"Client ID: {result['client_id']}")
        print(f"Client Name: {result['client_name']}")
        print(f"\nData Import:")
        print(f"  Rows inserted: {result['import_result']['rows_inserted']:,}")
        print(f"  Unique items: {result['import_result']['unique_items']}")
        if result['import_result']['date_range']:
            print(f"  Date range: {result['import_result']['date_range'][0]} to {result['import_result']['date_range'][1]}")
        print("\nYou can now use this client_id to test forecasts!")
        print("="*60)
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

