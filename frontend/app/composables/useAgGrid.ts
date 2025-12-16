/**
 * Composable for AG Grid integration
 * Handles data fetching and grid configuration
 */

import type { Product, ProductListResponse, ProductFilters } from "~/types/product";
import { logger } from "~~/server/utils/logger";

export const useAgGridProducts = () => {
  /**
   * Fetch products with filters and pagination
   */
  const fetchProducts = async (params: {
    page: number;
    pageSize: number;
    sortModel?: Array<{ colId: string; sort: "asc" | "desc" }>;
    filterModel?: Record<string, any>;
    search?: string;
    supplierId?: string;
  }): Promise<{ rowData: Product[]; totalRows: number }> => {
    try {
      // Build query parameters
      const queryParams: ProductFilters = {
        page: params.page,
        page_size: params.pageSize,
        ...(params.search && { search: params.search }),
        ...(params.supplierId && { supplier_id: params.supplierId }),
      };

      // Add sorting
      if (params.sortModel && params.sortModel.length > 0) {
        queryParams.sort = params.sortModel[0].colId;
        queryParams.order = params.sortModel[0].sort;
      }

      // Add filters (simplified - can be expanded)
      if (params.filterModel) {
        Object.entries(params.filterModel).forEach(([key, filter]) => {
          if (filter.filterType === "text") {
            queryParams.search = filter.filter;
          } else if (filter.filterType === "number") {
            if (filter.type === "greaterThan") {
              if (key === "dir") queryParams.min_dir = filter.filter;
              if (key === "stockout_risk") queryParams.min_risk = filter.filter;
              if (key === "current_stock") queryParams.min_stock = filter.filter;
            } else if (filter.type === "lessThan") {
              if (key === "dir") queryParams.max_dir = filter.filter;
              if (key === "stockout_risk") queryParams.max_risk = filter.filter;
              if (key === "current_stock") queryParams.max_stock = filter.filter;
            }
          } else if (filter.filterType === "set") {
            if (key === "status") queryParams.status = filter.values[0] as any;
            if (key === "category") queryParams.category = filter.values[0];
          }
        });
      }

      // Build query string
      const queryString = new URLSearchParams(
        Object.entries(queryParams)
          .filter(([_, v]) => v !== undefined && v !== null && v !== "")
          .map(([k, v]) => [k, String(v)])
      ).toString();

      const response = await $fetch<ProductListResponse>(
        `/api/products${queryString ? `?${queryString}` : ""}`
      );

      return {
        rowData: response.items,
        totalRows: response.total,
      };
    } catch (error: any) {
      // Re-throw 401 errors so they can be handled by the page
      // Other errors are also re-thrown
      logger.error("Error fetching products", { error });
      throw error;
    }
  };

  return {
    fetchProducts,
  };
};
