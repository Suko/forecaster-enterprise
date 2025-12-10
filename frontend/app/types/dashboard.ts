/**
 * Dashboard Types
 * Based on backend API reference
 */

export interface DashboardMetrics {
  total_skus: number
  total_inventory_value: string
  understocked_count: number
  overstocked_count: number
  average_dir: string
  understocked_value: string
  overstocked_value: string
}

export interface TopProduct {
  item_id: string
  product_name: string
  dir: string
  stockout_risk: string
  current_stock: number
  inventory_value: string
}

export interface DashboardResponse {
  metrics: DashboardMetrics
  top_understocked: TopProduct[]
  top_overstocked: TopProduct[]
}

export type TimePeriod = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'

export interface TrendDataPoint {
  date: string
  value: number
  label?: string
}

