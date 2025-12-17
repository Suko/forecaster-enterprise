<template>
  <div class="p-6 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-3xl font-bold">Inventory</h1>
      <div class="flex items-center gap-2">
        <UInput
          v-model="searchQuery"
          icon="i-lucide-search"
          placeholder="Search products..."
          class="w-64"
          @input="onSearch"
        />
        <UButton
          icon="i-lucide-columns"
          variant="ghost"
          @click="showColumnSelector = true"
        >
          Columns
        </UButton>
        <UButton
          icon="i-lucide-refresh-cw"
          variant="ghost"
          :loading="loading"
          @click="loadProducts"
        >
          Refresh
        </UButton>
        <UButton
          v-if="supplierId"
          icon="i-lucide-x"
          variant="ghost"
          :disabled="loading"
          @click="navigateTo('/inventory')"
        >
          Clear supplier
        </UButton>
      </div>
    </div>

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
      color="error"
      variant="soft"
      title="Error loading products"
      :description="error"
    />

    <!-- AG Grid Table -->
    <div
      v-else
      class="h-[calc(100vh-200px)]"
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
          :getRowHeight="getRowHeight"
          theme="legacy"
          class="ag-theme-alpine w-full h-full"
          @grid-ready="onGridReady"
          @pagination-changed="onPaginationChanged"
          @cell-clicked="onCellClicked"
        />
        <template #fallback>
          <div class="flex items-center justify-center h-full">
            <UIcon
              name="i-lucide-loader-2"
              class="w-8 h-8 animate-spin text-primary"
            />
          </div>
        </template>
      </ClientOnly>
    </div>
  </div>

  <!-- Column Visibility Selector -->
  <UModal
    v-model:open="showColumnSelector"
    :ui="{ content: 'sm:max-w-md' }"
  >
    <template #content>
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">Column Visibility</h3>
        </template>

        <div class="space-y-2 max-h-96 overflow-y-auto">
          <div
            v-for="col in availableColumns"
            :key="col.field"
            class="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded"
          >
            <label
              :for="`col-${col.field}`"
              class="flex-1 cursor-pointer"
            >
              {{ col.headerName }}
            </label>
            <USwitch
              :id="`col-${col.field}`"
              v-model="columnVisibility[col.field]"
              @update:model-value="updateColumnVisibility"
            />
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end">
            <UButton @click="showColumnSelector = false"> Close </UButton>
          </div>
        </template>
      </UCard>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { AgGridVue } from "ag-grid-vue3";
import { ModuleRegistry, AllCommunityModule } from "ag-grid-community";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import type { ColDef, GridReadyEvent } from "ag-grid-community";
import type { Product } from "~/types/product";

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule]);

definePageMeta({
  layout: "dashboard",
});

const { fetchProducts } = useAgGridProducts();
const { fetchSettings } = useSettings();
const { handleAuthError } = useAuthError();
const { fetchPreferences, getInventoryColumnVisibility, setInventoryColumnVisibility } =
  useUserPreferences();
const route = useRoute();

const supplierId = computed(() =>
  typeof route.query.supplier_id === "string" ? route.query.supplier_id : undefined
);
const itemQuery = computed(() =>
  typeof route.query.item === "string" ? route.query.item : undefined
);

