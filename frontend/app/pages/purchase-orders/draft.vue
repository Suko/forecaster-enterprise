<script setup lang="ts">
import type { CartItem } from "~/types/order";

definePageMeta({
  layout: "dashboard",
});

const { fetchCart, updateCartItem, removeFromCart, clearCart } = useOrderPlanningCart();
const { createPurchaseOrderFromCart } = usePurchaseOrders();
const { handleAuthError } = useAuthError();

const loading = ref(false);
const error = ref<string | null>(null);
const items = ref<CartItem[]>([]);
const totalValue = ref<string | number>("0");

const toast = useToast();

const draftQuantities = ref<Record<string, number | string>>({});

type PurchaseOrderDraft = {
  shipping_method?: string;
  shipping_unit?: string;
  notes?: string;
};

const poDrafts = ref<Record<string, PurchaseOrderDraft>>({});
const DRAFTS_STORAGE_KEY = "fe:po-drafts:v1";

const loadDraftsFromStorage = () => {
  if (!process.client) return;
  try {
    const raw = localStorage.getItem(DRAFTS_STORAGE_KEY);
    poDrafts.value = raw ? JSON.parse(raw) : {};
  } catch {
    poDrafts.value = {};
  }
};

const persistDraftsToStorage = () => {
  if (!process.client) return;
  try {
    localStorage.setItem(DRAFTS_STORAGE_KEY, JSON.stringify(poDrafts.value));
  } catch {
    // Ignore storage errors (private mode, quota, etc.)
  }
};

const keyFor = (item: CartItem) => `${item.item_id}::${item.supplier_id}`;

const groupedBySupplier = computed(() => {
  const groups = new Map<
    string,
    { supplier_id: string; supplier_name: string; items: CartItem[]; total: number }
  >();

  for (const item of items.value) {
    const supplierId = item.supplier_id;
    const current = groups.get(supplierId) || {
      supplier_id: supplierId,
      supplier_name: item.supplier_name,
      items: [],
      total: 0,
    };
    current.items.push(item);
    current.total += Number(item.total_price || 0);
    groups.set(supplierId, current);
  }

  return Array.from(groups.values());
});

const loadCart = async () => {
  if (loading.value) return;
  loading.value = true;
  error.value = null;
  try {
    // DEMO MODE: Use hardcoded demo cart data
    // const cart = await fetchCart();
    // items.value = cart.items || [];
    // totalValue.value = cart.total_value;
    
    // Demo cart items (hardcoded for demo)
    const demoCartItems: any[] = [
      {
        id: '1',
        item_id: 'M5_HOUSEHOLD_1_334',
        product_name: 'Product M5_HOUSEHOLD_1_334',
        supplier_id: 'SUPPLIER_1',
        supplier_name: 'Supplier 1',
        quantity: 70,
        unit_cost: '12.50',
        total_price: '875.00',
        moq: 50,
        lead_time_days: 14,
        notes: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: '2',
        item_id: 'M5_HOBBIES_1_387',
        product_name: 'Product M5_HOBBIES_1_387',
        supplier_id: 'SUPPLIER_1',
        supplier_name: 'Supplier 1',
        quantity: 30,
        unit_cost: '18.75',
        total_price: '562.50',
        moq: 25,
        lead_time_days: 14,
        notes: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: '3',
        item_id: 'M5_HOBBIES_1_404',
        product_name: 'Product M5_HOBBIES_1_404',
        supplier_id: 'SUPPLIER_2',
        supplier_name: 'Supplier 2',
        quantity: 90,
        unit_cost: '22.00',
        total_price: '1980.00',
        moq: 50,
        lead_time_days: 10,
        notes: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];
    
    items.value = demoCartItems;
    totalValue.value = demoCartItems.reduce((sum, item) => sum + parseFloat(item.total_price || '0'), 0).toString();
    
    const nextDrafts: Record<string, number> = {};
    const nextPoDrafts: Record<string, PurchaseOrderDraft> = { ...poDrafts.value };
    for (const item of items.value) {
      nextDrafts[keyFor(item)] = item.quantity;
      if (!nextPoDrafts[item.supplier_id]) {
        nextPoDrafts[item.supplier_id] = {};
      }
    }
    draftQuantities.value = nextDrafts;
    poDrafts.value = nextPoDrafts;
    persistDraftsToStorage();
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 200));
  } catch (err: any) {
    // Fallback to demo data
    error.value = null; // Don't show error in demo mode
    console.warn("Using demo cart data:", err);
  } finally {
    loading.value = false;
  }
};

