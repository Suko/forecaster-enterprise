/**
 * Product and Inventory Types
 * Based on backend API reference
 */

export interface Product {
  item_id: string
  product_name: string
  category?: string
  description?: string
  current_stock: number
  unit_cost: string
  dir: number
  stockout_risk: number
  status: "understocked" | "normal" | "overstocked"
  inventory_value: string
  forecasted_demand_30d?: string
}

export interface ProductDetail extends Product {
  suppliers?: SupplierProduct[]
}

export interface SupplierProduct {
  supplier_id: string
  supplier_name: string
  moq: number
  lead_time_days: number
  supplier_cost: string
}

export interface ProductMetrics {
  item_id: string
  current_stock: number
  dir: number
  stockout_risk: number
  status: "understocked" | "normal" | "overstocked"
  forecasted_demand_30d: string
  inventory_value: string
}

export interface ProductListResponse {
  items: Product[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ProductFilters {
  search?: string
  category?: string
  supplier_id?: string
  location_id?: string
  status?: "understocked" | "normal" | "overstocked"
  min_dir?: number
  max_dir?: number
  min_risk?: number
  max_risk?: number
  min_stock?: number
  max_stock?: number
  sort?: string
  order?: "asc" | "desc"
  page?: number
  page_size?: number
}

