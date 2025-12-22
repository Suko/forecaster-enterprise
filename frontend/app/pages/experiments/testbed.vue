<template>
  <div class="p-6 space-y-6">
    <ExperimentsTabs />
    <div class="flex items-center justify-between">
      <h1 class="text-3xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
        Test Bed - Forecast vs Actual
      </h1>
    </div>

    <!-- Controls Card -->
    <UCard>
      <template #header>
        <h3 class="text-lg font-semibold">Forecast Configuration</h3>
      </template>

      <!-- Filters Row -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <!-- Location Filter -->
        <UFormField label="Store/Location">
          <USelect
            v-model="selectedLocation"
            :items="locationOptions"
            placeholder="All Stores"
            :loading="loadingLocations"
          />
        </UFormField>

        <!-- Category Filter -->
        <UFormField label="Category">
          <USelect
            v-model="selectedCategory"
            :items="categoryOptions"
            placeholder="All Categories"
            :loading="loadingCategories"
          />
        </UFormField>

        <!-- SKU/Product Filter -->
        <UFormField label="SKU/Product">
          <USelect
            v-model="selectedSku"
            :items="productOptions"
            placeholder="Select a product"
            :loading="loadingProducts"
            :ui="{ content: 'min-w-fit max-w-[600px]' }"
          />
        </UFormField>
      </div>

      <!-- Forecast Settings Row -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <!-- Forecast Model -->
        <UFormField label="Forecast Model">
          <USelect
            v-model="selectedModel"
            :items="modelOptions"
            placeholder="Select model"
            :loading="loadingModels"
          />
        </UFormField>

        <!-- Forecast Horizon -->
        <UFormField
          label="Forecast Horizon (days)"
          hint="Max: 90 days"
        >
          <UInput
            v-model.number="forecastHorizon"
            type="number"
            :min="1"
            :max="90"
            placeholder="30"
          />
        </UFormField>

        <!-- Date Range Info -->
        <UFormField label="Data Range">
          <div class="text-sm text-muted py-2">
            <template v-if="dateRange">
              {{ dateRange.min_date }} to {{ dateRange.max_date }}
              <br>
              <span class="text-xs">({{ dateRange.total_days }} days available)</span>
            </template>
            <template v-else>
              Loading...
            </template>
          </div>
        </UFormField>
      </div>

      <!-- Chart Options -->
      <div class="border-t pt-4 flex flex-wrap items-center gap-6">
        <UCheckbox
          v-model="showRollingAverage"
          label="Show Rolling Average"
        />
        <div
          v-if="showRollingAverage"
          class="flex items-center gap-2"
        >
          <span class="text-sm">Window:</span>
          <USelect
            v-model="rollingAverageWindow"
            :items="rollingAverageOptions"
            class="w-24"
          />
        </div>
        <div
          v-if="chartData && availableMethodsForSelection.length > 0"
          class="flex items-center gap-2"
        >
          <span class="text-sm">Show Model:</span>
          <USelect
            v-model="selectedModelForChart"
            :items="availableMethodsForSelection"
            class="w-48"
          />
        </div>
      </div>

      <!-- Generate Button -->
      <div class="mt-6 flex items-center gap-4">
        <UButton
          :loading="isGenerating"
          :disabled="!selectedSku"
          @click="generateForecast"
        >
          {{ isGenerating ? 'Generating...' : 'Generate Forecast & Compare' }}
        </UButton>
        <div
          v-if="!selectedSku"
          class="text-sm text-amber-600"
        >
          Please select a product to generate forecast
        </div>
        <div
          v-else-if="chartData"
          class="text-sm text-muted"
        >
          Forecast generated for {{ forecastHorizon }} days
        </div>
      </div>
    </UCard>

    <!-- Error Alert -->
    <UAlert
      v-if="error"
      color="error"
      variant="soft"
      title="Error"
      :description="error"
      :close-button="{ icon: 'i-lucide-x', color: 'error', variant: 'link' }"
      @close="error = null"
    />

    <!-- Chart Section -->
    <UCard v-if="chartData">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold">
            {{ chartData.itemName }} ({{ chartData.itemId }})
          </h3>
          <div class="flex items-center gap-4">
            <!-- Metrics Display -->
            <div
              v-if="chartData.metrics"
              class="flex gap-4 text-sm"
            >
              <div class="flex flex-col">
                <span class="text-xs text-muted">MAPE</span>
                <span class="font-semibold">
                  {{ chartData.metrics.mape !== null ? chartData.metrics.mape.toFixed(1) + '%' : 'N/A' }}
                </span>
              </div>
              <div class="flex flex-col">
                <span class="text-xs text-muted">RMSE</span>
                <span class="font-semibold">
                  {{ chartData.metrics.rmse !== null ? chartData.metrics.rmse.toFixed(2) : 'N/A' }}
                </span>
              </div>
              <div class="flex flex-col">
                <span class="text-xs text-muted">MAE</span>
                <span class="font-semibold">
                  {{ chartData.metrics.mae !== null ? chartData.metrics.mae.toFixed(2) : 'N/A' }}
                </span>
              </div>
              <div
                v-if="chartData.metrics.forecastedSales !== null && chartData.metrics.forecastedSales !== undefined"
                class="flex flex-col"
              >
                <span class="text-xs text-muted">Forecasted</span>
                <span class="font-semibold">
                  {{ chartData.metrics.forecastedSales.toFixed(0) }}
                </span>
              </div>
              <div
                v-if="chartData.metrics.actualSales !== null && chartData.metrics.actualSales !== undefined"
                class="flex flex-col"
              >
                <span class="text-xs text-muted">Actual</span>
                <span class="font-semibold">
                  {{ chartData.metrics.actualSales.toFixed(0) }}
                </span>
              </div>
            </div>
            <!-- Reset Zoom Button -->
            <UButton
              v-if="showResetZoom"
              variant="ghost"
              size="xs"
              icon="i-lucide-zoom-out"
              @click="resetZoom"
            >
              Reset Zoom
            </UButton>
          </div>
        </div>
      </template>

      <div class="relative">
        <Line
          ref="chartRef"
          :data="chartData.chartConfig as any"
          :options="chartOptions"
        />
      </div>
    </UCard>

    <!-- SKU Classification Details -->
    <UCard v-if="skuClassification" class="mt-6">
      <template #header>
        <h3 class="text-lg font-semibold">SKU Classification & System Recommendation</h3>
      </template>
      <div class="space-y-4">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="flex flex-col">
            <span class="text-xs text-muted mb-1">ABC Classification</span>
            <span class="text-lg font-semibold">{{ skuClassification.abc_class }}</span>
            <span class="text-xs text-muted mt-1">
              {{ skuClassification.abc_class === 'A' ? 'Top 80% revenue' : skuClassification.abc_class === 'B' ? 'Next 15% revenue' : 'Bottom 5% revenue' }}
            </span>
          </div>
          <div class="flex flex-col">
            <span class="text-xs text-muted mb-1">XYZ Classification</span>
            <span class="text-lg font-semibold">{{ skuClassification.xyz_class }}</span>
            <span class="text-xs text-muted mt-1">
              {{ skuClassification.xyz_class === 'X' ? 'Low variability (CV < 0.5)' : skuClassification.xyz_class === 'Y' ? 'Medium variability (0.5-1.0)' : 'High variability (≥ 1.0)' }}
            </span>
          </div>
          <div class="flex flex-col">
            <span class="text-xs text-muted mb-1">Demand Pattern</span>
            <span class="text-lg font-semibold capitalize">{{ skuClassification.demand_pattern }}</span>
            <span class="text-xs text-muted mt-1">
              {{ skuClassification.demand_pattern === 'regular' ? 'ADI ≤ 1.32' : skuClassification.demand_pattern === 'intermittent' ? 'ADI > 1.32' : 'ADI > 1.32 & CV² > 0.49' }}
            </span>
          </div>
          <div class="flex flex-col">
            <span class="text-xs text-muted mb-1">Forecastability Score</span>
            <span class="text-lg font-semibold">{{ (skuClassification.forecastability_score * 100).toFixed(0) }}%</span>
            <span class="text-xs text-muted mt-1">0-100% (higher is better)</span>
          </div>
        </div>
        <div class="border-t pt-4">
          <div class="flex items-center justify-between">
            <div class="flex flex-col">
              <span class="text-xs text-muted mb-1">System Recommended Method</span>
              <div class="flex items-center gap-2">
                <span class="text-lg font-semibold">{{ getModelDisplayName(skuClassification.recommended_method) }}</span>
                <span class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  <span>✓</span>
                  <span>Recommended</span>
                </span>
              </div>
            </div>
            <div class="flex flex-col text-right">
              <span class="text-xs text-muted mb-1">Expected MAPE Range</span>
              <span class="text-sm font-medium">
                {{ skuClassification.expected_mape_range[0].toFixed(1) }}% - {{ skuClassification.expected_mape_range[1].toFixed(1) }}%
              </span>
            </div>
          </div>
        </div>
        <div v-if="skuClassification.warnings && skuClassification.warnings.length > 0" class="border-t pt-4">
          <span class="text-xs text-muted mb-2 block">Warnings</span>
          <ul class="list-disc list-inside space-y-1">
            <li v-for="warning in skuClassification.warnings" :key="warning" class="text-sm text-amber-600 dark:text-amber-400">
              {{ warning }}
            </li>
          </ul>
        </div>
      </div>
    </UCard>

    <!-- Comparison Table -->
    <UCard v-if="chartData" class="mt-6">
      <template #header>
        <h3 class="text-lg font-semibold">Model Comparison</h3>
      </template>
      <div v-if="!chartData.statistics || chartData.statistics.length === 0" class="text-center py-8 text-muted">
        <p>No quality metrics available yet.</p>
        <p class="text-sm mt-2">Generate a forecast and backfill actuals to see model comparison.</p>
      </div>
      <UTable
        v-else
        :data="chartData.statistics"
        :columns="comparisonTableColumns"
      >
        <template #method-cell="{ row }">
          <div class="flex items-center gap-2">
            <span class="font-medium">{{ getModelDisplayName(row.original.method) }}</span>
            <span
              v-if="systemRecommendedMethod && row.original.method === systemRecommendedMethod"
              class="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
              title="System recommended based on ABC-XYZ classification"
            >
              <span>✓</span>
              <span>Recommended</span>
            </span>
          </div>
        </template>
        <template #recommended-cell="{ row }">
          <div class="flex items-center gap-2">
            <span
              v-if="systemRecommendedMethod && row.original.method === systemRecommendedMethod"
              class="text-green-600 dark:text-green-400 font-medium"
            >
              ✓ System Choice
            </span>
            <span
              v-else-if="systemRecommendedMethod"
              class="text-muted text-sm"
            >
              —
            </span>
            <span
              v-else
              class="text-muted text-sm"
            >
              No classification
            </span>
          </div>
        </template>
        <template #mape-cell="{ row }">
          <span :class="row.original.mape !== null && row.original.mape !== undefined ? '' : 'text-muted'">
            {{ row.original.mape !== null && row.original.mape !== undefined ? row.original.mape.toFixed(1) + '%' : 'N/A' }}
          </span>
        </template>
        <template #rmse-cell="{ row }">
          <span :class="row.original.rmse !== null && row.original.rmse !== undefined ? '' : 'text-muted'">
            {{ row.original.rmse !== null && row.original.rmse !== undefined ? row.original.rmse.toFixed(2) : 'N/A' }}
          </span>
        </template>
        <template #mae-cell="{ row }">
          <span :class="row.original.mae !== null && row.original.mae !== undefined ? '' : 'text-muted'">
            {{ row.original.mae !== null && row.original.mae !== undefined ? row.original.mae.toFixed(2) : 'N/A' }}
          </span>
        </template>
        <template #bias-cell="{ row }">
          <span :class="row.original.bias !== null && row.original.bias !== undefined ? '' : 'text-muted'">
            {{ row.original.bias !== null && row.original.bias !== undefined ? row.original.bias.toFixed(2) : 'N/A' }}
          </span>
        </template>
        <template #samples-cell="{ row }">
          <span class="text-muted">{{ row.original.predictions_count || 0 }}</span>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { Line } from "vue-chartjs";
