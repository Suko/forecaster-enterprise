export interface Supplier {
  id: string;
  external_id?: string | null;
  name: string;
  contact_email?: string | null;
  contact_phone?: string | null;
  address?: string | null;
  supplier_type: "PO" | "WO" | string;
  default_moq: number;
  default_lead_time_days: number;
  is_synced: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  default_product_count?: number; // Count of products where this supplier is primary/default
  // Effective values (accounting for product-level overrides)
  effective_moq_avg?: number; // Average effective MOQ across all products
  effective_moq_min?: number; // Minimum effective MOQ
  effective_moq_max?: number; // Maximum effective MOQ
  custom_moq_count?: number; // Number of products with custom MOQ
  effective_lead_time_avg?: number; // Average effective lead time across all products
  effective_lead_time_min?: number; // Minimum effective lead time
  effective_lead_time_max?: number; // Maximum effective lead time
  custom_lead_time_count?: number; // Number of products with custom lead time
}

export interface SupplierListResponse {
  items: Supplier[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
