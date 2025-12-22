import type {
  ForecastModel,
  DateRange,
  ForecastResponse,
  TestBedForecastRequest,
  HistoricalDataPoint,
  QualityResponse,
  BackfillActualsRequest,
  BackfillActualsResponse,
  ExperimentProduct,
  CategoryListResponse,
} from "~/types/experiments";

/**
 * Composable for Experiments page API calls
 * Handles Test Bed and ROI Calculator functionality
 */
export const useExperiments = () => {
  /**
   * Get available forecast models
   */
  const fetchModels = async (): Promise<ForecastModel[]> => {
    return await $fetch<ForecastModel[]>("/api/experiments/models");
  };

  /**
   * Get date range for historical data
   */
  const fetchDateRange = async (itemId?: string): Promise<DateRange> => {
    const params = new URLSearchParams();
    if (itemId) params.append("item_id", itemId);
    const url = `/api/experiments/date-range${params.toString() ? `?${params.toString()}` : ""}`;
    return await $fetch<DateRange>(url);
  };

  /**
   * Generate forecast using existing forecast endpoint
   */
  const generateForecast = async (request: TestBedForecastRequest): Promise<ForecastResponse> => {
    return await $fetch<ForecastResponse>("/api/experiments/forecast", {
      method: "POST",
      body: request,
    });
  };

  /**
   * Get historical data for an item
   */
  const fetchHistoricalData = async (
    itemId: string,
    startDate?: string,
    endDate?: string
  ): Promise<HistoricalDataPoint[]> => {
    const params = new URLSearchParams();
    params.append("item_id", itemId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    return await $fetch<HistoricalDataPoint[]>(`/api/experiments/historical?${params.toString()}`);
  };

  /**
   * Backfill actual values for quality testing
   */
  const backfillActuals = async (request: BackfillActualsRequest): Promise<BackfillActualsResponse> => {
    return await $fetch<BackfillActualsResponse>("/api/experiments/actuals", {
      method: "POST",
      body: request,
    });
  };

  /**
   * Get quality metrics for an item
   */
  const fetchQualityMetrics = async (
    itemId: string,
    startDate?: string,
    endDate?: string
  ): Promise<QualityResponse> => {
    const params = new URLSearchParams();
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    const url = `/api/experiments/quality/${encodeURIComponent(itemId)}${params.toString() ? `?${params.toString()}` : ""}`;
    return await $fetch<QualityResponse>(url);
  };

  /**
   * Fetch products with optional filters
   */
  const fetchProducts = async (params?: {
    location_id?: string;
    category?: string;
    supplier_id?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<{ items: ExperimentProduct[]; total: number }> => {
    const queryParams = new URLSearchParams();
    if (params?.location_id) queryParams.append("location_id", params.location_id);
    if (params?.category) queryParams.append("category", params.category);
    if (params?.supplier_id) queryParams.append("supplier_id", params.supplier_id);
    if (params?.search) queryParams.append("search", params.search);
    if (params?.page) queryParams.append("page", params.page.toString());
    if (params?.page_size) queryParams.append("page_size", params.page_size.toString());

    const url = `/api/products${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    return await $fetch(url);
  };

  /**
   * Fetch product categories
   */
  const fetchCategories = async (): Promise<string[]> => {
    const response = await $fetch<CategoryListResponse>("/api/experiments/categories");
    return response.categories;
  };

  /**
   * Calculate rolling average for chart data
   */
  const calculateRollingAverage = (data: number[], window: number): (number | null)[] => {
    const result: (number | null)[] = [];
    for (let i = 0; i < data.length; i++) {
      if (i < window - 1) {
        result.push(null);
      } else {
        const slice = data.slice(i - window + 1, i + 1);
        const avg = slice.reduce((sum, val) => sum + val, 0) / window;
        result.push(Math.round(avg * 100) / 100);
      }
    }
    return result;
  };

  /**
   * Format currency for display
   */
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat("de-DE", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(value);
  };

  /**
   * Format percentage for display
   */
  const formatPercent = (value: number | null): string => {
    if (value === null) return "N/A";
    return `${value.toFixed(1)}%`;
  };

  return {
    fetchModels,
    fetchDateRange,
    generateForecast,
    fetchHistoricalData,
    backfillActuals,
    fetchQualityMetrics,
    fetchProducts,
    fetchCategories,
    calculateRollingAverage,
    formatCurrency,
    formatPercent,
  };
};

