/**
 * Product-Supplier Condition Types
 */

export interface ProductSupplierCondition {
  id: string;
  client_id: string;
  item_id: string;
  supplier_id: string;
  supplier: {
    id: string;
    name: string;
    contact_email?: string | null;
  };
  moq: number;
  lead_time_days: number;
  supplier_cost?: string | number | null;
  packaging_unit?: string | null;
  packaging_qty?: number | null;
  is_primary: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductSupplierUpdate {
  moq?: number;
  lead_time_days?: number;
  supplier_cost?: string | number;
  packaging_unit?: string;
  packaging_qty?: number;
  is_primary?: boolean;
  notes?: string;
}
