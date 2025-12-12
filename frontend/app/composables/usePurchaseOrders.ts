import type { PurchaseOrder, PurchaseOrdersListResponse } from "~/types/order";

export const usePurchaseOrders = () => {
  const fetchPurchaseOrders = async (params?: {
    status?: string;
    supplier_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<PurchaseOrdersListResponse> => {
    return await $fetch<PurchaseOrdersListResponse>("/api/purchase-orders", { query: params });
  };

  const fetchPurchaseOrder = async (id: string): Promise<PurchaseOrder> => {
    return await $fetch<PurchaseOrder>(`/api/purchase-orders/${encodeURIComponent(id)}`);
  };

  const createPurchaseOrderFromCart = async (data: {
    supplier_id: string;
    shipping_method?: string;
    shipping_unit?: string;
    notes?: string;
  }): Promise<PurchaseOrder> => {
    return await $fetch<PurchaseOrder>("/api/purchase-orders/from-cart", {
      method: "POST",
      body: data,
    });
  };

  const updatePurchaseOrderStatus = async (
    id: string,
    status: "pending" | "confirmed" | "shipped" | "received" | "cancelled"
  ): Promise<PurchaseOrder> => {
    return await $fetch<PurchaseOrder>(`/api/purchase-orders/${encodeURIComponent(id)}/status`, {
      method: "PUT",
      body: { status },
    });
  };

  return {
    fetchPurchaseOrders,
    fetchPurchaseOrder,
    createPurchaseOrderFromCart,
    updatePurchaseOrderStatus,
  };
};