import type {
  ForecastModel,
  DateRange,
  ForecastResponse,
  HistoricalDataPoint,
  MethodQuality,
  ExperimentProduct,
  ItemForecast,
  ChartData,
  ChartMetrics,
  SKUClassification,
} from "~/types/experiments";
import type { Location } from "~/types/location";

definePageMeta({
  layout: "dashboard",
});

// Composables
const { handleAuthError } = useAuthError();

// State - Filters
const selectedLocation = ref<string>("__all__");
const selectedCategory = ref<string>("__all__");
const selectedSku = ref<string>("");
const selectedModel = ref<string>("chronos-2");
const forecastHorizon = ref<number>(30);

// State - Chart Options
const showRollingAverage = ref(true);
const rollingAverageWindow = ref<number>(7);

// State - Data
const locations = ref<Location[]>([]);
const categories = ref<string[]>([]);
const products = ref<ExperimentProduct[]>([]);
const models = ref<ForecastModel[]>([]);
const dateRange = ref<DateRange | null>(null);

// State - Loading
const loadingLocations = ref(false);
const loadingCategories = ref(false);
const loadingProducts = ref(false);
const loadingModels = ref(false);
const isGenerating = ref(false);

// State - Results
const error = ref<string | null>(null);
const chartData = ref<ChartData | null>(null);
const chartRef = ref<InstanceType<typeof Line> | null>(null);
const showResetZoom = ref(false);
const selectedModelForChart = ref<string>("");
const allForecastsByMethod = ref<Map<string, ItemForecast>>(new Map());
const currentForecastRunId = ref<string | null>(null);
const actualSalesTotalRef = ref<number | null>(null); // Store actual sales total (doesn't change with model)
const systemRecommendedMethod = ref<string | null>(null); // Store system's recommended method from classification
const skuClassification = ref<SKUClassification | null>(null); // Store full classification details