const formatMoney = (value: string | number) => {
  const num = Number(value || 0);
  return `€${num.toLocaleString("de-DE", { maximumFractionDigits: 2 })}`;
};

const onUpdateQuantity = async (item: CartItem) => {
  const key = keyFor(item);
  const nextQty = Number(draftQuantities.value[key]);

  if (!Number.isFinite(nextQty) || nextQty <= 0) {
    toast.add({ title: "Invalid quantity", description: "Quantity must be >= 1", color: "red" });
    return;
  }

  try {
    await updateCartItem(item.item_id, item.supplier_id, { quantity: Math.floor(nextQty) });
    toast.add({
      title: "Updated",
      description: `${item.product_name} quantity updated`,
      color: "green",
    });
    await loadCart();
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    // Extract error message from FastAPI error response (detail field) or other sources
    const errorMessage =
      err.data?.detail || // FastAPI error detail
      err.data?.statusMessage || // Nuxt error statusMessage
      err.data?.message || // Generic error message
      err.message || // Error object message
      "Failed to update item";
    toast.add({
      title: "Update failed",
      description: errorMessage,
      color: "red",
    });
  }
};

const onRemoveItem = async (item: CartItem) => {
  try {
    await removeFromCart(item.item_id, item.supplier_id);
    toast.add({
      title: "Removed",
      description: `${item.product_name} removed from cart`,
      color: "green",
    });
    await loadCart();
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    const errorMessage =
      err.data?.detail ||
      err.data?.statusMessage ||
      err.data?.message ||
      err.message ||
      "Failed to remove item";
    toast.add({
      title: "Remove failed",
      description: errorMessage,
      color: "red",
    });
  }
};

const onClearCart = async () => {
  try {
    await clearCart();
    toast.add({ title: "Cleared", description: "Cart cleared", color: "green" });
    await loadCart();
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    toast.add({
      title: "Clear failed",
      description: err.message || "Failed to clear cart",
      color: "red",
    });
  }
};

const creatingPoSupplierId = ref<string | null>(null);

// Get supplier lead time (demo - from first item or default)
const getSupplierLeadTime = (supplierId: string): number => {
  const group = groupedBySupplier.value.find(g => g.supplier_id === supplierId);
  if (group && group.items.length > 0) {
    // Try to get lead time from item, or use default
    const item = group.items[0];
    return (item as any).lead_time_days || 14; // Demo default
  }
  return 14; // Demo default
};

