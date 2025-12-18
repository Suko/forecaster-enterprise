/**
 * Composable for AG Grid integration
 * Handles data fetching and grid configuration
 */

	import type { Product, ProductListResponse, ProductFilters } from "~/types/product";

	type AgGridTextFilter = { filterType: "text"; filter?: string };
	type AgGridNumberFilter = {
	  filterType: "number";
	  type?: "greaterThan" | "lessThan";
	  filter?: number;
	};
	type AgGridSetFilter = { filterType: "set"; values?: string[] };
	type AgGridFilter = AgGridTextFilter | AgGridNumberFilter | AgGridSetFilter;

	const isProductStatus = (value: string): value is NonNullable<ProductFilters["status"]> =>
	  value === "understocked" || value === "normal" || value === "overstocked";

	export const useAgGridProducts = () => {
	  /**
	   * Fetch products with filters and pagination
	   */
  const fetchProducts = async (params: {
	    page: number;
	    pageSize: number;
	    sortModel?: Array<{ colId: string; sort: "asc" | "desc" }>;
	    filterModel?: Record<string, AgGridFilter>;
	    search?: string;
	    supplierId?: string;
	  }): Promise<{ rowData: Product[]; totalRows: number }> => {
    // Build query parameters
    const queryParams: ProductFilters = {
      page: params.page,
      page_size: params.pageSize,
      ...(params.search && { search: params.search }),
      ...(params.supplierId && { supplier_id: params.supplierId }),
    };

    // Add sorting
    if (params.sortModel && params.sortModel.length > 0) {
      queryParams.sort = params.sortModel[0]!.colId;
      queryParams.order = params.sortModel[0]!.sort;
    }

	    // Add filters (simplified - can be expanded)
	    if (params.filterModel) {
	      Object.entries(params.filterModel).forEach(([key, filter]) => {
	        if (filter.filterType === "text") {
	          if (typeof filter.filter === "string") queryParams.search = filter.filter;
	        } else if (filter.filterType === "number") {
	          if (typeof filter.filter !== "number") return;
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
	          const value = filter.values?.[0];
	          if (typeof value !== "string") return;
	          if (key === "status" && isProductStatus(value)) queryParams.status = value;
	          if (key === "category") queryParams.category = value;
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
  };

  return {
    fetchProducts,
  };
};
