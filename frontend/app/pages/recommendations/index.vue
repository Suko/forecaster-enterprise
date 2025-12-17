<template>
  <div class="p-6 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-3xl font-bold">AI Recommendations</h1>
      <div class="flex items-center gap-2">
        <USelectMenu
          v-model="selectedType"
          :options="recommendationTypes"
          placeholder="Filter by type"
          class="w-48"
          @change="loadRecommendations"
        />
        <UButton
          icon="i-lucide-refresh-cw"
          variant="ghost"
          :loading="loading"
          @click="loadRecommendations"
        >
          Refresh
        </UButton>
      </div>
    </div>

    <!-- AI Query Section (Future: AG Grid AI Toolkit) -->
    <UCard>
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon
            name="i-lucide-sparkles"
            class="w-5 h-5 text-primary"
          />
          <h3 class="text-lg font-semibold">Natural Language Query</h3>
        </div>
      </template>
      <div class="p-4">
        <UInput
          v-model="aiQuery"
          placeholder="Ask about your inventory... (e.g., 'Show me all products with high stockout risk')"
          icon="i-lucide-message-square"
          size="lg"
          @keyup.enter="handleAIQuery"
        >
          <template #trailing>
            <UButton
              icon="i-lucide-send"
              variant="ghost"
              :loading="aiLoading"
              @click="handleAIQuery"
            />
          </template>
        </UInput>
        <p class="text-xs text-gray-500 mt-2">
          💡 Example queries: "Show understocked products", "Sort by inventory value", "Filter by
          category"
        </p>
      </div>
    </UCard>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="flex items-center justify-center py-12"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-8 h-8 animate-spin text-primary"
      />
    </div>

    <!-- Error State -->
    <UAlert
      v-else-if="error"
      color="warning"
      variant="soft"
      title="Error loading recommendations"
      :description="error"
    />

    <!-- Recommendations Grid -->
    <div
      v-else
      class="h-[calc(100vh-400px)]"
    >
      <ClientOnly>
        <ag-grid-vue
          :columnDefs="columnDefs"
          :rowData="rowData"
          :defaultColDef="defaultColDef"
          :pagination="true"
          :paginationPageSize="50"
          :paginationPageSizeSelector="[50, 100, 200, 500, 1000]"
          :rowSelection="{ mode: 'multiRow' }"
          theme="legacy"
          class="ag-theme-alpine w-full h-full"
          @grid-ready="onGridReady"
          @cell-clicked="onCellClicked"
        />
      </ClientOnly>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AgGridVue } from "ag-grid-vue3";
import { ModuleRegistry, AllCommunityModule } from "ag-grid-community";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import type { ColDef, GridReadyEvent } from "ag-grid-community";
import type { Recommendation, RecommendationType } from "~/types/recommendation";

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

definePageMeta({
  layout: "dashboard",
});

const { fetchRecommendations, addToCart } = useRecommendations();
const { handleAuthError } = useAuthError();

