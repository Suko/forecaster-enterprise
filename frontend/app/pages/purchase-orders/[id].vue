<script setup lang="ts">
import type { PurchaseOrder } from "~/types/order";
import type { Supplier } from "~/types/supplier";

definePageMeta({
  layout: "dashboard",
});

const route = useRoute();
const poId = computed(() => String(route.params.id || ""));

const { fetchPurchaseOrder, updatePurchaseOrderStatus } = usePurchaseOrders();
const { fetchSupplier } = useSuppliers();
const { handleAuthError } = useAuthError();
const toast = useToast();

const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const po = ref<PurchaseOrder | null>(null);

const supplierLoading = ref(false);
const supplierError = ref<string | null>(null);
const supplier = ref<Supplier | null>(null);

const statusOptions = [
  { label: "Pending", value: "pending" },
  { label: "Confirmed", value: "confirmed" },
  { label: "Shipped", value: "shipped" },
  { label: "Received", value: "received" },
  { label: "Cancelled", value: "cancelled" },
];

const selectedStatus = ref<"pending" | "confirmed" | "shipped" | "received" | "cancelled">("pending");

const formatMoney = (value: string | number) => {
  const num = Number(value || 0);
  return `€${num.toLocaleString("de-DE", { maximumFractionDigits: 2 })}`;
};

const loadPo = async () => {
  if (!poId.value) return;
  loading.value = true;
  error.value = null;
  try {
    const data = await fetchPurchaseOrder(poId.value);
    po.value = data;
    if (data.status && statusOptions.some((s) => s.value === data.status)) {
      selectedStatus.value = data.status as any;
    }

    // Load supplier info (for contact details)
    supplier.value = null;
    supplierError.value = null;
    if (data.supplier_id) {
      supplierLoading.value = true;
      try {
        supplier.value = await fetchSupplier(data.supplier_id);
      } catch (err: any) {
        const wasAuthError = await handleAuthError(err);
        if (!wasAuthError) {
          supplierError.value = err.message || "Failed to load supplier";
        }
      } finally {
        supplierLoading.value = false;
      }
    }
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    error.value = err.message || "Failed to load purchase order";
  } finally {
    loading.value = false;
  }
};

const onSaveStatus = async () => {
  if (!po.value) return;
  saving.value = true;
  try {
    const updated = await updatePurchaseOrderStatus(po.value.id, selectedStatus.value);
    po.value = updated;
    toast.add({ title: "Status updated", description: updated.status, color: "green" });
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    toast.add({ title: "Update failed", description: err.message || "Failed to update status", color: "red" });
  } finally {
    saving.value = false;
  }
};

onMounted(async () => {
  await loadPo();
});
</script>

<template>
  <div class="p-6 space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="text-3xl font-bold">Purchase Order</h1>
        <p v-if="po" class="text-sm text-muted">{{ po.po_number }} · {{ po.supplier_name }}</p>
      </div>
      <div class="flex items-center gap-2">
        <UButton icon="i-lucide-arrow-left" variant="ghost" @click="navigateTo('/purchase-orders')">
          Back
        </UButton>
        <UButton icon="i-lucide-refresh-cw" variant="ghost" :loading="loading" @click="loadPo">
          Refresh
        </UButton>
      </div>
    </div>

    <PurchaseOrdersSectionTabs />

    <div v-if="loading" class="flex items-center justify-center py-12">
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin text-primary" />
    </div>

    <UAlert v-else-if="error" color="error" variant="soft" title="Error loading purchase order" :description="error" />

    <div v-else-if="po" class="space-y-4">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-lg font-semibold">Overview</h2>
            <div class="text-sm text-muted">Total: {{ formatMoney(po.total_amount) }}</div>
          </div>
        </template>

        <div class="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-muted">Status</div>
            <div class="flex items-center gap-2 mt-1">
              <USelectMenu
                v-model="selectedStatus"
                :options="statusOptions"
                value-attribute="value"
                option-attribute="label"
                class="w-44"
              />
              <UButton :loading="saving" @click="onSaveStatus">Save</UButton>
            </div>
          </div>
          <div>
            <div class="text-xs text-muted">Dates</div>
            <div class="text-sm mt-1">
              Order: {{ po.order_date }}
              <span v-if="po.expected_delivery_date"> · ETA: {{ po.expected_delivery_date }}</span>
            </div>
          </div>
          <div>
            <div class="text-xs text-muted">Shipping</div>
            <div class="text-sm mt-1">
              <span v-if="po.shipping_method">{{ po.shipping_method }}</span>
              <span v-else class="text-muted">—</span>
              <span v-if="po.shipping_unit"> · {{ po.shipping_unit }}</span>
            </div>
          </div>
          <div>
            <div class="text-xs text-muted">Created By</div>
            <div class="text-sm mt-1">{{ po.created_by || '—' }}</div>
          </div>
          <div class="md:col-span-2">
            <div class="text-xs text-muted">Notes</div>
            <div class="text-sm mt-1 whitespace-pre-line">{{ po.notes || '—' }}</div>
          </div>
        </div>
      </UCard>

      <UCard>
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-lg font-semibold">Supplier</h2>
            <div class="flex items-center gap-2">
              <UButton
                icon="i-lucide-truck"
                variant="soft"
                @click="navigateTo(`/purchase-orders/suppliers/${po.supplier_id}`)"
              >
                View supplier
              </UButton>
              <UButton
                icon="i-lucide-receipt"
                variant="ghost"
                @click="navigateTo({ path: '/purchase-orders', query: { supplier_id: po.supplier_id } })"
              >
                All POs
              </UButton>
            </div>
          </div>
        </template>

        <div v-if="supplierLoading" class="p-6 flex items-center justify-center">
          <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-primary" />
        </div>
        <UAlert
          v-else-if="supplierError"
          color="error"
          variant="soft"
          title="Error loading supplier"
          :description="supplierError"
        />
        <div v-else class="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-muted">Name</div>
            <div class="text-sm mt-1">{{ supplier?.name || po.supplier_name }}</div>
          </div>
          <div>
            <div class="text-xs text-muted">Contact</div>
            <div class="text-sm mt-1">
              <div>{{ supplier?.contact_email || '—' }}</div>
              <div v-if="supplier?.contact_phone">{{ supplier.contact_phone }}</div>
            </div>
          </div>
          <div class="md:col-span-2">
            <div class="text-xs text-muted">Address</div>
            <div class="text-sm mt-1 whitespace-pre-line">{{ supplier?.address || '—' }}</div>
          </div>
        </div>
      </UCard>

      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold">Items</h2>
        </template>
        <div class="divide-y">
          <div v-for="item in po.items" :key="item.id" class="py-3 flex items-center gap-3">
            <div class="flex-1 min-w-0">
              <div class="font-medium truncate">{{ item.product_name }}</div>
              <div class="text-xs text-muted">{{ item.item_id }}</div>
            </div>
            <div class="text-right w-28">
              <div class="font-medium">{{ item.quantity }}</div>
              <div class="text-xs text-muted">Qty</div>
            </div>
            <div class="text-right w-32">
              <div class="font-medium">{{ formatMoney(item.total_price) }}</div>
              <div class="text-xs text-muted">Line total</div>
            </div>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
