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

const loadSuppliers = async (targetPage: number = page.value) => {
  if (loading.value) return;

  loading.value = true;
  error.value = null;

  try {
    const res = await fetchSuppliers({
      search: searchQuery.value || undefined,
      supplier_type: selectedType.value || undefined,
      page: targetPage,
      page_size: pageSize,
    });

    suppliers.value = res.items || [];
    total.value = res.total;
    totalPages.value = res.total_pages;
    page.value = res.page || targetPage;
  } catch (err: any) {
    const wasAuthError = await handleAuthError(err);
    if (wasAuthError) return;
    error.value = err.message || "Failed to load suppliers";
  } finally {
    loading.value = false;
  }
};

const goToPage = (targetPage: number) => {
  if (targetPage >= 1 && targetPage <= totalPages.value && targetPage !== page.value) {
    loadSuppliers(targetPage);
  }
};

const getVisiblePages = (): number[] => {
  const current = page.value;
  const total = totalPages.value;
  const pages: number[] = [];

  if (total <= 7) {
    // Show all pages if 7 or fewer
    for (let i = 1; i <= total; i++) {
      pages.push(i);
    }
  } else {
    // Show first page, pages around current, and last page
    pages.push(1);

    if (current > 3) {
      pages.push(-1); // Ellipsis marker
    }

    const start = Math.max(2, current - 1);
    const end = Math.min(total - 1, current + 1);

    for (let i = start; i <= end; i++) {
      if (!pages.includes(i)) {
        pages.push(i);
      }
    }

    if (current < total - 2) {
      pages.push(-1); // Ellipsis marker
    }

    if (!pages.includes(total)) {
      pages.push(total);
    }
  }

  return pages;
};

let searchTimeout: ReturnType<typeof setTimeout> | null = null;
watch(searchQuery, async () => {
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    page.value = 1;
    void loadSuppliers(1);
  }, 250);
});

watch(selectedType, async () => {
  page.value = 1;
  await loadSuppliers(1);
});

const badgeColorForType = (supplierType: string) => {
  if (supplierType === "PO") return "info";
  if (supplierType === "WO") return "primary";
  return "neutral";
};

onMounted(async () => {
  await loadSuppliers(1);
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
          @click="loadSuppliers(page)"
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
                color="success"
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
              <div class="flex items-center gap-1">
                <span>MOQ:</span>
                <span class="font-medium">{{ supplier.default_moq || 0 }}</span>
                <span
                  v-if="
                    supplier.effective_moq_avg !== undefined &&
                    supplier.effective_moq_avg !== supplier.default_moq
                  "
                  class="text-primary"
                >
                  (avg: {{ supplier.effective_moq_avg }})
                </span>
                <span
                  v-if="supplier.custom_moq_count && supplier.custom_moq_count > 0"
                  class="text-blue-600"
                >
                  · {{ supplier.custom_moq_count }} custom
                </span>
              </div>
              <div class="flex items-center gap-1">
                <span>Lead:</span>
                <span class="font-medium">{{ supplier.default_lead_time_days || 14 }}d</span>
                <span
                  v-if="
                    supplier.effective_lead_time_avg !== undefined &&
                    supplier.effective_lead_time_avg !== supplier.default_lead_time_days
                  "
                  class="text-primary"
                >
                  (avg: {{ supplier.effective_lead_time_avg }}d)
                </span>
                <span
                  v-if="supplier.custom_lead_time_count && supplier.custom_lead_time_count > 0"
                  class="text-blue-600"
                >
                  · {{ supplier.custom_lead_time_count }} custom
                </span>
              </div>
              <span
                v-if="
                  supplier.default_product_count !== undefined && supplier.default_product_count > 0
                "
              >
                {{ supplier.default_product_count }} product{{
                  supplier.default_product_count !== 1 ? "s" : ""
                }}
                (default)
              </span>
            </div>
          </div>
          <UIcon
            name="i-lucide-chevron-right"
            class="size-4 text-muted"
          />
        </div>
      </UCard>

      <!-- Pagination -->
      <div
        v-if="totalPages > 1"
        class="pt-4 border-t flex items-center justify-between"
      >
        <div class="text-sm text-muted">
          Showing {{ (page - 1) * pageSize + 1 }} to {{ Math.min(page * pageSize, total) }} of
          {{ total }} suppliers
        </div>
        <div class="flex items-center gap-2">
          <UButton
            icon="i-lucide-chevron-left"
            variant="ghost"
            size="sm"
            :disabled="page <= 1 || loading"
            @click="goToPage(page - 1)"
          >
            Previous
          </UButton>
          <div class="flex items-center gap-1">
            <template
              v-for="pageNum in getVisiblePages()"
              :key="pageNum"
            >
              <span
                v-if="pageNum === -1"
                class="px-2 text-sm text-muted"
              >
                ...
              </span>
              <UButton
                v-else
                :variant="pageNum === page ? 'solid' : 'ghost'"
                size="sm"
                :disabled="loading"
                @click="goToPage(pageNum)"
              >
                {{ pageNum }}
              </UButton>
            </template>
          </div>
          <UButton
            icon="i-lucide-chevron-right"
            icon-position="right"
            variant="ghost"
            size="sm"
            :disabled="page >= totalPages || loading"
            @click="goToPage(page + 1)"
          >
            Next
          </UButton>
        </div>
      </div>
    </div>
  </div>
</template>