// Store raw data for recalculating rolling average without regenerating forecast
const rawHistoricalValues = ref<number[]>([]);
const rawHistoricalDates = ref<string[]>([]);
const rawForecastData = ref<number[]>([]);
const rawForecastDates = ref<string[]>([]);
const rawActualData = ref<(number | null)[]>([]);
const rawAllDates = ref<string[]>([]);

// Comparison table columns
const comparisonTableColumns = computed(() => [
  {
    id: "method",
    accessorKey: "method",
    header: "Model",
  },
  {
    id: "mape",
    accessorKey: "mape",
    header: "MAPE",
  },
  {
    id: "rmse",
    accessorKey: "rmse",
    header: "RMSE",
  },
  {
    id: "mae",
    accessorKey: "mae",
    header: "MAE",
  },
  {
    id: "bias",
    accessorKey: "bias",
    header: "Bias",
  },
  {
    id: "samples",
    accessorKey: "predictions_count",
    header: "Samples",
  },
  {
    id: "recommended",
    accessorKey: "recommended",
    header: "System Recommendation",
  },
]);

// Options for selects
// Note: Cannot use empty string as value - use special value instead
const locationOptions = computed(() => [
  { label: "All Stores", value: "__all__" },
  ...locations.value.map((l) => ({ label: l.name, value: l.location_id })),
]);

const categoryOptions = computed(() => [
  { label: "All Categories", value: "__all__" },
  ...categories.value.map((c) => ({ label: c, value: c })),
]);

const productOptions = computed(() =>
  products.value.map((p) => ({
    label: `${p.item_id} - ${p.product_name}`,
    value: p.item_id,
  }))
);

const modelOptions = computed(() =>
  models.value.map((m) => ({
    label: m.name,
    value: m.id,
  }))
);

const rollingAverageOptions = [
  { label: "3 days", value: 3 },
  { label: "7 days", value: 7 },
  { label: "14 days", value: 14 },
  { label: "30 days", value: 30 },
];

// Chart options
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: true,
  aspectRatio: 3,
  scales: {
    y: {
      beginAtZero: true,
      title: { display: true, text: "Units Sold" },
      ticks: { precision: 0 },
    },
    x: {
      title: { display: true, text: "Date" },
      ticks: { maxRotation: 45, minRotation: 45 },
    },
  },
  plugins: {
    legend: {
      display: true,
      position: "top" as const,
      labels: { padding: 15, usePointStyle: true },
    },
    title: { display: false },
    tooltip: {
      mode: "index" as const,
      intersect: false,
    },
    zoom: {
      zoom: {
        wheel: {
          enabled: true,
          speed: 0.1,
        },
        pinch: {
          enabled: true,
        },
        mode: "x" as const,
        drag: {
          enabled: true,
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          borderColor: "rgba(59, 130, 246, 0.3)",
          borderWidth: 1,
        },
      },
      pan: {
        enabled: true,
        mode: "x" as const,
        modifierKey: "ctrl" as const,
      },
    },
    annotation: chartData.value?.cutoffDate
      ? {
          annotations: {
            cutoffLine: {
              type: "line" as const,
              xMin: chartData.value.cutoffDate,
              xMax: chartData.value.cutoffDate,
              borderColor: "rgb(239, 68, 68)",
              borderWidth: 2,
              borderDash: [5, 5],
              label: {
                display: true,
                content: `Cutoff: ${chartData.value.cutoffDate}`,
                position: "start" as const,
                backgroundColor: "rgba(239, 68, 68, 0.8)",
                color: "white",
                font: {
                  size: 12,
                },
              },
            },
          },
        }
      : undefined,
  },
  interaction: {
    mode: "nearest" as const,
    axis: "x" as const,
    intersect: false,
  },
  onHover: (_event: any, activeElements: any[]) => {
    // Track zoom state
    if (chartRef.value?.chart) {
      const chart = chartRef.value.chart as any;
      if (chart.isZoomed) {
        showResetZoom.value = true;
      }
    }
  },
}));

