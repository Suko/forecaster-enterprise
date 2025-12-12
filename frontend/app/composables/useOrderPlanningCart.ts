import type { CartItem, CartResponse } from "~/types/order";

export const useOrderPlanningCart = () => {
  const fetchCart = async (): Promise<CartResponse> => {
    return await $fetch<CartResponse>("/api/order-planning/cart");
  };

  const updateCartItem = async (
    itemId: string,
    supplierId: string,
    updates: { quantity?: number; notes?: string }
  ): Promise<CartItem> => {
    return await $fetch<CartItem>(`/api/order-planning/cart/${encodeURIComponent(itemId)}`, {
      method: "PUT",
      query: { supplier_id: supplierId },
      body: updates,
    });
  };

  const removeFromCart = async (itemId: string, supplierId: string): Promise<{ message: string }> => {
    return await $fetch<{ message: string }>(`/api/order-planning/cart/${encodeURIComponent(itemId)}`, {
      method: "DELETE",
      query: { supplier_id: supplierId },
    });
  };

  const clearCart = async (): Promise<{ message: string }> => {
    return await $fetch<{ message: string }>("/api/order-planning/cart/clear", {
      method: "POST",
    });
  };

  return {
    fetchCart,
    updateCartItem,
    removeFromCart,
    clearCart,
  };
};

