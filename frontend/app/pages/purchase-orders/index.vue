<script setup lang="ts">
import type { PurchaseOrderListItem } from "~/types/order";

definePageMeta({
  layout: "dashboard",
});

const { fetchPurchaseOrders } = usePurchaseOrders();
const { handleAuthError } = useAuthError();

const route = useRoute();
const supplierFilterId = computed(() =>
  typeof route.query.supplier_id === "string" ? route.query.supplier_id : undefined
);

const loading = ref(false);
const error = ref<string | null>(null);
const orders = ref<PurchaseOrderListItem[]>([]);

const statusOptions = [
  { label: "All", value: null },
  { label: "Pending", value: "pending" },
  { label: "Confirmed", value: "confirmed" },
  { label: "Shipped", value: "shipped" },
  { label: "Received", value: "received" },
  { label: "Cancelled", value: "cancelled" },
];

const selectedStatus = ref<string | null>(null);

const formatMoney = (value: string | number) => {
  const num = Number(value || 0);
  return `€${num.toLocaleString("de-DE", { maximumFractionDigits: 2 })}`;
};

const loadOrders = async () => {
  if (loading.value) return;
  loading.value = true;
  error.value = null;
  try {
    const res = await fetchPurchaseOrders({
      status: selectedStatus.value || undefined,
      supplier_id: supplierFilterId.value,
      page: 1,
      page_size: 50,
    });
    orders.value = res.items || [];
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    error.value = err.message || "Failed to load purchase orders";
  } finally {
    loading.value = false;
  }
};

const badgeColorForStatus = (status: string) => {
  if (status === "pending") return "yellow";
  if (status === "confirmed") return "blue";
  if (status === "shipped") return "purple";
  if (status === "received") return "green";
  if (status === "cancelled") return "red";
  return "gray";
};

watch(selectedStatus, async () => {
  await loadOrders();
});

watch(supplierFilterId, async () => {
  await loadOrders();
});

onMounted(async () => {
  await loadOrders();
});
</script>

<template>
  <div class="p-6 space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="text-3xl font-bold">Purchase Orders</h1>
        <p class="text-sm text-muted">
          Track orders through their lifecycle.
          <span v-if="supplierFilterId"> (filtered by supplier)</span>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <USelectMenu
          v-model="selectedStatus"
          :options="statusOptions"
          value-attribute="value"
          option-attribute="label"
          placeholder="Filter by status"
          class="w-44"
        />
        <UButton
          v-if="supplierFilterId"
          icon="i-lucide-x"
          variant="ghost"
          @click="navigateTo('/purchase-orders')"
        >
          Clear supplier
        </UButton>
        <UButton icon="i-lucide-refresh-cw" variant="ghost" :loading="loading" @click="loadOrders">
          Refresh
        </UButton>
      </div>
    </div>

    <PurchaseOrdersSectionTabs />

    <div v-if="loading && orders.length === 0" class="flex items-center justify-center py-12">
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin text-primary" />
    </div>

    <UAlert v-else-if="error" color="error" variant="soft" title="Error loading purchase orders" :description="error" />

    <UCard v-else-if="orders.length === 0">
      <div class="p-6 text-center text-muted">
        No purchase orders yet. Create one from the cart.
      </div>
    </UCard>

    <div v-else class="space-y-2">
      <UCard
        v-for="po in orders"
        :key="po.id"
        class="cursor-pointer hover:shadow-sm transition-shadow"
        @click="navigateTo(`/purchase-orders/${po.id}`)"
      >
        <div class="p-4 flex items-center justify-between gap-4">
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <div class="font-semibold">{{ po.po_number }}</div>
              <UBadge :color="badgeColorForStatus(po.status)" variant="soft">{{ po.status }}</UBadge>
            </div>
            <div class="text-sm text-muted truncate">{{ po.supplier_name }}</div>
            <div class="text-xs text-muted">
              Order date: {{ po.order_date }}
              <span v-if="po.expected_delivery_date"> · ETA: {{ po.expected_delivery_date }}</span>
            </div>
          </div>
          <div class="text-right">
            <div class="font-medium">{{ formatMoney(po.total_amount) }}</div>
            <div class="text-xs text-muted">Total</div>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
