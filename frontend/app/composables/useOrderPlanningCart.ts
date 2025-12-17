import type { CartItem, CartResponse } from "~/types/order";

export const useOrderPlanningCart = () => {
  const { isDemoMode } = useDemoMode();
  const demoApi = isDemoMode.value ? useDemoApi() : null;

  const fetchCart = async (): Promise<CartResponse> => {
    // Use demo API if in demo mode
    if (isDemoMode.value && demoApi) {
      return await demoApi.getCart();
    }
    return await $fetch<CartResponse>("/api/order-planning/cart");
  };

  const updateCartItem = async (
    itemId: string,
    supplierId: string,
    updates: { quantity?: number; notes?: string }
  ): Promise<CartItem> => {
    // Use demo API if in demo mode
    if (isDemoMode.value && demoApi) {
      const cart = await demoApi.updateCartItem(itemId, supplierId, updates);
      const item = cart.items.find(item => item.item_id === itemId && item.supplier_id === supplierId);
      if (!item) {
        throw new Error(`Cart item not found: ${itemId}`);
      }
      return item;
    }
    return await $fetch<CartItem>(`/api/order-planning/cart/${encodeURIComponent(itemId)}`, {
      method: "PUT",
      query: { supplier_id: supplierId },
      body: updates,
    });
  };

  const removeFromCart = async (
    itemId: string,
    supplierId: string
  ): Promise<{ message: string }> => {
    // Use demo API if in demo mode
    if (isDemoMode.value && demoApi) {
      await demoApi.removeFromCart(itemId, supplierId);
      return { message: "Item removed from cart" };
    }
    return await $fetch<{ message: string }>(
      `/api/order-planning/cart/${encodeURIComponent(itemId)}`,
      {
        method: "DELETE",
        query: { supplier_id: supplierId },
      }
    );
  };

  const clearCart = async (): Promise<{ message: string }> => {
    // Use demo API if in demo mode
    if (isDemoMode.value && demoApi) {
      await demoApi.clearCart();
      return { message: "Cart cleared" };
    }
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
