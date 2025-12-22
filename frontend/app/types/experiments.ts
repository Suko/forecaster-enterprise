/**
 * Experiments Page Types
 * Types for Test Bed and ROI Calculator
 */

// Available forecast models
export interface ForecastModel {
  id: string;
  name: string;
  description: string;
  is_ml: boolean;
}

// Date range for historical data
export interface DateRange {
  min_date: string;
  max_date: string;
  total_days: number;
}

// Forecast request for test bed
export interface TestBedForecastRequest {
  item_ids: string[];
  prediction_length: number;
  model: string;
  include_baseline: boolean;
  run_all_methods?: boolean; // Run all methods for comparison (Test Bed use case)
  skip_persistence?: boolean; // Skip saving to database (Test Bed use case)
  training_end_date?: string; // YYYY-MM-DD format for backtesting
}

// Single prediction
export interface Prediction {
  date: string;
  point_forecast: number;
  quantiles?: {
    p10?: number;
    p50?: number;
    p90?: number;
  };
}

// Item forecast result
export interface ItemForecast {
  item_id: string;
  method_used: string;
  predictions: Prediction[];
  classification?: SKUClassification;
}

// SKU classification info
export interface SKUClassification {
  abc_class: string;
  xyz_class: string;
  demand_pattern: string;
  forecastability_score: number;
  recommended_method: string;
  expected_mape_range: [number, number];
  warnings: string[];
}

// Forecast response
export interface ForecastResponse {
  forecast_id: string;
  primary_model: string;
  forecasts: ItemForecast[];
}

// Historical data point
export interface HistoricalDataPoint {
  date: string;
  units_sold: number;
}

// Quality metrics
export interface MethodQuality {
  method: string;
  predictions_count: number;
  actuals_count: number;
  mape: number | null;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
}

export interface QualityResponse {
  item_id: string;
  period: {
    start: string | null;
    end: string | null;
  };
  methods: MethodQuality[];
}

// Chart data series
export interface ChartDataSeries {
  label: string;
  data: (number | null)[];
  borderColor: string;
  backgroundColor: string;
  borderWidth: number;
  borderDash?: number[];
  pointRadius: number;
  pointStyle?: string;
  fill: boolean;
  tension: number;
  spanGaps: boolean;
}

export interface ChartMetrics {
  mape: number | null;
  rmse: number | null;
  mae: number | null;
  forecastedSales?: number | null;
  actualSales?: number | null;
}

export interface ChartData {
  itemId: string;
  itemName: string;
  statistics: MethodQuality[];
  metrics: ChartMetrics;
  cutoffDate?: string;
  chartConfig: {
    labels: string[];
    datasets: any[];
  };
}

// Test bed state
export interface TestBedState {
  selectedLocation: string;
  selectedSku: string;
  selectedCategory: string;
  selectedSupplier: string;
  selectedModel: string;
  forecastHorizon: number;
  isLoading: boolean;
  error: string | null;
}

// ROI Calculator types
export interface ROICalculatorState {
  selectedSku: string;
  forecastHorizon: number;
  holdingCostPercent: number;
  stockoutCostMultiplier: number;
  isLoading: boolean;
  error: string | null;
}

export interface ROIMetrics {
  currentInventoryCost: number;
  optimizedInventoryCost: number;
  potentialSavings: number;
  savingsPercent: number;
  stockoutReduction: number;
}

// Backfill actuals request
export interface BackfillActualsRequest {
  item_id: string;
  actuals: Array<{
    date: string;
    actual_value: number;
  }>;
}

export interface BackfillActualsResponse {
  updated_count: number;
  message: string;
}

// Product with minimal fields for experiments
export interface ExperimentProduct {
  item_id: string;
  product_name: string;
  category?: string;
}

// Category list
export interface CategoryListResponse {
  categories: string[];
}

