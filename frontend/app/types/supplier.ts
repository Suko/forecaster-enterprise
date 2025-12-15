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
}

export interface SupplierListResponse {
  items: Supplier[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
