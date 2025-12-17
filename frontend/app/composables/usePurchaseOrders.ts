import type { PurchaseOrder, PurchaseOrdersListResponse } from "~/types/order";

export const usePurchaseOrders = () => {
  const { isDemoMode } = useDemoMode();
  const demoApi = isDemoMode.value ? useDemoApi() : null;

  const fetchPurchaseOrders = async (params?: {
    status?: string;
    supplier_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<PurchaseOrdersListResponse> => {
    // Use demo API if in demo mode
    if (isDemoMode.value && demoApi) {
      return await demoApi.getPurchaseOrders(params);
    }
    return await $fetch<PurchaseOrdersListResponse>("/api/purchase-orders", { query: params });
  };

  const fetchPurchaseOrder = async (id: string): Promise<PurchaseOrder> => {
    // Use demo API if in demo mode
    if (isDemoMode.value && demoApi) {
      return await demoApi.getPurchaseOrder(id);
    }
    return await $fetch<PurchaseOrder>(`/api/purchase-orders/${encodeURIComponent(id)}`);
  };

  const createPurchaseOrderFromCart = async (data: {
    supplier_id: string;
    shipping_method?: string;
    shipping_unit?: string;
    notes?: string;
  }): Promise<PurchaseOrder> => {
    // Use demo API if in demo mode
    if (isDemoMode.value && demoApi) {
      return await demoApi.createPurchaseOrderFromCart(data);
    }
    return await $fetch<PurchaseOrder>("/api/purchase-orders/from-cart", {
      method: "POST",
      body: data,
    });
  };

  const updatePurchaseOrderStatus = async (
    id: string,
    status: "pending" | "confirmed" | "shipped" | "received" | "cancelled"
  ): Promise<PurchaseOrder> => {
    // In demo mode, return updated PO (no persistence)
    if (isDemoMode.value && demoApi) {
      const po = await demoApi.getPurchaseOrder(id);
      return { ...po, status, updated_at: new Date().toISOString() };
    }
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