const resetZoom = () => {
  if (chartRef.value?.chart) {
    (chartRef.value.chart as any).resetZoom();
    showResetZoom.value = false;
  }
};

// Model color mapping
const modelColors: Record<string, { border: string; bg: string }> = {
  "chronos-2": { border: "rgb(20, 184, 166)", bg: "rgba(20, 184, 166, 0.1)" },
  statistical_ma7: { border: "rgb(236, 72, 153)", bg: "rgba(236, 72, 153, 0.15)" },
  sba: { border: "rgb(168, 85, 247)", bg: "rgba(168, 85, 247, 0.1)" },
  croston: { border: "rgb(249, 115, 22)", bg: "rgba(249, 115, 22, 0.1)" },
  min_max: { border: "rgb(34, 197, 94)", bg: "rgba(34, 197, 94, 0.1)" },
};

// Helper functions for styling
const getStatBorderClass = (method: string) => {
  if (method === "chronos-2") return "border-teal-400";
  if (method === "statistical_ma7") return "border-pink-400";
  return "border-gray-200";
};

const getStatTextClass = (method: string) => {
  if (method === "chronos-2") return "text-teal-600";
  if (method === "statistical_ma7") return "text-pink-600";
  return "text-gray-500";
};

const getStatValueClass = (method: string) => {
  if (method === "chronos-2") return "text-teal-700";
  if (method === "statistical_ma7") return "text-pink-700";
  return "text-gray-900";
};

const getModelDisplayName = (method: string) => {
  const model = models.value.find((m) => m.id === method);
  return model?.name || method;
};

// Available methods for chart selection (from quality metrics)
const availableMethodsForSelection = computed(() => {
  if (!chartData.value?.statistics || chartData.value.statistics.length === 0) {
    return [];
  }
  return chartData.value.statistics.map((stat) => ({
    label: getModelDisplayName(stat.method),
    value: stat.method,
  }));
});

// Rolling average calculation
const calculateRollingAverage = (values: number[], window: number): (number | null)[] => {
  const result: (number | null)[] = [];
  for (let i = 0; i < values.length; i++) {
    if (i < window - 1) {
      result.push(null);
    } else {
      const slice = values.slice(i - window + 1, i + 1);
      const avg = slice.reduce((sum, val) => sum + val, 0) / window;
      result.push(Math.round(avg * 100) / 100);
    }
  }
  return result;
};

// Quality metrics calculation (in-memory for Test Bed when skip_persistence=true)
const calculateMAPE = (actuals: number[], forecasts: number[]): number | null => {
  if (actuals.length !== forecasts.length || actuals.length === 0) return null;
  const errors: number[] = [];
  for (let i = 0; i < actuals.length; i++) {
    const actual = actuals[i];
    const forecast = forecasts[i];
    if (actual !== undefined && forecast !== undefined && actual > 0) {
      errors.push(Math.abs((actual - forecast) / actual));
    }
  }
  if (errors.length === 0) return null;
  return (100.0 / errors.length) * errors.reduce((sum, e) => sum + e, 0);
};

const calculateMAE = (actuals: number[], forecasts: number[]): number | null => {
  if (actuals.length !== forecasts.length || actuals.length === 0) return null;
  const errors = actuals.map((a, i) => {
    const f = forecasts[i];
    return f !== undefined ? Math.abs(a - f) : 0;
  });
  return errors.reduce((sum, e) => sum + e, 0) / errors.length;
};

const calculateRMSE = (actuals: number[], forecasts: number[]): number | null => {
  if (actuals.length !== forecasts.length || actuals.length === 0) return null;
  const squaredErrors = actuals.map((a, i) => {
    const f = forecasts[i];
    return f !== undefined ? Math.pow(a - f, 2) : 0;
  });
  const mse = squaredErrors.reduce((sum, e) => sum + e, 0) / squaredErrors.length;
  return Math.sqrt(mse);
};

const calculateBias = (actuals: number[], forecasts: number[]): number | null => {
  if (actuals.length !== forecasts.length || actuals.length === 0) return null;
  const errors = actuals.map((a, i) => {
    const f = forecasts[i];
    return f !== undefined ? f - a : 0;
  });
  return errors.reduce((sum, e) => sum + e, 0) / errors.length;
};

// Data loading functions
const loadLocations = async () => {
  loadingLocations.value = true;
  try {
    const response = await $fetch<{ items: Location[] }>("/api/locations");
    locations.value = response.items || [];
  } catch (err) {
    await handleAuthError(err);
    locations.value = [];
  } finally {
    loadingLocations.value = false;
  }
};

const loadCategories = async () => {
  loadingCategories.value = true;
  try {
    const response = await $fetch<{ categories: string[] }>("/api/experiments/categories");
    categories.value = response.categories || [];
  } catch (err) {
    await handleAuthError(err);
    categories.value = [];
  } finally {
    loadingCategories.value = false;
  }
};

const loadProducts = async () => {
  loadingProducts.value = true;
  try {
    const params = new URLSearchParams();
    if (selectedLocation.value && selectedLocation.value !== "__all__") {
      params.append("location_id", selectedLocation.value);
    }
    if (selectedCategory.value && selectedCategory.value !== "__all__") {
      params.append("category", selectedCategory.value);
    }
    params.append("page_size", "100");

    const url = `/api/products${params.toString() ? `?${params.toString()}` : ""}`;
    const response = await $fetch<{ items: ExperimentProduct[] }>(url);
    products.value = response.items || [];
  } catch (err) {
    await handleAuthError(err);
    products.value = [];
  } finally {
    loadingProducts.value = false;
  }
};

