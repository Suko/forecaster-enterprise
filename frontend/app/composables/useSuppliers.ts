import type { Supplier, SupplierListResponse } from "~/types/supplier";

export const useSuppliers = () => {
  const fetchSuppliers = async (params?: {
    search?: string;
    supplier_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<SupplierListResponse> => {
    return await $fetch<SupplierListResponse>("/api/suppliers", { query: params });
  };

  const fetchSupplier = async (id: string): Promise<Supplier> => {
    return await $fetch<Supplier>(`/api/suppliers/${encodeURIComponent(id)}`);
  };

  const updateSupplier = async (
    id: string,
    data: {
      name?: string;
      contact_email?: string;
      contact_phone?: string;
      address?: string;
      supplier_type?: string;
      default_moq?: number;
      default_lead_time_days?: number;
      notes?: string;
      apply_to_existing?: boolean;
    }
  ): Promise<Supplier> => {
    return await $fetch<Supplier>(`/api/suppliers/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: data,
    });
  };

  return {
    fetchSuppliers,
    fetchSupplier,
    updateSupplier,
  };
};
