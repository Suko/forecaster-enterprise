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
          icon="i-lucide-refresh-cw"
          variant="ghost"
          :loading="loading"
          @click="loadProducts"
        >
          Refresh
        </UButton>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin text-primary" />
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
    <div v-else class="h-[calc(100vh-200px)]">
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
          @pagination-changed="onPaginationChanged"
        />
        <template #fallback>
          <div class="flex items-center justify-center h-full">
            <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin text-primary" />
          </div>
        </template>
      </ClientOnly>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AgGridVue } from 'ag-grid-vue3'
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import type { ColDef, GridReadyEvent } from 'ag-grid-community'
import type { Product } from '~/types/product'

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule])

definePageMeta({
  layout: 'dashboard',
})

const { fetchProducts } = useAgGridProducts()

const rowData = ref<Product[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const gridApi = ref<any>(null)
const gridInitialized = ref(false)

// Column Definitions
const columnDefs = ref<ColDef[]>([
  {
    field: 'item_id',
    headerName: 'SKU',
    filter: 'agTextColumnFilter',
    sortable: true,
    resizable: true,
    width: 120,
  },
  {
    field: 'product_name',
    headerName: 'Product Name',
    filter: 'agTextColumnFilter',
    sortable: true,
    resizable: true,
    flex: 1,
  },
  {
    field: 'category',
    headerName: 'Category',
    filter: 'agTextColumnFilter',
    sortable: true,
    resizable: true,
    width: 150,
  },
  {
    field: 'current_stock',
    headerName: 'Stock',
    filter: 'agNumberColumnFilter',
    sortable: true,
    resizable: true,
    width: 100,
    type: 'numericColumn',
  },
  {
    field: 'unit_cost',
    headerName: 'Unit Cost',
    filter: 'agNumberColumnFilter',
    sortable: true,
    resizable: true,
    width: 120,
    type: 'numericColumn',
    valueFormatter: (params) => `€${parseFloat(params.value || '0').toFixed(2)}`,
  },
  {
    field: 'inventory_value',
    headerName: 'Inventory Value',
    filter: 'agNumberColumnFilter',
    sortable: true,
    resizable: true,
    width: 150,
    type: 'numericColumn',
    valueFormatter: (params) => `€${parseFloat(params.value || '0').toLocaleString()}`,
  },
  {
    field: 'dir',
    headerName: 'DIR (Days)',
    filter: 'agNumberColumnFilter',
    sortable: true,
    resizable: true,
    width: 120,
    type: 'numericColumn',
    valueFormatter: (params) => {
      const value = Number(params.value)
      return isNaN(value) ? '0' : value.toFixed(1)
    },
    cellStyle: (params) => {
      if (params.value < 14) return { backgroundColor: '#fee2e2' } // Red for low
      if (params.value > 90) return { backgroundColor: '#dcfce7' } // Green for high
      return null
    },
  },
  {
    field: 'stockout_risk',
    headerName: 'Risk Score',
    filter: 'agNumberColumnFilter',
    sortable: true,
    resizable: true,
    width: 120,
    type: 'numericColumn',
    valueFormatter: (params) => {
      const value = Number(params.value)
      return isNaN(value) ? '0%' : `${(value * 100).toFixed(1)}%`
    },
    cellStyle: (params) => {
      const risk = params.value * 100
      if (risk > 70) return { backgroundColor: '#fee2e2' } // Red
      if (risk > 40) return { backgroundColor: '#fef3c7' } // Yellow
      return { backgroundColor: '#dcfce7' } // Green
    },
  },
  {
    field: 'status',
    headerName: 'Status',
    filter: 'agTextColumnFilter',
    sortable: true,
    resizable: true,
    width: 150,
    cellRenderer: (params: any) => {
      const status = params.value || 'normal'
      const colors: Record<string, string> = {
        understocked: 'red',
        overstocked: 'green',
        normal: 'gray',
      }
      const color = colors[status] || 'gray'
      return `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-${color}-100 text-${color}-800 whitespace-nowrap">${status}</span>`
    },
    cellStyle: { overflow: 'visible' },
  },
])

const defaultColDef: ColDef = {
  resizable: true,
  sortable: true,
  filter: true,
}

const onGridReady = (params: GridReadyEvent) => {
  // Only set API reference, don't load data here
  // Data loading happens in onMounted to prevent loops
  if (!gridInitialized.value) {
    gridApi.value = params.api
    gridInitialized.value = true
  } else {
    // Grid was recreated, just update the API reference
    gridApi.value = params.api
  }
}

const { handleAuthError } = useAuthError()

const loadProducts = async () => {
  // Prevent concurrent calls
  if (loading.value) {
    return
  }
  
  loading.value = true
  error.value = null

  try {
    // Fetch all products (up to 1000, which is the API max)
    // AG Grid will handle client-side pagination
    const result = await fetchProducts({
      page: 1,
      pageSize: 1000, // Fetch all products
      search: searchQuery.value || undefined,
    })
    rowData.value = result.rowData
    
    // Reset to first page after loading
    if (gridApi.value) {
      gridApi.value.paginationGoToPage(0)
    }
  } catch (err: any) {
    // Handle 401 errors - redirect to login
    const wasAuthError = await handleAuthError(err)
    if (wasAuthError) {
      // Redirect is handled, just return
      return
    }
    error.value = err.message || 'Failed to load products'
    console.error('Products error:', err)
  } finally {
    loading.value = false
  }
}

const onPaginationChanged = () => {
  // Client-side pagination - no action needed
}

// Load data on mount, not on grid ready
onMounted(() => {
  loadProducts()
})

const onSearch = () => {
  // Debounce search - reload after user stops typing
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }
  searchTimeout.value = setTimeout(() => {
    loadProducts() // Reload all products with search filter
  }, 500)
}

const searchTimeout = ref<NodeJS.Timeout | null>(null)

onUnmounted(() => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }
  // Clean up grid API
  if (gridApi.value) {
    try {
      gridApi.value.destroy()
    } catch (e) {
      // Grid may already be destroyed
    }
    gridApi.value = null
  }
  // Reset grid initialized flag when component unmounts
  gridInitialized.value = false
})
</script>