const loadModels = async () => {
  loadingModels.value = true;
  try {
    const response = await $fetch<ForecastModel[]>("/api/experiments/models");
    models.value = response || [];
  } catch (err) {
    await handleAuthError(err);
    models.value = [];
  } finally {
    loadingModels.value = false;
  }
};

const loadDateRange = async () => {
  try {
    const response = await $fetch<DateRange>("/api/experiments/date-range");
    dateRange.value = response;
  } catch (err) {
    await handleAuthError(err);
  }
};

// Watch filters to reload products
watch([selectedLocation, selectedCategory], () => {
  loadProducts();
  selectedSku.value = "";
});

// Generate forecast
const generateForecast = async () => {
  if (!selectedSku.value) return;

  isGenerating.value = true;
  error.value = null;
  chartData.value = null;

  // Ensure we have a valid model selected
  const modelToUse = selectedModel.value || "chronos-2";

  try {
    // Step 1: Get historical data
    const allHistoricalData = await $fetch<HistoricalDataPoint[]>(
      `/api/experiments/historical?item_id=${encodeURIComponent(selectedSku.value)}`
    );

    if (allHistoricalData.length === 0) {
      throw new Error("No historical data available for this product");
    }

    // Step 1.5: Calculate cutoff date for backtesting
    // Use latest date - forecast horizon to create a cutoff point
    const sortedDates = allHistoricalData.map((d) => d.date).sort();
    const latestDate = sortedDates[sortedDates.length - 1];
    if (!latestDate) {
      throw new Error("No historical data available");
    }
    const cutoffDateObj = new Date(latestDate);
    cutoffDateObj.setDate(cutoffDateObj.getDate() - forecastHorizon.value);
    const cutoffDate = cutoffDateObj.toISOString().split("T")[0];

    // Filter historical data to only show up to cutoff date (for backtesting visualization)
    const historicalDataFiltered = cutoffDate ? allHistoricalData.filter((d) => d.date <= cutoffDate) : allHistoricalData;

    // Step 2: Generate forecast (using selected model, not hardcoded)
    // Pass training_end_date (cutoff) for backtesting - this ensures forecasts start from cutoff + 1
    
    const forecastResponse = await $fetch<ForecastResponse>("/api/experiments/forecast", {
      method: "POST",
      body: {
        item_ids: [selectedSku.value],
        prediction_length: forecastHorizon.value,
        model: modelToUse, // Use selected model, not hardcoded
        include_baseline: true,
        run_all_methods: true, // Test Bed: run all methods for comparison
        skip_persistence: true, // Test Bed: don't save to database (testing/verification only)
        training_end_date: cutoffDate || undefined, // For backtesting: only use data up to this date
      },
    });

    if (!forecastResponse.forecasts || forecastResponse.forecasts.length === 0) {
      throw new Error("No forecast generated");
    }

    // When run_all_methods=true, we get multiple forecasts (one per method)
    // Use the primary model's forecast for the main chart, but keep all for metrics
    const forecast = forecastResponse.forecasts.find(f => f.method_used === modelToUse) || forecastResponse.forecasts[0];
    
    if (!forecast) {
      throw new Error("No forecast data available in response");
    }
    
    // Store system's recommended method and full classification (if available)
    if (forecast.classification) {
      // Store full classification details
      skuClassification.value = forecast.classification;
      
      // Map classification method names to our method IDs
      const methodMap: Record<string, string> = {
        "chronos2": "chronos-2",
        "chronos-2": "chronos-2",
        "ma7": "statistical_ma7",
        "statistical_ma7": "statistical_ma7",
        "sba": "sba",
        "croston": "croston",
        "min_max": "min_max",
      };
      systemRecommendedMethod.value = methodMap[forecast.classification.recommended_method] || forecast.classification.recommended_method;
    } else {
      systemRecommendedMethod.value = null;
      skuClassification.value = null;
    }
    
    // Store forecast_run_id for fetching other methods (only if not skip_persistence)
    // When skip_persistence=true, forecast_id is temporary and not in database
    const skipPersistence = true; // Test Bed always skips persistence
    if (!skipPersistence) {
      currentForecastRunId.value = forecastResponse.forecast_id;
    } else {
      currentForecastRunId.value = null; // Can't fetch from DB if not persisted
    }
    
    // Set initial selected model for chart
    selectedModelForChart.value = forecast.method_used || modelToUse;

    // Step 3: Calculate quality metrics
    // Note: If skip_persistence=true, we calculate metrics in-memory (no database backfill needed)
    // Get dates from forecast period - use actuals AFTER cutoff date for backtesting
    const forecastDates = forecast.predictions.map((p) => p.date);
    // Normalize dates to YYYY-MM-DD format for comparison
    const forecastDatesSet = new Set(forecastDates.map((d) => String(d).split("T")[0]));
    
    // Use all historical data (not filtered) to get actuals after cutoff
    const actualsForBackfill = cutoffDate ? allHistoricalData
      .filter((h) => {
        const hDate = h.date ? String(h.date).split("T")[0] : null; // Normalize to YYYY-MM-DD
        if (!hDate) return false;
        const isAfterCutoff = hDate > cutoffDate;
        const isInForecast = forecastDatesSet.has(hDate);
        return isAfterCutoff && isInForecast;
      })
      .map((h) => {
        const dateStr = h.date ? String(h.date).split("T")[0] : "";
        return {
          date: dateStr, // Ensure YYYY-MM-DD format
          actual_value: h.units_sold 
        };
      })
      .filter((a) => a.date !== "") : []; // Filter out invalid dates
    
    if (actualsForBackfill.length < forecastHorizon.value) {
      const forecastDatesList = Array.from(forecastDatesSet).sort();
      const backfilledDates = actualsForBackfill.map(a => a.date).sort();
      const missingDates = forecastDatesList.filter(d => !backfilledDates.includes(d));
      console.warn("Missing dates for backfill:", missingDates);
    }

    // Step 3.5: Calculate quality metrics
    // Since skip_persistence=true, we calculate metrics in-memory from forecast response
    let qualityMetrics: MethodQuality[] = [];
    let primaryMetrics: ChartMetrics = {
      mape: null,
      rmse: null,
      mae: null,
      forecastedSales: null,
      actualSales: null,
    };
    
    // Create a map of actuals by date for quick lookup
    const actualsByDate = new Map<string, number>();
    actualsForBackfill.forEach((a) => {
      if (a.date) {
        actualsByDate.set(a.date, a.actual_value);
      }
    });
    
    // Calculate metrics for each method in the forecast response
    // When run_all_methods=true, forecastResponse.forecasts contains all methods
    if (forecastResponse.forecasts && forecastResponse.forecasts.length > 0) {
      // Group forecasts by method (when run_all_methods=true, we get multiple ItemForecast objects)
      const forecastsByMethod = new Map<string, ItemForecast>();
      forecastResponse.forecasts.forEach((f) => {
        forecastsByMethod.set(f.method_used, f);
      });
      
      // Store all forecasts for model selector switching (when skip_persistence=true)
      allForecastsByMethod.value = forecastsByMethod;
      
      // Calculate metrics for each method
      for (const [method, methodForecast] of forecastsByMethod) {
        try {
          // Calculate metrics in-memory
          const predictions = methodForecast.predictions;
          const actuals: number[] = [];
          const forecasts: number[] = [];
          
          for (const pred of predictions) {
            const predDate = pred.date ? String(pred.date).split("T")[0] : null;
            if (predDate) {
              const actual = actualsByDate.get(predDate);
              if (actual !== undefined) {
                actuals.push(actual);
                forecasts.push(pred.point_forecast);
              }
            }
          }
          
          if (actuals.length > 0) {
            const mape = calculateMAPE(actuals, forecasts);
            const mae = calculateMAE(actuals, forecasts);
            const rmse = calculateRMSE(actuals, forecasts);
            const bias = calculateBias(actuals, forecasts);
            
            qualityMetrics.push({
              method,
              predictions_count: actuals.length,
              actuals_count: actuals.length,
              mape,
              mae,
              rmse,
              bias,
            });
          }
        } catch (err) {
          console.warn(`Error calculating metrics for method ${method}:`, err);
        }
      }
    }
    
    // Get metrics for the model that was actually used
    const actualModelUsedForMetrics = forecast.method_used || modelToUse;
    const selectedModelMetrics = qualityMetrics.find((m) => m.method === actualModelUsedForMetrics);
    
    if (selectedModelMetrics) {
      primaryMetrics = {
        mape: selectedModelMetrics.mape,
        rmse: selectedModelMetrics.rmse,
        mae: selectedModelMetrics.mae,
      };
    } else {
      console.warn(`No metrics found for method: ${actualModelUsedForMetrics}. Available methods:`, qualityMetrics.map((m) => m.method));
      // Try to use first available method as fallback
      if (qualityMetrics.length > 0) {
        const fallbackMetrics = qualityMetrics[0];
        if (fallbackMetrics) {
          primaryMetrics = {
            mape: fallbackMetrics.mape,
            rmse: fallbackMetrics.rmse,
            mae: fallbackMetrics.mae,
          };
        }
      }
    }

    // Step 5: Prepare chart data
    // Use the filtered historical data we created earlier
    const histDates = historicalDataFiltered.map((d) => d.date);
    const histValues = historicalDataFiltered.map((d) => d.units_sold);
    const forecastValues = forecast.predictions.map((p) => p.point_forecast);
    
    // Store raw data for reactive rolling average updates
    rawHistoricalValues.value = histValues;
    rawHistoricalDates.value = histDates;
    rawForecastData.value = forecastValues;
    rawForecastDates.value = forecastDates;

    // Get actuals after cutoff for ground truth line
    const actualsAfterCutoff = cutoffDate ? allHistoricalData
      .filter((h) => h.date && h.date > cutoffDate)
      .sort((a, b) => (a.date || "").localeCompare(b.date || "")) : [];
    
    // Calculate forecasted and actual sales totals for the selected method
    const forecastedSalesTotal = forecastValues.reduce((sum, val) => sum + val, 0);
    // Calculate actual sales total - this is the same for all models (historical data)
    const actualSalesTotal = actualsAfterCutoff.reduce((sum, a) => sum + (a.units_sold || 0), 0);
    // Store it so we can reuse it when switching models
    actualSalesTotalRef.value = actualSalesTotal;

    // Calculate rolling average
    const rollingAvgValues = showRollingAverage.value
      ? calculateRollingAverage(histValues, rollingAverageWindow.value)
      : [];

    // Combine dates: historical up to cutoff + forecast dates + actuals after cutoff
    const allDates = [
      ...histDates,
      ...forecastDates.filter((d) => !histDates.includes(d)),
      ...actualsAfterCutoff.map((a) => a.date).filter((d) => !histDates.includes(d) && !forecastDates.includes(d)),
    ].sort();
    
    // Store all dates for reactive updates
    rawAllDates.value = allDates;

    // Prepare data arrays with null padding
    const histData = [...histValues, ...Array(forecastDates.length).fill(null)];
    const rollingAvgData = showRollingAverage.value
      ? [...rollingAvgValues, ...Array(forecastDates.length).fill(null)]
      : [];
    const forecastData = [...Array(histValues.length).fill(null), ...forecastValues];

    // Get actual values for forecast period (ground truth)
    const actualData = allDates.map((date) => {
      const historical = historicalDataFiltered.find((h: HistoricalDataPoint) => h.date === date);
      return historical ? historical.units_sold : null;
    });
    
    // Store actual data for reactive updates
    rawActualData.value = actualData;

    // Build datasets
    const datasets: object[] = [
      {
        label: `Historical (${histValues.length} days)`,
        data: histData,
        borderColor: "rgb(107, 114, 128)",
        backgroundColor: "rgba(107, 114, 128, 0.1)",
        pointRadius: 3,
        pointStyle: "circle",
        tension: 0.1,
        borderWidth: 2,
        spanGaps: false,
      },
    ];

    if (showRollingAverage.value) {
      datasets.push({
        label: `${rollingAverageWindow.value}-day Rolling Average`,
        data: rollingAvgData,
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        pointRadius: 0,
        tension: 0.3,
        borderWidth: 2,
        borderDash: [3, 3],
        fill: false,
        spanGaps: false,
      });
    }

    // Add forecast line - use the model that was actually used (from forecast response)
    const actualModelUsedForChart = forecast.method_used || modelToUse;
    const modelColor = modelColors[actualModelUsedForChart] || modelColors["chronos-2"] || { border: "rgb(59, 130, 246)", bg: "rgba(59, 130, 246, 0.1)" };
    const mapeForModel = qualityMetrics.find((m) => m.method === actualModelUsedForChart)?.mape;
    datasets.push({
      label: `${getModelDisplayName(actualModelUsedForChart)} Forecast (${forecastHorizon.value}d)${mapeForModel !== null && mapeForModel !== undefined ? ` - MAPE: ${mapeForModel.toFixed(1)}%` : ""}`,
      data: forecastData,
      borderColor: modelColor.border,
      backgroundColor: modelColor.bg,
      borderDash: [5, 5],
      pointRadius: 4,
      pointStyle: "circle",
      tension: 0.1,
      borderWidth: 2,
      spanGaps: false,
    });

    // Add actual ground truth line (only for forecast period, after cutoff)
    const actualGroundTruth = allDates.map((date) => {
      // Only show actuals after cutoff date
      if (!cutoffDate || date <= cutoffDate) return null;
      const actual = actualsAfterCutoff.find((a) => a.date === date);
      return actual ? actual.units_sold : null;
    });

    if (actualGroundTruth.some((v) => v !== null)) {
      datasets.push({
        label: `Actual Ground Truth (${forecastHorizon.value}d)`,
        data: actualGroundTruth,
        borderColor: "rgb(0, 0, 0)",
        backgroundColor: "rgba(0, 0, 0, 0.2)",
        pointRadius: 5,
        pointStyle: "rect",
        tension: 0.1,
        borderWidth: 2,
        spanGaps: false,
      });
    }

    // Get product name
    const product = products.value.find((p) => p.item_id === selectedSku.value);

    // Set initial selected model for chart (already set above)


    chartData.value = {
      itemId: selectedSku.value,
      itemName: product?.product_name || selectedSku.value,
      statistics: qualityMetrics || [],
      metrics: {
        ...primaryMetrics,
        forecastedSales: forecastedSalesTotal,
        actualSales: actualSalesTotal,
      },
      cutoffDate,
      chartConfig: {
        labels: allDates,
        datasets: datasets as any, // Type assertion for Chart.js compatibility
      },
    };
  } catch (err: unknown) {
    const wasAuthError = await handleAuthError(err);
    if (!wasAuthError) {
      error.value = err instanceof Error ? err.message : "Failed to generate forecast";
    }
  } finally {
    isGenerating.value = false;
  }
};