const rowData = ref<Recommendation[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const aiQuery = ref("");
const aiLoading = ref(false);
const selectedType = ref<RecommendationType | null>(null);
const gridApi = ref<any>(null);
const gridInitialized = ref(false);

const recommendationTypes: Array<{
  label: string;
  value: RecommendationType | null;
}> = [
  { label: "All Types", value: null },
  { label: "Reorder", value: "REORDER" },
  { label: "Urgent", value: "URGENT" },
  { label: "Reduce Order", value: "REDUCE_ORDER" },
  { label: "Dead Stock", value: "DEAD_STOCK" },
  { label: "Promote", value: "PROMOTE" },
];

// Column Definitions
const columnDefs = ref<ColDef[]>([
  {
    field: "type",
    headerName: "Type",
    filter: "agTextColumnFilter",
    sortable: true,
    resizable: true,
    width: 140,
    cellRenderer: (params: any) => {
      const type = params.value;
      const colors: Record<string, string> = {
        REORDER: "blue",
        URGENT: "red",
        REDUCE_ORDER: "orange",
        DEAD_STOCK: "gray",
        PROMOTE: "green",
      };
      const color = colors[type] || "gray";
      return `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-${color}-100 text-${color}-800">${type}</span>`;
    },
  },
  {
    field: "priority",
    headerName: "Priority",
    filter: "agTextColumnFilter",
    sortable: true,
    resizable: true,
    width: 120,
    cellRenderer: (params: any) => {
      const priority = params.value;
      const colors: Record<string, string> = {
        high: "red",
        medium: "yellow",
        low: "green",
      };
      const color = colors[priority] || "gray";
      return `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-${color}-100 text-${color}-800">${priority}</span>`;
    },
  },
  {
    field: "item_id",
    headerName: "SKU",
    filter: "agTextColumnFilter",
    sortable: true,
    resizable: true,
    width: 120,
  },
  {
    field: "product_name",
    headerName: "Product Name",
    filter: "agTextColumnFilter",
    sortable: true,
    resizable: true,
    flex: 1,
  },
  {
    field: "reason",
    headerName: "Reason",
    filter: "agTextColumnFilter",
    sortable: true,
    resizable: true,
    flex: 1,
    wrapText: true,
    autoHeight: true,
  },
  {
    field: "suggested_quantity",
    headerName: "Suggested Qty",
    filter: "agNumberColumnFilter",
    sortable: true,
    resizable: true,
    width: 140,
    type: "numericColumn",
  },
  {
    field: "supplier_name",
    headerName: "Supplier",
    filter: "agTextColumnFilter",
    sortable: true,
    resizable: true,
    width: 150,
  },
  {
    headerName: "Actions",
    field: "actions",
    width: 120,
    cellRenderer: (params: any) => {
      const buttonId = `add-cart-${params.node.id}`;
      return `
        <button 
          id="${buttonId}"
          class="px-3 py-1 text-sm bg-primary-500 text-white rounded hover:bg-primary-600"
        >
          Add to Cart
        </button>
      `;
    },
  },
]);

const defaultColDef: ColDef = {
  resizable: true,
  sortable: true,
  filter: true,
};

const onGridReady = (params: GridReadyEvent) => {
  // Only set API reference, don't load data here
  // Data loading happens in onMounted to prevent loops
  if (!gridInitialized.value) {
    gridApi.value = params.api;
    gridInitialized.value = true;
  } else {
    // Grid was recreated, just update the API reference
    gridApi.value = params.api;
  }
};

const onCellClicked = async (params: any) => {
  if (params.column.colId === "actions") {
    try {
      await addToCart(params.data.item_id, params.data.supplier_id, params.data.suggested_quantity);
      // Show success notification
      const toast = useToast();
      toast.add({
        title: "Added to cart",
        description: `${params.data.product_name} added to order planning cart`,
        color: "success",
      });
    } catch (err: any) {
      // Handle 401 errors - redirect to login
      const wasAuthError = await handleAuthError(err);
      if (wasAuthError) {
        // Redirect is handled, just return
        return;
      }
      const toast = useToast();
      toast.add({
        title: "Error",
        description: "Failed to add item to cart",
        color: "warning",
      });
    }
  }
};

const loadRecommendations = async () => {
  // Prevent concurrent calls
  if (loading.value) {
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const recommendations = await fetchRecommendations({
      recommendation_type: selectedType.value || undefined,
    });
    rowData.value = recommendations;
  } catch (err: any) {
    // Handle 401 errors - redirect to login
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) {
      // Redirect is handled, just return
      return;
    }
    error.value = err.message || "Failed to load recommendations";
  } finally {
    loading.value = false;
  }
};

// Load data on mount, not on grid ready
onMounted(() => {
  loadRecommendations();
});

onUnmounted(() => {
  // Reset grid initialized flag when component unmounts
  gridInitialized.value = false;
});

const handleAIQuery = async () => {
  if (!aiQuery.value.trim()) return;

  aiLoading.value = true;
  try {
    // TODO: Implement AG Grid AI Toolkit integration
    // For now, just show a message (logging intentionally removed - not needed)
    // In the future, this will use gridApi.getStructuredSchema() and send to LLM
    alert(
      "AI Toolkit integration coming soon! This will use AG Grid AI Toolkit to process natural language queries."
    );
  } catch {
    // AI toolkit integration not yet implemented
  } finally {
    aiLoading.value = false;
  }
};
</script>
