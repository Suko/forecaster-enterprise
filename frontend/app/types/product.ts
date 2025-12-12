/**
 * Product and Inventory Types
 * Based on backend API reference
 */

export interface SupplierSummary {
  supplier_id: string;
  supplier_name: string;
  moq: number;
  lead_time_days: number;
  is_primary: boolean;
}

export interface LocationStockSummary {
  location_id: string;
  location_name: string;
  current_stock: number;
}

export interface Product {
  item_id: string;
  product_name: string;
  category?: string;
  description?: string;
  current_stock: number;
  unit_cost: string;
  safety_buffer_days?: number | null;
  dir: number;
  stockout_risk: number;
  status: "understocked" | "normal" | "overstocked";
  inventory_value: string;
  forecasted_demand_30d?: string;
  // All suppliers for this product
  suppliers?: SupplierSummary[] | null;
  // Stock per location
  locations?: LocationStockSummary[];
  // Legacy fields (deprecated, kept for backward compatibility)
  primary_supplier_name?: string | null;
  primary_supplier_moq?: number | null;
  primary_supplier_lead_time_days?: number | null;
}

export interface ProductDetail extends Product {
  suppliers?: SupplierProduct[];
}

export interface SupplierProduct {
  supplier_id: string;
  supplier_name: string;
  moq: number;
  lead_time_days: number;
  supplier_cost: string;
}

export interface ProductMetrics {
  item_id: string;
  current_stock: number;
  dir: number;
  stockout_risk: number;
  status: "understocked" | "normal" | "overstocked";
  forecasted_demand_30d: string;
  inventory_value: string;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ProductFilters {
  search?: string;
  category?: string;
  supplier_id?: string;
  location_id?: string;
  status?: "understocked" | "normal" | "overstocked";
  min_dir?: number;
  max_dir?: number;
  min_risk?: number;
  max_risk?: number;
  min_stock?: number;
  max_stock?: number;
  sort?: string;
  order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}
