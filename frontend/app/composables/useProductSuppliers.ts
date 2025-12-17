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
  const { isDemoMode } = useDemoMode();
  const demoApi = isDemoMode.value ? useDemoApi() : null;

  /**
   * Get all suppliers for a product with conditions (MOQ, lead time, etc.)
   */
  const getProductSuppliers = async (itemId: string): Promise<ProductSupplierCondition[]> => {
    // In demo mode, get from product data
    if (isDemoMode.value && demoApi) {
      const product = await demoApi.getProduct(itemId);
      return product.suppliers?.map(s => ({
        supplier_id: s.supplier_id,
        supplier_name: s.supplier_name,
        moq: s.moq || 0,
        lead_time_days: s.lead_time_days || 0,
        supplier_cost: s.supplier_cost || "0.00",
        packaging_unit: s.packaging_unit || null,
        packaging_qty: s.packaging_qty || null,
        is_primary: s.is_primary || false,
        notes: null,
      })) || [];
    }
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
    // In demo mode, return mock (no persistence)
    if (isDemoMode.value) {
      return {
        supplier_id: data.supplier_id,
        supplier_name: "Demo Supplier",
        moq: data.moq || 0,
        lead_time_days: data.lead_time_days || 0,
        supplier_cost: String(data.supplier_cost || "0.00"),
        packaging_unit: data.packaging_unit || null,
        packaging_qty: data.packaging_qty || null,
        is_primary: data.is_primary || false,
        notes: data.notes || null,
      };
    }
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
    // In demo mode, return updated mock (no persistence)
    if (isDemoMode.value) {
      const suppliers = await getProductSuppliers(itemId);
      const supplier = suppliers.find(s => s.supplier_id === supplierId);
      if (!supplier) {
        throw createError({
          statusCode: 404,
          statusMessage: "Product supplier not found",
        });
      }
      return { ...supplier, ...data };
    }
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