// Get estimated arrival date
const getEstimatedArrival = (supplierId: string): string => {
  const leadTime = getSupplierLeadTime(supplierId);
  const arrivalDate = new Date();
  arrivalDate.setDate(arrivalDate.getDate() + leadTime);
  return arrivalDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

// Check for MOQ issues
const hasMOQIssues = (group: { supplier_id: string; supplier_name: string; items: CartItem[]; total: number }): boolean => {
  return group.items.some(item => {
    const qty = Number(draftQuantities.value[keyFor(item)]);
    return item.moq > 0 && qty < item.moq;
  });
};

// Get MOQ warning message
const getMOQWarningMessage = (group: { supplier_id: string; supplier_name: string; items: CartItem[]; total: number }): string => {
  const issues = group.items
    .filter(item => {
      const qty = Number(draftQuantities.value[keyFor(item)]);
      return item.moq > 0 && qty < item.moq;
    })
    .map(item => `${item.product_name} (qty: ${draftQuantities.value[keyFor(item)]}, MOQ: ${item.moq})`);
  
  if (issues.length === 0) return '';
  return `Some items are below MOQ. Adjust quantities: ${issues.join(', ')}`;
};

// Calculate days of demand coverage for this PO
const getDaysOfDemandCoverage = (group: { supplier_id: string; supplier_name: string; items: CartItem[]; total: number }): number => {
  const leadTime = getSupplierLeadTime(group.supplier_id);
  const totalQuantity = group.items.reduce((sum, item) => sum + Number(draftQuantities.value[keyFor(item)]), 0);
  
  // Estimate: assume average daily sales per item
  // For demo: use rough estimate based on quantities
  const avgDailySalesPerItem = 15; // Demo constant
  const totalDailyDemand = group.items.length * avgDailySalesPerItem;
  const daysOfCoverage = totalDailyDemand > 0 ? Math.round(totalQuantity / totalDailyDemand) : leadTime + 7;
  
  return Math.max(leadTime + 7, daysOfCoverage); // At least lead time + buffer
};

// Calculate percentage of risk resolved
const getRiskResolved = (group: { supplier_id: string; supplier_name: string; items: CartItem[]; total: number }): number => {
  // For demo: estimate based on number of items and their urgency
  // Assume each item in cart resolves some risk
  const itemsCount = group.items.length;
  const avgRiskPerItem = 15; // Demo: each item resolves ~15% of total risk
  const riskResolved = Math.min(100, itemsCount * avgRiskPerItem);
  
  return Math.round(riskResolved);
};

// Export draft PO to CSV
const exportDraftPO = (group: { supplier_id: string; supplier_name: string; items: CartItem[]; total: number }) => {
  const leadTime = getSupplierLeadTime(group.supplier_id);
  const arrivalDate = getEstimatedArrival(group.supplier_id);
  
  // Build CSV content
  const headers = ['SKU', 'Product Name', 'Quantity', 'Unit Cost', 'Line Total', 'MOQ', 'Lead Time (days)', 'Est. Arrival'];
  const rows = group.items.map(item => [
    item.item_id,
    item.product_name,
    item.quantity.toString(),
    item.unit_cost,
    item.total_price,
    (item.moq || 0).toString(),
    leadTime.toString(),
    arrivalDate,
  ]);
  
  const csvContent = [
    `Draft Purchase Order - ${group.supplier_name}`,
    `Generated: ${new Date().toLocaleDateString()}`,
    `Total Value: ${formatMoney(group.total)}`,
    '',
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
  ].join('\n');
  
  // Download CSV
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', `PO_Draft_${group.supplier_name}_${new Date().toISOString().split('T')[0]}.csv`);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  const toast = useToast();
  toast.add({
    title: "Draft PO exported",
    description: `CSV file downloaded for ${group.supplier_name}`,
    color: "success",
    icon: "i-lucide-check-circle",
  });
};

const onCreatePoForSupplier = async (supplierId: string) => {
  if (creatingPoSupplierId.value) return;
  creatingPoSupplierId.value = supplierId;
  try {
    const draft = poDrafts.value[supplierId] || {};
    const po = await createPurchaseOrderFromCart({
      supplier_id: supplierId,
      shipping_method: draft.shipping_method,
      shipping_unit: draft.shipping_unit,
      notes: draft.notes,
    });
    poDrafts.value[supplierId] = {};
    persistDraftsToStorage();
    toast.add({ title: "Purchase order created", description: po.po_number, color: "green" });
    await loadCart();
    await navigateTo(`/purchase-orders/${po.id}`);
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    const errorMessage =
      err.data?.detail ||
      err.data?.statusMessage ||
      err.data?.message ||
      err.message ||
      "Failed to create PO";
    toast.add({
      title: "Create PO failed",
      description: errorMessage,
      color: "red",
    });
  } finally {
    creatingPoSupplierId.value = null;
  }
};

onMounted(async () => {
  loadDraftsFromStorage();
  watch(poDrafts, persistDraftsToStorage, { deep: true });
  await loadCart();
});
</script>

<template>
  <div class="p-6 space-y-4">
    <div>
      <h1 class="text-3xl font-bold">Purchase Orders</h1>
      <p class="text-sm text-muted">Draft and create POs per supplier.</p>
    </div>

    <PurchaseOrdersSectionTabs />

    <div class="flex items-center justify-end gap-2">
      <UButton
        icon="i-lucide-refresh-cw"
        variant="ghost"
        :loading="loading"
        @click="loadCart"
      >
        Refresh
      </UButton>
      <UButton
        icon="i-lucide-trash-2"
        color="red"
        variant="soft"
        :disabled="loading || items.length === 0"
        @click="onClearCart"
      >
        Clear cart
      </UButton>
    </div>

    <div
      v-if="loading"
      class="flex items-center justify-center py-12"
    >
      <UIcon
        name="i-lucide-loader-2"
        class="w-8 h-8 animate-spin text-primary"
      />
    </div>

    <UAlert
      v-else-if="error"
      color="error"
      variant="soft"
      title="Error loading cart"
      :description="error"
    />

    <UCard v-else-if="items.length === 0">
      <div class="p-6 text-center text-muted">
        Your cart is empty. Add items from Recommendations to start an order.
      </div>
    </UCard>

    <div
      v-else
      class="space-y-4"
    >
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">Summary</h2>
            <div class="text-sm text-muted">
              {{ items.length }} item(s) · {{ formatMoney(totalValue) }}
            </div>
          </div>
        </template>
      </UCard>

      <UCard
        v-for="group in groupedBySupplier"
        :key="group.supplier_id"
      >
        <template #header>
          <div class="space-y-3">
            <div class="flex items-center justify-between gap-3">
              <div class="flex-1">
                <button
                  class="font-semibold text-left hover:underline"
                  type="button"
                  @click="navigateTo(`/purchase-orders/suppliers/${group.supplier_id}`)"
                >
                  {{ group.supplier_name }}
                </button>
                <div class="flex items-center gap-4 mt-1">
                  <p class="text-xs text-muted">
                    {{ group.items.length }} item(s) · {{ formatMoney(group.total) }}
                  </p>
                  <div
                    v-if="getSupplierLeadTime(group.supplier_id)"
                    class="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400"
                  >
                    <UIcon
                      name="i-lucide-clock"
                      class="w-3 h-3"
                    />
                    <span>Lead time: {{ getSupplierLeadTime(group.supplier_id) }} days</span>
                    <span class="text-gray-400">·</span>
                    <span>Est. arrival: {{ getEstimatedArrival(group.supplier_id) }}</span>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <UButton
                  icon="i-lucide-download"
                  variant="outline"
                  size="sm"
                  @click="exportDraftPO(group)"
                >
                  Export
                </UButton>
                <UButton
                  icon="i-lucide-file-plus-2"
                  :loading="creatingPoSupplierId === group.supplier_id"
                  @click="onCreatePoForSupplier(group.supplier_id)"
                >
                  Create PO
                </UButton>
              </div>
            </div>
            
            <!-- PO Summary -->
            <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800">
              <div class="flex items-center justify-between gap-4 text-sm">
                <div class="flex items-center gap-4">
                  <div>
                    <span class="text-gray-600 dark:text-gray-400">This PO covers</span>
                    <span class="font-semibold text-gray-900 dark:text-gray-100 ml-1">{{ getDaysOfDemandCoverage(group) }} days</span>
                    <span class="text-gray-600 dark:text-gray-400 ml-1">of demand</span>
                  </div>
                  <div>
                    <span class="text-gray-600 dark:text-gray-400">and resolves</span>
                    <span class="font-semibold text-gray-900 dark:text-gray-100 ml-1">{{ getRiskResolved(group) }}%</span>
                    <span class="text-gray-600 dark:text-gray-400 ml-1">of current risk</span>
                  </div>
                </div>
                <div
                  v-if="hasMOQIssues(group)"
                  class="flex items-center gap-1 text-orange-600 dark:text-orange-400 text-xs font-medium"
                >
                  <UIcon
                    name="i-lucide-alert-triangle"
                    class="w-4 h-4"
                  />
                  <span>Some items below MOQ</span>
                </div>
                <div
                  v-else
                  class="flex items-center gap-1 text-green-600 dark:text-green-400 text-xs font-medium"
                >
                  <UIcon
                    name="i-lucide-check-circle"
                    class="w-4 h-4"
                  />
                  <span>All MOQs met</span>
                </div>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Quantities are recommendations and can be adjusted.
              </p>
            </div>
          </div>
        </template>

        <!-- MOQ Warning -->
        <UAlert
          v-if="hasMOQIssues(group)"
          color="warning"
          variant="soft"
          class="mx-4 mb-4"
          title="MOQ Warning"
          :description="getMOQWarningMessage(group)"
        />

        <div class="p-4 space-y-3">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
            <UInput
              v-model="poDrafts[group.supplier_id].shipping_method"
              placeholder="Shipping method (optional)"
              size="sm"
            />
            <UInput
              v-model="poDrafts[group.supplier_id].shipping_unit"
              placeholder="Shipping unit (optional)"
              size="sm"
            />
            <UInput
              v-model="poDrafts[group.supplier_id].notes"
              placeholder="Notes (optional)"
              size="sm"
            />
          </div>
        </div>

        <div class="divide-y">
          <div
            v-for="item in group.items"
            :key="keyFor(item)"
            class="py-3 flex items-center gap-3"
          >
            <div class="flex-1 min-w-0">
              <div class="font-medium truncate">{{ item.product_name }}</div>
              <div class="text-xs text-muted">{{ item.item_id }}</div>
              <div class="text-xs text-muted">
                Unit: {{ formatMoney(item.unit_cost) }} · Total: {{ formatMoney(item.total_price) }}
              </div>
            </div>

            <div class="flex items-center gap-2">
              <div class="w-28">
                <UInput
                  v-model.number="draftQuantities[keyFor(item)]"
                  type="number"
                  :min="item.moq > 0 ? item.moq : 1"
                  step="1"
                  size="sm"
                  :class="Number(draftQuantities[keyFor(item)]) < item.moq && item.moq > 0 ? 'ring-2 ring-red-500' : ''"
                />
              </div>
              <div
                v-if="item.moq > 0"
                class="text-xs whitespace-nowrap"
                :class="Number(draftQuantities[keyFor(item)]) < item.moq ? 'text-red-600 dark:text-red-400 font-medium' : 'text-muted'"
              >
                MOQ: {{ item.moq }}
              </div>
            </div>

            <UButton
              size="sm"
              variant="soft"
              @click="onUpdateQuantity(item)"
            >
              Update
            </UButton>
            <UButton
              size="sm"
              color="red"
              variant="ghost"
              @click="onRemoveItem(item)"
            >
              Remove
            </UButton>
          </div>
        </div>
        
        <!-- Supplier Summary Footer -->
        <div class="border-t p-4 bg-gray-50 dark:bg-gray-900/50">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p class="text-gray-500 dark:text-gray-400">Items</p>
              <p class="font-semibold">{{ group.items.length }}</p>
            </div>
            <div>
              <p class="text-gray-500 dark:text-gray-400">Total Quantity</p>
              <p class="font-semibold">{{ group.items.reduce((sum, item) => sum + Number(draftQuantities[keyFor(item)]), 0) }}</p>
            </div>
            <div>
              <p class="text-gray-500 dark:text-gray-400">Lead Time</p>
              <p class="font-semibold">{{ getSupplierLeadTime(group.supplier_id) }} days</p>
            </div>
            <div>
              <p class="text-gray-500 dark:text-gray-400">Total Value</p>
              <p class="font-semibold">{{ formatMoney(group.total) }}</p>
            </div>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