// Update chart with new rolling average settings
const updateRollingAverage = () => {
  if (!chartData.value || rawHistoricalValues.value.length === 0) return;
  
  // Recalculate rolling average with current settings
  const rollingAvgValues = showRollingAverage.value
    ? calculateRollingAverage(rawHistoricalValues.value, rollingAverageWindow.value)
    : [];
  
  // Prepare data arrays with null padding
  const histData = [...rawHistoricalValues.value, ...Array(rawForecastData.value.length).fill(null)];
  const rollingAvgData = showRollingAverage.value
    ? [...rollingAvgValues, ...Array(rawForecastData.value.length).fill(null)]
    : [];
  const forecastData = [...Array(rawHistoricalValues.value.length).fill(null), ...rawForecastData.value];
  
  // Rebuild datasets
  const datasets: object[] = [
    {
      label: `Historical (${rawHistoricalValues.value.length} days)`,
      data: histData,
      borderColor: "rgb(107, 114, 128)",
      backgroundColor: "rgba(107, 114, 128, 0.1)",
      pointRadius: 3,
      pointStyle: "circle",
      tension: 0.1,
      borderWidth: 2,
      spanGaps: false,
    },
  ];
  
  if (showRollingAverage.value) {
    datasets.push({
      label: `${rollingAverageWindow.value}-day Rolling Average`,
      data: rollingAvgData,
      borderColor: "rgb(59, 130, 246)",
      backgroundColor: "rgba(59, 130, 246, 0.1)",
      pointRadius: 0,
      tension: 0.3,
      borderWidth: 2,
      borderDash: [3, 3],
      fill: false,
      spanGaps: false,
    });
  }
  
  // Add forecast line (preserve existing forecast dataset)
  const existingForecastDataset = chartData.value.chartConfig.datasets.find((d: any) => 
    d.label && typeof d.label === 'string' && d.label.includes("Forecast")
  );
  if (existingForecastDataset) {
    datasets.push({ ...existingForecastDataset });
  }
  
  // Add actual ground truth line (preserve existing)
  const existingActualDataset = chartData.value.chartConfig.datasets.find((d: any) => 
    d.label && typeof d.label === 'string' && d.label.includes("Actual Ground Truth")
  );
  if (existingActualDataset) {
    datasets.push({ ...existingActualDataset });
  }
  
  // Update chart data
  chartData.value = {
    ...chartData.value,
    chartConfig: {
      labels: rawAllDates.value,
      datasets,
    },
  };
};

