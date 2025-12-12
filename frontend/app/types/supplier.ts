export interface Supplier {
  id: string
  external_id?: string | null
  name: string
  contact_email?: string | null
  contact_phone?: string | null
  address?: string | null
  supplier_type: "PO" | "WO" | string
  is_synced: boolean
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface SupplierListResponse {
  items: Supplier[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

