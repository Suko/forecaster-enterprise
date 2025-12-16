<script setup lang="ts">
import type { CartItem } from "~/types/order";
import { logger } from "~~/server/utils/logger";

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
    const cart = await fetchCart();
    items.value = cart.items || [];
    totalValue.value = cart.total_value;
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
  } catch (err: any) {
    logger.error("Load cart error", { error: err });
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    error.value = err.message || "Failed to load cart";
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
    logger.error("Update cart quantity error", { error: err });
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
    logger.error("Remove cart item error", { error: err });
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
    logger.error("Clear cart error", { error: err });
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
    logger.error("Create purchase order error", { error: err });
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
          <div class="flex items-center justify-between gap-3">
            <div>
              <button
                class="font-semibold text-left hover:underline"
                type="button"
                @click="navigateTo(`/purchase-orders/suppliers/${group.supplier_id}`)"
              >
                {{ group.supplier_name }}
              </button>
              <p class="text-xs text-muted">
                {{ group.items.length }} item(s) · {{ formatMoney(group.total) }}
              </p>
            </div>
            <UButton
              icon="i-lucide-file-plus-2"
              :loading="creatingPoSupplierId === group.supplier_id"
              @click="onCreatePoForSupplier(group.supplier_id)"
            >
              Create PO
            </UButton>
          </div>
        </template>

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
                  :class="
                    Number(draftQuantities[keyFor(item)]) < item.moq && item.moq > 0
                      ? 'ring-2 ring-red-500'
                      : ''
                  "
                />
              </div>
              <div
                v-if="item.moq > 0"
                class="text-xs whitespace-nowrap"
                :class="
                  Number(draftQuantities[keyFor(item)]) < item.moq
                    ? 'text-red-600 dark:text-red-400 font-medium'
                    : 'text-muted'
                "
              >
                MOQ: {{ item.moq }}
              </div>
            </div>

            <UButton
              size="sm"
              variant="soft"
              @click="onUpdateQuantity(item)"
              >Update</UButton
            >
            <UButton
              size="sm"
              color="red"
              variant="ghost"
              @click="onRemoveItem(item)"
              >Remove</UButton
            >
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