// Watch rolling average settings and update chart
watch([showRollingAverage, rollingAverageWindow], () => {
  if (chartData.value) {
    updateRollingAverage();
  }
});

// Watch selected model for chart and update forecast line
watch(selectedModelForChart, async (newMethod) => {
  if (!newMethod || !selectedSku.value || !chartData.value) {
    return;
  }
  
  // If we have in-memory forecasts (skip_persistence=true), use those
  if (allForecastsByMethod.value.has(newMethod)) {
    const methodForecast = allForecastsByMethod.value.get(newMethod);
    if (methodForecast) {
      const forecastValues = methodForecast.predictions.map((p) => p.point_forecast);
      rawForecastData.value = forecastValues;
      updateChartWithNewForecast(newMethod, forecastValues);
      return;
    }
  }
  
  // Otherwise, fetch from database (if we have a forecast_run_id)
  if (!currentForecastRunId.value) {
    console.warn("No forecast run ID available and no in-memory forecast found for method:", newMethod);
    return;
  }
  
  try {
    // Fetch forecast results for the selected method
    const response = await $fetch<{
      forecast_id: string;
      method: string;
      forecasts: Array<{
        item_id: string;
        method_used: string;
        predictions: Array<{
          date: string;
          point_forecast: number;
        }>;
      }>;
    }>(`/api/experiments/forecast/${currentForecastRunId.value}/results`, {
      query: { method: newMethod },
    });
    
    if (!response.forecasts || response.forecasts.length === 0) {
      console.warn(`No forecast results found for method: ${newMethod}`);
      return;
    }
    
    const methodForecast = response.forecasts[0];
    if (!methodForecast) {
      console.warn(`No forecast found for method ${selectedModelForChart.value} in run ${currentForecastRunId.value}`);
      return;
    }
    const forecastValues = methodForecast.predictions.map((p: { point_forecast: number }) => p.point_forecast);
    
    // Update raw forecast data
    rawForecastData.value = forecastValues;
    
    // Update chart with new forecast line
    updateChartWithNewForecast(newMethod, forecastValues);
  } catch (err) {
    console.error("Error fetching forecast for method:", err);
    await handleAuthError(err);
  }
});

