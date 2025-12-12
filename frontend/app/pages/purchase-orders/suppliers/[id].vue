<script setup lang="ts">
import type { Supplier } from "~/types/supplier";
import type { Product, ProductListResponse } from "~/types/product";

definePageMeta({
  layout: "dashboard",
});

const route = useRoute();
const supplierId = computed(() => String(route.params.id || ""));

const { fetchSupplier } = useSuppliers();
const { handleAuthError } = useAuthError();

const loading = ref(false);
const error = ref<string | null>(null);
const supplier = ref<Supplier | null>(null);

const productsLoading = ref(false);
const productsError = ref<string | null>(null);
const products = ref<Product[]>([]);

const badgeColorForType = (supplierType: string) => {
  if (supplierType === "PO") return "blue";
  if (supplierType === "WO") return "purple";
  return "gray";
};

const loadSupplier = async () => {
  if (!supplierId.value) return;
  loading.value = true;
  error.value = null;
  try {
    supplier.value = await fetchSupplier(supplierId.value);
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    error.value = err.message || "Failed to load supplier";
  } finally {
    loading.value = false;
  }
};

const loadProducts = async () => {
  if (!supplierId.value) return;
  productsLoading.value = true;
  productsError.value = null;
  try {
    const res = await $fetch<ProductListResponse>("/api/products", {
      query: {
        page: 1,
        page_size: 50,
        supplier_id: supplierId.value,
      },
    });
    products.value = res.items || [];
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    productsError.value = err.message || "Failed to load products";
  } finally {
    productsLoading.value = false;
  }
};

onMounted(async () => {
  await loadSupplier();
  await loadProducts();
});
</script>

<template>
  <div class="p-6 space-y-4">
    <div>
      <h1 class="text-3xl font-bold">Purchase Orders</h1>
      <p v-if="supplier" class="text-sm text-muted">{{ supplier.name }}</p>
    </div>

    <PurchaseOrdersSectionTabs />

    <div class="flex items-center justify-end gap-2">
      <UButton icon="i-lucide-arrow-left" variant="ghost" @click="navigateTo('/purchase-orders/suppliers')">
        Back
      </UButton>
      <UButton icon="i-lucide-refresh-cw" variant="ghost" :loading="loading" @click="loadSupplier">
        Refresh
      </UButton>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-12">
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin text-primary" />
    </div>

    <UAlert v-else-if="error" color="error" variant="soft" title="Error loading supplier" :description="error" />

    <div v-else-if="supplier" class="space-y-4">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <h2 class="text-lg font-semibold">{{ supplier.name }}</h2>
              <UBadge :color="badgeColorForType(supplier.supplier_type)" variant="soft">
                {{ supplier.supplier_type }}
              </UBadge>
              <UBadge v-if="supplier.is_synced" color="green" variant="soft">Synced</UBadge>
            </div>
            <div class="flex items-center gap-2">
              <UButton
                icon="i-lucide-receipt"
                variant="soft"
                @click="navigateTo({ path: '/purchase-orders', query: { supplier_id: supplier.id } })"
              >
                Orders
              </UButton>
              <UButton
                icon="i-lucide-package"
                variant="soft"
                @click="navigateTo({ path: '/inventory', query: { supplier_id: supplier.id } })"
              >
                Inventory
              </UButton>
            </div>
          </div>
        </template>

        <div class="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-muted">Contact</div>
            <div class="text-sm mt-1">
              <div>{{ supplier.contact_email || 'No email' }}</div>
              <div v-if="supplier.contact_phone">{{ supplier.contact_phone }}</div>
            </div>
          </div>
          <div>
            <div class="text-xs text-muted">External ID</div>
            <div class="text-sm mt-1">{{ supplier.external_id || '—' }}</div>
          </div>
          <div class="md:col-span-2">
            <div class="text-xs text-muted">Address</div>
            <div class="text-sm mt-1 whitespace-pre-line">{{ supplier.address || '—' }}</div>
          </div>
          <div class="md:col-span-2">
            <div class="text-xs text-muted">Notes</div>
            <div class="text-sm mt-1 whitespace-pre-line">{{ supplier.notes || '—' }}</div>
          </div>
        </div>
      </UCard>

      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold">Products (first 50)</h2>
            <UButton icon="i-lucide-refresh-cw" variant="ghost" :loading="productsLoading" @click="loadProducts">
              Refresh
            </UButton>
          </div>
        </template>

        <div v-if="productsLoading" class="p-6 flex items-center justify-center">
          <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-primary" />
        </div>
        <UAlert
          v-else-if="productsError"
          color="error"
          variant="soft"
          title="Error loading products"
          :description="productsError"
        />
        <div v-else-if="products.length === 0" class="p-6 text-center text-muted">No products linked.</div>
        <div v-else class="divide-y">
          <div v-for="p in products" :key="p.item_id" class="py-3 flex items-center justify-between gap-4">
            <div class="min-w-0">
              <div class="font-medium truncate">{{ p.product_name }}</div>
              <div class="text-xs text-muted">{{ p.item_id }} · {{ p.category || 'Uncategorized' }}</div>
            </div>
            <UButton size="sm" variant="soft" @click="navigateTo({ path: '/inventory', query: { item: p.item_id } })">
              View
            </UButton>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>

