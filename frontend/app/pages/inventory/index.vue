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
          icon="i-lucide-download"
          variant="outline"
          color="primary"
          @click="handleExcelDownload"
        >
          Export to Excel
        </UButton>
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

    <!-- Quick Filter Buttons -->
    <div class="flex items-center gap-2 flex-wrap">
      <UButton
        :variant="activeFilter === 'all' ? 'solid' : 'outline'"
        :color="activeFilter === 'all' ? 'primary' : 'gray'"
        :class="activeFilter === 'all' ? 'ring-2 ring-primary-500 ring-offset-2' : ''"
        @click="applyQuickFilter('all')"
      >
        All
        <UBadge
          :label="filterCounts.all.toString()"
          :color="activeFilter === 'all' ? 'white' : 'gray'"
          variant="solid"
          class="ml-2"
        />
      </UButton>
      <UButton
        :variant="activeFilter === 'understocked' ? 'solid' : 'outline'"
        :color="activeFilter === 'understocked' ? 'red' : 'gray'"
        :class="activeFilter === 'understocked' ? 'ring-2 ring-red-500 ring-offset-2' : ''"
        icon="i-lucide-alert-triangle"
        @click="applyQuickFilter('understocked')"
      >
        Understocked
        <UBadge
          :label="filterCounts.understocked.toString()"
          :color="activeFilter === 'understocked' ? 'white' : 'red'"
          variant="solid"
          class="ml-2"
        />
      </UButton>
      <UButton
        :variant="activeFilter === 'overstocked' ? 'solid' : 'outline'"
        :color="activeFilter === 'overstocked' ? 'green' : 'gray'"
        :class="activeFilter === 'overstocked' ? 'ring-2 ring-green-500 ring-offset-2' : ''"
        icon="i-lucide-trending-up"
        @click="applyQuickFilter('overstocked')"
      >
        Overstocked
        <UBadge
          :label="filterCounts.overstocked.toString()"
          :color="activeFilter === 'overstocked' ? 'white' : 'green'"
          variant="solid"
          class="ml-2"
        />
      </UButton>
      <UButton
        :variant="activeFilter === 'at-risk' ? 'solid' : 'outline'"
        :color="activeFilter === 'at-risk' ? 'orange' : 'gray'"
        :class="activeFilter === 'at-risk' ? 'ring-2 ring-orange-500 ring-offset-2' : ''"
        icon="i-lucide-alert-circle"
        @click="applyQuickFilter('at-risk')"
      >
        At Risk (DIR < 14)
        <UBadge
          :label="filterCounts.atRisk.toString()"
          :color="activeFilter === 'at-risk' ? 'white' : 'orange'"
          variant="solid"
          class="ml-2"
        />
      </UButton>
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
    :ui="{ width: 'sm:max-w-md' }"
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
            <UButton
              @click="showColumnSelector = false"
            >
              Close
            </UButton>
          </div>
        </template>
      </UCard>
    </template>
  </UModal>

  <!-- Product Detail Modal -->
  <UModal
    v-model:open="showProductModal"
    :ui="{ width: 'sm:max-w-4xl' }"
  >
    <template #content>
      <UCard v-if="selectedProduct">
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-xl font-bold">{{ selectedProduct.product_name || selectedProduct.item_id }}</h3>
              <p class="text-sm text-gray-500 mt-1">{{ selectedProduct.item_id }}</p>
            </div>
            <UButton
              icon="i-lucide-x"
              variant="ghost"
              @click="showProductModal = false"
            />
          </div>
        </template>

        <div class="space-y-6">
          <!-- Product Info Grid -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p class="text-sm text-gray-500">Current Stock</p>
              <p class="text-lg font-semibold">{{ selectedProduct.current_stock || 0 }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">DIR (Days)</p>
              <p class="text-lg font-semibold">{{ (Number(selectedProduct.dir) || 0).toFixed(1) }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Risk Score</p>
              <p class="text-lg font-semibold">{{ ((Number(selectedProduct.stockout_risk) || 0) * 100).toFixed(1) }}%</p>
            </div>
            <div>
              <p class="text-sm text-gray-500">Inventory Value</p>
              <p class="text-lg font-semibold">€{{ (Number(selectedProduct.inventory_value) || 0).toLocaleString() }}</p>
            </div>
          </div>

          <!-- Why This Is Risky Section -->
          <div
            v-if="selectedProduct && riskExplanation"
            class="border-t pt-6"
          >
            <h4 class="text-lg font-semibold mb-4 flex items-center gap-2">
              <UIcon
                name="i-lucide-alert-triangle"
                class="w-5 h-5 text-red-500"
              />
              Why This Is Risky
            </h4>
            <UCard class="bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
              <ul class="space-y-2 text-sm">
                <li
                  v-for="(point, index) in riskExplanation.points"
                  :key="index"
                  class="flex items-start gap-2"
                >
                  <UIcon
                    name="i-lucide-circle"
                    class="w-1.5 h-1.5 mt-2 text-red-600 dark:text-red-400 flex-shrink-0"
                  />
                  <span class="text-gray-700 dark:text-gray-300">{{ point }}</span>
                </li>
              </ul>
            </UCard>
          </div>

          <!-- Forecast Chart (Demo) -->
          <div class="border-t pt-6">
            <h4 class="text-lg font-semibold mb-4">Forecast & Stock History</h4>
            <DashboardTrendChart
              title=""
              :data="demoProductHistoricalData"
              :forecast-data="demoProductForecastData"
              :show-forecast="true"
              label="Units"
              color="rgb(59, 130, 246)"
            />
          </div>

          <!-- Quick Actions -->
          <div class="flex items-center gap-2 border-t pt-4">
            <UButton
              icon="i-lucide-shopping-cart"
              color="primary"
              @click="handleAddToCartFromModal"
            >
              Add to Cart
            </UButton>
            <UButton
              variant="outline"
              @click="showProductModal = false"
            >
              Close
            </UButton>
          </div>
        </div>
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
const { fetchPreferences, getInventoryColumnVisibility, setInventoryColumnVisibility } = useUserPreferences();
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
      const locations = params.value as Array<{ location_id: string; location_name: string; current_stock: number }> | null | undefined;
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
        const expandIcon = isExpanded ? '▼' : '▶';
        const expandText = isExpanded ? 'Show less' : `Show ${otherLocations.length} more`;
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
        html += '</div>';
      }
      
      html += '</div>';
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
      const suppliers = params.value as Array<{ supplier_name: string; moq: number; lead_time_days: number; is_primary: boolean }> | null | undefined;
      const itemId = params.data?.item_id;
      const isExpanded = expandedRows.value.has(`${itemId}_suppliers`);
      
      if (!suppliers || suppliers.length === 0) {
        return '<span class="text-gray-400">No suppliers</span>';
      }
      
      // Find primary supplier
      const primarySupplier = suppliers.find(s => s.is_primary) || suppliers[0];
      const otherSuppliers = suppliers.filter(s => s !== primarySupplier);
      const hasMoreSuppliers = otherSuppliers.length > 0;
      
      let html = '<div class="py-1 min-w-0">';
      
      // Always show primary supplier
      const primaryBadge = '<span class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 ml-1 whitespace-nowrap">Primary</span>';
      html += `
        <div class="flex items-center gap-1 flex-wrap">
          <span class="font-medium text-sm">${primarySupplier.supplier_name}</span>${primaryBadge}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">MOQ: ${primarySupplier.moq} | Lead: ${primarySupplier.lead_time_days}d</div>
      `;
      
      // Show expand/collapse button if there are more suppliers
      if (hasMoreSuppliers) {
        const expandIcon = isExpanded ? '▼' : '▶';
        const expandText = isExpanded ? 'Show less' : `Show ${otherSuppliers.length} more`;
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
        html += '</div>';
      }
      
      html += '</div>';
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
    field: "money_impact",
    headerName: "€ Impact",
    filter: "agTextColumnFilter",
    sortable: true,
    resizable: true,
    width: 200,
    cellRenderer: (params: any) => {
      const product = params.data;
      const status = product?.status || "normal";
      const inventoryValue = parseFloat(product?.inventory_value || "0");
      const unitCost = parseFloat(product?.unit_cost || "0");
      const stockoutRisk = Number(product?.stockout_risk || 0);
      const dir = Number(product?.dir || 0);
      
      // Get sales velocity
      const salesVelocity = product?.sales_velocity || { avg_30d: 0 };
      const avgDailySales = salesVelocity.avg_30d / 30 || 0;
      
      // Calculate € impact based on status
      if (status === "overstocked") {
        // Cash tied up in overstock
        return `
          <div class="py-1">
            <div class="text-sm font-medium text-orange-700 dark:text-orange-300">
              Cash tied up: €${Math.round(inventoryValue).toLocaleString()}
            </div>
          </div>
        `;
      } else if (status === "understocked" || dir < 14 || stockoutRisk > 0.7) {
        // Revenue at risk (14 days)
        // Estimate: avg_daily_sales * unit_price * 14 * risk_factor
        const unitPrice = unitCost * 1.5; // Assume 50% markup for revenue estimate
        const riskFactor = Math.max(stockoutRisk, 0.5); // At least 50% risk if flagged
        const revenueAtRisk = avgDailySales * unitPrice * 14 * riskFactor;
        
        return `
          <div class="py-1">
            <div class="text-sm font-medium text-red-700 dark:text-red-300">
              Est. revenue at risk (14d): €${Math.round(revenueAtRisk).toLocaleString()}
            </div>
          </div>
        `;
      } else {
        return `
          <div class="py-1">
            <div class="text-sm text-gray-500 dark:text-gray-400">
              No immediate risk
            </div>
          </div>
        `;
      }
    },
    valueGetter: (params: any) => {
      // For sorting, use numeric value
      const product = params.data;
      const status = product?.status || "normal";
      const inventoryValue = parseFloat(product?.inventory_value || "0");
      
      if (status === "overstocked") {
        return inventoryValue;
      } else {
        // For understocked, use a high value so they sort to top
        return 999999999;
      }
    },
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
  {
    field: "sales_velocity",
    headerName: "Sales Velocity",
    filter: "agTextColumnFilter",
    sortable: true,
    resizable: true,
    width: 200,
    cellRenderer: (params: any) => {
      const sales = params.data?.sales_velocity || {
        avg_7d: 0,
        avg_30d: 0,
        avg_90d: 0,
        trend_7d: 0,
        trend_30d: 0,
      };
      
      const avg7d = sales.avg_7d || 0;
      const avg30d = sales.avg_30d || 0;
      const avg90d = sales.avg_90d || 0;
      const trend7d = sales.trend_7d || 0; // -1 (down), 0 (stable), 1 (up)
      const trend30d = sales.trend_30d || 0;
      
      const getTrendIcon = (trend: number) => {
        if (trend > 0) return '📈'; // Up
        if (trend < 0) return '📉'; // Down
        return '➡️'; // Stable
      };
      
      const getTrendColor = (trend: number) => {
        if (trend > 0) return 'text-green-600 dark:text-green-400';
        if (trend < 0) return 'text-red-600 dark:text-red-400';
        return 'text-gray-600 dark:text-gray-400';
      };
      
      return `
        <div class="py-1 space-y-1">
          <div class="flex items-center gap-1 text-xs">
            <span class="font-medium">7d:</span>
            <span>${avg7d.toFixed(1)}</span>
            <span class="${getTrendColor(trend7d)}">${getTrendIcon(trend7d)}</span>
          </div>
          <div class="flex items-center gap-1 text-xs">
            <span class="font-medium">30d:</span>
            <span>${avg30d.toFixed(1)}</span>
            <span class="${getTrendColor(trend30d)}">${getTrendIcon(trend30d)}</span>
          </div>
          <div class="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
            <span class="font-medium">90d:</span>
            <span>${avg90d.toFixed(1)}</span>
          </div>
        </div>
      `;
    },
    valueGetter: (params: any) => {
      // For sorting, use 30-day average
      return params.data?.sales_velocity?.avg_30d || 0;
    },
    cellStyle: { overflow: "visible", padding: "8px" },
  },
  {
    field: "actions",
    headerName: "Actions",
    sortable: false,
    filter: false,
    resizable: false,
    width: 180,
    pinned: "right",
    cellRenderer: (params: any) => {
      const itemId = params.data?.item_id || "";
      const productName = params.data?.product_name || "";
      return `
        <div class="flex items-center gap-2 h-full">
          <button 
            class="action-btn-view px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300 rounded transition-colors"
            data-item-id="${itemId}"
            data-action="view"
            title="View Details"
          >
            <span class="flex items-center gap-1">
              <span>👁</span>
              <span>View</span>
            </span>
          </button>
          <button 
            class="action-btn-cart px-2 py-1 text-xs bg-green-100 hover:bg-green-200 dark:bg-green-900 dark:hover:bg-green-800 text-green-700 dark:text-green-300 rounded transition-colors"
            data-item-id="${itemId}"
            data-product-name="${productName}"
            data-action="cart"
            title="Add to Cart"
          >
            <span class="flex items-center gap-1">
              <span>🛒</span>
              <span>Cart</span>
            </span>
          </button>
        </div>
      `;
    },
    cellStyle: { overflow: "visible", display: "flex", alignItems: "center" },
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
if (typeof window !== 'undefined') {
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

// Demo products data (hardcoded for demo branch)
const getDemoProducts = (): Product[] => {
  const categories = ["HOUSEHOLD", "HOBBIES", "FOODS", "ELECTRONICS"];
  const statuses: ("understocked" | "normal" | "overstocked")[] = ["understocked", "normal", "overstocked"];
  const products: Product[] = [];
  
  for (let i = 1; i <= 50; i++) {
    const category = categories[i % categories.length];
    const itemId = `M5_${category}_1_${String(i).padStart(3, '0')}`;
    const dir = i < 10 ? Math.random() * 10 + 1 : i < 30 ? Math.random() * 60 + 10 : Math.random() * 200 + 100;
    const stockoutRisk = dir < 14 ? Math.random() * 0.3 + 0.7 : dir < 30 ? Math.random() * 0.4 + 0.3 : Math.random() * 0.2;
    const status = dir < 14 ? "understocked" : dir > 90 ? "overstocked" : "normal";
    const currentStock = Math.floor(Math.random() * 500 + 50);
    const unitCost = (Math.random() * 50 + 10).toFixed(2);
    const inventoryValue = (currentStock * parseFloat(unitCost)).toFixed(2);
    
    // Generate demo sales velocity data
    const baseSales = Math.random() * 50 + 10; // Base daily sales
    const avg90d = baseSales;
    const avg30d = baseSales + (Math.random() - 0.5) * 10; // Some variation
    const avg7d = avg30d + (Math.random() - 0.5) * 5; // More recent variation
    
    // Calculate trends (comparing to previous period)
    const trend7d = avg7d > avg30d ? 1 : avg7d < avg30d ? -1 : 0;
    const trend30d = avg30d > avg90d ? 1 : avg30d < avg90d ? -1 : 0;
    
    const product: any = {
      item_id: itemId,
      product_name: `Product ${itemId}`,
      category: category,
      current_stock: currentStock,
      unit_cost: unitCost,
      safety_buffer_days: 7,
      dir: dir,
      stockout_risk: stockoutRisk,
      status: status,
      inventory_value: inventoryValue,
      sales_velocity: {
        avg_7d: Math.max(0, avg7d),
        avg_30d: Math.max(0, avg30d),
        avg_90d: Math.max(0, avg90d),
        trend_7d: trend7d,
        trend_30d: trend30d,
      },
      suppliers: [
        {
          supplier_id: `SUPPLIER_${i % 5 + 1}`,
          supplier_name: `Supplier ${i % 5 + 1}`,
          moq: Math.floor(Math.random() * 100 + 10),
          lead_time_days: Math.floor(Math.random() * 14 + 3),
          is_primary: true,
        },
        ...(i % 3 === 0 ? [{
          supplier_id: `SUPPLIER_${(i % 5 + 2) % 5 + 1}`,
          supplier_name: `Supplier ${(i % 5 + 2) % 5 + 1}`,
          moq: Math.floor(Math.random() * 100 + 10),
          lead_time_days: Math.floor(Math.random() * 14 + 3),
          is_primary: false,
        }] : []),
      ],
      locations: [
        {
          location_id: "WAREHOUSE_1",
          location_name: "Main Warehouse",
          current_stock: Math.floor(currentStock * 0.7),
        },
        ...(i % 2 === 0 ? [{
          location_id: "STORE_1",
          location_name: "Store Front",
          current_stock: Math.floor(currentStock * 0.3),
        }] : []),
      ],
    };
    
    products.push(product);
  }
  
  return products;
};

const loadProducts = async () => {
  // Prevent concurrent calls
  if (loading.value) {
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    // DEMO MODE: Use hardcoded data instead of API call
    // const result = await fetchProducts({
    //   page: 1,
    //   pageSize: 1000,
    //   search: searchQuery.value || undefined,
    //   supplierId: supplierId.value,
    // });
    
    let demoProducts = getDemoProducts();
    
    // Apply search filter if present
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase();
      demoProducts = demoProducts.filter(p => 
        p.item_id.toLowerCase().includes(query) || 
        p.product_name.toLowerCase().includes(query) ||
        p.category?.toLowerCase().includes(query)
      );
    }
    
    // Apply supplier filter if present
    if (supplierId.value) {
      demoProducts = demoProducts.filter(p => 
        p.suppliers?.some(s => s.supplier_id === supplierId.value)
      );
    }
    
    rowData.value = demoProducts;
    
    // Simulate network delay for demo
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // Reset expanded rows when loading new data
    expandedRows.value.clear();
    // Reset to first page after loading
    if (gridApi.value) {
      gridApi.value.paginationGoToPage(0);
      gridApi.value.resetRowHeights();
    }
  } catch (err: any) {
    // Fallback to demo data on error
    rowData.value = getDemoProducts();
    console.warn("Using demo data due to error:", err);
  } finally {
    loading.value = false;
  }
};

const onPaginationChanged = () => {
  // Client-side pagination - no action needed
};

// Quick filter state
const activeFilter = ref<'all' | 'understocked' | 'overstocked' | 'at-risk'>('all');

// Filter counts (computed from rowData)
const filterCounts = computed(() => {
  const all = rowData.value.length;
  const understocked = rowData.value.filter(p => p.status === 'understocked').length;
  const overstocked = rowData.value.filter(p => p.status === 'overstocked').length;
  const atRisk = rowData.value.filter(p => p.dir < 14).length;
  
  return {
    all,
    understocked,
    overstocked,
    atRisk,
  };
});

// Apply quick filter
const applyQuickFilter = (filter: 'all' | 'understocked' | 'overstocked' | 'at-risk') => {
  activeFilter.value = filter;
  
  if (!gridApi.value) return;
  
  // Clear existing filters
  gridApi.value.setFilterModel(null);
  
  if (filter === 'all') {
    // Show all
    return;
  }
  
  // Apply filter based on selection
  const filterModel: any = {};
  
  if (filter === 'understocked') {
    filterModel.status = {
      type: 'equals',
      filter: 'understocked',
    };
  } else if (filter === 'overstocked') {
    filterModel.status = {
      type: 'equals',
      filter: 'overstocked',
    };
  } else if (filter === 'at-risk') {
    filterModel.dir = {
      type: 'lessThan',
      filter: 14,
    };
  }
  
  gridApi.value.setFilterModel(filterModel);
};

// Product detail modal
const showProductModal = ref(false);
const selectedProduct = ref<Product | null>(null);

// Handle cell clicks for expand/collapse buttons and actions
const onCellClicked = async (params: any) => {
  // Handle expand/collapse buttons
  const expandBtn = params.event?.target?.closest('.supplier-expand-btn, .location-expand-btn');
  if (expandBtn) {
    const itemId = expandBtn.getAttribute('data-item-id');
    const type = expandBtn.getAttribute('data-type') || 'suppliers';
    if (itemId) {
      toggleSupplierRow(itemId, type);
    }
    return;
  }
  
  // Handle action buttons
  const actionBtn = params.event?.target?.closest('.action-btn-view, .action-btn-cart');
  if (actionBtn) {
    const action = actionBtn.getAttribute('data-action');
    const itemId = actionBtn.getAttribute('data-item-id');
    const productName = actionBtn.getAttribute('data-product-name');
    
    if (action === 'view') {
      // Find product in rowData
      const product = rowData.value.find(p => p.item_id === itemId);
      if (product) {
        selectedProduct.value = product;
        showProductModal.value = true;
      }
    } else if (action === 'cart') {
      // Add to cart (DEMO MODE)
      const toast = useToast();
      try {
        // DEMO MODE: Simulate add to cart without API call
        // const { addToCart } = useRecommendations();
        // const product = rowData.value.find(p => p.item_id === itemId);
        // const supplierId = product?.suppliers?.[0]?.supplier_id || undefined;
        // await addToCart(itemId, supplierId);
        
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 300));
        
        toast.add({
          title: "Added to cart",
          description: `${productName || itemId} added to order planning cart`,
          color: "success",
          icon: "i-lucide-check-circle",
        });
        
        // Refresh cart count in header (trigger reload)
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('cart-updated'));
        }
      } catch (err: any) {
        toast.add({
          title: "Error",
          description: "Failed to add item to cart",
          color: "error",
          icon: "i-lucide-alert-circle",
        });
      }
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
      console.error("Failed to load settings:", err);
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
      visibility[field] = savedVisibility[field] !== undefined 
        ? savedVisibility[field] 
        : col.hide !== true; // Default to visible unless explicitly hidden
    });
    columnVisibility.value = visibility;
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (!wasAuthError) {
      console.error("Failed to load column preferences:", err);
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
  } catch (err: any) {
    console.error("Failed to save column preferences:", err);
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

// Demo historical data for product detail modal
const demoProductHistoricalData = computed(() => {
  if (!selectedProduct.value) return [];
  
  const data = [];
  const today = new Date();
  
  // Historical data (last 60 days)
  for (let i = 60; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    const baseValue = Number(selectedProduct.value.current_stock) || 100;
    const trend = Math.sin(i / 10) * 20;
    const noise = (Math.random() - 0.5) * 10;
    const value = Math.max(0, baseValue + trend + noise);
    data.push({
      date: date.toISOString().split('T')[0],
      value: Math.round(value),
    });
  }
  
  return data;
});

// Risk explanation for product detail modal
const riskExplanation = computed(() => {
  if (!selectedProduct.value) return null;
  
  const product = selectedProduct.value;
  const currentStock = Number(product.current_stock) || 0;
  const dir = Number(product.dir) || 0;
  const stockoutRisk = (Number(product.stockout_risk) || 0) * 100;
  const unitCost = parseFloat(product.unit_cost || '0');
  
  // Get sales velocity (from demo data we added earlier)
  const salesVelocity = product.sales_velocity || {
    avg_7d: 0,
    avg_30d: 0,
    avg_90d: 0,
  };
  const avgDailySales = Math.max(salesVelocity.avg_30d / 30, 0.1); // Use 30d average
  
  // Get supplier info
  const primarySupplier = product.suppliers?.find(s => s.is_primary) || product.suppliers?.[0];
  const leadTimeDays = primarySupplier?.lead_time_days || 14;
  const moq = primarySupplier?.moq || 0;
  
  // Calculate safety stock (simple: 7 days of sales)
  const safetyDays = product.safety_buffer_days || 7;
  const safetyStock = Math.ceil(avgDailySales * safetyDays);
  
  // Calculate days until stockout
  const daysOfCover = avgDailySales > 0 ? currentStock / avgDailySales : 0;
  const daysUntilStockout = Math.max(daysOfCover - leadTimeDays, 0);
  
  // Calculate recommended reorder quantity
  const reviewPeriodDays = 7; // Demo constant
  const reorderQty = Math.max(
    Math.ceil((leadTimeDays + reviewPeriodDays + safetyDays) * avgDailySales - currentStock),
    0
  );
  
  const points: string[] = [];
  
  // Build explanation points
  if (avgDailySales > 0) {
    points.push(`Average daily sales: ${avgDailySales.toFixed(1)} units/day (based on 30-day velocity)`);
  }
  
  points.push(`Current stock: ${currentStock} units`);
  
  if (primarySupplier) {
    points.push(`Lead time: ${leadTimeDays} days (${primarySupplier.supplier_name})`);
  }
  
  points.push(`Safety stock target: ${safetyStock} units (${safetyDays} days coverage)`);
  
  if (daysUntilStockout >= 0) {
    points.push(`Days until stockout: ${daysUntilStockout.toFixed(1)} days (${daysOfCover.toFixed(1)} days cover - ${leadTimeDays} days lead time)`);
  } else {
    points.push(`⚠️ Stockout risk: Only ${daysOfCover.toFixed(1)} days of stock remaining, but lead time is ${leadTimeDays} days`);
  }
  
  if (reorderQty > 0) {
    points.push(`Recommended reorder: ${reorderQty} units to cover lead time + review period + safety buffer`);
  }
  
  if (moq > 0 && reorderQty < moq) {
    points.push(`⚠️ Note: Recommended qty (${reorderQty}) is below MOQ (${moq}). Consider ordering at least ${moq} units.`);
  }
  
  return {
    points,
    avgDailySales,
    daysUntilStockout,
    reorderQty,
  };
});

// Demo forecast data with confidence intervals for product detail modal
const demoProductForecastData = computed(() => {
  if (!selectedProduct.value) return [];
  
  const data = [];
  const today = new Date();
  const currentStock = Number(selectedProduct.value.current_stock) || 100;
  
  // Forecast data (next 30 days)
  for (let i = 1; i <= 30; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() + i);
    const forecastTrend = -i * 2; // Decreasing trend
    const forecastNoise = (Math.random() - 0.5) * 15;
    const value = Math.max(0, currentStock + forecastTrend + forecastNoise);
    const confidence = 15; // Confidence interval width
    data.push({
      date: date.toISOString().split('T')[0],
      value: Math.round(value),
      lower: Math.max(0, value - confidence),
      upper: value + confidence,
    });
  }
  
  return data;
});

// Handle Excel download (non-functional for demo)
const handleExcelDownload = () => {
  const toast = useToast();
  toast.add({
    title: "Export to Excel",
    description: "Excel export feature coming soon!",
    color: "info",
    icon: "i-lucide-info",
  });
};

// Handle add to cart from modal
const handleAddToCartFromModal = async () => {
  if (!selectedProduct.value) return;
  
  const toast = useToast();
  try {
    // DEMO MODE: Simulate add to cart without API call
    // const { addToCart } = useRecommendations();
    // const supplierId = selectedProduct.value.suppliers?.[0]?.supplier_id || undefined;
    // await addToCart(selectedProduct.value.item_id, supplierId);
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 300));
    
    toast.add({
      title: "Added to cart",
      description: `${selectedProduct.value.product_name || selectedProduct.value.item_id} added to order planning cart`,
      color: "success",
      icon: "i-lucide-check-circle",
    });
    
    // Refresh cart count
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('cart-updated'));
    }
  } catch (err: any) {
    toast.add({
      title: "Error",
      description: "Failed to add item to cart",
      color: "error",
      icon: "i-lucide-alert-circle",
    });
  }
};

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