// Update chart with new forecast method
const updateChartWithNewForecast = (method: string, forecastValues: number[]) => {
  if (!chartData.value || rawHistoricalValues.value.length === 0) return;
  
  // Get metrics for the selected method
  const methodMetrics = chartData.value.statistics?.find((m) => m.method === method);
  
  // Calculate forecasted sales total for this method
  const forecastedSales = forecastValues.reduce((sum, val) => sum + val, 0);
  
  // Use stored actual sales total (doesn't change with model - it's historical data)
  // If not available, try to get from chart dataset as fallback
  let actualSales: number | null = actualSalesTotalRef.value;
  if (actualSales === null) {
    const actualDataset = chartData.value.chartConfig.datasets.find((d: any) => 
      d.label && typeof d.label === 'string' && d.label.includes("Actual Ground Truth")
    ) as { data?: (number | null)[] } | undefined;
    if (actualDataset && actualDataset.data) {
      const actualValues = (actualDataset.data as (number | null)[]).filter((v): v is number => v !== null);
      actualSales = actualValues.reduce((sum, val) => sum + val, 0);
    }
  }
  
  // Recalculate rolling average if needed
  const rollingAvgValues = showRollingAverage.value
    ? calculateRollingAverage(rawHistoricalValues.value, rollingAverageWindow.value)
    : [];

  // Prepare data arrays
  const histData = [...rawHistoricalValues.value, ...Array(forecastValues.length).fill(null)];
  const rollingAvgData = showRollingAverage.value
    ? [...rollingAvgValues, ...Array(forecastValues.length).fill(null)]
    : [];
  const forecastData = [...Array(rawHistoricalValues.value.length).fill(null), ...forecastValues];
  
  // Rebuild datasets
  const datasets: object[] = [
    {
      label: `Historical (${rawHistoricalValues.value.length} days)`,
      data: histData,
      borderColor: "rgb(107, 114, 128)",
      backgroundColor: "rgba(107, 114, 128, 0.1)",
      pointRadius: 3,
      pointStyle: "circle",
      tension: 0.1,
      borderWidth: 2,
      spanGaps: false,
    },
  ];
  
  if (showRollingAverage.value) {
    datasets.push({
      label: `${rollingAverageWindow.value}-day Rolling Average`,
      data: rollingAvgData,
      borderColor: "rgb(59, 130, 246)",
      backgroundColor: "rgba(59, 130, 246, 0.1)",
      pointRadius: 0,
      tension: 0.3,
      borderWidth: 2,
      borderDash: [3, 3],
      fill: false,
      spanGaps: false,
    });
  }
  
  // Add forecast line with selected method
  const modelColor = modelColors[method] || modelColors["chronos-2"] || { border: "rgb(59, 130, 246)", bg: "rgba(59, 130, 246, 0.1)" };
  const mapeForModel = methodMetrics?.mape;
  datasets.push({
    label: `${getModelDisplayName(method)} Forecast (${forecastHorizon.value}d)${mapeForModel !== null && mapeForModel !== undefined ? ` - MAPE: ${mapeForModel.toFixed(1)}%` : ""}`,
    data: forecastData,
    borderColor: modelColor.border,
    backgroundColor: modelColor.bg,
    borderDash: [5, 5],
    pointRadius: 4,
    pointStyle: "circle",
    tension: 0.1,
    borderWidth: 2,
    spanGaps: false,
  });
  
  // Add actual ground truth line (preserve existing)
  const existingActualDataset = chartData.value.chartConfig.datasets.find((d: any) => 
    d.label && typeof d.label === 'string' && d.label.includes("Actual Ground Truth")
  );
  if (existingActualDataset) {
    datasets.push({ ...existingActualDataset });
  }
  
  // Update chart data with new metrics
  chartData.value = {
    ...chartData.value,
    metrics: {
      mape: methodMetrics?.mape ?? null,
      rmse: methodMetrics?.rmse ?? null,
      mae: methodMetrics?.mae ?? null,
      forecastedSales: forecastedSales,
      actualSales: actualSales,
    },
    chartConfig: {
      labels: rawAllDates.value,
      datasets: datasets as any, // Type assertion for Chart.js compatibility
    },
  };
};

// Chart model selection is handled by the watcher on selectedModelForChart

// Initial load
onMounted(async () => {
  await Promise.all([loadLocations(), loadCategories(), loadModels(), loadDateRange()]);
  await loadProducts();
});
</script>

