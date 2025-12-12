import type { Supplier, SupplierListResponse } from "~/types/supplier";

export const useSuppliers = () => {
  const fetchSuppliers = async (params?: {
    search?: string
    supplier_type?: string
    page?: number
    page_size?: number
  }): Promise<SupplierListResponse> => {
    return await $fetch<SupplierListResponse>("/api/suppliers", { query: params });
  };

  const fetchSupplier = async (id: string): Promise<Supplier> => {
    return await $fetch<Supplier>(`/api/suppliers/${encodeURIComponent(id)}`);
  };

  return {
    fetchSuppliers,
    fetchSupplier,
  };
};

