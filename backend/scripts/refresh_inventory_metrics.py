"""
Refresh inventory metrics for one or all clients.

This script runs the metrics service across every SKU for a client,
persisting the results into `inventory_metrics` so frontend filters work
without needing to compute metrics client-side.
"""
import argparse
import asyncio
from uuid import UUID

from sqlalchemy import select

from models.client import Client
from models.database import get_async_session_local
from services.inventory_metrics_service import InventoryMetricsService


async def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh inventory_metrics table")
    parser.add_argument(
        "--client-id",
        type=str,
        help="UUID of the client to refresh"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Refresh metrics for every client"
    )
    parser.add_argument(
        "--location-id",
        type=str,
        default="UNSPECIFIED",
        help="Location ID to attach to aggregated metrics (default: UNSPECIFIED)"
    )

    args = parser.parse_args()

    if not args.client_id and not args.all:
        parser.error("Either --client-id or --all must be provided")

    session_local = get_async_session_local()
    async with session_local() as session:
        service = InventoryMetricsService(session)

        client_ids: list[UUID] = []
        if args.client_id:
            client_ids = [UUID(args.client_id)]
        elif args.all:
            result = await session.execute(select(Client.client_id))
            client_ids = [UUID(client_id) for client_id in result.scalars().all()]

        for client_id in client_ids:
            print(f"Refreshing inventory metrics for client {client_id}")
            await service.refresh_client_metrics(client_id, location_id=args.location_id)
            print(f"Completed client {client_id}")


if __name__ == "__main__":
    asyncio.run(main())
