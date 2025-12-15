import type { ProductSupplierCondition, ProductSupplierUpdate } from "~/types/inventory";

export interface ProductSupplierCreate {
  supplier_id: string;
  moq?: number;
  lead_time_days?: number;
  supplier_cost?: string | number;
  packaging_unit?: string;
  packaging_qty?: number;
  is_primary?: boolean;
  notes?: string;
}

export const useProductSuppliers = () => {
  /**
   * Get all suppliers for a product with conditions (MOQ, lead time, etc.)
   */
  const getProductSuppliers = async (itemId: string): Promise<ProductSupplierCondition[]> => {
    return await $fetch<ProductSupplierCondition[]>(
      `/api/products/${encodeURIComponent(itemId)}/suppliers`
    );
  };

  /**
   * Add product-supplier condition (MOQ, lead time, etc.)
   */
  const addProductSupplier = async (
    itemId: string,
    data: ProductSupplierCreate
  ): Promise<ProductSupplierCondition> => {
    return await $fetch<ProductSupplierCondition>(
      `/api/products/${encodeURIComponent(itemId)}/suppliers`,
      {
        method: "POST",
        body: data,
      }
    );
  };

  /**
   * Update product-supplier condition (MOQ, lead time, etc.)
   */
  const updateProductSupplier = async (
    itemId: string,
    supplierId: string,
    data: ProductSupplierUpdate
  ): Promise<ProductSupplierCondition> => {
    return await $fetch<ProductSupplierCondition>(
      `/api/products/${encodeURIComponent(itemId)}/suppliers/${encodeURIComponent(supplierId)}`,
      {
        method: "PUT",
        body: data,
      }
    );
  };

  return {
    getProductSuppliers,
    addProductSupplier,
    updateProductSupplier,
  };
};
