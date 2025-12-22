"""
Simulation Service

Orchestrates day-by-day simulation of the system using historical data.
Validates system effectiveness by comparing simulated vs real outcomes.
"""
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from decimal import Decimal
import logging
from collections import defaultdict
import pandas as pd

from models.product import Product
from models.stock import StockLevel
from models.product_supplier import ProductSupplierCondition
from models.supplier import Supplier
from models.settings import ClientSettings
from forecasting.services.forecast_service import ForecastService
from forecasting.applications.inventory.calculator import InventoryCalculator
from services.simulation.order_simulator import OrderSimulator, SimulatedOrder
from services.simulation.comparison_engine import ComparisonEngine
from schemas.simulation import (
    SimulationRequest, SimulationResponse, SimulationMetrics,
    SimulationImprovements, DailyComparison, ItemLevelResult
)

logger = logging.getLogger(__name__)


class SimulationService:
    """Service for running historical simulations"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize simulation service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.forecast_service = ForecastService(db)
        self.inventory_calc = InventoryCalculator()
        self.order_simulator = OrderSimulator()
        self.comparison_engine = ComparisonEngine()
        self._forecast_cache: Dict[Tuple[str, date], float] = {}
    
    async def run_simulation(
        self,
        request: SimulationRequest
    ) -> SimulationResponse:
        """
        Run simulation over historical period.
        
        Args:
            request: Simulation request with dates, items, config
        
        Returns:
            SimulationResponse with results
        """
        import uuid as uuid_module
        simulation_id = uuid_module.uuid4()
        
        try:
            # Reset state
            self.order_simulator.reset()
            self.comparison_engine.reset()
            self._forecast_cache = {}  # Clear forecast cache
            
            # Get configuration (use defaults if not provided)
            from schemas.simulation import SimulationConfig
            config = request.simulation_config or SimulationConfig()
            
            # Get initial stock levels at start_date
            initial_stock = await self._get_stock_snapshot(
                request.client_id,
                request.start_date,
                request.item_ids
            )
            
            # Get all items to simulate
            item_ids = request.item_ids or await self._get_all_item_ids(request.client_id)
            
            # OPTIMIZATION: Limit items for testing (remove this limit for production)
            # For now, limit to first 5 items to speed up testing
            if not request.item_ids and len(item_ids) > 5:
                logger.info(f"Limiting simulation to first 5 items (out of {len(item_ids)} total) for performance")
                item_ids = item_ids[:5]
            
            # Get product data (lead times, costs, etc.)
            products = await self._get_products(request.client_id, item_ids)
            
            # Initialize simulated stock levels - start with initial stock at start_date
            simulated_stock: Dict[str, float] = {
                item_id: initial_stock.get(item_id, 0.0)
                for item_id in item_ids
            }
            
            # Initialize real stock levels - use stock_on_date for start_date if available,
            # otherwise use initial_stock snapshot
            real_stock: Dict[str, float] = {}
            for item_id in item_ids:
                # Try to get real stock from database for start_date
                real_stock_start = await self._get_real_stock_for_date(
                    request.client_id,
                    item_id,
                    request.start_date
                )
                if real_stock_start is not None:
                    real_stock[item_id] = real_stock_start
                else:
                    # Fallback to initial stock snapshot
                    real_stock[item_id] = initial_stock.get(item_id, 0.0)
            
            # Day-by-day simulation loop
            current_date = request.start_date
            total_days = (request.end_date - request.start_date).days + 1
            
            logger.info(f"Starting simulation: {request.start_date} to {request.end_date} ({total_days} days)")
            
            day_count = 0
            while current_date <= request.end_date:
                day_count += 1
                if day_count % 30 == 0:
                    logger.info(f"Simulation progress: {day_count}/{total_days} days ({day_count*100//total_days}%)")
                
                # Process order arrivals (orders placed earlier that arrive today)
                arriving_orders = self.order_simulator.get_orders_arriving(current_date)
                for order in arriving_orders:
                    simulated_stock[order.item_id] += order.quantity
                    self.order_simulator.mark_order_received(order)
                
                # For each item, simulate the day
                for item_id in item_ids:
                    product = products.get(item_id)
                    if not product:
                        continue
                    
                    # Initialize order tracking variables
                    order_placed = False
                    order_quantity: Optional[float] = None
                    
                    # Get actual sales for this day (from historical data)
                    actual_sales = await self._get_actual_sales(
                        request.client_id,
                        item_id,
                        current_date
                    )
                    
                    # IMPORTANT: Simulated and real stock are INDEPENDENT after day 1
                    # - Simulated stock: Follows our system's logic (forecasts, reorder points, orders)
                    # - Real stock: Historical data from database (actual inventory management)
                    # They only match at the start, then diverge based on different decisions
                    
                    # Get real stock from database (for comparison only, not used in simulation logic)
                    real_stock_today = await self._get_real_stock_for_date(
                        request.client_id,
                        item_id,
                        current_date
                    )
                    
                    if real_stock_today is not None:
                        # Use actual historical stock data from database for this specific date
                        # This is independent of simulated stock - just for comparison
                        real_stock[item_id] = real_stock_today
                    else:
                        # Fallback: calculate from previous day minus sales
                        # This is approximate since we don't know when real orders arrived
                        # Only used when stock_on_date is not available in database
                        real_stock[item_id] = max(0.0, real_stock[item_id] - actual_sales)
                    
                    # SIMULATED STOCK LOGIC (independent of real stock)
                    # Check reorder point BEFORE subtracting sales (start-of-day check)
                    # This prevents placing orders every day when stock is already low
                    stock_before_sales = simulated_stock[item_id]
                    
                    # Update simulated stock levels (subtract sales)
                    simulated_stock[item_id] = max(0.0, simulated_stock[item_id] - actual_sales)
                    
                    # Generate forecast (using data up to current_date)
                    # OPTIMIZATION: Only generate forecast weekly (every 7 days) to reduce computation time
                    # For simulation, we can use cached forecast for a few days
                    days_since_start = (current_date - request.start_date).days
                    should_regenerate_forecast = (
                        days_since_start == 0 or  # First day
                        days_since_start % 7 == 0  # Weekly refresh
                    )
                    
                    if should_regenerate_forecast:
                        logger.info(f"Generating forecast for {item_id} on {current_date} (day {days_since_start})")
                        forecast_demand = await self._get_forecasted_demand(
                            request.client_id,
                            item_id,
                            current_date,
                            prediction_length=30
                        )
                        # Cache forecast for next 7 days
                        self._forecast_cache[(item_id, current_date)] = forecast_demand
                        logger.info(f"Cached forecast for {item_id}: {forecast_demand:.2f}")
                    else:
                        # Use cached forecast (from most recent generation)
                        # Find most recent cached forecast for this item
                        cached_forecast = None
                        for (cached_item, cached_date), cached_value in self._forecast_cache.items():
                            if cached_item == item_id and cached_date <= current_date:
                                if cached_forecast is None or cached_date > cached_forecast[0]:
                                    cached_forecast = (cached_date, cached_value)
                        forecast_demand = cached_forecast[1] if cached_forecast else 0.0
                    
                    # DEBUG: Log forecast and stock status
                    if days_since_start % 30 == 0:  # Log every 30 days
                        logger.info(f"Day {days_since_start} - {item_id}: stock={simulated_stock[item_id]:.1f}, forecast={forecast_demand:.2f}, sales={actual_sales:.1f}")
                    
                    # If forecast is 0, use historical average as fallback
                    if forecast_demand <= 0:
                        # Get average daily sales from last 30 days
                        historical_avg = await self._get_historical_average_demand(
                            request.client_id,
                            item_id,
                            current_date,
                            days=30
                        )
                        if historical_avg > 0:
                            forecast_demand = historical_avg * 30  # 30-day forecast
                            logger.debug(f"Using historical average for {item_id}: {historical_avg:.2f}/day = {forecast_demand:.2f} for 30 days")
                    
                    if forecast_demand > 0:
                        # Calculate inventory recommendations
                        avg_daily_demand = forecast_demand / 30.0
                        
                        # Get lead time, MOQ, and safety stock days
                        lead_time_days = await self._get_lead_time(
                            request.client_id,
                            item_id
                        )
                        moq = await self._get_moq(
                            request.client_id,
                            item_id
                        )
                        safety_stock_days = product.safety_buffer_days or 7
                        
                        # Calculate safety stock and reorder point
                        safety_stock = self.inventory_calc.calculate_safety_stock(
                            avg_daily_demand,
                            lead_time_days,
                            safety_stock_days,
                            config.service_level
                        )
                        
                        reorder_point = self.inventory_calc.calculate_reorder_point(
                            avg_daily_demand,
                            lead_time_days,
                            safety_stock
                        )
                        
                        # Check if we should place an order
                        # Use stock BEFORE sales to check reorder point (start-of-day inventory)
                        # Also check if we already have an order in transit for this item
                        orders_in_transit = [
                            o for o in self.order_simulator.orders
                            if o.item_id == item_id and not o.received and o.arrival_date > current_date
                        ]
                        
                        # DEBUG: Log reorder point calculation
                        if days_since_start % 30 == 0:  # Log every 30 days
                            logger.info(f"Day {days_since_start} - {item_id}: stock_before={stock_before_sales:.1f}, stock_after={simulated_stock[item_id]:.1f}, reorder_point={reorder_point:.1f}, orders_in_transit={len(orders_in_transit)}")
                        
                        # Only place order if:
                        # 1. Stock before sales is at or below reorder point
                        # 2. No orders already in transit (prevent duplicate orders)
                        if config.auto_place_orders and stock_before_sales <= reorder_point and len(orders_in_transit) == 0:
                            # Calculate recommended order quantity
                            recommended_qty = self.inventory_calc.calculate_recommended_order_quantity(
                                forecast_demand,
                                safety_stock,
                                simulated_stock[item_id],
                                moq=moq  # Use actual MOQ from product-supplier
                            )
                            
                            # Place order
                            order = self.order_simulator.place_order(
                                item_id=item_id,
                                quantity=recommended_qty,
                                order_date=current_date,
                                lead_time_days=lead_time_days + config.lead_time_buffer_days,
                                min_order_quantity=config.min_order_quantity
                            )
                            
                            if order:
                                order_placed = True
                                order_quantity = order.quantity
                    
                    # Record daily comparison
                    unit_cost = Decimal(str(product.unit_cost)) if product.unit_cost else Decimal("0")
                    self.comparison_engine.record_daily_comparison(
                        current_date=current_date,
                        item_id=item_id,
                        simulated_stock=simulated_stock[item_id],
                        real_stock=real_stock[item_id],
                        unit_cost=unit_cost,
                        actual_sales=actual_sales,
                        order_placed=order_placed,
                        order_quantity=order_quantity
                    )
                
                # Move to next day
                current_date += timedelta(days=1)
            
            # Calculate final metrics
            results = self._calculate_results()
            improvements = self._calculate_improvements(results)
            
            # Build response
            return SimulationResponse(
                simulation_id=simulation_id,
                status="completed",
                start_date=request.start_date,
                end_date=request.end_date,
                total_days=total_days,
                results=results,
                improvements=improvements,
                daily_comparison=self._format_daily_comparisons(),
                item_level_results=self._format_item_level_results(item_ids)
            )
        
        except Exception as e:
            logger.error(f"Simulation failed: {e}", exc_info=True)
            return SimulationResponse(
                simulation_id=simulation_id,
                status="failed",
                start_date=request.start_date,
                end_date=request.end_date,
                total_days=(request.end_date - request.start_date).days + 1,
                error_message=str(e)
            )
    
    async def _get_stock_snapshot(
        self,
        client_id: UUID,
        snapshot_date: date,
        item_ids: Optional[List[str]]
    ) -> Dict[str, float]:
        """
        Get stock levels at a specific date.
        
        First tries to get from ts_demand_daily.stock_on_date (historical data).
        Falls back to current stock_levels if historical data not available.
        """
        # Try to get historical stock from ts_demand_daily
        query = text("""
            SELECT item_id, SUM(stock_on_date) as total_stock
            FROM ts_demand_daily
            WHERE client_id = :client_id
              AND date_local = :snapshot_date
        """)
        
        params = {
            "client_id": str(client_id),
            "snapshot_date": snapshot_date
        }
        
        if item_ids:
            query = text("""
                SELECT item_id, SUM(stock_on_date) as total_stock
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND date_local = :snapshot_date
                  AND item_id = ANY(:item_ids)
                GROUP BY item_id
            """)
            params["item_ids"] = item_ids
        
        result = await self.db.execute(query, params)
        rows = result.all()
        
        stock_dict: Dict[str, float] = {}
        for row in rows:
            if row.total_stock is not None:
                stock_dict[row.item_id] = float(row.total_stock)
        
        # If we got historical data, return it
        if stock_dict:
            return stock_dict
        
        # Fallback: use current stock levels
        query = select(StockLevel).where(
            StockLevel.client_id == client_id
        )
        
        if item_ids:
            query = query.where(StockLevel.item_id.in_(item_ids))
        
        result = await self.db.execute(query)
        stock_levels = result.scalars().all()
        
        # Aggregate by item_id (sum across locations)
        for stock in stock_levels:
            if stock.item_id not in stock_dict:
                stock_dict[stock.item_id] = 0.0
            stock_dict[stock.item_id] += float(stock.current_stock)
        
        return stock_dict
    
    async def _get_real_stock_for_date(
        self,
        client_id: UUID,
        item_id: str,
        target_date: date
    ) -> Optional[float]:
        """
        Get real historical stock level for a specific date.
        
        Uses ts_demand_daily.stock_on_date if available.
        Returns None if stock_on_date is not populated (NULL), otherwise returns the stock value.
        """
        query = text("""
            SELECT 
                SUM(stock_on_date) as total_stock,
                COUNT(stock_on_date) as has_data
            FROM ts_demand_daily
            WHERE client_id = :client_id
              AND item_id = :item_id
              AND date_local = :target_date
        """)
        
        result = await self.db.execute(query, {
            "client_id": str(client_id),
            "item_id": item_id,
            "target_date": target_date
        })
        row = result.one()
        
        # If has_data > 0, stock_on_date exists (even if it's 0)
        # If has_data = 0, stock_on_date is NULL (no data)
        if row.has_data and row.has_data > 0:
            return float(row.total_stock) if row.total_stock is not None else 0.0
        else:
            return None  # No stock data available for this date
    
    async def _get_all_item_ids(self, client_id: UUID) -> List[str]:
        """Get all item IDs for a client"""
        query = select(Product.item_id).where(Product.client_id == client_id)
        result = await self.db.execute(query)
        return [row[0] for row in result.all()]
    
    async def _get_products(
        self,
        client_id: UUID,
        item_ids: List[str]
    ) -> Dict[str, Product]:
        """Get product data for items"""
        query = select(Product).where(
            Product.client_id == client_id,
            Product.item_id.in_(item_ids)
        )
        result = await self.db.execute(query)
        products = result.scalars().all()
        return {p.item_id: p for p in products}
    
    async def _get_actual_sales(
        self,
        client_id: UUID,
        item_id: str,
        sale_date: date
    ) -> float:
        """Get actual sales for a specific item and date"""
        query = text("""
            SELECT COALESCE(SUM(units_sold), 0) as total_sales
            FROM ts_demand_daily
            WHERE client_id = :client_id
              AND item_id = :item_id
              AND date_local = :sale_date
        """)
        
        result = await self.db.execute(query, {
            "client_id": str(client_id),
            "item_id": item_id,
            "sale_date": sale_date
        })
        row = result.one()
        return float(row.total_sales) if row.total_sales else 0.0
    
    async def _get_forecasted_demand(
        self,
        client_id: UUID,
        item_id: str,
        training_end_date: date,
        prediction_length: int = 30
    ) -> float:
        """
        Get forecasted demand for next 30 days.
        
        Uses existing ForecastService with training_end_date parameter.
        """
        try:
            # First, check if we have training data up to training_end_date
            training_data_count = await self._check_training_data(
                client_id, item_id, training_end_date
            )
            
            if training_data_count < 7:  # Need at least 7 days for forecasting
                logger.warning(
                    f"Insufficient training data for {item_id} up to {training_end_date}: "
                    f"only {training_data_count} days available (need 7+)"
                )
                return 0.0
            
            forecast_run = await self.forecast_service.generate_forecast(
                client_id=str(client_id),
                user_id=None,
                item_ids=[item_id],
                prediction_length=prediction_length,
                primary_model="chronos-2",
                include_baseline=False,
                training_end_date=training_end_date,
                skip_persistence=True  # Don't save to DB during simulation
            )
            
            # Get forecast results
            # When skip_persistence=True, results are stored in-memory in forecast_run._results_by_method
            # We need to access them directly instead of querying the database
            if hasattr(forecast_run, '_results_by_method') and forecast_run._results_by_method:
                # Extract results from in-memory storage
                method = forecast_run.recommended_method or forecast_run.primary_model or "chronos-2"
                if method in forecast_run._results_by_method:
                    item_results = forecast_run._results_by_method[method]
                    if item_id in item_results:
                        # Convert DataFrame to list of dicts (matching get_forecast_results format)
                        predictions_df = item_results[item_id]
                        if not predictions_df.empty:
                            predictions = []
                            for _, row in predictions_df.iterrows():
                                prediction = {
                                    "date": pd.to_datetime(row["timestamp"]).date() if "timestamp" in row else None,
                                    "point_forecast": float(row.get("point_forecast", 0.0))
                                }
                                # Add quantiles if available
                                quantiles = {}
                                for q in ["p10", "p50", "p90"]:
                                    if q in row and pd.notna(row[q]):
                                        quantiles[q] = float(row[q])
                                if quantiles:
                                    prediction["quantiles"] = quantiles
                                predictions.append(prediction)
                            
                            # Sum all forecasted values
                            total_forecast = sum(p.get("point_forecast", 0.0) for p in predictions)
                            
                            if total_forecast == 0.0:
                                logger.warning(
                                    f"Forecast returned 0 for {item_id} on {training_end_date}. "
                                    f"Number of predictions: {len(predictions)}"
                                )
                            
                            return float(total_forecast)
            
            # Fallback: Try database query (in case skip_persistence was False or results not in memory)
            results = await self.forecast_service.get_forecast_results(
                forecast_run_id=forecast_run.forecast_run_id
            )
            
            if item_id not in results:
                logger.warning(
                    f"No forecast results returned for {item_id} on {training_end_date}. "
                    f"Forecast run status: {forecast_run.status}"
                )
                return 0.0
            
            if not results[item_id]:
                logger.warning(
                    f"Empty forecast results for {item_id} on {training_end_date}. "
                    f"Expected {prediction_length} predictions, got 0"
                )
                return 0.0
            
            # Sum all forecasted values
            total_forecast = sum(
                p.get("point_forecast", 0.0) for p in results[item_id]
            )
            
            if total_forecast == 0.0:
                logger.warning(
                    f"Forecast returned 0 for {item_id} on {training_end_date}. "
                    f"Number of predictions: {len(results[item_id])}, "
                    f"Sample values: {[p.get('point_forecast', 0) for p in results[item_id][:5]]}"
                )
            
            return float(total_forecast)
        
        except Exception as e:
            logger.error(
                f"Forecast generation failed for {item_id} on {training_end_date}: {e}",
                exc_info=True
            )
            return 0.0
    
    async def _check_training_data(
        self,
        client_id: UUID,
        item_id: str,
        end_date: date
    ) -> int:
        """Check how many days of training data we have up to end_date"""
        query = text("""
            SELECT COUNT(DISTINCT date_local) as data_days
            FROM ts_demand_daily
            WHERE client_id = :client_id
              AND item_id = :item_id
              AND date_local <= :end_date
        """)
        
        result = await self.db.execute(query, {
            "client_id": str(client_id),
            "item_id": item_id,
            "end_date": end_date
        })
        row = result.one()
        return int(row.data_days) if row.data_days else 0
    
    async def _get_lead_time(
        self,
        client_id: UUID,
        item_id: str
    ) -> int:
        """Get lead time for an item (from product-supplier or default)"""
        # Try to get from product-supplier conditions
        query = select(ProductSupplierCondition).where(
            ProductSupplierCondition.client_id == client_id,
            ProductSupplierCondition.item_id == item_id,
            ProductSupplierCondition.is_primary == True
        ).limit(1)
        
        result = await self.db.execute(query)
        condition = result.scalar_one_or_none()
        
        if condition and condition.lead_time_days:
            return condition.lead_time_days
        
        # Default lead time
        return 7
    
    async def _get_moq(
        self,
        client_id: UUID,
        item_id: str
    ) -> Optional[int]:
        """
        Get MOQ (Minimum Order Quantity) for an item.
        
        Fallback chain:
        1. product_supplier_conditions.moq (if exists and > 0)
        2. suppliers.default_moq (if > 0)
        3. None (no MOQ constraint)
        """
        # Try to get from product-supplier conditions (primary supplier)
        query = select(ProductSupplierCondition).where(
            ProductSupplierCondition.client_id == client_id,
            ProductSupplierCondition.item_id == item_id,
            ProductSupplierCondition.is_primary == True
        ).limit(1)
        
        result = await self.db.execute(query)
        condition = result.scalar_one_or_none()
        
        if condition and condition.moq and condition.moq > 0:
            return condition.moq
        
        # Fallback to supplier default (if we have a supplier)
        if condition and condition.supplier_id:
            supplier_query = select(Supplier).where(
                Supplier.client_id == client_id,
                Supplier.id == condition.supplier_id
            )
            supplier_result = await self.db.execute(supplier_query)
            supplier = supplier_result.scalar_one_or_none()
            
            if supplier and supplier.default_moq and supplier.default_moq > 0:
                return supplier.default_moq
        
        # No MOQ constraint
        return None
    
    async def _get_historical_average_demand(
        self,
        client_id: UUID,
        item_id: str,
        end_date: date,
        days: int = 30
    ) -> float:
        """Get average daily demand from historical data"""
        from datetime import timedelta
        start_date = end_date - timedelta(days=days)
        
        query = text("""
            SELECT AVG(daily_total) as avg_demand
            FROM (
                SELECT date_local, SUM(units_sold) as daily_total
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND item_id = :item_id
                  AND date_local >= :start_date
                  AND date_local < :end_date
                GROUP BY date_local
            ) daily_totals
        """)
        
        result = await self.db.execute(query, {
            "client_id": str(client_id),
            "item_id": item_id,
            "start_date": start_date,
            "end_date": end_date
        })
        row = result.one()
        return float(row.avg_demand) if row.avg_demand else 0.0
    
    def _calculate_results(self) -> SimulationMetrics:
        """Calculate overall simulation metrics"""
        stockout_rate = self.comparison_engine.calculate_stockout_rate()
        inventory_value = self.comparison_engine.calculate_inventory_value()
        service_level = self.comparison_engine.calculate_service_level()
        
        # Total cost (simplified: inventory carrying cost)
        # TODO: Add stockout cost and ordering cost
        total_cost_sim = inventory_value["simulated"]
        total_cost_real = inventory_value["real"]
        
        return SimulationMetrics(
            stockout_rate=stockout_rate,
            inventory_value=inventory_value,
            service_level=service_level,
            total_cost={
                "simulated": total_cost_sim,
                "real": total_cost_real
            }
        )
    
    def _calculate_improvements(self, results: SimulationMetrics) -> SimulationImprovements:
        """Calculate improvement metrics vs baseline"""
        real_stockout_rate = results.stockout_rate["real"]
        sim_stockout_rate = results.stockout_rate["simulated"]
        
        stockout_reduction = 0.0
        if real_stockout_rate > 0:
            stockout_reduction = (real_stockout_rate - sim_stockout_rate) / real_stockout_rate
        
        real_inv_value = results.inventory_value["real"]
        sim_inv_value = results.inventory_value["simulated"]
        
        inventory_reduction = 0.0
        if real_inv_value > 0:
            inventory_reduction = (real_inv_value - sim_inv_value) / real_inv_value
        
        cost_savings = results.total_cost["real"] - results.total_cost["simulated"]
        
        service_level_improvement = results.service_level["simulated"] - results.service_level["real"]
        
        return SimulationImprovements(
            stockout_reduction=stockout_reduction,
            inventory_reduction=inventory_reduction,
            cost_savings=cost_savings,
            service_level_improvement=service_level_improvement
        )
    
    def _format_daily_comparisons(self) -> List[DailyComparison]:
        """Format daily comparisons for response"""
        comparisons = self.comparison_engine.get_daily_comparisons()
        return [
            DailyComparison(
                date=c["date"],
                item_id=c["item_id"],
                simulated_stock=c["simulated_stock"],
                real_stock=c["real_stock"],
                actual_sales=c.get("actual_sales"),
                simulated_stockout=c["simulated_stockout"],
                real_stockout=c["real_stockout"],
                order_placed=c.get("order_placed"),
                order_quantity=c.get("order_quantity")
            )
            for c in comparisons
        ]
    
    def _format_item_level_results(self, item_ids: List[str]) -> List[ItemLevelResult]:
        """Format item-level results for response"""
        results = []
        
        for item_id in item_ids:
            stockout_rate = self.comparison_engine.calculate_stockout_rate(item_id)
            inventory_value = self.comparison_engine.calculate_inventory_value(item_id)
            service_level = self.comparison_engine.calculate_service_level(item_id)
            total_orders = self.order_simulator.get_total_orders_placed(item_id)
            
            # Calculate improvements
            real_stockout = stockout_rate["real"]
            sim_stockout = stockout_rate["simulated"]
            stockout_reduction = 0.0
            if real_stockout > 0:
                stockout_reduction = (real_stockout - sim_stockout) / real_stockout
            
            real_inv = inventory_value["real"]
            sim_inv = inventory_value["simulated"]
            inventory_reduction = 0.0
            if real_inv > 0:
                inventory_reduction = (real_inv - sim_inv) / real_inv
            
            results.append(ItemLevelResult(
                item_id=item_id,
                stockout_rate=stockout_rate,
                inventory_value=inventory_value,
                service_level=service_level,
                total_orders_placed=total_orders,
                improvement={
                    "stockout_reduction": stockout_reduction,
                    "inventory_reduction": inventory_reduction
                }
            ))
        
        return results

