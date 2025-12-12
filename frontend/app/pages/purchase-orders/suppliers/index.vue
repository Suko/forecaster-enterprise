<script setup lang="ts">
import type { Supplier } from "~/types/supplier";

definePageMeta({
  layout: "dashboard",
});

const { fetchSuppliers } = useSuppliers();
const { handleAuthError } = useAuthError();

const loading = ref(false);
const error = ref<string | null>(null);
const suppliers = ref<Supplier[]>([]);

const searchQuery = ref("");
const selectedType = ref<string | null>(null);

const page = ref(1);
const pageSize = 50;
const totalPages = ref(0);
const total = ref(0);

const typeOptions = [
  { label: "All Types", value: null },
  { label: "Purchase Orders (PO)", value: "PO" },
  { label: "Work Orders (WO)", value: "WO" },
];

const loadSuppliers = async (opts?: { reset?: boolean }) => {
  const reset = opts?.reset ?? true;
  if (loading.value) return;

  if (reset) {
    page.value = 1;
  }

  loading.value = true;
  error.value = null;

  try {
    const res = await fetchSuppliers({
      search: searchQuery.value || undefined,
      supplier_type: selectedType.value || undefined,
      page: page.value,
      page_size: pageSize,
    });

    total.value = res.total;
    totalPages.value = res.total_pages;

    if (reset) {
      suppliers.value = res.items || [];
    } else {
      suppliers.value = suppliers.value.concat(res.items || []);
    }
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    error.value = err.message || "Failed to load suppliers";
  } finally {
    loading.value = false;
  }
};

const loadMore = async () => {
  if (page.value >= totalPages.value) return;
  page.value += 1;
  await loadSuppliers({ reset: false });
};

let searchTimeout: ReturnType<typeof setTimeout> | null = null;
watch(searchQuery, async () => {
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    void loadSuppliers({ reset: true });
  }, 250);
});

watch(selectedType, async () => {
  await loadSuppliers({ reset: true });
});

const badgeColorForType = (supplierType: string) => {
  if (supplierType === "PO") return "blue";
  if (supplierType === "WO") return "purple";
  return "gray";
};

onMounted(async () => {
  await loadSuppliers({ reset: true });
});
</script>

<template>
  <div class="p-6 space-y-4">
    <div>
      <h1 class="text-3xl font-bold">Purchase Orders</h1>
      <p class="text-sm text-muted">Suppliers linked to your catalog.</p>
    </div>

    <PurchaseOrdersSectionTabs />

    <div class="flex items-center justify-between gap-3">
      <div class="text-sm text-muted">{{ total }} supplier(s)</div>
      <div class="flex items-center gap-2">
        <UInput
          v-model="searchQuery"
          icon="i-lucide-search"
          placeholder="Search suppliers..."
          class="w-64"
        />
        <USelectMenu
          v-model="selectedType"
          :options="typeOptions"
          value-attribute="value"
          option-attribute="label"
          class="w-56"
        />
        <UButton
          icon="i-lucide-refresh-cw"
          variant="ghost"
          :loading="loading"
          @click="loadSuppliers({ reset: true })"
        >
          Refresh
        </UButton>
      </div>
    </div>

    <div
      v-if="loading && suppliers.length === 0"
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
      title="Error loading suppliers"
      :description="error"
    />

    <UCard v-else-if="suppliers.length === 0">
      <div class="p-6 text-center text-muted">No suppliers found.</div>
    </UCard>

    <div
      v-else
      class="space-y-2"
    >
      <UCard
        v-for="supplier in suppliers"
        :key="supplier.id"
        class="cursor-pointer hover:shadow-sm transition-shadow"
        @click="navigateTo(`/purchase-orders/suppliers/${supplier.id}`)"
      >
        <div class="p-4 flex items-center justify-between gap-4">
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <div class="font-semibold truncate">{{ supplier.name }}</div>
              <UBadge
                :color="badgeColorForType(supplier.supplier_type)"
                variant="soft"
              >
                {{ supplier.supplier_type }}
              </UBadge>
              <UBadge
                v-if="supplier.is_synced"
                color="green"
                variant="soft"
                >Synced</UBadge
              >
            </div>
            <div class="text-sm text-muted truncate">
              {{ supplier.contact_email || "No email" }}
            </div>
            <div
              v-if="supplier.contact_phone"
              class="text-xs text-muted"
            >
              {{ supplier.contact_phone }}
            </div>
            <div class="flex items-center gap-4 mt-2 text-xs text-muted">
              <span>MOQ: {{ supplier.default_moq || 0 }}</span>
              <span>Lead: {{ supplier.default_lead_time_days || 14 }}d</span>
            </div>
          </div>
          <UIcon
            name="i-lucide-chevron-right"
            class="size-4 text-muted"
          />
        </div>
      </UCard>

      <div
        v-if="page < totalPages"
        class="pt-2"
      >
        <UButton
          :loading="loading"
          variant="soft"
          block
          @click="loadMore"
        >
          Load more
        </UButton>
      </div>
    </div>
  </div>
</template>
