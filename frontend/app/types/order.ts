export interface CartItem {
  id: string
  session_id: string
  item_id: string
  supplier_id: string
  quantity: number
  unit_cost: string | number
  total_price: string | number
  packaging_unit?: string | null
  packaging_qty?: number | null
  notes?: string | null
  product_name: string
  supplier_name: string
  created_at: string
  updated_at: string
}

export interface CartResponse {
  items: CartItem[]
  total_items: number
  total_value: string | number
  suppliers?: Array<{
    supplier_id: string
    supplier_name: string
    items: string[]
  }>
}

export interface PurchaseOrderListItem {
  id: string
  po_number: string
  supplier_id: string
  supplier_name: string
  status: "pending" | "confirmed" | "shipped" | "received" | "cancelled" | string
  order_date: string
  expected_delivery_date?: string | null
  total_amount: number
  created_at: string
}

export interface PurchaseOrdersListResponse {
  items: PurchaseOrderListItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface PurchaseOrderItem {
  id: string
  item_id: string
  product_name: string
  quantity: number
  unit_cost: string | number
  total_price: string | number
  packaging_unit?: string | null
  packaging_qty?: number | null
}

export interface PurchaseOrder {
  id: string
  po_number: string
  supplier_id: string
  supplier_name: string
  status: "pending" | "confirmed" | "shipped" | "received" | "cancelled" | string
  order_date: string
  expected_delivery_date?: string | null
  total_amount: string | number
  shipping_method?: string | null
  shipping_unit?: string | null
  notes?: string | null
  created_by?: string | null
  items: PurchaseOrderItem[]
  created_at: string
  updated_at: string
}

