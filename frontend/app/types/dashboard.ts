/**
 * Dashboard Types
 * Based on backend API reference
 */

export interface DashboardMetrics {
  total_products: number
  total_value: string
  understocked_count: number
  overstocked_count: number
  high_risk_count: number
  average_dir?: number
  understocked_value?: string
  overstocked_value?: string
}

export interface TopProduct {
  item_id: string
  product_name: string
  dir: number
  stockout_risk: number
  current_stock?: number
  unit_cost?: string
  inventory_value?: string
  forecasted_demand_30d?: number
}

export interface DashboardResponse {
  total_products: number
  total_value: string
  understocked_count: number
  overstocked_count: number
  high_risk_count: number
  top_understocked: TopProduct[]
  top_overstocked: TopProduct[]
}

export type TimePeriod = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'

export interface TrendDataPoint {
  date: string
  value: number
  label?: string
}