const rowData = ref<Product[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const searchQuery = ref("");
const gridApi = ref<any>(null);
const gridInitialized = ref(false);
const defaultBufferDays = ref<number>(7); // Default fallback
const showColumnSelector = ref(false);
const columnVisibility = ref<{ [field: string]: boolean }>({});
const expandedRows = ref<Set<string>>(new Set()); // Track expanded rows by item_id

// Base column definitions (all possible columns)
const baseColumnDefs: ColDef[] = [
  {
    field: "item_id",
    headerName: "SKU / Product Name",
    filter: "agTextColumnFilter",
    sortable: true,
    resizable: true,
    flex: 1,
    minWidth: 200,
    cellRenderer: (params: any) => {
      const itemId = params.value || "";
      const productName = params.data?.product_name || "";
      return `
        <div class="py-1">
          <div class="font-medium text-sm">${itemId}</div>
          <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">${productName}</div>
        </div>
      `;
    },
    valueGetter: (params: any) => {
      // For filtering and sorting, use both item_id and product_name
      const itemId = params.data?.item_id || "";
      const productName = params.data?.product_name || "";
      return `${itemId} ${productName}`;
    },
  },
  {
    field: "category",
    headerName: "Category",
    filter: "agTextColumnFilter",
    sortable: true,
    resizable: true,
    width: 150,
  },
  {
    field: "locations",
    headerName: "Locations",
    filter: "agTextColumnFilter",
    sortable: false,
    resizable: true,
    flex: 1,
    minWidth: 200,
    maxWidth: 400,
    hide: false,
    cellRenderer: (params: any) => {
      const locations = params.value as
        | Array<{ location_id: string; location_name: string; current_stock: number }>
        | null
        | undefined;
      const itemId = params.data?.item_id;
      const isExpanded = expandedRows.value.has(`${itemId}_locations`);

      if (!locations || locations.length === 0) {
        return '<span class="text-gray-400">No locations</span>';
      }

      // Show first location by default
      const firstLocation = locations[0];
      const otherLocations = locations.slice(1);
      const hasMoreLocations = otherLocations.length > 0;

      let html = '<div class="py-1 min-w-0">';

      // Always show first location
      html += `
        <div class="flex items-center gap-1 flex-wrap">
          <span class="font-medium text-sm">${firstLocation.location_name}</span>
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Stock: ${firstLocation.current_stock}</div>
      `;

      // Show expand/collapse button if there are more locations
      if (hasMoreLocations) {
        const expandIcon = isExpanded ? "▼" : "▶";
        const expandText = isExpanded ? "Show less" : `Show ${otherLocations.length} more`;
        html += `
          <button 
            class="mt-1 text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 location-expand-btn"
            data-item-id="${itemId}"
            data-type="locations"
          >
            <span>${expandIcon}</span>
            <span>${expandText}</span>
          </button>
        `;
      }

      // Show other locations if expanded
      if (isExpanded && hasMoreLocations) {
        html += '<div class="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 space-y-2">';
        otherLocations.forEach((loc) => {
          html += `
            <div class="py-1">
              <div class="flex items-center gap-1">
                <span class="font-medium text-sm">${loc.location_name}</span>
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Stock: ${loc.current_stock}</div>
            </div>
          `;
        });
        html += "</div>";
      }

      html += "</div>";
      return html;
    },
    cellStyle: { overflow: "visible", padding: "8px", whiteSpace: "normal", lineHeight: "1.5" },
    autoHeight: true,
  },
  {
    field: "suppliers",
    headerName: "Suppliers",
    filter: "agTextColumnFilter",
    sortable: false,
    resizable: true,
    flex: 1,
    minWidth: 200,
    maxWidth: 400,
    hide: false,
    cellRenderer: (params: any) => {
      const suppliers = params.value as
        | Array<{ supplier_name: string; moq: number; lead_time_days: number; is_primary: boolean }>
        | null
        | undefined;
      const itemId = params.data?.item_id;
      const isExpanded = expandedRows.value.has(`${itemId}_suppliers`);

      if (!suppliers || suppliers.length === 0) {
        return '<span class="text-gray-400">No suppliers</span>';
      }

      // Find primary supplier
      const primarySupplier = suppliers.find((s) => s.is_primary) || suppliers[0];
      const otherSuppliers = suppliers.filter((s) => s !== primarySupplier);
      const hasMoreSuppliers = otherSuppliers.length > 0;

      let html = '<div class="py-1 min-w-0">';

      // Always show primary supplier
      const primaryBadge =
        '<span class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 ml-1 whitespace-nowrap">Primary</span>';
      html += `
        <div class="flex items-center gap-1 flex-wrap">
          <span class="font-medium text-sm">${primarySupplier.supplier_name}</span>${primaryBadge}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">MOQ: ${primarySupplier.moq} | Lead: ${primarySupplier.lead_time_days}d</div>
      `;

      // Show expand/collapse button if there are more suppliers
      if (hasMoreSuppliers) {
        const expandIcon = isExpanded ? "▼" : "▶";
        const expandText = isExpanded ? "Show less" : `Show ${otherSuppliers.length} more`;
        html += `
          <button 
            class="mt-1 text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 supplier-expand-btn"
            data-item-id="${itemId}"
            data-type="suppliers"
          >
            <span>${expandIcon}</span>
            <span>${expandText}</span>
          </button>
        `;
      }

      // Show other suppliers if expanded
      if (isExpanded && hasMoreSuppliers) {
        html += '<div class="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 space-y-2">';
        otherSuppliers.forEach((s) => {
          html += `
            <div class="py-1">
              <div class="flex items-center gap-1">
                <span class="font-medium text-sm">${s.supplier_name}</span>
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">MOQ: ${s.moq} | Lead: ${s.lead_time_days}d</div>
            </div>
          `;
        });
        html += "</div>";
      }

      html += "</div>";
      return html;
    },
    cellStyle: { overflow: "visible", padding: "8px", whiteSpace: "normal", lineHeight: "1.5" },
    autoHeight: true,
  },
  {
    field: "current_stock",
    headerName: "Stock",
    filter: "agNumberColumnFilter",
    sortable: true,
    resizable: true,
    width: 100,
    type: "numericColumn",
  },
  {
    field: "unit_cost",
    headerName: "Unit Cost",
    filter: "agNumberColumnFilter",
    sortable: true,
    resizable: true,
    width: 120,
    type: "numericColumn",
    valueFormatter: (params) => `€${parseFloat(params.value || "0").toFixed(2)}`,
  },
  {
    field: "safety_buffer_days",
    headerName: "Buffer (Days)",
    filter: "agNumberColumnFilter",
    sortable: true,
    resizable: true,
    width: 120,
    type: "numericColumn",
    valueFormatter: (params) => {
      if (params.value === null || params.value === undefined) {
        return `${defaultBufferDays.value}d`;
      }
      return `${params.value}d`;
    },
  },
  {
    field: "inventory_value",
    headerName: "Inventory Value",
    filter: "agNumberColumnFilter",
    sortable: true,
    resizable: true,
    width: 150,
    type: "numericColumn",
    valueFormatter: (params) => `€${parseFloat(params.value || "0").toLocaleString()}`,
  },
  {
    field: "dir",
    headerName: "DIR (Days)",
    filter: "agNumberColumnFilter",
    sortable: true,
    resizable: true,
    width: 120,
    type: "numericColumn",
    valueFormatter: (params) => {
      const value = Number(params.value);
      return isNaN(value) ? "0" : value.toFixed(1);
    },
    cellStyle: (params) => {
      if (params.value < 14) return { backgroundColor: "#fee2e2" }; // Red for low
      if (params.value > 90) return { backgroundColor: "#dcfce7" }; // Green for high
      return null;
    },
  },
  {
    field: "stockout_risk",
    headerName: "Risk Score",
    filter: "agNumberColumnFilter",
    sortable: true,
    resizable: true,
    width: 120,
    type: "numericColumn",
    valueFormatter: (params) => {
      const value = Number(params.value);
      return isNaN(value) ? "0%" : `${(value * 100).toFixed(1)}%`;
    },
    cellStyle: (params) => {
      const risk = params.value * 100;
      if (risk > 70) return { backgroundColor: "#fee2e2" }; // Red
      if (risk > 40) return { backgroundColor: "#fef3c7" }; // Yellow
      return { backgroundColor: "#dcfce7" }; // Green
    },
  },
  {
    field: "status",
    headerName: "Status",
    filter: "agTextColumnFilter",
    sortable: true,
    resizable: true,
    width: 150,
    cellRenderer: (params: any) => {
      const status = params.value || "normal";
      const colors: Record<string, string> = {
        understocked: "red",
        overstocked: "green",
        normal: "gray",
      };
      const color = colors[status] || "gray";
      return `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-${color}-100 text-${color}-800 whitespace-nowrap">${status}</span>`;
    },
    cellStyle: { overflow: "visible" },
  },
];

// Available columns reference
const availableColumns = computed(() => baseColumnDefs);

// Column Definitions (will be filtered based on visibility)
const columnDefs = computed(() => {
  return baseColumnDefs.map((col) => ({
    ...col,
    hide: !columnVisibility.value[col.field as string],
  }));
});

const defaultColDef: ColDef = {
  resizable: true,
  sortable: true,
  filter: true,
};

// Toggle row expansion (for suppliers or locations)
const toggleSupplierRow = (itemId: string, type: string = "suppliers") => {
  const key = `${itemId}_${type}`;
  if (expandedRows.value.has(key)) {
    expandedRows.value.delete(key);
  } else {
    expandedRows.value.add(key);
  }
  // Refresh the grid to update row heights
  if (gridApi.value) {
    gridApi.value.refreshCells({ force: true });
    gridApi.value.resetRowHeights();
  }
};

// Expose toggle function to window for cell renderer
if (typeof window !== "undefined") {
  (window as any).toggleSupplierRow = toggleSupplierRow;
}

// Calculate row height based on expansion state and number of suppliers/locations
const getRowHeight = (params: any) => {
  const suppliers = params.data?.suppliers;
  const locations = params.data?.locations;
  const itemId = params.data?.item_id;
  const isSuppliersExpanded = expandedRows.value.has(`${itemId}_suppliers`);
  const isLocationsExpanded = expandedRows.value.has(`${itemId}_locations`);

  let height = 50; // Base height

  // Calculate height for suppliers
  if (suppliers && Array.isArray(suppliers)) {
    if (isSuppliersExpanded) {
      height = Math.max(height, 50 + suppliers.length * 60);
    } else {
      height = Math.max(height, 80); // Primary supplier + expand button
    }
  }

  // Calculate height for locations
  if (locations && Array.isArray(locations)) {
    if (isLocationsExpanded) {
      height = Math.max(height, 50 + locations.length * 60);
    } else {
      height = Math.max(height, 80); // First location + expand button
    }
  }

  return height;
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

const loadProducts = async () => {
  // Prevent concurrent calls
  if (loading.value) {
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    // Fetch all products (up to 1000, which is the API max)
    // AG Grid will handle client-side pagination
    const result = await fetchProducts({
      page: 1,
      pageSize: 1000, // Fetch all products
      search: searchQuery.value || undefined,
      supplierId: supplierId.value,
    });
    rowData.value = result.rowData;
    // Reset expanded rows when loading new data
    expandedRows.value.clear();
    // Reset to first page after loading
    if (gridApi.value) {
      gridApi.value.paginationGoToPage(0);
      gridApi.value.resetRowHeights();
    }
  } catch (err: any) {
    // Handle 401 errors - redirect to login
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) {
      // Redirect is handled, just return
      return;
    }
    error.value = err.message || "Failed to load products";
  } finally {
    loading.value = false;
  }
};

const onPaginationChanged = () => {
  // Client-side pagination - no action needed
};

// Handle cell clicks for expand/collapse buttons
const onCellClicked = (params: any) => {
  const expandBtn = params.event?.target?.closest(".supplier-expand-btn, .location-expand-btn");
  if (expandBtn) {
    const itemId = expandBtn.getAttribute("data-item-id");
    const type = expandBtn.getAttribute("data-type") || "suppliers";
    if (itemId) {
      toggleSupplierRow(itemId, type);
    }
  }
};

const loadSettings = async () => {
  try {
    const settings = await fetchSettings();
    defaultBufferDays.value = settings.safety_buffer_days;
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (!wasAuthError) {
      // Error is already logged on server side
    }
  }
};

const loadColumnPreferences = async () => {
  try {
    await fetchPreferences();
    const savedVisibility = getInventoryColumnVisibility();

    // Initialize column visibility with saved preferences or defaults
    const visibility: { [field: string]: boolean } = {};
    baseColumnDefs.forEach((col) => {
      const field = col.field as string;
      // Use saved preference, or default to true (visible) for most columns
      visibility[field] =
        savedVisibility[field] !== undefined ? savedVisibility[field] : col.hide !== true; // Default to visible unless explicitly hidden
    });
    columnVisibility.value = visibility;
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (!wasAuthError) {
      // Set defaults if loading fails
      baseColumnDefs.forEach((col) => {
        const field = col.field as string;
        columnVisibility.value[field] = col.hide !== true;
      });
    }
  }
};

const updateColumnVisibility = async () => {
  try {
    await setInventoryColumnVisibility(columnVisibility.value);
    // Grid will automatically update via computed columnDefs
  } catch {
    // Error is already logged on server side
  }
};

// Load data on mount, not on grid ready
onMounted(async () => {
  if (itemQuery.value && !searchQuery.value) {
    searchQuery.value = itemQuery.value;
  }
  await loadSettings();
  await loadColumnPreferences();
  loadProducts();
});

watch(supplierId, () => {
  loadProducts();
});

const onSearch = () => {
  // Debounce search - reload after user stops typing
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  searchTimeout.value = setTimeout(() => {
    loadProducts(); // Reload all products with search filter
  }, 500);
};

const searchTimeout = ref<NodeJS.Timeout | null>(null);

onUnmounted(() => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value);
  }
  // Clean up grid API
  if (gridApi.value) {
    try {
      gridApi.value.destroy();
    } catch (e) {
      // Grid may already be destroyed
    }
    gridApi.value = null;
  }
  // Reset grid initialized flag when component unmounts
  gridInitialized.value = false;
});
</script>
